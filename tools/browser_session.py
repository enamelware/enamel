# Copyright (c) 2026 Mario Carabotta
# SPDX-License-Identifier: MIT
"""A small websocket client for the browser check (Python standard library only).

browser_check.py starts its own headless Firefox and drives it over WebDriver
BiDi through this Session: it sends one command at a time and gives up with a
clear message when an answer never comes.
"""
import base64, json, os, socket, struct, time


class Session:
    def __init__(self, ws_url, timeout=30):
        host, path = ws_url[len("ws://"):].split("/", 1)
        h, p = host.split(":")
        self.sock = socket.create_connection((h, int(p)), timeout=timeout)
        key = base64.b64encode(os.urandom(16)).decode()
        self.sock.sendall((f"GET /{path} HTTP/1.1\r\nHost: {host}\r\nUpgrade: websocket\r\n"
                           f"Connection: Upgrade\r\nSec-WebSocket-Key: {key}\r\n"
                           "Sec-WebSocket-Version: 13\r\n\r\n").encode())
        buf = b""
        while b"\r\n\r\n" not in buf:
            chunk = self.sock.recv(4096)
            if not chunk:  # closed before answering: never wait on it
                self.sock.close()
                raise ConnectionError("browser socket closed during the handshake")
            buf += chunk
        head, self.buf = buf.split(b"\r\n\r\n", 1)
        if b" 101 " not in head.split(b"\r\n")[0]:
            raise ConnectionError(head.decode(errors="replace"))
        self.next_id = 0
        self.events = []

    def _need(self, n):
        while len(self.buf) < n:
            chunk = self.sock.recv(1 << 20)
            if not chunk:
                raise EOFError("browser socket closed")
            self.buf += chunk

    def _recv(self):
        payload = b""
        while True:
            self._need(2)
            b1, b2 = self.buf[0], self.buf[1]
            n, off = b2 & 0x7F, 2
            if n == 126:
                self._need(4); n = struct.unpack(">H", self.buf[2:4])[0]; off = 4
            elif n == 127:
                self._need(10); n = struct.unpack(">Q", self.buf[2:10])[0]; off = 10
            self._need(off + n)
            payload += self.buf[off:off + n]
            self.buf = self.buf[off + n:]
            if b1 & 0x80:
                return json.loads(payload)

    def call(self, method, _limit=None, **params):
        """Send one command and return its result. With _limit (seconds), give
        up with TimeoutError once that long has passed without the answer, even
        while other messages keep arriving."""
        self.next_id += 1
        msg = json.dumps({"id": self.next_id, "method": method, "params": params}).encode()
        n = len(msg)
        if n < 126:
            hdr = b"\x81" + bytes([0x80 | n])
        elif n < 65536:
            hdr = b"\x81\xfe" + struct.pack(">H", n)
        else:
            hdr = b"\x81\xff" + struct.pack(">Q", n)
        mask = os.urandom(4)
        self.sock.sendall(hdr + mask + bytes(b ^ mask[i % 4] for i, b in enumerate(msg)))
        end = time.monotonic() + _limit if _limit else None
        default = self.sock.gettimeout()
        while True:
            if end is not None:
                left = end - time.monotonic()
                if left <= 0:
                    raise TimeoutError(f"{method} gave no answer within {_limit:g} s")
                self.sock.settimeout(min(left, default) if default else left)
            try:
                r = self._recv()
            except socket.timeout:
                if end is not None and time.monotonic() >= end - 0.05:
                    raise TimeoutError(f"{method} gave no answer within {_limit:g} s") from None
                raise
            finally:
                self.sock.settimeout(default)
            if r.get("id") == self.next_id:
                if "error" in r:
                    raise RuntimeError(f"{method}: {r['error']}")
                return r.get("result", {})
            self.events.append(r)

    def close(self):
        self.sock.close()
