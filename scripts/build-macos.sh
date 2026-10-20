#!/usr/bin/env bash
# SPDX-License-Identifier: MIT
# Build Espressif QEMU (pinned tag) + M5StopWatch board patches on macOS (Apple Silicon / Intel)
# -> bin/Darwin-<arch>/ (dylibs bundled, ad-hoc signed; runs without Homebrew afterwards).
#   ./build-macos.sh            install deps with Homebrew, then build
#   ./build-macos.sh --no-brew  do not touch Homebrew: build libgpg-error/libgcrypt locally (static),
#                               get ninja from a local Python venv; glib/pixman/sdl2/libpng/pkgconf
#                               must already be installed (brew install glib pixman sdl2 libpng pkgconf)
set -euo pipefail
export MACOSX_DEPLOYMENT_TARGET=${MACOSX_DEPLOYMENT_TARGET:-26.0}  # match Homebrew bottles; release binaries run on macOS 26+
TAG=esp-develop-9.2.2-20260417
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
WORK="${WORK:-$ROOT/build}"
JOBS="$(sysctl -n hw.ncpu 2>/dev/null || echo 8)"
mkdir -p "$WORK"
BREW_PREFIX="$(brew --prefix 2>/dev/null || echo /opt/homebrew)"
export PATH="$BREW_PREFIX/bin:$PATH"

EXTRA=()
if [ "${1:-}" != "--no-brew" ]; then
  brew install glib pixman sdl2 libgcrypt libpng pkgconf ninja
else
  DEPS="$WORK/deps"; mkdir -p "$DEPS/src"
  if [ ! -x "$WORK/venv/bin/ninja" ]; then
    python3 -m venv "$WORK/venv" && "$WORK/venv/bin/pip" install -q ninja
  fi
  export PATH="$WORK/venv/bin:$PATH"
  build_dep() { # name version
    local n=$1 v=$2
    [ -f "$DEPS/lib/lib$n.a" ] && return 0
    ( cd "$DEPS/src" && curl -fsSLO "https://gnupg.org/ftp/gcrypt/$n/$n-$v.tar.bz2" && tar xjf "$n-$v.tar.bz2" &&
      cd "$n-$v" && ./configure -q --prefix="$DEPS" --disable-shared --enable-static --with-pic \
        --disable-doc ${3:-} && make -j"$JOBS" >/dev/null && make install >/dev/null )
  }
  build_dep libgpg-error 1.51 "--disable-tests --disable-nls"
  build_dep libgcrypt 1.11.0 "--with-libgpg-error-prefix=$DEPS --disable-asm"
  export PATH="$DEPS/bin:$PATH" PKG_CONFIG_PATH="$DEPS/lib/pkgconfig:${PKG_CONFIG_PATH:-}"
  EXTRA=(--extra-ldflags="$DEPS/lib/libgpg-error.a")
fi

if [ ! -d "$WORK/qemu/.git" ]; then
  git clone --depth 1 -b "$TAG" https://github.com/espressif/qemu "$WORK/qemu"
fi
cd "$WORK/qemu"
for p in "$ROOT"/patches/*.patch; do   # apply each patch once (re-runs pick up newly added patches)
  subj="$(sed -n 's/^Subject: \(\[PATCH[^]]*\] \)\{0,1\}//p' "$p" | head -1 | cut -c1-50)"
  grep -qF "$subj" <<<"$(git log --format=%s -n 50)" || git -c user.name=m5sw -c user.email=m5sw@local am "$p"
done
# upstream fork bug: slirp is declared "found" even when disabled -> net/slirp.c fails without libslirp
perl -pi -e 's/^  slirp = declare_dependency\(dependencies: \[slirp_dep\],/  slirp = not slirp_dep.found() ? not_found : declare_dependency(dependencies: [slirp_dep],/' meson.build
mkdir -p build && cd build
../configure --target-list=xtensa-softmmu --enable-gcrypt --enable-cocoa --enable-sdl --enable-png \
  --disable-docs --disable-werror --disable-gtk --disable-gnutls --disable-nettle --disable-vnc \
  --disable-slirp --disable-curl --disable-libssh --disable-zstd --disable-bzip2 --disable-curses \
  --disable-auth-pam --disable-dbus-display --disable-tpm ${EXTRA[@]+"${EXTRA[@]}"}
ninja -j"$JOBS" qemu-system-xtensa
OUT="$ROOT/bin/Darwin-$(uname -m)"
rm -rf "$OUT"
# self-contained: copy Homebrew dylibs into $OUT/lib, rewrite to @executable_path/@loader_path, ad-hoc sign
python3 "$ROOT/scripts/bundle-macos.py" qemu-system-xtensa "$OUT"
cp ../pc-bios/esp32s3_rev0_rom.bin "$OUT/"
echo "Built: $OUT/qemu-system-xtensa"
