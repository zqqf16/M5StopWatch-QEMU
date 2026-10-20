# Changelog

## 0.1.0 — 2026-10-20
First public release.
* QEMU machine `m5stopwatch` (patches 0001–0005 on espressif/qemu esp-develop-9.2.2-20260417): octal PSRAM,
  I2C master, GP-SPI2/GDMA, CO5300 QSPI display + TE, M5PM1, M5IOE1, CST820, BMI270, RX8130, ES8311 ID.
* Live sensor QOM properties (BMI270 accel/gyro, M5PM1 VBAT/VIN/charging).
* `run.sh`: native/SDL/headless/web, `--fw`, `--reset`, `--serial-tcp`, `--list`, OS/arch binary selection.
* Web UI: device frame, HUD, serial console (SSE), IMU/battery controls with charts and 3D cube,
  firmware select/upload/`?fw=`, shortcuts and command palette.
* License: project code MIT; QEMU patches and binaries GPL-2.0-or-later; THIRD_PARTY_NOTICES.md.
* Portable prebuilt binaries: macOS arm64 (bundled dylibs, ad-hoc signed), Linux x86_64 (glibc ≥ 2.35, bundled libs).
* `scripts/fetch-firmware.sh` for the official factory firmware; `uart-echo-test` sample firmware.
