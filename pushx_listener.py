#!/usr/bin/env python3
"""
pushx_listener.py - intercept Reolink battery-cam PIR motion pushes.

Reolink Argus 2 (FreeRTOS / GM8136) battery cams POST a JSON alarm to
    http://pushx.reolink.com/devices/<UID>/notifications
on PIR wake. Redirect that hostname to this host via LAN DNS (see
docs/dns-redirect.md) and every motion event lands here as a plain HTTP POST
on port 80. No cloud, no hub, no camera modification.

Run (port 80 needs root):
    sudo python3 pushx_listener.py --log /tmp/pushx.log

Options:
    --port N      listen port (default 80; the cam always dials :80)
    --log PATH    append events to PATH (also always printed to stdout)
    --forward     relay to the real pushx too, so Reolink app push still works

Stdlib only. Wire on_motion() into your NVR / Home Assistant when ready.
"""
import argparse
import datetime
import http.client
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

REAL_PUSHX_IP = "104.18.24.250"  # pushx.reolink.com (Cloudflare) - verify, may rotate
OK_BODY = b'{"status":{"code":0,"detail":"OK"},"data":{"sent":0}}'

ARGS = None


def ts():
    return datetime.datetime.now().isoformat(timespec="seconds")


def emit(line):
    print(line, flush=True)
    if ARGS and ARGS.log:
        try:
            with open(ARGS.log, "a") as f:
                f.write(line + "\n")
        except OSError as e:
            print(f"[warn] log write failed: {e}", flush=True)


def on_motion(uid, alarm):
    """HOOK: this is where a motion event enters your system.

    For now it just logs. To integrate, fire your camera's motion/record
    trigger here, keyed on `uid` (map uid -> camera).
    """
    emit(
        f"[{ts()}] >>> MOTION uid={uid} "
        f"device={alarm.get('device')!r} name={alarm.get('name')!r} "
        f"channel={alarm.get('channel')} alarmTime={alarm.get('alarmTime')}"
    )


class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, *a):  # silence noisy default logging
        pass

    def _reply(self, code=200, body=OK_BODY):
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Connection", "keep-alive")
        self.end_headers()
        if body:
            self.wfile.write(body)

    def _read_body(self):
        length = int(self.headers.get("Content-Length") or 0)
        return self.rfile.read(length) if length else b""

    def do_POST(self):
        raw = self._read_body()
        emit(f"[{ts()}] POST {self.path} from {self.client_address[0]} len={len(raw)}")
        emit(f"    body: {raw.decode('utf-8', 'replace')}")
        uid = None
        parts = self.path.strip("/").split("/")
        if len(parts) >= 2 and parts[0] == "devices":
            uid = parts[1]
        try:
            data = json.loads(raw or b"{}")
        except ValueError:
            data = {}
        if data.get("type") == "alarm":
            on_motion(uid, data.get("alarm", {}))
        if ARGS.forward:
            self._forward("POST", raw)
        else:
            self._reply()

    def do_GET(self):
        emit(f"[{ts()}] GET {self.path} from {self.client_address[0]}")
        if ARGS.forward:
            self._forward("GET", b"")
        else:
            self._reply()

    def _forward(self, method, body):
        try:
            conn = http.client.HTTPConnection(REAL_PUSHX_IP, 80, timeout=5)
            headers = {k: v for k, v in self.headers.items()}
            headers["Host"] = "pushx.reolink.com"
            conn.request(method, self.path, body=body or None, headers=headers)
            r = conn.getresponse()
            rb = r.read()
            self.send_response(r.status)
            self.send_header("Content-Type", r.getheader("Content-Type", "application/json"))
            self.send_header("Content-Length", str(len(rb)))
            self.send_header("Connection", "keep-alive")
            self.end_headers()
            self.wfile.write(rb)
            conn.close()
        except OSError as e:
            emit(f"[warn] forward failed: {e}")
            self._reply()


def main():
    global ARGS
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=80)
    ap.add_argument("--log", default=None)
    ap.add_argument("--forward", action="store_true")
    ARGS = ap.parse_args()
    srv = ThreadingHTTPServer(("0.0.0.0", ARGS.port), Handler)
    emit(f"[{ts()}] pushx listener on :{ARGS.port}  forward={ARGS.forward}  log={ARGS.log}")
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        emit("bye")


if __name__ == "__main__":
    main()
