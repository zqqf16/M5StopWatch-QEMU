# firmware/

* `uart-echo-test.bin` — built from `uart-echo-test/` (ESP-IDF 5.5, `idf.py build && esptool.py merge_bin -o ../uart-echo-test.bin ...`).
  Prints a banner and echoes each UART0 line upper-cased. MIT.
* Official factory firmware: run `../scripts/fetch-firmware.sh` (done automatically by `run.sh`). It downloads
  `C152-StopWatch-UserDemo-V0.5-20260528_0x0.bin` from the
  [M5StopWatch-UserDemo V0.5 release](https://github.com/m5stack/M5StopWatch-UserDemo/releases) and checks its sha256.
  © M5Stack, MIT; contains ESP-IDF (Apache-2.0), LVGL (MIT) and other components under their licenses.

Put other merged ESP32-S3 images (offset 0x0, ≤ 16 MB) here; `*.bin` is git-ignored.
