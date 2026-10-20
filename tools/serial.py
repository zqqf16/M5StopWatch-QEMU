#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Minimal serial monitor for QEMU's UART0 when started with ./run.sh --serial-tcp PORT
(or any '-serial tcp:...' / unix socket).  Lines typed on stdin are sent with CRLF.
usage: serial.py [HOST:]PORT | /path/to/unix.sock   [--eol crlf|lf|cr] [--log FILE]
Ctrl-C to quit."""
import socket, sys, threading
a = sys.argv[1:]
if not a: print(__doc__); sys.exit(1)
eol = {'crlf': b'\r\n', 'lf': b'\n', 'cr': b'\r'}[a[a.index('--eol') + 1] if '--eol' in a else 'crlf']
log = open(a[a.index('--log') + 1], 'ab') if '--log' in a else None
t = a[0]
if '/' in t:
    s = socket.socket(socket.AF_UNIX); s.connect(t)
else:
    h, _, p = t.rpartition(':'); s = socket.create_connection((h or '127.0.0.1', int(p)))
def rx():
    while True:
        d = s.recv(4096)
        if not d: print('\n[serial.py] connection closed'); break
        sys.stdout.buffer.write(d); sys.stdout.buffer.flush()
        if log: log.write(d); log.flush()
    import os; os._exit(0)
threading.Thread(target=rx, daemon=True).start()
try:
    for line in sys.stdin.buffer:
        s.sendall(line.rstrip(b'\r\n') + eol)
    threading.Event().wait()
except KeyboardInterrupt:
    pass
