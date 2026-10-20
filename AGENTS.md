# AGENTS.md — guide for coding agents and contributors

## Repo map
```
run.sh                  launcher: picks bin/<OS>-<arch>, builds run/flash.bin, starts QEMU (native|sdl|headless|web)
patches/000N-*.patch    QEMU patches (git format-patch, apply in order on espressif/qemu esp-develop-9.2.2-20260417)
scripts/build-*.sh      clone + patch + configure + build QEMU, install into bin/<OS>-<arch>/
scripts/bundle-*.{sh,py} make the binary relocatable (Linux: $ORIGIN/lib RPATH; macOS: @executable_path + codesign)
scripts/fetch-firmware.sh  download + sha256-verify the official factory image into firmware/
scripts/make-release.sh build release archives into dist/
web/server.py           web UI backend (stdlib only): QEMU lifecycle, QMP, SSE serial, HTTP API
web/index.html          single-file web UI (no CDN, no build step)
tools/qmp.py            QMP CLI: shot/key/tap/swipe/qom-set
tools/serial.py         raw TCP serial client for --serial-tcp
firmware/               firmware images (.bin are git-ignored except uart-echo-test.bin) + uart-echo-test source
bin/<OS>-<arch>/        prebuilt qemu-system-xtensa + lib/ + esp32s3_rev0_rom.bin (git-ignored, shipped in releases)
docs/                   ARCHITECTURE.md, images/
run/                    runtime state (flash.bin, qmp.sock, logs) — git-ignored
```

## Build / test
```bash
scripts/build-linux.sh            # or scripts/build-macos.sh ; incremental: re-run, only ninja runs
BUNDLE=1 scripts/build-linux.sh   # relocatable Linux bundle
./run.sh --headless               # boot factory fw; expect "Project name: StopWatch-UserDemo" then "[Launcher] on create"
./run.sh --headless --fw uart-echo-test.bin --serial-tcp 5555 &   python3 tools/serial.py 5555
```

Headless smoke test (no display, scriptable):
```bash
./run.sh --headless > run/log.txt 2>&1 &
sleep 20; grep -q "Launcher\] on create" run/log.txt
python3 tools/qmp.py run/qmp.sock shot run/a.png key b sleep 1 shot run/b.png
python3 tools/qmp.py run/qmp.sock qom-set /machine/m5pm1 vbat-mv 3500
```
Web: `./run.sh --web --port 8466 &` then `curl -s localhost:8466/api/state`, `curl -o f.png localhost:8466/frame.png`,
`curl -XPOST -d '{"accel-x":0.5}' localhost:8466/api/sensor`. Screenshots: headless Chrome against the web UI.

## Patch workflow
1. Work in the QEMU checkout `build/qemu` (created by the build script; patches are committed there by `git am`).
2. Edit, rebuild with `ninja -C build/qemu/build qemu-system-xtensa`, test.
3. Commit in `build/qemu` (one logical change per commit, subject `hw/...: ...`), then
   `git -C build/qemu format-patch -1 -o ../../patches --start-number N` (keep numbering contiguous).
4. Build scripts skip patches whose subject already exists in `git log`, so re-running is safe.

## Adding a device model
* I2C slave: new file in `hw/misc/` (or `hw/sensor/`) deriving `TYPE_I2C_SLAVE`; implement `event/recv/send`;
  register in `hw/misc/meson.build` + `Kconfig` (`select` from `M5STOPWATCH`).
* Instantiate in `hw/xtensa/m5stopwatch.c` with `i2c_slave_create_simple(bus, TYPE, addr)` and
  `object_property_add_child(machine, "name", ...)` so it is reachable at `/machine/name` for QMP.
* Expose live values as QOM properties (`object_class_property_add`, see bmi270 / m5pm1 in patch 0005) and,
  if the web UI should drive them, add them to `SENS_PATH` and `SENS` (defaults) in `web/server.py` and a control in `web/index.html`.
* Register maps: take them from the M5Stack driver sources / datasheets; log unknown accesses with
  `qemu_log_mask(LOG_UNIMP, ...)`.

## Conventions
* QEMU code: QEMU coding style (4 spaces, `/* */`), SPDX `GPL-2.0-or-later` header in new files.
* Scripts/tools: bash with `set -euo pipefail`, python3 stdlib only, SPDX `MIT` header, executable bit set.
* No external CDN or npm in the web UI. Keep `index.html` single-file.
* Never commit firmware images other than our own, run/ artifacts, or binaries (bin/ goes in releases).
* Times in logs are host time; the guest RTC is UTC.
