# Third-party notices

This repository's own code is MIT (see [LICENSE](LICENSE)). This file lists everything else that is
part of the repository or of the release archives, with its license. License texts are in [LICENSES/](LICENSES/);
the release archives additionally contain the upstream copyright/license files of each bundled library in
`bin/<platform>/licenses/`.

## QEMU (patches/ and qemu-system-xtensa binaries)

| component | version | license | source |
|---|---|---|---|
| Espressif QEMU fork (`qemu-system-xtensa`) | tag `esp-develop-9.2.2-20260417` + `patches/0001…0005` | GPL-2.0-or-later (QEMU as a whole GPL-2.0; individual files GPL-2.0-or-later, LGPL-2.1-or-later, MIT, BSD) | https://github.com/espressif/qemu/tree/esp-develop-9.2.2-20260417 |
| `patches/*.patch` (this project's QEMU changes) | 0.1.0 | GPL-2.0-or-later | this repository |

QEMU © Fabrice Bellard and the QEMU contributors; ESP32-S3 support © Espressif Systems (Shanghai) Co., Ltd.

### Written source offer (GPL-2.0 §3, LGPL-2.1 §6)
The complete corresponding source for the `qemu-system-xtensa` binaries in every release is:
1. espressif/qemu at the pinned tag above (`git clone -b esp-develop-9.2.2-20260417 https://github.com/espressif/qemu`),
2. `patches/` and the build scripts `scripts/build-*.sh`, `scripts/bundle-*` from this repository at the release tag,
   also published as `m5stopwatch-qemu-<ver>-src.zip` on the same GitHub release page.
The bundled LGPL libraries are unmodified distribution packages (Ubuntu 22.04 "jammy" for Linux, Homebrew for macOS);
their sources are available from the URLs below, from `apt-get source <package>=<version>` on Ubuntu 22.04, or from
the Homebrew formula's source URL. For at least three years after each release, the maintainer
(zqqf16 <zqqf16@gmail.com>, https://github.com/zqqf16/M5StopWatch-QEMU) will provide on request a copy of any of
these sources, for no more than the cost of physically distributing it. The shared libraries can be replaced by the
user (they are plain files in `bin/<platform>/lib/`); libgcrypt/libgpg-error, which are statically linked into the
macOS binary, can be relinked by rebuilding with `scripts/build-macos.sh` from the source above.

## Espressif ROM image

| file | license / copyright | source |
|---|---|---|
| `bin/*/esp32s3_rev0_rom.bin` | © Espressif Systems (Shanghai) Co., Ltd. Redistributed unmodified, as shipped by Espressif in espressif/qemu (`pc-bios/`) release packages; the same ROM is published as ELF in esp-rom-elfs (Apache-2.0). | https://github.com/espressif/qemu/releases/tag/esp-develop-9.2.2-20260417 , https://github.com/espressif/esp-rom-elfs |

## Bundled libraries — Linux x86_64 (`bin/Linux-x86_64/lib/`, from Ubuntu 22.04 packages)

| file(s) | project | version | license | source |
|---|---|---|---|---|
| libFLAC.so.8 | flac | 1.3.3-2build2 | BSD-3-Clause (libFLAC) | https://xiph.org/flac/ |
| libSDL2-2.0.so.0 | libsdl2 | 2.0.20+dfsg-2build1 | Zlib | https://libsdl.org/ |
| libX11.so.6, libX11-xcb.so.1 | libx11 | 2:1.7.5-1 | X11/MIT | https://gitlab.freedesktop.org/xorg/lib/libx11 |
| libXau.so.6 | libxau | 1:1.0.9-1build5 | MIT | https://gitlab.freedesktop.org/xorg/lib/libxau |
| libXcursor.so.1 | libxcursor | 1:1.2.0-2build4 | MIT | https://gitlab.freedesktop.org/xorg/lib/libxcursor |
| libXdmcp.so.6 | libxdmcp | 1:1.1.3-0ubuntu5 | MIT | https://gitlab.freedesktop.org/xorg/lib/libxdmcp |
| libXext.so.6 | libxext | 2:1.3.4-1build1 | MIT | https://gitlab.freedesktop.org/xorg/lib/libxext |
| libXfixes.so.3 | libxfixes | 1:6.0.0-1 | MIT | https://gitlab.freedesktop.org/xorg/lib/libxfixes |
| libXi.so.6 | libxi | 2:1.8-1build1 | MIT | https://gitlab.freedesktop.org/xorg/lib/libxi |
| libXinerama.so.1 | libxinerama | 2:1.1.4-3 | MIT | https://gitlab.freedesktop.org/xorg/lib/libxinerama |
| libXrandr.so.2 | libxrandr | 2:1.5.2-1build1 | MIT | https://gitlab.freedesktop.org/xorg/lib/libxrandr |
| libXrender.so.1 | libxrender | 1:0.9.10-1build4 | MIT | https://gitlab.freedesktop.org/xorg/lib/libxrender |
| libXss.so.1 | libxss | 1:1.2.3-1build2 | MIT | https://gitlab.freedesktop.org/xorg/lib/libxscrnsaver |
| libXxf86vm.so.1 | libxxf86vm | 1:1.1.4-1build3 | MIT | https://gitlab.freedesktop.org/xorg/lib/libxxf86vm |
| libxcb.so.1 | libxcb | 1.14-3ubuntu3 | MIT | https://xcb.freedesktop.org/ |
| libxkbcommon.so.0 | libxkbcommon | 1.4.0-1 | MIT | https://xkbcommon.org/ |
| libwayland-{client,cursor,egl,server}.so | wayland | 1.20.0-1 | MIT | https://wayland.freedesktop.org/ |
| libdecor-0.so.0 | libdecor-0 | 0.1.0-3build1 | MIT | https://gitlab.freedesktop.org/libdecor/libdecor |
| libdrm.so.2 | libdrm | 2.4.110-1ubuntu1 | MIT | https://gitlab.freedesktop.org/mesa/drm |
| libgbm.so.1 | mesa | 22.0.1-1ubuntu2 | MIT | https://mesa3d.org/ |
| libapparmor.so.1 | apparmor | 3.0.4-2ubuntu2 | LGPL-2.1 | https://apparmor.net/ |
| libasound.so.2 | alsa-lib | 1.2.6.1-1ubuntu1 | LGPL-2.1-or-later | https://www.alsa-project.org/ |
| libasyncns.so.0 | libasyncns | 0.8-6build2 | LGPL-2.1-or-later | http://0pointer.de/lennart/projects/libasyncns/ |
| libblkid.so.1, libmount.so.1 | util-linux | 2.37.2-4ubuntu3 | LGPL-2.1-or-later | https://github.com/util-linux/util-linux |
| libbsd.so.0 | libbsd | 0.11.5-1 | BSD-3-Clause / BSD-2-Clause / ISC (various) | https://libbsd.freedesktop.org/ |
| libmd.so.0 | libmd | 1.0.4-1build1 | BSD-3-Clause / BSD-2-Clause / public domain | https://www.hadrons.org/software/libmd/ |
| libcap.so.2 | libcap2 | 1:2.44-1build3 | BSD-3-Clause or GPL-2.0 | https://sites.google.com/site/fullycapable/ |
| libdbus-1.so.3 | dbus | 1.12.20-2ubuntu4 | AFL-2.1 or GPL-2.0-or-later | https://dbus.freedesktop.org/ |
| libexpat.so.1 | expat | 2.4.7-1 | MIT | https://libexpat.github.io/ |
| libffi.so.8 | libffi | 3.4.2-4 | MIT | https://sourceware.org/libffi/ |
| libgcc_s.so.1, libstdc++.so.6 | gcc-12 | 12-20220319-1ubuntu1 | GPL-3.0-or-later WITH GCC-exception-3.1 | https://gcc.gnu.org/ |
| libgcrypt.so.20 | libgcrypt20 | 1.9.4-3ubuntu3 | LGPL-2.1-or-later | https://gnupg.org/software/libgcrypt/ |
| libgpg-error.so.0 | libgpg-error | 1.43-3 | LGPL-2.1-or-later | https://gnupg.org/software/libgpg-error/ |
| libglib-2.0, libgio-2.0, libgobject-2.0, libgmodule-2.0 | glib2.0 | 2.72.1-1 | LGPL-2.1-or-later | https://gitlab.gnome.org/GNOME/glib |
| liblz4.so.1 | lz4 | 1.9.3-2build2 | BSD-2-Clause | https://github.com/lz4/lz4 |
| liblzma.so.5 | xz-utils | 5.2.5-2ubuntu1 | public domain | https://tukaani.org/xz/ |
| libogg.so.0 | libogg | 1.3.5-0ubuntu3 | BSD-3-Clause | https://xiph.org/ogg/ |
| libopus.so.0 | opus | 1.3.1-0.1build2 | BSD-3-Clause | https://opus-codec.org/ |
| libvorbis.so.0, libvorbisenc.so.2 | libvorbis | 1.3.7-1build2 | BSD-3-Clause | https://xiph.org/vorbis/ |
| libpcre.so.3 | pcre3 | 2:8.39-13build5 | BSD-3-Clause | https://www.pcre.org/ |
| libpcre2-8.so.0 | pcre2 | 10.39-3build1 | BSD-3-Clause | https://www.pcre.org/ |
| libpixman-1.so.0 | pixman | 0.40.0-1build4 | MIT | https://pixman.org/ |
| libpng16.so.16 | libpng1.6 | 1.6.37-3build5 | libpng-2.0 | http://www.libpng.org/pub/png/libpng.html |
| libpulse.so.0, libpulsecommon-15.99.so | pulseaudio | 1:15.99.1+dfsg1-1ubuntu1 | LGPL-2.1-or-later | https://www.freedesktop.org/wiki/Software/PulseAudio/ |
| libselinux.so.1 | libselinux | 3.3-1build2 | public domain | https://github.com/SELinuxProject/selinux |
| libsndfile.so.1 | libsndfile | 1.0.31-2build1 | LGPL-2.1-or-later | https://libsndfile.github.io/libsndfile/ |
| libsndio.so.7 | sndio | 1.8.1-1.1 | ISC | https://sndio.org/ |
| libsystemd.so.0 | systemd | 249.11-0ubuntu3 | LGPL-2.1-or-later | https://systemd.io/ |
| libz.so.1 | zlib | 1:1.2.11.dfsg-2ubuntu9 | Zlib | https://zlib.net/ |
| libzstd.so.1 | libzstd | 1.4.8+dfsg-3build1 | BSD-3-Clause or GPL-2.0 | https://github.com/facebook/zstd |

glibc (libc, libm, libpthread, libdl, librt, ld-linux) is **not** bundled; the host's is used.

## Bundled libraries — macOS arm64 (`bin/Darwin-arm64/lib/`, from Homebrew)

| file(s) | project | version | license | source |
|---|---|---|---|---|
| libSDL2-2.0.0.dylib | sdl2-compat | 2.32.72 | Zlib | https://github.com/libsdl-org/sdl2-compat |
| libSDL3.dylib | sdl3 | 3.4.16 | Zlib | https://libsdl.org/ |
| libglib-2.0, libgio-2.0, libgobject-2.0, libgmodule-2.0 | glib | 2.88.3 | LGPL-2.1-or-later | https://gitlab.gnome.org/GNOME/glib |
| libintl.8.dylib | gettext (libintl) | 1.0 | LGPL-2.1-or-later | https://www.gnu.org/software/gettext/ |
| libpcre2-8.0.dylib | pcre2 | 10.48 | BSD-3-Clause | https://github.com/PCRE2Project/pcre2 |
| libpixman-1.0.dylib | pixman | 0.46.4 | MIT | https://pixman.org/ |
| libpng16.16.dylib | libpng | 1.6.58 | libpng-2.0 | https://www.libpng.org/pub/png/libpng.html |
| (static in qemu-system-xtensa) | libgcrypt / libgpg-error | built by scripts/build-macos.sh --no-brew | LGPL-2.1-or-later | https://gnupg.org/ |

## Firmware

| file | license | bundled? | source |
|---|---|---|---|
| `C152-StopWatch-UserDemo-V0.5-20260528_0x0.bin` (factory firmware) | © M5Stack, MIT; contains ESP-IDF (Apache-2.0), LVGL (MIT) and other components under their own licenses | **no** — downloaded by `scripts/fetch-firmware.sh` | https://github.com/m5stack/M5StopWatch-UserDemo/releases/tag/V0.5 |
| `firmware/uart-echo-test.bin` | MIT (this project); built with ESP-IDF 5.5 (Apache-2.0 components incl. bootloader, FreeRTOS MIT) | yes | `firmware/uart-echo-test/`, https://github.com/espressif/esp-idf |

## Web UI assets
`web/index.html` contains no third-party code, fonts or images and loads nothing from a CDN (system fonts only).
The device-frame artwork is original CSS/SVG. `docs/images/*.png` are screenshots of this emulator running the
M5Stack factory firmware (UI © M5Stack).

## License texts (`LICENSES/`)
GPL-2.0, GPL-3.0 (GCC runtime, with exception), LGPL-2.1, MIT, X11, BSD-2-Clause, BSD-3-Clause, Zlib, libpng-2.0, Apache-2.0, ISC, AFL-2.1, GCC-exception-3.1.
