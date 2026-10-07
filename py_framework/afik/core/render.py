"""
Converts the in-memory Widget tree (see core/widget_base.py) into real
Protobuf bytes or granular JSON TreePatches matching ir_spec/widget.proto,
ready to be sent to the Rust bridge and Flutter runtime.

Wire framing: 1-byte message type tag + 4-byte big-endian length
prefix + payload.
  0x01: MSG_RENDER_TREE     (Full tree Protobuf)
  0x02: MSG_CALLBACK_EVENT  (Dart -> Rust -> Python)
  0x03: MSG_PLUGIN_CALL     (Python -> Rust -> Dart)
  0x04: MSG_TREE_PATCH      (Granular diff JSON)
  0x05: MSG_PLUGIN_RESPONSE (Dart -> Rust -> Python)
"""

from __future__ import annotations

import copy
import json
import struct
from typing import Any, Optional

from afik.core.widget_base import Widget
from afik.generated import widget_pb2

MSG_RENDER_TREE = 0x01
MSG_CALLBACK_EVENT = 0x02
MSG_PLUGIN_CALL = 0x03
MSG_TREE_PATCH = 0x04
MSG_PLUGIN_RESPONSE = 0x05


def resolve_tree(widget: Any, is_root: bool = True) -> Widget:
    """Recursively resolves all Components in the tree into a concrete primitive Widget tree in a single pass.
    Preserves any 'slot' property assigned by a parent layout and ensures Component build() is only invoked once.

    A root resolution is one frame: when it succeeds, the State objects that were not reached
    are disposed (see ``afik.core.state.sweep_states``).
    """
    if not is_root:
        return _resolve_node(widget)

    from afik.core.state import begin_frame, sweep_states
    begin_frame()
    resolved = _resolve_node(widget)      # a build that raises leaves every state alone
    sweep_states()
    return resolved


def _segment(child: Any, index: int) -> str:
    """One step of a node's path: the widget type and its key or position among its siblings."""
    props = getattr(child, "props", None)
    key = props.get("key") if isinstance(props, dict) else None
    return f"{type(child).__name__}[{key if key else index}]"


def _resolve_node(widget: Any, path: str = "root", parent_path: str = "") -> Widget:
    from afik.core.state import _build_position

    slot = getattr(widget, "props", {}).get("slot")
    current = widget
    depth = 0
    while hasattr(current, "build") and callable(current.build):
        # A component may return another component: each level gets its own identity.
        _build_position.set((f"{path}~{depth}" if depth else path, parent_path))
        current = current.build()
        _build_position.set(None)
        depth += 1
        if current is None:
            raise ValueError(f"Component '{widget.__class__.__name__}.build()' returned None. Must return a Widget.")
    children = getattr(current, "children", None)
    if isinstance(current, Widget) and isinstance(children, list) and children:
        # Work on a copy: the source widgets (often cached by the user, e.g. an
        # imperative self.layout) must keep their Component children, otherwise
        # those components would be frozen at their first render.
        resolve_child = _resolve_page if current.widget_type == "MaterialApp" else _resolve_node
        resolved_children = [
            resolve_child(c, f"{path}/{_segment(c, i)}", path) for i, c in enumerate(children)
        ]
        current = copy.copy(current)
        current.props = dict(current.props)
        current.children = resolved_children
    if slot and isinstance(current, Widget) and "slot" not in current.props:
        current.props["slot"] = slot
    return current


def _resolve_page(page: Any, path: str = "root", parent_path: str = "") -> Widget:
    """Resolves one Navigator page; the states created under it belong to that page."""
    from afik.core.state import _current_owner, page_owner_token
    token = _current_owner.set(page_owner_token(page))
    try:
        return _resolve_node(page, path, parent_path)
    finally:
        _current_owner.reset(token)


def resolve_widget(widget: Any) -> Widget:
    """Backward-compatible resolution of Component or Widget."""
    slot = getattr(widget, "props", {}).get("slot")
    current = widget
    while hasattr(current, "build") and callable(current.build):
        current = current.build()
        if current is None:
            raise ValueError(f"Component '{widget.__class__.__name__}.build()' returned None. Must return a Widget.")
    if slot and isinstance(current, Widget) and "slot" not in current.props:
        current.props["slot"] = slot
    return current


