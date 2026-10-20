#!/usr/bin/env bash
# SPDX-License-Identifier: MIT
# Make a relocatable Linux qemu-system-xtensa: copy every shared library it needs
# (except the glibc core, which must come from the host) into OUT/lib.
#
# The executable must be linked with  -Wl,--disable-new-dtags,-rpath,$ORIGIN/lib
# (scripts/build-linux.sh does this when BUNDLE=1). DT_RPATH (not RUNPATH) also covers the
# libraries' own dependencies, so the bundled .so files need no patching. (patchelf-edited
# executables misbehaved, hence link-time rpath. Note: $ORIGIN needs /proc mounted.)
# Build on an OLD distro (e.g. Ubuntu 22.04 / glibc 2.35) so the result runs on that glibc or newer.
#
#   usage: scripts/bundle-linux.sh path/to/qemu-system-xtensa path/to/esp32s3_rev0_rom.bin OUT_DIR
set -euo pipefail
EXE=$1; ROM=$2; OUT=$3
readelf -d "$EXE" | grep -q 'RPATH.*\$ORIGIN/lib' || { echo "error: $EXE lacks DT_RPATH \$ORIGIN/lib (see header)" >&2; exit 1; }
mkdir -p "$OUT/lib"
cp "$EXE" "$OUT/qemu-system-xtensa"; cp "$ROM" "$OUT/"
strip --strip-unneeded "$OUT/qemu-system-xtensa"
SKIP='^(linux-vdso|ld-linux|libc\.so|libm\.so|libpthread\.so|libdl\.so|librt\.so|libresolv\.so|libutil\.so)'
ldd "$EXE" | awk '/=> \//{print $1" "$3}' | while read -r name path; do
  [[ "$name" =~ $SKIP ]] && continue
  cp -L "$path" "$OUT/lib/$name"; chmod 644 "$OUT/lib/$name"
  # a library with its own DT_RUNPATH (e.g. libpulse -> /usr/lib/.../pulseaudio) ignores the exe's RPATH
  # for its deps; point it at the bundle dir instead (needs patchelf)
  if readelf -d "$OUT/lib/$name" | grep -q RUNPATH; then
    command -v patchelf >/dev/null || { echo "error: $name has RUNPATH; install patchelf" >&2; exit 1; }
    patchelf --set-rpath '$ORIGIN' "$OUT/lib/$name"
  fi
done
echo "bundled $(ls "$OUT/lib" | wc -l) libs into $OUT/lib (needs host glibc >= $(ldd --version | head -1 | awk '{print $NF}'))"
