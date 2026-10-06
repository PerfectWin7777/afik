"""Integration tests of the Rust relay (needs `cargo build` in rust_bridge/)."""

from __future__ import annotations

import os
import socket
import struct
import subprocess
import time
import unittest
from pathlib import Path

import pyflutter as pf
from pyflutter.core.bridge import RESYNC_CALLBACK_ID, read_frame
from pyflutter.core.render import (
    MSG_CALLBACK_EVENT,
    MSG_RENDER_TREE,
    MSG_TREE_PATCH,
    encode_frame,
    render_tree_frame,
    tree_patch_frame,
)
from pyflutter.generated import widget_pb2

ROOT = Path(__file__).resolve().parents[2]
BINARY = next(
    (p for p in (ROOT / "rust_bridge/target/debug/pyflutter-bridge",
                 ROOT / "rust_bridge/target/release/pyflutter-bridge") if p.exists()),
    None,
)


def _free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def _read_socket_frame(sock: socket.socket):
    return read_frame(sock.makefile("rb"))


# The CI job that builds the bridge sets PYFLUTTER_REQUIRE_BRIDGE=1: there, a missing binary is a
# failure instead of a silent skip.
REQUIRE_BRIDGE = os.environ.get("PYFLUTTER_REQUIRE_BRIDGE") == "1"


@unittest.skipIf(BINARY is None and not REQUIRE_BRIDGE, "rust bridge binary not built")
class TestRelay(unittest.TestCase):
    def setUp(self):
        if BINARY is None:
            self.fail("PYFLUTTER_REQUIRE_BRIDGE=1 but rust_bridge/target/{debug,release}/pyflutter-bridge is missing")
        self.port = _free_port()
        self.proc = subprocess.Popen(
            [str(BINARY), "--dart-port", str(self.port), "--token", "s3cret"],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
        )
        for _ in range(50):
            try:
                socket.create_connection(("127.0.0.1", self.port), timeout=0.2).close()
                break
            except OSError:
                time.sleep(0.1)

    def tearDown(self):
        self.proc.kill()
        self.proc.wait()

    def _connect(self, token: str | None = "s3cret") -> socket.socket:
        sock = socket.create_connection(("127.0.0.1", self.port), timeout=3)
        if token is not None:
            sock.sendall(encode_frame(0x06, token.encode()))
        return sock

    def _send(self, frame: bytes) -> None:
        self.proc.stdin.write(frame)
        self.proc.stdin.flush()

    def test_client_without_valid_token_is_rejected(self):
        self._send(render_tree_frame(pf.Text("hi")))
        bad = self._connect(token="wrong")
        bad.settimeout(2)
        self.assertEqual(bad.recv(1), b"")  # connection closed, nothing received

    def test_tree_is_relayed_and_cached_for_reconnection(self):
        self._send(render_tree_frame(pf.Text("hi")))
        first = self._connect()
        msg_type, _ = _read_socket_frame(first)
        self.assertEqual(msg_type, MSG_RENDER_TREE)
        first.close()
        time.sleep(0.3)
        second = self._connect()
        msg_type, _ = _read_socket_frame(second)
        self.assertEqual(msg_type, MSG_RENDER_TREE)

    def test_reconnection_after_patch_requests_full_resync(self):
        self._send(render_tree_frame(pf.Text("hi")))
        first = self._connect()
        _read_socket_frame(first)
        self._send(tree_patch_frame([{"id": "root", "props": {"text": "yo"}}]))
        msg_type, _ = _read_socket_frame(first)
        self.assertEqual(msg_type, MSG_TREE_PATCH)
        first.close()
        time.sleep(0.3)
        second = self._connect()
        # The stale cached tree must NOT be replayed; Python is asked to resend.
        frame = read_frame(self.proc.stdout)
        self.assertEqual(frame[0], MSG_CALLBACK_EVENT)
        event = widget_pb2.CallbackEvent()
        event.ParseFromString(frame[1])
        self.assertEqual(event.callback_id, RESYNC_CALLBACK_ID)
        second.close()

    def test_forged_huge_frame_is_refused(self):
        sock = self._connect()
        sock.sendall(struct.pack(">BI", MSG_CALLBACK_EVENT, 0xFFFFFFFF))
        sock.settimeout(2)
        self.assertEqual(sock.recv(1), b"")  # relay dropped the client instead of allocating 4 GiB


if __name__ == "__main__":
    unittest.main()
