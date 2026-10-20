#!/usr/bin/env bash
# SPDX-License-Identifier: MIT
# Run M5Stack StopWatch firmware (default: the official factory image) on the patched QEMU.
#
#   ./run.sh                   native window (Cocoa on macOS, SDL on Linux), serial on this terminal
#   ./run.sh --sdl             SDL window
#   ./run.sh --web [--port N]  web UI at http://127.0.0.1:8466 (needs python3)
#   ./run.sh --headless        no display; serial on this terminal, QMP at run/qmp.sock
#   ./run.sh --fw FILE.bin     merged 0x0 image (name in firmware/ or any path)
#   ./run.sh --reset           re-create the 16 MB flash image (erases NVS/settings)
#   ./run.sh --serial-tcp 5555 UART0 on tcp 127.0.0.1:5555 (client: python3 tools/serial.py 5555)
#   ./run.sh --list            list firmware/*.bin
#
# Env: QEMU=/path/to/qemu-system-xtensa  ROMDIR=dir containing esp32s3_rev0_rom.bin
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
for a in "$@"; do [ "$a" = -h ] || [ "$a" = --help ] && { sed -n '3,14p' "$0" | sed 's/^# \{0,1\}//'; exit 0; }; done

os="$(uname -s)"; arch="$(uname -m)"
case "$os-$arch" in
  Darwin-arm64|Darwin-x86_64|Linux-x86_64|Linux-aarch64) PLAT="$os-$arch";;
  Linux-arm64) PLAT="Linux-aarch64";;
  *) PLAT="$os-$arch";;
esac
BINDIR="$HERE/bin/$PLAT"
QEMU="${QEMU:-$BINDIR/qemu-system-xtensa}"
ROMDIR="${ROMDIR:-$(dirname "$QEMU")}"
if [ ! -x "$QEMU" ]; then
  echo "error: no QEMU binary for $PLAT (looked for $QEMU)." >&2
  echo "       prebuilt: Darwin-arm64, Linux-x86_64. Otherwise build one:" >&2
  echo "       scripts/build-linux.sh  or  scripts/build-macos.sh   (or set QEMU=/path/to/qemu-system-xtensa)" >&2
  exit 1
fi
[ -f "$ROMDIR/esp32s3_rev0_rom.bin" ] || { echo "error: $ROMDIR/esp32s3_rev0_rom.bin missing (set ROMDIR=)" >&2; exit 1; }
if [ "$os" = Darwin ] && command -v xattr >/dev/null; then
  xattr -dr com.apple.quarantine "$(dirname "$QEMU")" 2>/dev/null || true   # unsigned download -> Gatekeeper
fi

DEFFW=C152-StopWatch-UserDemo-V0.5-20260528_0x0.bin
FW="${FW:-$HERE/firmware/$DEFFW}"
RUN="$HERE/run"; mkdir -p "$RUN"
MODE=native; RESET=0; SERTCP=""; PORT=8466
while [ $# -gt 0 ]; do case "$1" in
  --sdl) MODE=sdl;; --web) MODE=web;; --headless) MODE=headless;; --reset) RESET=1;;
  --fw) FW="$2"; shift;; --serial-tcp) SERTCP="$2"; shift;; --port) PORT="$2"; shift;;
  --list) (cd "$HERE/firmware" && ls -1 *.bin uploads/*.bin 2>/dev/null) || true; exit 0;;
  -h|--help) sed -n '3,14p' "$0" | sed 's/^# \{0,1\}//'; exit 0;;
  *) echo "unknown option $1 (see --help)" >&2; exit 1;; esac; shift; done
[ -f "$FW" ] || [ ! -f "$HERE/firmware/$FW" ] || FW="$HERE/firmware/$FW"
if [ ! -f "$FW" ]; then
  if [ "$(basename "$FW")" = "$DEFFW" ]; then "$HERE/scripts/fetch-firmware.sh"
  else echo "error: firmware not found: $FW" >&2; exit 1; fi
fi

if [ "$MODE" = web ]; then
  command -v python3 >/dev/null || { echo "error: --web needs python3" >&2; exit 1; }
  exec python3 -u "$HERE/web/server.py" --qemu "$QEMU" --rom-dir "$ROMDIR" --fw "$FW" --port "$PORT"
fi

sha256() { if command -v sha256sum >/dev/null; then sha256sum "$1"; else shasum -a 256 "$1"; fi | cut -d' ' -f1; }
SHA="$(sha256 "$FW")"
SIZE=$(wc -c < "$FW" | tr -d ' '); FLASH=$((16 * 1024 * 1024))
[ "$SIZE" -le "$FLASH" ] || { echo "error: image larger than 16 MB" >&2; exit 1; }
# flash image persists (NVS/settings) per firmware; rebuilt on --reset or when the firmware changes
if [ ! -f "$RUN/flash.bin" ] || [ $RESET = 1 ] || [ "$(cat "$RUN/flash.sha" 2>/dev/null)" != "$SHA" ]; then
  cp "$FW" "$RUN/flash.bin.tmp"
  head -c $((FLASH - SIZE)) /dev/zero | LC_ALL=C tr '\000' '\377' >> "$RUN/flash.bin.tmp"   # pad with 0xFF
  mv "$RUN/flash.bin.tmp" "$RUN/flash.bin"; echo "$SHA" > "$RUN/flash.sha"
  echo "flash image: $RUN/flash.bin (16 MB, fresh)"
fi
echo "firmware: $(basename "$FW")  sha256 ${SHA:0:16}  qemu: $QEMU"
case "$MODE" in
  native) if [ "$os" = Darwin ]; then DISP=(-display cocoa,zoom-to-fit=on); else DISP=(-display sdl); fi;;
  sdl) DISP=(-display sdl);;
  headless) DISP=(-display none);;
esac
if [ -n "$SERTCP" ]; then
  SER=(-serial "tcp:127.0.0.1:$SERTCP,server=on,wait=off"); echo "serial: tcp 127.0.0.1:$SERTCP -> python3 tools/serial.py $SERTCP"
else
  SER=(-serial mon:stdio); echo "serial: this terminal (Ctrl-A X quit, Ctrl-A C QEMU monitor)"
fi
QMP="$RUN/qmp.sock"; rm -f "$QMP"
echo "keys: A/Left = KEYA, B/Right = KEYB, P = PWR, mouse = touch, A+B long press = home"
exec "$QEMU" -M m5stopwatch -drive file="$RUN/flash.bin",if=mtd,format=raw -L "$ROMDIR" \
     -qmp unix:"$QMP",server=on,wait=off "${DISP[@]}" "${SER[@]}"
