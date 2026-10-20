#!/usr/bin/env bash
# SPDX-License-Identifier: MIT
# Build release archives into ${OUT:-dist/}:
#   m5stopwatch-qemu-<ver>-src.zip, -macos-arm64.zip, -linux-x86_64.tar.gz (for each bin/ present)
# Usage: scripts/make-release.sh [version]
set -euo pipefail
ROOT=$(cd "$(dirname "$0")/.." && pwd); cd "$ROOT"
VER=${1:-$(sed -n 's/^## \([0-9][^ ]*\).*/\1/p' CHANGELOG.md | head -1)}
OUT=${OUT:-$ROOT/dist}; mkdir -p "$OUT"
N=m5stopwatch-qemu-$VER
STAGE=$(mktemp -d); trap 'rm -rf "$STAGE"' EXIT
# source = tracked files if git repo, else everything not ignored-ish
if git rev-parse --git-dir >/dev/null 2>&1; then
  git ls-files > "$STAGE/files"
else
  find . -type f ! -path './bin/*/*' ! -path './run/*' ! -path './dist/*' ! -path './build/*' | sed 's#^\./##' > "$STAGE/files"
fi
mkdir -p "$STAGE/$N"; tar -cf - -T "$STAGE/files" | tar -xf - -C "$STAGE/$N"
mkzip() {  # mkzip out.zip dir  (keeps unix modes + symlinks)
  python3 - "$1" "$2" <<'PY'
import os, sys, zipfile, stat
out, base = sys.argv[1], sys.argv[2]
parent = os.path.dirname(base)
with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as z:
    for dp, dns, fns in os.walk(base):
        dns.sort()
        for f in sorted(fns):
            p = os.path.join(dp, f); a = os.path.relpath(p, parent)
            st = os.lstat(p); zi = zipfile.ZipInfo(a, (2026, 10, 20, 0, 0, 0))
            zi.create_system = 3; zi.external_attr = (st.st_mode & 0xFFFF) << 16
            if stat.S_ISLNK(st.st_mode):
                z.writestr(zi, os.readlink(p))
            else:
                zi.compress_type = zipfile.ZIP_DEFLATED
                with open(p, "rb") as fh: z.writestr(zi, fh.read())
PY
}
rm -f "$OUT/$N"-*
mkzip "$OUT/$N-src.zip" "$STAGE/$N"
for P in bin/*/; do
  P=$(basename "$P"); [ -x "bin/$P/qemu-system-xtensa" ] || continue
  rm -rf "$STAGE/$N/bin/"*/; cp -a "bin/$P" "$STAGE/$N/bin/"
  case $P in
    Darwin-arm64)  mkzip "$OUT/$N-macos-arm64.zip" "$STAGE/$N" ;;
    Darwin-x86_64) mkzip "$OUT/$N-macos-x86_64.zip" "$STAGE/$N" ;;
    Linux-*)       tar -C "$STAGE" --owner=0 --group=0 -czf "$OUT/$N-linux-${P#Linux-}.tar.gz" "$N" ;;
  esac
done
( cd "$OUT" && { command -v sha256sum >/dev/null && sha256sum "$N"-*.zip "$N"-*.tar.gz || shasum -a 256 "$N"-*.zip "$N"-*.tar.gz; } > "$N-SHA256SUMS.txt" )
ls -l "$OUT/$N"-*
