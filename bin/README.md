# bin/

Prebuilt QEMU per platform, selected by `run.sh` from `uname -s`-`uname -m`:
`Darwin-arm64/`, `Darwin-x86_64/`, `Linux-x86_64/`, `Linux-aarch64/`. Each holds `qemu-system-xtensa`,
`lib/` (bundled shared libraries) and `esp32s3_rev0_rom.bin`. Binaries are not tracked in git — get them
from a release archive or build with `scripts/build-*.sh`. GPL-2.0-or-later; source = espressif/qemu tag + `../patches/`.
Bundled libraries' license files are in `bin/<platform>/licenses/`; see `../THIRD_PARTY_NOTICES.md`.
