#!/usr/bin/env bash
# SPDX-License-Identifier: MIT
# Download the official M5Stack StopWatch factory firmware (MIT, github.com/m5stack/M5StopWatch-UserDemo)
# into firmware/. Third-party firmware is not redistributed here; drop your own merged 0x0 .bin files
# into firmware/ (or upload them from the web UI).
set -euo pipefail
HERE="$(cd "$(dirname "$0")/.." && pwd)"
NAME=C152-StopWatch-UserDemo-V0.5-20260528_0x0.bin
URL=https://github.com/m5stack/M5StopWatch-UserDemo/releases/download/V0.5/$NAME
SHA256=6395799089341e0ae96072c2a3418d469d6797b2ab8ee0cab1c9ed24a42acbbe
OUT="$HERE/firmware/$NAME"
mkdir -p "$HERE/firmware"
if [ ! -f "$OUT" ]; then
  echo "downloading $URL"
  if command -v curl >/dev/null; then curl -fL --retry 3 -o "$OUT.part" "$URL"
  elif command -v wget >/dev/null; then wget -O "$OUT.part" "$URL"
  else echo "error: need curl or wget" >&2; exit 1; fi
  mv "$OUT.part" "$OUT"
fi
got=$( (command -v sha256sum >/dev/null && sha256sum "$OUT" || shasum -a 256 "$OUT") | cut -d' ' -f1)
[ "$got" = "$SHA256" ] || { echo "error: sha256 mismatch for $OUT ($got)" >&2; exit 1; }
echo "ok: $OUT"
