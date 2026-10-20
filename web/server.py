#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""M5StopWatch QEMU web UI server (Python 3 standard library only).

It starts QEMU itself, so it can switch firmware (full teardown + fresh flash image).
  * screen: CO5300 framebuffer via QMP screendump (PNG polling)
  * input : mouse -> CST820 touch, A/B/P buttons -> KEYA/KEYB/PWR
  * serial: UART0 streamed to the page via Server-Sent Events; POST /api/serial writes to UART0
  * firmware: lists firmware/*.bin (+ firmware/uploads/), upload from page, ?fw=NAME URL param

usage: web/server.py [--port 8466] [--fw NAME_OR_PATH] [--qemu BIN] [--rom-dir DIR]
                     [--fw-dir DIR] [--run-dir DIR] [--bind 127.0.0.1]
"""
import argparse, hashlib, json, os, re, shutil, socket, subprocess, sys, threading, time, urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))   # repo / release root
import platform
BIN = os.path.join(HERE, 'bin', '%s-%s' % (platform.system(), platform.machine().replace('aarch64', 'arm64') if platform.system() == 'Darwin' else platform.machine()))
ap = argparse.ArgumentParser()
ap.add_argument('--port', type=int, default=8466)
ap.add_argument('--bind', default='127.0.0.1')
ap.add_argument('--qemu', default=os.environ.get('QEMU', os.path.join(BIN, 'qemu-system-xtensa')))
ap.add_argument('--rom-dir', default=os.environ.get('ROMDIR', BIN))
ap.add_argument('--fw-dir', default=os.path.join(HERE, 'firmware'))
ap.add_argument('--run-dir', default=os.path.join(HERE, 'run'))
ap.add_argument('--fw', default='C152-StopWatch-UserDemo-V0.5-20260528_0x0.bin')
A = ap.parse_args()
if os.path.isfile(A.fw): A.fw = os.path.abspath(A.fw)
UPL = os.path.join(A.fw_dir, 'uploads')
os.makedirs(A.run_dir, exist_ok=True); os.makedirs(UPL, exist_ok=True)
FLASH = 16 << 20

def fw_list():
    out = []
    for d, pre in ((A.fw_dir, ''), (UPL, 'uploads/')):
        for n in sorted(os.listdir(d)):
            p = os.path.join(d, n)
            if n.lower().endswith('.bin') and os.path.isfile(p):
                out.append({'name': pre + n, 'size': os.path.getsize(p)})
    return out

def fw_path(name):
    if os.path.isabs(name) and name in (os.path.abspath(A.fw), getattr(emu, 'path', None)) and os.path.isfile(name):
        return name
    p = os.path.realpath(os.path.join(A.fw_dir, name))
    if not p.startswith(os.path.realpath(A.fw_dir) + os.sep) or not os.path.isfile(p):
        raise ValueError('unknown firmware: %s' % name)
    return p

class QMP:
    def __init__(self, path):
        self.s = socket.socket(socket.AF_UNIX); self.s.connect(path); self.s.settimeout(10)
        self.f = self.s.makefile('rw'); self.f.readline(); self.cmd('qmp_capabilities')
    def cmd(self, name, **args):
        self.f.write(json.dumps({'execute': name, 'arguments': args}) + '\n'); self.f.flush()
        while True:
            r = json.loads(self.f.readline())
            if 'return' in r or 'error' in r:
                return r
    def close(self):
        try: self.s.close()
        except Exception: pass

class Emu:
    """One QEMU instance; restart() tears everything down and boots a fresh flash image."""
    def __init__(self):
        self.lock = threading.RLock()      # guards proc/qmp/serial socket
        self.proc = None; self.qmp = None; self.ser = None
        self.gen = 0; self.fw = None; self.sha = None; self.state = 'stopped'
        self.log = bytearray(); self.cond = threading.Condition()
        self.logf = None; self.error = ''

    def _append(self, data):
        with self.cond:
            self.log += data
            if len(self.log) > 2_000_000:
                cut = len(self.log) - 1_500_000; del self.log[:cut]; self.base += cut
            self.cond.notify_all()
        if self.logf: self.logf.write(data); self.logf.flush()

    def stop(self):
        with self.lock:
            if self.qmp:
                try: self.qmp.cmd('quit')
                except Exception: pass
                self.qmp.close(); self.qmp = None
            if self.ser:
                try: self.ser.close()
                except Exception: pass
                self.ser = None
            if self.proc:
                try: self.proc.wait(3)
                except subprocess.TimeoutExpired:
                    self.proc.kill(); self.proc.wait()
                self.proc = None
            if self.logf: self.logf.close(); self.logf = None
            self.state = 'stopped'

    def start(self, name):
        with self.lock:
            self.stop()
            path = fw_path(name); self.path = path
            data = open(path, 'rb').read()
            if len(data) > FLASH: raise ValueError('image larger than 16 MB')
            self.gen += 1
            self.fw = name if not os.path.isabs(name) else os.path.basename(name)
            self.base = 0
            self.sha = hashlib.sha256(data).hexdigest()
            flash = os.path.join(A.run_dir, 'web_flash.bin')     # fresh image on every (re)start
            with open(flash, 'wb') as f: f.write(data + b'\xff' * (FLASH - len(data)))
            qs = os.path.join(A.run_dir, 'web_qmp.sock'); ss = os.path.join(A.run_dir, 'web_serial.sock')
            for p in (qs, ss):
                if os.path.exists(p): os.unlink(p)
            with self.cond:
                self.log = bytearray(); self.base = 0; self.cond.notify_all()
            self.logf = open(os.path.join(A.run_dir, 'serial.log'), 'wb')
            self._append(('\r\n[viewer] ===== boot %s sha256=%s =====\r\n' % (self.fw, self.sha[:12])).encode())
            cmd = [A.qemu, '-M', 'm5stopwatch', '-drive', 'file=%s,if=mtd,format=raw' % flash, '-L', A.rom_dir,
                   '-display', 'none', '-qmp', 'unix:%s,server=on,wait=off' % qs,
                   '-chardev', 'socket,id=ser0,path=%s,server=on,wait=on' % ss, '-serial', 'chardev:ser0']
            self.state = 'starting'; self.error = ''
            self.proc = subprocess.Popen(cmd, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                                         stderr=open(os.path.join(A.run_dir, 'qemu_stderr.log'), 'wb'))
            # serial first (QEMU waits for it, so no boot output is lost), then QMP
            for _ in range(100):
                if self.proc.poll() is not None: break
                try:
                    s = socket.socket(socket.AF_UNIX); s.connect(ss); self.ser = s; break
                except OSError: time.sleep(0.05)
            for _ in range(100):
                if self.proc.poll() is not None: break
                try: self.qmp = QMP(qs); break
                except OSError: time.sleep(0.05)
            if not (self.ser and self.qmp):
                self.error = 'QEMU failed to start: ' + open(os.path.join(A.run_dir, 'qemu_stderr.log')).read()[-500:]
                self.state = 'error'; print(self.error, file=sys.stderr); return
            self.state = 'running'; self.t0 = time.time()
            try: sens_apply(dict(SENS))
            except Exception as e: print('sensor apply failed:', e, file=sys.stderr)
            threading.Thread(target=self._reader, args=(self.ser, self.gen), daemon=True).start()
            print('[viewer] running %s (sha256 %s), pid %d' % (self.fw, self.sha[:12], self.proc.pid))

    def _reader(self, s, gen):
        while True:
            try: d = s.recv(4096)
            except OSError: d = b''
            if not d: break
            if gen == self.gen: self._append(d)
        if gen == self.gen and self.state == 'running':
            self.state = 'exited'; self._append(b'\r\n[viewer] QEMU exited\r\n')

    def serial_write(self, data):
        with self.lock:
            if self.ser: self.ser.sendall(data)

    def qmpcmd(self, name, **kw):
        with self.lock:
            if not self.qmp: return None
            return self.qmp.cmd(name, **kw)

emu = Emu()
# live sensor values (re-applied after every (re)boot); QOM paths from patch 0005
SENS_PATH = {'accel-x': 'bmi270', 'accel-y': 'bmi270', 'accel-z': 'bmi270',
             'gyro-x': 'bmi270', 'gyro-y': 'bmi270', 'gyro-z': 'bmi270',
             'vbat-mv': 'm5pm1', 'vin-mv': 'm5pm1', 'vinout-mv': 'm5pm1', 'charging': 'm5pm1'}
SENS = {'accel-x': 0.0, 'accel-y': 0.0, 'accel-z': 1.0, 'gyro-x': 0.0, 'gyro-y': 0.0, 'gyro-z': 0.0,
        'vbat-mv': 4000, 'vin-mv': 5000, 'vinout-mv': 5000, 'charging': False}
SENS_OK = None   # None = unknown, False = binary without patch 0005

def sens_apply(vals):
    global SENS_OK
    errs = {}
    for k, v in vals.items():
        if k not in SENS_PATH: errs[k] = 'unknown'; continue
        v = bool(v) if k == 'charging' else (int(v) if k.endswith('-mv') else float(v))
        SENS[k] = v
        r = emu.qmpcmd('qom-set', path='/machine/' + SENS_PATH[k], property=k, value=v)
        if r and 'error' in r: errs[k] = r['error'].get('desc'); SENS_OK = False
        elif r: SENS_OK = True
    return errs
FRAME = os.path.join(A.run_dir, 'web_frame.png')
PAGE = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'index.html'), 'rb').read()

class H(BaseHTTPRequestHandler):
    protocol_version = 'HTTP/1.1'
    def log_message(self, *a): pass
    def send(self, code, body=b'', ctype='application/json', extra=()):
        self.send_response(code); self.send_header('Content-Type', ctype)
        self.send_header('Cache-Control', 'no-store, no-cache, must-revalidate, max-age=0')
        self.send_header('Pragma', 'no-cache'); self.send_header('Expires', '0')
        for k, v in extra: self.send_header(k, v)
        self.send_header('Content-Length', str(len(body))); self.end_headers(); self.wfile.write(body)
    def js(self, o, code=200): self.send(code, json.dumps(o).encode())
    def st(self):
        return {'fw': emu.fw, 'sha256': emu.sha, 'gen': emu.gen, 'state': emu.state, 'error': emu.error,
                'firmware': fw_list(), 'uptime': (time.time() - getattr(emu, 't0', time.time())) if emu.state == 'running' else 0,
                'sensors': SENS, 'sensors_ok': SENS_OK}

    def do_GET(self):
        u = urllib.parse.urlparse(self.path); q = urllib.parse.parse_qs(u.query)
        if u.path == '/frame.png':
            r = None
            try:
                with emu.lock:
                    r = emu.qmpcmd('screendump', filename=FRAME, format='png')
                    data = open(FRAME, 'rb').read() if r and 'return' in r else None
            except Exception: data = None
            if not data: return self.send(503, b'not running', 'text/plain')
            tag = '"%s"' % hashlib.md5(data).hexdigest()
            if self.headers.get('If-None-Match') == tag:      # unchanged frame -> 304, no body
                self.send_response(304); self.send_header('ETag', tag); self.send_header('X-Gen', str(emu.gen))
                self.send_header('Cache-Control', 'no-cache'); self.send_header('Content-Length', '0'); self.end_headers(); return
            self.send(200, data, 'image/png', [('X-Gen', str(emu.gen)), ('ETag', tag)])
        elif u.path == '/api/ping':                        # QMP round-trip latency
            t = time.perf_counter(); r = None
            try: r = emu.qmpcmd('query-status')
            except Exception: pass
            self.js({'qmp_ms': (time.perf_counter() - t) * 1000, 'status': (r or {}).get('return', {}).get('status'),
                     'uptime': (time.time() - getattr(emu, 't0', time.time())) if emu.state == 'running' else 0,
                     'gen': emu.gen, 'state': emu.state})
        elif u.path == '/api/state':
            self.js(self.st())
        elif u.path == '/api/log':                         # full current log (download)
            with emu.cond: d = bytes(emu.log)
            self.send(200, d, 'text/plain; charset=utf-8',
                      [('Content-Disposition', 'attachment; filename="serial-%s.log"' % re.sub(r'[^\w.-]', '_', emu.fw or 'x'))])
        elif u.path == '/api/serial':                      # SSE stream of UART0
            self.send_response(200); self.send_header('Content-Type', 'text/event-stream')
            self.send_header('Cache-Control', 'no-store'); self.send_header('Connection', 'close'); self.end_headers()
            self.close_connection = True
            gen = None; pos = 0
            try:
                while True:
                    with emu.cond:
                        if gen != emu.gen:
                            gen = emu.gen; pos = 0
                            self.wfile.write(('event: reset\ndata: %s\n\n' % json.dumps(self.st())).encode())
                        while pos >= emu.base + len(emu.log) and gen == emu.gen:
                            if not emu.cond.wait(15): break
                        pos = max(pos, emu.base)
                        chunk = bytes(emu.log[pos - emu.base:]) if gen == emu.gen else b''; pos += len(chunk)
                    if chunk:
                        self.wfile.write(('data: %s\n\n' % json.dumps(chunk.decode('utf-8', 'replace'))).encode())
                    else:
                        self.wfile.write(b': ping\n\n')
                    self.wfile.flush()
            except (BrokenPipeError, ConnectionResetError, OSError):
                return
        elif u.path in ('/', '/index.html'):
            self.send(200, PAGE, 'text/html; charset=utf-8')
        else:
            self.send(404, b'not found', 'text/plain')

    def do_POST(self):
        u = urllib.parse.urlparse(self.path); q = urllib.parse.parse_qs(u.query)
        body = self.rfile.read(int(self.headers.get('Content-Length') or 0))
        try:
            if u.path == '/input':
                o = json.loads(body); ev = []
                if o['t'] == 'touch':
                    ev = [{'type': 'abs', 'data': {'axis': 'x', 'value': int(o['x'] * 32767 / 465)}},
                          {'type': 'abs', 'data': {'axis': 'y', 'value': int(o['y'] * 32767 / 465)}},
                          {'type': 'btn', 'data': {'down': bool(o['d']), 'button': 'left'}}]
                elif o['t'] == 'key':
                    ev = [{'type': 'key', 'data': {'down': bool(o['d']), 'key': {'type': 'qcode', 'data': k}}} for k in o['k']]
                emu.qmpcmd('input-send-event', events=ev); return self.send(204)
            if u.path == '/api/sensor':
                errs = sens_apply(json.loads(body))
                return self.js({'sensors': SENS, 'errors': errs, 'sensors_ok': SENS_OK}, 400 if errs else 200)
            if u.path == '/api/serial':
                emu.serial_write(body); return self.send(204)
            if u.path == '/api/switch':
                emu.start(json.loads(body)['fw']); return self.js(self.st())
            if u.path == '/api/reset':                     # reboot same firmware with fresh flash
                emu.start(emu.path); return self.js(self.st())
            if u.path == '/api/upload':
                name = re.sub(r'[^\w.-]', '_', os.path.basename(q.get('name', ['upload.bin'])[0]))
                if not name.lower().endswith('.bin'): name += '.bin'
                if len(body) > FLASH or len(body) < 0x1000: return self.js({'error': 'size must be 4 KB .. 16 MB'}, 400)
                if body[0] != 0xE9: return self.js({'error': 'not a merged 0x0 image (byte 0 != 0xE9)'}, 400)
                open(os.path.join(UPL, name), 'wb').write(body)
                emu.start('uploads/' + name); return self.js(self.st())
        except Exception as e:
            return self.js({'error': str(e)}, 400)
        self.send(404, b'', 'text/plain')

import signal
def _bye(*_):
    emu.stop(); os._exit(0)
for _s in (signal.SIGTERM, signal.SIGHUP): signal.signal(_s, _bye)
try:
    emu.start(A.fw)
except ValueError as e:
    print(e, file=sys.stderr)
    if not fw_list(): sys.exit('no firmware in %s (run scripts/fetch-firmware.sh)' % A.fw_dir)
    emu.start(fw_list()[0]['name'])
srv = ThreadingHTTPServer((A.bind, A.port), H); srv.daemon_threads = True
print('M5StopWatch web viewer: http://%s:%d' % (A.bind, A.port))
try: srv.serve_forever()
except KeyboardInterrupt: pass
finally: emu.stop()
