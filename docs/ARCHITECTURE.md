# Architecture

M5StopWatch-QEMU runs the **unmodified** M5Stack StopWatch firmware (ESP32-S3R8, 16 MB flash,
8 MB octal PSRAM, CO5300 466×466 QSPI AMOLED) on Espressif's QEMU fork
([espressif/qemu](https://github.com/espressif/qemu), tag `esp-develop-9.2.2-20260417`).
Everything board-specific lives in five patches under `patches/`, which add a new machine
`-M m5stopwatch` on top of the upstream `esp32s3` SoC model.

```
 firmware (merged 0x0 image, padded to 16 MB) ──► -drive if=mtd ──► ESP32-S3 SPI flash/MMU (upstream)
                                                                    │
           ┌────────────────────────── m5stopwatch machine ────────┴──────────────────────────────┐
           │ ssi_psram (octal, 8 MB)          upstream, fixed by 0001                               │
           │ GPIO matrix                     0003: real register file, W1TS/W1TC, IN = OUT|ext       │
           │ I2C0 @0x60013000 (new, 0004) ─┬─ M5PM1  0x6E  PMIC: VBAT/VIN/5VINOUT, CHG_STAT, PWR key  │
           │                               ├─ M5IOE1 0x4F  IO expander (GPIO_IN mirrors GPIO_OUT)   │
           │                               ├─ CST820 0x15  touch  ◄── QEMU mouse (abs)              │
           │                               ├─ BMI270 0x68  IMU    ◄── QOM accel-*/gyro-* (0005)     │
           │                               ├─ RX8130 0x32  RTC (host UTC + offset, writable)        │
           │                               └─ ES8311 0x18  codec (ID registers only)                │
           │ GP-SPI2 @0x60024000 (new, 0004) + GDMA out-link ──► CO5300 panel ──► QEMU console      │
           │ TE pulse on GPIO38 (~60 Hz)      keyboard ──► KEYA (GPIO2) / KEYB (GPIO1) / PWR (M5PM1)│
           └──────────────────────────────────────────────────────────────────────────────────────┘
 host side:  run.sh ── QEMU ── QMP (unix socket) ── web/server.py ── browser (web/index.html)
                         └──── UART0 (chardev socket / stdio / tcp) ──┘
```

## Patches

| patch | what | why |
|---|---|---|
| 0001 `ssi_psram` | ignore out-of-range (negative) addresses | flash and PSRAM share SPI1; stray accesses crashed QEMU |
| 0002 `ui` PPM screendump | correct stride when `3*width % 4 != 0` | 466-px-wide console was sheared |
| 0003 `esp32_gpio` | functional GPIO register file: OUT/ENABLE + W1TS/W1TC, IN computed from outputs and external inputs (pull-up default 1), output-change listeners | buttons, software chip-select of the panel, TE |
| 0004 `m5stopwatch` machine | `hw/m5stopwatch/*`: S3 I2C master, six I2C slave models, GP-SPI2 + GDMA, CO5300 panel, input handler, octal PSRAM wiring | the board itself |
| 0005 sensor QOM properties | live `qom-set`-able values for BMI270 / M5PM1, data-ready bits, stable `/machine/<model>` paths | IMU and battery from the web UI / QMP |

## Display: CO5300 over QSPI (`co5300.c`, `esp32s3_gpspi.c`)

* The firmware drives the panel through **GP-SPI2** in QSPI mode with DMA. The model implements the
  SPI2 user registers (USER/USER1/USER2/MS_DLEN/W0–W15, command/address/MOSI phases) and walks the
  **GDMA out-link descriptor chain**, including chains that continue across several SPI transactions and
  buffers located in PSRAM. QSPI 4-line mode does not change the byte stream, so it is transparent.
* Transactions are framed by the **software chip-select on GPIO39** (observed via the 0003 GPIO listener).
* The byte stream is parsed as CO5300 commands: `0x02 00 <cmd> 00 + params` for register writes
  (CASET/RASET/MADCTL/COLMOD/0x51 brightness/display on-off/sleep/invert) and `0x32|0x12 00 2C|3C 00 + RGB565`
  for pixel writes. GRAM is 480×480; the visible window is 466×466 with column offset 6 (matching the
  firmware's `offset_x = 6`). Brightness (0x51) scales the output. The panel is a QEMU graphic console,
  so `screendump`, Cocoa, SDL all work.
* **TE** (tearing effect) on GPIO38: a ~60 Hz timer pulses the input high for 0.5 ms; LVGL's flush waits on it.

## I2C (`esp32s3_i2c.c`, `m5sw_i2c_devs.c`)

* ESP32-S3 I2C master at 0x60013000: COMD0–7 command list, TX/RX FIFO, START/WRITE/READ/STOP/END,
  repeated start, NACK detection, interrupts. (Upstream `esp32s3` has no I2C controller; the firmware loops
  on `probe device timeout` without it.)
* All slaves share one generic register-file device (`M5SW_I2C_DEV`, property `model=`), with per-model
  read/write hooks. Register maps come from the firmware sources (`components/M5PM1`, `M5IOE1`, `main/hal/drivers`).
* **M5PM1** PMIC: IDs, VREF, `VBAT_L/H` 0x22, `VIN_L/H` 0x24, `5VINOUT_L/H` 0x26 (mV, from QOM properties),
  `GPIO_IN` 0x12 bit2 = CHG_STAT (low = charging), `BTN_STATUS` 0x48 bit0 = power key.
* **M5IOE1** IO expander: UID/revision accepted by the driver; `GPIO_IN` reads back `GPIO_OUT` for outputs, 1 for inputs.
* **CST820** touch: chip id, finger count, event and 12-bit X/Y from the QEMU absolute mouse.
* **BMI270**: chip id 0x24, soft reset, config-file upload (`INIT_DATA` burst without auto-increment),
  `INTERNAL_STATUS` = init OK, `STATUS`/`INT_STATUS_1` data-ready, ACC/GYR data registers computed at read time
  from the `accel-*`(g)/`gyro-*`(°/s) properties using the range the firmware programmed (ACC_RANGE 0x41, GYR_RANGE 0x43).
* **RX8130CE** RTC: BCD time = host UTC + offset; writing the time registers sets the offset.
* **ES8311**: chip id registers only (no I2S/audio path).

## Input

`co5300.c` registers a QEMU input handler: keys `A`/`Left` → KEYA (GPIO2, active low), `B`/`Right` → KEYB (GPIO1),
`P` → M5PM1 power-key bit; absolute mouse → CST820 coordinates in panel pixels (0..465).
The web UI sends the same events through QMP `input-send-event`.

## Host tools

* `run.sh` — picks `bin/<OS>-<arch>/`, pads the firmware to a 16 MB flash image (`run/flash.bin`, kept per firmware
  sha256 so NVS survives restarts), starts QEMU with QMP at `run/qmp.sock`.
* `web/server.py` — stdlib HTTP server that owns the QEMU process: restarts it on firmware switch (fresh flash),
  streams UART0 over SSE from a `wait=on` unix-socket chardev (no boot output lost), relays input and sensor
  values over QMP, serves frames from `screendump` with ETag/304.
* `tools/qmp.py` (scriptable screenshots/keys/touch), `tools/serial.py` (TCP/unix serial client).
