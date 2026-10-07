"""
Drives the Rust bridge subprocess: sends the current widget tree or diff patches,
listens for incoming CallbackEvent and PluginResponse frames, invokes the matching
Python callback, then re-sends the updated tree.
"""

from __future__ import annotations

import struct
import subprocess
from typing import Callable, Optional

from afik.core.render import (
    MSG_CALLBACK_EVENT,
    MSG_PLUGIN_RESPONSE,
    assign_node_ids,
    decode_callback_event,
    diff_snapshots,
    render_tree_frame,
    tree_patch_frame,
    widget_to_snapshot,
)
from afik.core.widget_base import Widget, invoke_callback

# Sent by the Rust relay when a Dart client connected and its tree is outdated.
RESYNC_CALLBACK_ID = "__afik_resync__"
MAX_FRAME_BYTES = 64 * 1024 * 1024


def read_frame(stream) -> tuple[int, bytes] | None:
    """Reads one [type byte][4-byte length][payload] frame from a
    subprocess stdout stream. Returns None on EOF (including a truncated frame).
    """
    header = stream.read(5)
    if len(header) < 5:
        return None
    msg_type, length = struct.unpack(">BI", header)
    if length > MAX_FRAME_BYTES:
        raise ValueError(f"Bridge frame of {length} bytes exceeds the {MAX_FRAME_BYTES} byte limit")
    payload = stream.read(length) if length else b""
    if len(payload) < length:
        return None
    return msg_type, payload


class BridgeSession:
    """Owns one running rust_bridge subprocess for the lifetime of a
    dev session (mirrors what `afik run` will do for real, per
    vision doc §5.1).
    """

    def __init__(self, bridge_binary: str, extra_args: list[str] | None = None):
        self.process = subprocess.Popen(
            [bridge_binary, *(extra_args or [])],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=None,  # let Rust's eprintln! show up directly
        )
        self._last_snapshot: Optional[dict] = None

    def reset_snapshot(self) -> None:
        """Clears the cached tree snapshot (used during hot restart)."""
        self._last_snapshot = None

    def send_tree(self, root: Widget, force_full: bool = False, resolved: bool = False) -> None:
        """Sends the widget tree to the bridge. Uses granular TreePatch diffing
        whenever possible, falling back to full RenderTree if structural changes occurred.

        ``resolved=True`` says ``root`` already went through ``resolve_tree`` (the runner does it
        to tag the root), so the Components are not built a second time.
        """
        if self.process.poll() is not None:
            raise RuntimeError(
                f"Rust bridge process exited prematurely (exit code: {self.process.returncode})."
            )
        try:
            from afik.core.render import resolve_tree
            from afik.core.widget_base import collect_active_callback_ids, sweep_stale_callbacks

            if resolved:
                concrete_root = root
            else:
                concrete_root = resolve_tree(root)
            assign_node_ids(concrete_root)
            new_snapshot = widget_to_snapshot(concrete_root)

            # Prune unreferenced callbacks from memory
            active_ids = collect_active_callback_ids(concrete_root)
            sweep_stale_callbacks(active_ids)

            if not force_full and self._last_snapshot is not None:
                diff = diff_snapshots(self._last_snapshot, new_snapshot)
                if diff is not None:
                    if len(diff) == 0:
                        # Perfect match: zero bytes needed over the wire
                        return
                    if len(diff) <= 60:
                        # Send optimized granular patch
                        self._last_snapshot = new_snapshot
                        self.process.stdin.write(tree_patch_frame(diff))
                        self.process.stdin.flush()
                        return

            # Full tree snapshot
            self._last_snapshot = new_snapshot
            self.process.stdin.write(render_tree_frame(concrete_root, resolved=True))
            self.process.stdin.flush()
        except (BrokenPipeError, OSError) as e:
            raise RuntimeError(f"Failed to communicate with Rust bridge: {e}")

    def next_event(self):
        """Blocks until the next frame arrives from the bridge.
        Returns (msg_type, decoded_payload) or None on EOF.
        """
        while True:
            frame = read_frame(self.process.stdout)
            if frame is None:
                return None
            msg_type, payload = frame
            if msg_type == MSG_CALLBACK_EVENT:
                return (MSG_CALLBACK_EVENT, decode_callback_event(payload))
            if msg_type == MSG_PLUGIN_RESPONSE:
                return (MSG_PLUGIN_RESPONSE, payload)
            # unknown frame type: ignore and keep reading

    def close(self) -> None:
        if self.process.poll() is None:
            try:
                self.process.stdin.close()
            except Exception:
                pass
            try:
                self.process.terminate()
                self.process.wait(timeout=1)
            except Exception:
                try:
                    self.process.kill()
                except Exception:
                    pass

    def __del__(self):
        self.close()


def run_loop(bridge_binary: str, build_tree: Callable[[], Widget],
             max_iterations: int = 5) -> None:
    """Runs `max_iterations` rounds of: send tree -> wait for callback
    event -> invoke it -> re-send updated tree.
    """
    session = BridgeSession(bridge_binary)
    try:
        session.send_tree(build_tree())
        for _ in range(max_iterations):
            event_pair = session.next_event()
            if event_pair is None:
                break
            msg_type, event = event_pair
            if msg_type == MSG_CALLBACK_EVENT and event:
                invoke_callback(event.callback_id, dict(event.event_data))
                session.send_tree(build_tree())
    finally:
        session.close()
