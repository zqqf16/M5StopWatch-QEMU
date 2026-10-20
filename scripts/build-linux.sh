#!/usr/bin/env bash
# SPDX-License-Identifier: MIT
# Build qemu-system-xtensa with the M5StopWatch patches on Debian/Ubuntu (x86_64/aarch64).
#   scripts/build-linux.sh            apt-get install build deps, then build -> bin/Linux-<arch>/
#   scripts/build-linux.sh --no-apt   skip apt-get
#   BUNDLE=1 scripts/build-linux.sh   also bundle shared libs (portable; build on an old distro, e.g. Ubuntu 22.04)
set -euo pipefail
TAG=esp-develop-9.2.2-20260417
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
WORK="${WORK:-$ROOT/build}"
if [ "${1:-}" != "--no-apt" ]; then
  sudo apt-get install -y git build-essential python3-venv ninja-build pkg-config flex bison \
    libglib2.0-dev libpixman-1-dev libsdl2-dev libgcrypt20-dev libpng-dev python3-tomli
fi
mkdir -p "$WORK"
[ -d "$WORK/qemu/.git" ] || git clone --depth 1 -b "$TAG" https://github.com/espressif/qemu "$WORK/qemu"
cd "$WORK/qemu"
for p in "$ROOT"/patches/*.patch; do   # apply each patch once (re-runs pick up newly added patches)
  subj="$(sed -n 's/^Subject: \(\[PATCH[^]]*\] \)\{0,1\}//p' "$p" | head -1 | cut -c1-50)"
  grep -qF "$subj" <<<"$(git log --format=%s -n 50)" || git -c user.name=m5sw -c user.email=m5sw@local am "$p"
done
# upstream fork bug: slirp is declared "found" even when disabled -> net/slirp.c fails without libslirp
perl -pi -e 's/^  slirp = declare_dependency\(dependencies: \[slirp_dep\],/  slirp = not slirp_dep.found() ? not_found : declare_dependency(dependencies: [slirp_dep],/' meson.build
mkdir -p build && cd build
# only what the board needs: SDL + PNG screendump + gcrypt; everything else off (smaller, fewer runtime deps)
EXTRA=(); [ "${BUNDLE:-0}" = 1 ] && EXTRA=(--extra-ldflags='-Wl,--disable-new-dtags,-rpath,$ORIGIN/lib')
../configure --target-list=xtensa-softmmu --enable-gcrypt --enable-sdl --enable-png --disable-docs --disable-werror "${EXTRA[@]}" \
  --disable-gtk --disable-gnutls --disable-nettle --disable-vnc --disable-slirp --disable-curl --disable-libssh \
  --disable-zstd --disable-bzip2 --disable-curses --disable-auth-pam --disable-tpm --disable-opengl \
  --disable-virglrenderer --disable-libudev --disable-alsa --disable-pa --disable-pipewire --disable-jack \
  --disable-oss --disable-spice --disable-libusb --disable-usb-redir --disable-seccomp --disable-cap-ng \
  --disable-attr --disable-libnfs --disable-rbd --disable-glusterfs --disable-libiscsi --disable-numa \
  --disable-lzo --disable-snappy --disable-xkbcommon --disable-dbus-display --disable-linux-io-uring --disable-libdw
ninja qemu-system-xtensa
OUT="$ROOT/bin/Linux-$(uname -m)"
if [ "${BUNDLE:-0}" = 1 ]; then      # relocatable: copy .so deps to $OUT/lib, RUNPATH=$ORIGIN/lib
  rm -rf "$OUT"; "$ROOT/scripts/bundle-linux.sh" qemu-system-xtensa ../pc-bios/esp32s3_rev0_rom.bin "$OUT"
else
  mkdir -p "$OUT"; cp qemu-system-xtensa ../pc-bios/esp32s3_rev0_rom.bin "$OUT/"
fi
echo "Built: $OUT/qemu-system-xtensa"
