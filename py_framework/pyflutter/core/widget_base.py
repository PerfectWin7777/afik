"""
Base classes for the PyFlutter widget tree.
Lightweight, zero-dependency, and fully typed for IDE autocomplete and embedded runtimes.
"""

from __future__ import annotations

import itertools
import uuid
from typing import Any, Callable, Optional


_callback_registry: dict[str, Callable] = {}


def _register_callback(fn: Optional[Callable]) -> str:
    """Registers a Python callback and returns its unique callback_id."""
    if fn is None:
        return ""
    callback_id = uuid.uuid4().hex
    _callback_registry[callback_id] = fn
    return callback_id


def invoke_callback(callback_id: str, event_data: dict[str, str]) -> None:
    """Invokes a registered callback with optional event data."""
    fn = _callback_registry.get(callback_id)
    if fn is None:
        return
    if event_data:
        fn(**event_data)
    else:
        fn()


def clear_callbacks() -> None:
    """Clears all registered callbacks (used during hot reload/restart)."""
    _callback_registry.clear()


class Widget:
    """
    Base class for every PyFlutter widget.
    
    Subclasses define typed constructors with docstrings for full IDE support,
    and automatically serialize properties for the Protobuf IR bridge.
    """

    widget_type: str = "Widget"

    def __init__(self, **props: Any):
        self.props: dict[str, str] = {}
        self.children: list[Widget] = []
        self.callback_id: str = ""
        self._populate_props(props)

    def _populate_props(self, props: dict[str, Any]) -> None:
        raw_props = props.pop("raw_props", None)
        for k, v in props.items():
            if v is not None:
                if isinstance(v, bool):
                    self.props[k] = "true" if v else "false"
                else:
                    self.props[k] = str(v)
        if raw_props:
            for k, v in raw_props.items():
                self.props[str(k)] = str(v)

    def padding(
        self,
        all: Optional[float] = None,
        *,
        horizontal: Optional[float] = None,
        vertical: Optional[float] = None,
        top: Optional[float] = None,
        bottom: Optional[float] = None,
        left: Optional[float] = None,
        right: Optional[float] = None,
    ) -> Widget:
        """Wraps this widget in a Padding widget."""
        from pyflutter.widgets.widgets import Padding
        return Padding(
            self,
            all=all,
            horizontal=horizontal,
            vertical=vertical,
            top=top,
            bottom=bottom,
            left=left,
            right=right,
        )

    def center(self) -> Widget:
        """Wraps this widget in a Center widget."""
        from pyflutter.widgets.widgets import Center
        return Center(self)

    def expanded(self, flex: int = 1) -> Widget:
        """Wraps this widget in an Expanded widget."""
        from pyflutter.widgets.widgets import Expanded
        return Expanded(self, flex=flex)

    def card(
        self,
        elevation: Optional[float] = None,
        color: Optional[str] = None,
        margin: Optional[float] = None,
        border_radius: Optional[float] = None,
    ) -> Widget:
        """Wraps this widget in a Card widget."""
        from pyflutter.widgets.widgets import Card
        return Card(
            self,
            elevation=elevation,
            color=color,
            margin=margin,
            border_radius=border_radius,
        )

    def add_widget(self, child: Widget) -> Widget:
        """Appends a child widget (imperative Qt-style API). Returns self."""
        self.children.append(child)
        return self

    def to_ir_dict(self) -> dict:
        """Produces a dictionary mirroring the Protobuf Widget message."""
        return {
            "type": self.widget_type,
            "props": dict(self.props),
            "children": [c.to_ir_dict() for c in self.children],
            "callback_id": self.callback_id,
        }


class Component(Widget):
    """
    Pythonic component base class (equivalent to Flutter's StatelessWidget).
    
    Subclasses encapsulate state and UI subtrees by overriding `build(self) -> Widget`.
    This provides true OOP design, modularity, and clean separation of concerns.
    """
    widget_type: str = "Component"

    def build(self) -> Widget:
        raise NotImplementedError(
            f"Component '{self.__class__.__name__}' must implement the 'build()' method."
        )

    def update(self) -> None:
        """
        Triggers an immediate asynchronous UI update.
        Pushes the re-rendered widget tree to the connected device.
        """
        from pyflutter.app import update
        update()


# Idiomatic Flutter alias for developers coming from Flutter
StatelessWidget = Component


def new_widget_id() -> str:
    return f"w{next(_id_counter)}"


_id_counter = itertools.count()
