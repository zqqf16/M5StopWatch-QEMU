#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Make a self-contained macOS qemu-system-xtensa: copy every non-system dylib it
needs (Homebrew etc.) into <out>/lib, rewrite load commands to @loader_path,
and ad-hoc codesign everything.

usage: scripts/bundle-macos.py path/to/qemu-system-xtensa OUT_DIR   (e.g. bin/Darwin-arm64)
"""
import os, shutil, subprocess, sys

SYSTEM = ('/usr/lib/', '/System/')

def deps(path):
    out = subprocess.check_output(['otool', '-L', path], text=True).splitlines()[1:]
    return [l.strip().split(' (')[0] for l in out if l.strip()]

def rpaths(path):
    out = subprocess.check_output(['otool', '-l', path], text=True).splitlines()
    return [out[i + 2].split()[1] for i, l in enumerate(out) if 'LC_RPATH' in l]

def resolve(ref, owner, owner_rpaths):
    d = os.path.dirname(owner)
    if ref.startswith('@loader_path/') or ref.startswith('@executable_path/'):
        return os.path.realpath(os.path.join(d, ref.split('/', 1)[1]))
    if ref.startswith('@rpath/'):
        for rp in owner_rpaths:
            rp = rp.replace('@loader_path', d).replace('@executable_path', d)
            p = os.path.join(rp, ref[7:])
            if os.path.exists(p):
                return os.path.realpath(p)
        for base in ('/opt/homebrew/lib', '/usr/local/lib'):
            p = os.path.join(base, ref[7:])
            if os.path.exists(p):
                return os.path.realpath(p)
        raise SystemExit('cannot resolve %s from %s' % (ref, owner))
    return os.path.realpath(ref)

def main():
    exe, out = sys.argv[1], sys.argv[2]
    lib = os.path.join(out, 'lib'); os.makedirs(lib, exist_ok=True)
    dst_exe = os.path.join(out, os.path.basename(exe))
    shutil.copy2(exe, dst_exe); os.chmod(dst_exe, 0o755)
    todo = [(exe, dst_exe, True)]; done = {}
    while todo:
        src, dst, is_exe = todo.pop()
        rps = rpaths(src)
        subprocess.run(['install_name_tool', '-id', '@loader_path/' + os.path.basename(dst), dst],
                       check=False, stderr=subprocess.DEVNULL) if not is_exe else None
        for ref in deps(src):
            if ref.startswith(SYSTEM) or os.path.basename(ref) == os.path.basename(src):
                continue
            real = resolve(ref, src, rps)
            name = os.path.basename(real)
            if real not in done:
                d = os.path.join(lib, name)
                shutil.copy2(real, d); os.chmod(d, 0o755)
                done[real] = d; todo.append((real, d, False))
            new = ('@executable_path/lib/' if is_exe else '@loader_path/') + name
            subprocess.check_call(['install_name_tool', '-change', ref, new, dst], stderr=subprocess.DEVNULL)
        for rp in rps:   # drop absolute rpaths into Homebrew
            if rp.startswith(('/opt/', '/usr/local')):
                subprocess.run(['install_name_tool', '-delete_rpath', rp, dst], check=False)
    # Homebrew's SDL2 is sdl2-compat, which dlopen()s SDL3 from @loader_path/libSDL3.dylib
    if any('SDL2' in os.path.basename(k) for k in done):
        for cand in ('/opt/homebrew/opt/sdl3/lib/libSDL3.0.dylib', '/usr/local/opt/sdl3/lib/libSDL3.0.dylib'):
            if os.path.exists(cand):
                d = os.path.join(lib, 'libSDL3.dylib'); shutil.copy2(os.path.realpath(cand), d); os.chmod(d, 0o755)
                subprocess.check_call(['install_name_tool', '-id', '@loader_path/libSDL3.dylib', d], stderr=subprocess.DEVNULL)
                done[cand] = d; break
    for f in list(done.values()) + [dst_exe]:
        subprocess.check_call(['codesign', '--force', '-s', '-', f], stderr=subprocess.DEVNULL)
    bad = [f for f in list(done.values()) + [dst_exe] for r in deps(f) if r.startswith(('/opt/', '/usr/local'))]
    print('bundled %d dylibs into %s' % (len(done), lib))
    if bad: raise SystemExit('still referencing Homebrew: %s' % bad)

main()
