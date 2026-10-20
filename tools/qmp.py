#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Tiny QMP client for the M5StopWatch QEMU board.
usage: qmp.py SOCK cmd [cmd...]
  shot FILE.png            screendump (PNG)
  key NAME [HOLD_MS]       press/release a key (a / b / left / right)
  keys A,B HOLD_MS         hold several keys simultaneously
  tap X Y                  touch tap at panel pixel (0..465)
  swipe X0 Y0 X1 Y1 [MS]   touch drag
  sleep SEC
"""
import json, socket, sys, time

class QMP:
    def __init__(self, path):
        self.s = socket.socket(socket.AF_UNIX); self.s.connect(path)
        self.f = self.s.makefile('rw')
        self.f.readline(); self.cmd('qmp_capabilities')
    def cmd(self, name, **args):
        self.f.write(json.dumps({'execute': name, 'arguments': args}) + '\n'); self.f.flush()
        while True:
            r = json.loads(self.f.readline())
            if 'return' in r or 'error' in r:
                if 'error' in r: print('QMP error:', r['error'], file=sys.stderr)
                return r
    def keyev(self, names, down):
        self.cmd('input-send-event', events=[{'type': 'key', 'data': {'down': down, 'key': {'type': 'qcode', 'data': n}}} for n in names])
    def abs(self, x, y, btn=None):
        ev = [{'type': 'abs', 'data': {'axis': 'x', 'value': int(x * 32767 / 465)}},
              {'type': 'abs', 'data': {'axis': 'y', 'value': int(y * 32767 / 465)}}]
        if btn is not None:
            ev.append({'type': 'btn', 'data': {'down': btn, 'button': 'left'}})
        self.cmd('input-send-event', events=ev)

def main():
    q = QMP(sys.argv[1]); a = sys.argv[2:]; i = 0
    while i < len(a):
        c = a[i]
        if c == 'shot':
            q.cmd('screendump', filename=a[i+1], format='png'); i += 2
        elif c == 'key':
            hold = int(a[i+2]) if i + 2 < len(a) and a[i+2].isdigit() else 150
            q.keyev([a[i+1]], True); time.sleep(hold / 1000); q.keyev([a[i+1]], False)
            i += 3 if i + 2 < len(a) and a[i+2].isdigit() else 2
        elif c == 'keys':
            ks = a[i+1].split(','); q.keyev(ks, True); time.sleep(int(a[i+2]) / 1000); q.keyev(ks, False); i += 3
        elif c == 'tap':
            x, y = float(a[i+1]), float(a[i+2]); q.abs(x, y, True); time.sleep(0.15); q.abs(x, y, False); i += 3
        elif c == 'swipe':
            x0, y0, x1, y1 = map(float, a[i+1:i+5]); ms = 400
            n = 12; q.abs(x0, y0, True)
            for k in range(1, n + 1):
                time.sleep(ms / 1000 / n); q.abs(x0 + (x1 - x0) * k / n, y0 + (y1 - y0) * k / n)
            q.abs(x1, y1, False); i += 5
        elif c == 'sleep':
            time.sleep(float(a[i+1])); i += 2
        else:
            print('unknown', c); i += 1

main()