def assign_node_ids(widget: Any, path: str = "root") -> None:
    """Assigns deterministic hierarchical structural IDs (_nid) to all widgets in the tree."""
    resolved = resolve_widget(widget)
    key = resolved.props.get("key")
    nid = f"{path}[{key}]" if key else path
    resolved.props["_nid"] = nid

    for idx, child in enumerate(resolved.children):
        assign_node_ids(child, f"{nid}.{idx}")


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
        msg.props[key] = str(value)
    for child in resolved.children:
        msg.children.append(widget_to_proto(child))
    return msg


def widget_to_snapshot(widget: Any) -> dict:
    """Recursively serializes a Widget into a lightweight dict tree for diffing."""
    resolved = resolve_widget(widget)
    return {
        "_nid": resolved.props.get("_nid", ""),
        "type": resolved.widget_type,
        "props": dict(resolved.props),
        "callback_id": resolved.callback_id,
        "children": [widget_to_snapshot(c) for c in resolved.children],
    }


def diff_snapshots(old: Optional[dict], new: Optional[dict]) -> Optional[list[dict]]:
    """Compares two tree snapshots.
    Returns:
        - None: if structural change occurred (root type changed, child count changed, etc.)
                which requires a full RenderTree rebuild.
        - list[dict]: list of granular update operations:
          [{"id": "root.0.1", "props": {"text": "5"}, "remove": ["color"], "callback_id": "..."}]

        ``props`` holds the props whose value is new or changed (an empty string is a real
        value, not a removal); ``remove`` lists the props that no longer exist.
    """
    if old is None or new is None:
        return None
    if old.get("type") != new.get("type"):
        return None
    if old.get("_nid") != new.get("_nid"):
        # Keyed nodes moved/replaced: Dart cannot address the new id, resend everything.
        return None
    if len(old.get("children", [])) != len(new.get("children", [])):
        return None

    updates: list[dict] = []

    # Check prop differences
    old_props = old.get("props", {})
    new_props = new.get("props", {})
    changed_props: dict[str, str] = {}

    for k, v in new_props.items():
        if k not in old_props or old_props[k] != v:
            changed_props[k] = v

    removed_props = [k for k in old_props if k not in new_props]

    old_cb = old.get("callback_id", "")
    new_cb = new.get("callback_id", "")
    cb_changed = (old_cb != new_cb)

    if changed_props or removed_props or cb_changed:
        op: dict[str, Any] = {"id": new.get("_nid", "")}
        if changed_props:
            op["props"] = changed_props
        if removed_props:
            op["remove"] = removed_props
        if cb_changed:
            op["callback_id"] = new_cb
        updates.append(op)

    # Check children recursively
    old_children = old.get("children", [])
    new_children = new.get("children", [])
    for oc, nc in zip(old_children, new_children):
        child_diff = diff_snapshots(oc, nc)
        if child_diff is None:
            return None  # structural change inside child subtree
        updates.extend(child_diff)

    return updates


def encode_frame(msg_type: int, payload: bytes) -> bytes:
    """Wraps a payload with the [type byte][4-byte length] header the
    Rust bridge expects.
    """
    header = struct.pack(">BI", msg_type, len(payload))
    return header + payload


def render_tree_frame(root: Any, *, resolved: bool = False, sweep: bool = True) -> bytes:
    """Encodes `root` as a framed RenderTree message, ready to write
    directly to the Rust bridge's stdin.

    `resolved=True` means `root` is already a concrete tree with node ids assigned
    (and callbacks already swept), which avoids a second resolution pass.
    """
    if resolved:
        concrete_root = root
    else:
        concrete_root = resolve_tree(root)
        assign_node_ids(concrete_root)
        if sweep:
            from afik.core.widget_base import collect_active_callback_ids, sweep_stale_callbacks
            sweep_stale_callbacks(collect_active_callback_ids(concrete_root))
    tree = widget_pb2.RenderTree(root=widget_to_proto(concrete_root))
    return encode_frame(MSG_RENDER_TREE, tree.SerializeToString())


def tree_patch_frame(updates: list[dict]) -> bytes:
    """Encodes a list of node update patches as a framed MSG_TREE_PATCH message."""
    payload = json.dumps({"type": "patch", "updates": updates}).encode("utf-8")
    return encode_frame(MSG_TREE_PATCH, payload)


def decode_callback_event(payload: bytes) -> widget_pb2.CallbackEvent:
    event = widget_pb2.CallbackEvent()
    event.ParseFromString(payload)
    return event
