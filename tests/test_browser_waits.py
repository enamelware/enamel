# Copyright (c) 2026 Mario Carabotta
# SPDX-License-Identifier: MIT
"""Issue #5: the style guide check never waits forever on the browser. A run
of the full check once sat for hours; every wait on Firefox now has a limit
and gives up with a message saying what never came.

These tests talk to a stand-in for Firefox's socket, not to Firefox.

    scripts/test.sh unit tests.test_browser_waits
"""
import json
import os
import socket
import sys
import threading
import time
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
import browser_check  # noqa: E402
from browser_session import Session  # noqa: E402


def frame(obj):
    data = json.dumps(obj).encode()
    return b"\x81" + bytes([126]) + len(data).to_bytes(2, "big") + data


class StandIn:
    """Accepts one connection. 'chatty' answers the handshake, then sends an
    event every 0.1 s and never answers a command; 'closes' hangs up during
    the handshake."""

    def __init__(self, kind):
        self.kind = kind
        self.server = socket.socket()
        self.server.bind(("127.0.0.1", 0))
        self.server.listen(1)
        self.port = self.server.getsockname()[1]
        self.stop = False
        threading.Thread(target=self.serve, daemon=True).start()

    def serve(self):
        conn, _ = self.server.accept()
        conn.recv(4096)
        if self.kind == "closes":
            conn.close()
            return
        conn.sendall(b"HTTP/1.1 101 Switching Protocols\r\n\r\n")
        try:
            while not self.stop:
                conn.sendall(frame({"method": "log.entryAdded", "params": {"level": "info"}}))
                time.sleep(0.1)
        except OSError:
            pass
        conn.close()

    def close(self):
        self.stop = True
        self.server.close()


class BrowserWaits(unittest.TestCase):
    def test_a_command_gives_up_at_its_limit_while_events_keep_coming(self):
        s = StandIn("chatty")
        try:
            session = Session(f"ws://127.0.0.1:{s.port}/session", timeout=120)
            start = time.monotonic()
            with self.assertRaises(TimeoutError) as e:
                session.call("script.callFunction", _limit=1)
            self.assertLess(time.monotonic() - start, 5)
            self.assertIn("script.callFunction", str(e.exception))
            self.assertTrue(session.events, "events that arrived meanwhile are kept")
            session.close()
        finally:
            s.close()

    def test_a_socket_closed_during_the_handshake_is_an_error_not_a_wait(self):
        s = StandIn("closes")
        try:
            with self.assertRaises(ConnectionError):
                Session(f"ws://127.0.0.1:{s.port}/session", timeout=5)
        finally:
            s.close()

    def test_a_script_that_never_finishes_says_which_one(self):
        s = StandIn("chatty")
        old = browser_check.RUN_LIMIT
        try:
            browser_check.RUN_LIMIT = 1
            ff = browser_check.Firefox.__new__(browser_check.Firefox)
            ff.s, ff.ctx = Session(f"ws://127.0.0.1:{s.port}/session", timeout=120), "ctx"
            with self.assertRaises(RuntimeError) as e:
                ff.run("async () => new Promise(() => {})", {}, "the Resize page check (full motion)")
            self.assertIn("the Resize page check (full motion) did not finish within 1 s", str(e.exception))
            ff.s.close()
        finally:
            browser_check.RUN_LIMIT = old
            s.close()

    def test_every_browser_call_has_a_limit(self):
        with open(os.path.join(ROOT, "tools", "browser_check.py")) as f:
            text = f.read()
        calls = text.count("self.s.call(")
        self.assertGreater(calls, 0)
        self.assertEqual(text.count("_limit="), calls, "a call to Firefox without a time limit")


if __name__ == "__main__":
    unittest.main()
