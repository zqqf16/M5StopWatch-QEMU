# M5StopWatch-QEMU

[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE) [![QEMU patches: GPL-2.0-or-later](https://img.shields.io/badge/QEMU%20patches%20%26%20binaries-GPL--2.0--or--later-orange.svg)](LICENSES/GPL-2.0.txt) ![platforms](https://img.shields.io/badge/prebuilt-macOS%20arm64%20%7C%20Linux%20x86__64-informational)

Run the **unmodified** [M5Stack StopWatch](https://docs.m5stack.com/) factory firmware (ESP32-S3,
CO5300 466×466 AMOLED) in QEMU — with display, buttons, touch, IMU, battery, serial console and a
web UI. No hardware needed.

[中文说明 / Chinese README](README.zh-CN.md)

![web UI](docs/images/web-ui.png)

| launcher | watch face | IMU app (accel set over QMP) |
|---|---|---|
| ![](docs/images/launcher.png) | ![](docs/images/watchface.png) | ![](docs/images/imu-app.png) |

## Features

* New QEMU machine `-M m5stopwatch` on top of Espressif's QEMU fork (5 patches, see [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)):
  octal PSRAM, ESP32-S3 I2C master, GP-SPI2 + GDMA, CO5300 QSPI panel, TE, M5PM1 PMIC, M5IOE1 IO expander,
  CST820 touch, BMI270 IMU, RX8130 RTC, ES8311 (ID only).
* Boots the official factory image byte-for-byte: guide → launcher → watch face, stopwatch, IMU, … all work.
* Keys A / B / power, A+B long press, mouse = touch.
* **Live sensors over QMP**: accelerometer/gyroscope (g, °/s), battery voltage, USB/VIN, charging.
* **Web UI** (`./run.sh --web`, Python stdlib only, works offline): device frame with clickable keys,
  HUD (state, uptime, boot #, firmware + sha256, fps, QMP latency), colourised serial console with filter and
  input, IMU sliders + drag-to-tilt + presets + oscilloscope + 3D orientation cube, battery gauge and chart,
  firmware selector / upload / `?fw=`, keyboard shortcuts (`?`) and a command palette (`Ctrl+K`).
* Prebuilt, self-contained binaries for **macOS arm64** and **Linux x86_64** (no Homebrew / no apt packages needed).

## Quick start

Download a release archive for your platform, unpack, then:

```bash
./run.sh                 # native window (Cocoa on macOS, SDL on Linux); serial log in this terminal
./run.sh --web           # open http://127.0.0.1:8466   (needs python3)
./run.sh --headless      # no display; serial in terminal, QMP at run/qmp.sock
```

On first start `run.sh` downloads the official factory firmware (`scripts/fetch-firmware.sh`, sha256-checked)
from the [M5StopWatch-UserDemo releases](https://github.com/m5stack/M5StopWatch-UserDemo/releases).
On macOS, `run.sh` removes the download quarantine flag from `bin/Darwin-arm64` automatically (binaries are
ad-hoc signed).

Requirements: macOS 26+ on Apple Silicon, or Linux x86_64 with glibc ≥ 2.35 (Ubuntu 22.04+, Debian 12+).
`python3` only for `--web` and the helper tools. Other platforms: build from source (below).

### CLI

| option | meaning |
|---|---|
| *(none)* / `--sdl` | native Cocoa window (macOS) / SDL window |
| `--web [--port N]` | web UI (QEMU managed by `web/server.py`) |
| `--headless` | `-display none` |
| `--fw FILE.bin` | firmware: name in `firmware/` or any path to a merged 0x0 image (≤ 16 MB) |
| `--reset` | recreate the flash image (erases NVS / settings → guide screen again) |
| `--serial-tcp PORT` | UART0 on `tcp:127.0.0.1:PORT` (client: `python3 tools/serial.py PORT`) |
| `--list` | list firmware |
| env `QEMU=`, `ROMDIR=` | use another QEMU binary / ROM directory |

Keys: `A`/`←` KEYA (yellow), `B`/`→` KEYB (blue), `P` power, hold A+B ≈ 2 s = home. Mouse = touch.
Default mode: `Ctrl-A X` quits, `Ctrl-A C` toggles the QEMU monitor.

## Web UI

`./run.sh --web` starts `web/server.py`, which owns the QEMU process:

* firmware switch / upload / reset = full QEMU teardown and a **fresh 16 MB flash** built from the chosen bin;
  `?fw=name.bin` in the URL boots that image; all responses are `no-store`.
* UART0 is streamed via Server-Sent Events from the very first ROM line; input is written to UART0.
* Sensor values are re-applied after every boot.

| | |
|---|---|
| ![](docs/images/web-serial.png) | ![](docs/images/web-power.png) |

HTTP API (JSON): `GET /api/state`, `GET /api/ping`, `GET /frame.png` (ETag/304), `GET /api/serial` (SSE),
`GET /api/log`, `POST /api/serial` (raw bytes), `POST /input` (`{"t":"key","k":["a"],"d":1}` /
`{"t":"touch","x":233,"y":233,"d":1}`), `POST /api/sensor` (`{"accel-x":0.5,"vbat-mv":3600}`),
`POST /api/switch` (`{"fw":"name.bin"}`), `POST /api/reset`, `POST /api/upload?name=x.bin` (body = image).

## Sensors / QMP API

| QOM path | property | unit | default |
|---|---|---|---|
| `/machine/bmi270` | `accel-x`, `accel-y`, `accel-z` | g (sensor frame) | 0, 0, 1 |
| `/machine/bmi270` | `gyro-x`, `gyro-y`, `gyro-z` | °/s | 0 |
| `/machine/m5pm1` | `vbat-mv`, `vin-mv`, `vinout-mv` | mV | 4000, 5000, 5000 |
| `/machine/m5pm1` | `charging` | bool | false |

```bash
# QEMU monitor (Ctrl-A C in default mode)
(qemu) qom-set /machine/bmi270 accel-x 0.5
(qemu) qom-set /machine/m5pm1 vbat-mv 3500
# QMP
python3 tools/qmp.py run/qmp.sock shot a.png key b sleep 1 tap 233 233 swipe 380 233 80 233
{"execute":"qom-set","arguments":{"path":"/machine/m5pm1","property":"charging","value":true}}
```

The factory firmware maps VBAT 3.3 V → 0 %, 4.2 V → 100 % (with a slow low-pass filter); USB present = VIN > 4 V.
Its IMU app reads accel X/Y swapped (as on the real device).

## Firmware

| file | source | bundled |
|---|---|---|
| `C152-StopWatch-UserDemo-V0.5-20260528_0x0.bin` | official factory image, [m5stack/M5StopWatch-UserDemo](https://github.com/m5stack/M5StopWatch-UserDemo) (MIT) | downloaded by `scripts/fetch-firmware.sh` |
| `uart-echo-test.bin` | this repo, `firmware/uart-echo-test/` (ESP-IDF 5.5), echoes each UART line upper-cased | yes |

Any merged ESP32-S3 image starting at 0x0 (byte 0 = 0xE9, ≤ 16 MB) can be dropped into `firmware/` or uploaded
from the web UI. Images that need Wi-Fi/BLE/audio or hardware not modelled here may stall.

## Limitations

* No Wi-Fi/BLE (no RF in QEMU), no I2S audio (ES8311 answers ID only), no BMM150 magnetometer, no BMI270
  feature engine (steps/gestures).
* GPIO interrupts are not modelled (the firmware polls the keys).
* Battery is not simulated — the voltage is whatever you set.
* RTC follows host UTC (firmware default time zone GMT0).
* TCG emulation: roughly real-time, not cycle-accurate. Web display is PNG polling (~12–15 fps when the screen changes).

## Building from source

```bash
scripts/build-macos.sh            # Homebrew deps; output bin/Darwin-<arch>/ with bundled dylibs, ad-hoc signed
scripts/build-macos.sh --no-brew  # build libgcrypt/libgpg-error locally, don't touch Homebrew
scripts/build-linux.sh            # apt deps; output bin/Linux-<arch>/
BUNDLE=1 scripts/build-linux.sh   # relocatable bundle (build on Ubuntu 22.04 for glibc 2.35 compatibility)
scripts/make-release.sh 0.1.0     # release archives into dist/
```

The scripts clone `espressif/qemu` at the pinned tag into `build/qemu`, apply every `patches/*.patch` not
yet applied (`git am`), configure a minimal `xtensa-softmmu` build and install into `bin/<OS>-<arch>/`.
See [AGENTS.md](AGENTS.md) for the development workflow and [CONTRIBUTING.md](CONTRIBUTING.md).

## License

* **This project's own code is MIT** — `run.sh`, `scripts/`, `web/`, `tools/`, `firmware/uart-echo-test/`, docs. See [LICENSE](LICENSE).
* **Exceptions (GPL-2.0-or-later):** `patches/*.patch` are modifications of QEMU, and the prebuilt
  `bin/*/qemu-system-xtensa` binaries in the release archives are QEMU builds; both are GPL-2.0-or-later
  ([LICENSES/GPL-2.0.txt](LICENSES/GPL-2.0.txt)). Corresponding source: espressif/qemu tag
  `esp-develop-9.2.2-20260417` + `patches/` + build scripts (also attached to each release as `-src.zip`).
* **Bundled libraries** (glib, SDL, pixman, libpng, …) keep their own licenses (LGPL-2.1, Zlib, MIT, BSD, …) —
  full list with versions, sources and the written source offer in [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).
* **Espressif ROM** — `bin/*/esp32s3_rev0_rom.bin` is the ESP32-S3 mask-ROM image, © Espressif Systems (Shanghai)
  Co., Ltd., redistributed unmodified exactly as Espressif ships it with
  [espressif/qemu releases](https://github.com/espressif/qemu/releases) (`pc-bios/`); the matching ROM ELFs are
  published in [espressif/esp-rom-elfs](https://github.com/espressif/esp-rom-elfs).
* **M5Stack factory firmware** is © M5Stack (MIT) and is **not** included; `scripts/fetch-firmware.sh` downloads it from the official release.

## Acknowledgements

* [Espressif QEMU](https://github.com/espressif/qemu) (GPL-2.0) — ESP32-S3 SoC model this builds on.
* [M5Stack](https://github.com/m5stack/M5StopWatch-UserDemo) — StopWatch hardware, factory firmware and
  driver sources used as the register-map reference (MIT).
* QEMU project and the libraries above.

This project is not affiliated with M5Stack or Espressif.
