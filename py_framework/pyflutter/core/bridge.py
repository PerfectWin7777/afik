"""
Drives the Rust bridge subprocess: sends the current widget tree,
listens for incoming CallbackEvent frames, invokes the matching Python
callback, then re-sends the updated tree.

This is the POC stand-in for the real pyflutter CLI (vision doc §5.1) —
same responsibility (own the bridge process, own the reload loop), much
smaller scope: no device detection, no keyboard-driven r/R/q yet, just
enough to prove the full duplex round trip without Flutter.
"""

from __future__ import annotations

import struct
import subprocess
from typing import Callable

from pyflutter.core.render import (
    MSG_CALLBACK_EVENT,
    MSG_RENDER_TREE,
    decode_callback_event,
    render_tree_frame,
)
from pyflutter.core.widget_base import Widget, invoke_callback


def read_frame(stream) -> tuple[int, bytes] | None:
    """Reads one [type byte][4-byte length][payload] frame from a
    subprocess stdout stream. Returns None on EOF.
    """
    header = stream.read(5)
    if len(header) < 5:
        return None
    msg_type, length = struct.unpack(">BI", header)
    payload = stream.read(length)
    return msg_type, payload


class BridgeSession:
    """Owns one running rust_bridge subprocess for the lifetime of a
    dev session (mirrors what `pyflutter run` will do for real, per
    vision doc §5.1).
    """

    def __init__(self, bridge_binary: str, extra_args: list[str] | None = None):
        self.process = subprocess.Popen(
            [bridge_binary, *(extra_args or [])],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=None,  # let Rust's eprintln! show up directly, useful while debugging
        )

    def send_tree(self, root: Widget) -> None:
        self.process.stdin.write(render_tree_frame(root))
        self.process.stdin.flush()

    def next_event(self):
        """Blocks until the next CallbackEvent arrives, or returns None
        on EOF (bridge process exited / closed stdout).
        """
        frame = read_frame(self.process.stdout)
        if frame is None:
            return None
        msg_type, payload = frame
        if msg_type != MSG_CALLBACK_EVENT:
            return self.next_event()  # ignore unexpected message types
        return decode_callback_event(payload)

    def close(self) -> None:
        self.process.stdin.close()
        self.process.terminate()
        self.process.wait(timeout=2)


def run_loop(bridge_binary: str, build_tree: Callable[[], Widget],
             max_iterations: int = 5) -> None:
    """Runs `max_iterations` rounds of: send tree -> wait for callback
    event -> invoke it -> re-send updated tree. Stops early if the
    bridge has no more callbacks to simulate (see main.rs: it looks for
    the first widget with a callback_id and "taps" it).
    """
    session = BridgeSession(bridge_binary)
    try:
        session.send_tree(build_tree())

        for i in range(max_iterations):
            event = session.next_event()
            if event is None:
                print(f"[python] bridge closed after {i} round(s)")
                break

            print(f"[python] received callback event: callback_id={event.callback_id}")
            invoke_callback(event.callback_id, dict(event.event_data))

            # Re-send the (mutated) tree so the bridge can simulate the
            # next tap. In the real system this send is triggered by
            # the app's own update()/page.update() call, not a fixed loop.
            session.send_tree(build_tree())
    finally:
        session.close()
