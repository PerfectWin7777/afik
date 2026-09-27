"""
Converts the in-memory Widget tree (see core/widget_base.py) into real
Protobuf bytes matching ir_spec/widget.proto, ready to be sent to the
Rust bridge.

Wire framing: 1-byte message type tag + 4-byte big-endian length
prefix + payload. This matches rust_bridge/src/main.rs's read_frame /
write_frame (see comments there for why a length prefix is needed on a
raw stream, and why a type tag — to allow RenderTree and CallbackEvent
to share the same stdin/stdout stream).
"""

from __future__ import annotations

import struct

from pyflutter.core.widget_base import Widget
from pyflutter.generated import widget_pb2

MSG_RENDER_TREE = 0x01
MSG_CALLBACK_EVENT = 0x02


def resolve_widget(widget: Any) -> Widget:
    """Recursively resolves any Component (or object implementing build())
    into its concrete primitive Widget tree.
    Preserves any 'slot' property assigned by a parent layout (e.g., Scaffold or AppBar).
    """
    slot = getattr(widget, "props", {}).get("slot")
    while hasattr(widget, "build") and callable(widget.build):
        widget = widget.build()
        if widget is None:
            raise ValueError("Component build() returned None. Must return a Widget.")
    if slot and isinstance(widget, Widget) and "slot" not in widget.props:
        widget.props["slot"] = slot
    return widget


def widget_to_proto(widget: Any) -> widget_pb2.Widget:
    """Recursively converts a Widget (and its children) to the
    generated protobuf Widget message.
    """
    resolved = resolve_widget(widget)
    msg = widget_pb2.Widget(
        type=resolved.widget_type,
        callback_id=resolved.callback_id,
    )
    for key, value in resolved.props.items():
        msg.props[key] = value
    for child in resolved.children:
        msg.children.append(widget_to_proto(child))
    return msg


def encode_frame(msg_type: int, payload: bytes) -> bytes:
    """Wraps a payload with the [type byte][4-byte length] header the
    Rust bridge expects.
    """
    header = struct.pack(">BI", msg_type, len(payload))
    return header + payload


def render_tree_frame(root: Any) -> bytes:
    """Encodes `root` as a framed RenderTree message, ready to write
    directly to the Rust bridge's stdin.
    """
    tree = widget_pb2.RenderTree(root=widget_to_proto(root))
    return encode_frame(MSG_RENDER_TREE, tree.SerializeToString())


def decode_callback_event(payload: bytes) -> widget_pb2.CallbackEvent:
    event = widget_pb2.CallbackEvent()
    event.ParseFromString(payload)
    return event

