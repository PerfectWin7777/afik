"""
Base classes for the PyFlutter widget tree.
Lightweight, zero-dependency, and fully typed for IDE autocomplete and embedded runtimes.
"""

from __future__ import annotations

import itertools
import uuid
from typing import Any, Callable, Optional


_callback_registry: dict[str, Callable] = {}


def _register_callback(
    fn_or_id: Optional[Callable | str] = None,
    fn: Optional[Callable] = None,
) -> str:
    """Registers a Python callback and returns its unique callback_id.
    
    Supports:
        _register_callback(callable) -> str (auto-generated UUID)
        _register_callback(custom_id, callable) -> str (custom_id)
    """
    if fn is not None:
        callback_id = str(fn_or_id) if fn_or_id else uuid.uuid4().hex
        target_fn = fn
    elif callable(fn_or_id):
        callback_id = uuid.uuid4().hex
        target_fn = fn_or_id
    elif fn_or_id is None:
        return ""
    else:
        return str(fn_or_id)

    _callback_registry[callback_id] = target_fn
    return callback_id


def _call_callable(target: Callable, *args: Any, **kwargs: Any) -> Any:
    """Invokes target function with best matching arguments without repeated retries."""
    import inspect
    sig = None
    try:
        sig = inspect.signature(target)
    except (ValueError, TypeError):
        pass

    if sig is not None:
        params = list(sig.parameters.values())
        has_varargs = any(p.kind == inspect.Parameter.VAR_POSITIONAL for p in params)
        has_varkw = any(p.kind == inspect.Parameter.VAR_KEYWORD for p in params)

        if has_varargs and has_varkw:
            return target(*args, **kwargs)
        elif has_varargs:
            return target(*args)

        pos_params = [
            p for p in params
            if p.kind in (inspect.Parameter.POSITIONAL_ONLY, inspect.Parameter.POSITIONAL_OR_KEYWORD)
        ]
        kw_params = {
            p.name for p in params
            if p.kind in (inspect.Parameter.KEYWORD_ONLY, inspect.Parameter.POSITIONAL_OR_KEYWORD)
        }

        matched_kwargs = {k: v for k, v in kwargs.items() if k in kw_params}
        if matched_kwargs and len(matched_kwargs) == len(kwargs):
            return target(**matched_kwargs)

        if args and len(pos_params) > 0:
            return target(*args[:len(pos_params)])
        elif kwargs and len(pos_params) > 0:
            return target(*list(kwargs.values())[:len(pos_params)])
        else:
            return target()
    else:
        if kwargs:
            try:
                return target(**kwargs)
            except TypeError:
                pass
        if args:
            try:
                return target(*args)
            except TypeError:
                pass
        return target()


def invoke_callback(callback_id: str, event_data: dict[str, str]) -> None:
    """Invokes a registered callback with optional event data."""
    fn = _callback_registry.get(callback_id)
    if fn is None:
        return
    try:
        if event_data:
            _call_callable(fn, **event_data)
        else:
            _call_callable(fn)
    except Exception as e:
        from pyflutter.core.logger import logger
        logger.error(f"Error inside callback {callback_id}: {e}", exc_info=True)


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

    def add(self, child: Widget) -> Widget:
        """Appends a child widget to this container. Returns self for chaining."""
        self.children.append(child)
        return self

    def add_widget(self, child: Widget) -> Widget:
        """Appends a child widget (imperative Qt-style API). Returns self."""
        self.children.append(child)
        return self

    def add_widgets(self, *children: Widget) -> Widget:
        """Appends multiple child widgets to this container. Returns self."""
        for child in children:
            self.children.append(child)
        return self

    def add_layout(self, layout: Widget) -> Widget:
        """Appends a child layout (Qt-style addLayout). Returns self."""
        self.children.append(layout)
        return self

    def add_spacing(self, size: float = 8.0) -> Widget:
        """Appends spacing between children based on layout orientation."""
        from pyflutter.widgets.widgets import SizedBox
        if self.widget_type == "Row":
            self.children.append(SizedBox(width=size))
        elif self.widget_type in ("Column", "ListView"):
            self.children.append(SizedBox(height=size))
        else:
            self.children.append(SizedBox(width=size, height=size))
        return self

    def add_stretch(self, flex: int = 1) -> Widget:
        """Appends a flexible space (Qt-style addStretch). Returns self."""
        from pyflutter.widgets.widgets import Spacer
        self.children.append(Spacer(flex=flex))
        return self

    def add_divider(
        self,
        height: Optional[float] = 16.0,
        thickness: Optional[float] = 1.0,
        indent: Optional[float] = None,
        end_indent: Optional[float] = None,
        color: Optional[str] = None,
    ) -> Widget:
        """Appends a visual Divider line. Returns self."""
        from pyflutter.widgets.widgets import Divider
        self.children.append(Divider(height=height, thickness=thickness, indent=indent, end_indent=end_indent, color=color))
        return self

    def count(self) -> int:
        """Returns the number of child widgets (Qt QLayout.count)."""
        return len(self.children)

    def item_at(self, index: int) -> Optional[Widget]:
        """Returns the child widget at the given index (Qt QLayout.itemAt)."""
        if 0 <= index < len(self.children):
            return self.children[index]
        return None

    def insert_widget(self, index: int, child: Widget) -> Widget:
        """Inserts a child widget at the given index (Qt QLayout.insertWidget). Returns self."""
        self.children.insert(index, child)
        return self

    def remove_widget(self, child: Widget) -> Widget:
        """Removes a child widget if present (Qt QLayout.removeWidget). Returns self."""
        if child in self.children:
            self.children.remove(child)
        return self

    def clear(self) -> Widget:
        """Removes all child widgets from this container. Returns self."""
        self.children.clear()
        return self

    # Qt-style camelCase aliases for muscle memory
    addWidget = add_widget
    addWidgets = add_widgets
    addLayout = add_layout
    addSpacing = add_spacing
    addStretch = add_stretch
    addSpacer = add_stretch
    addDivider = add_divider
    itemAt = item_at
    insertWidget = insert_widget
    removeWidget = remove_widget

    def __enter__(self) -> Widget:
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    def to_ir_dict(self) -> dict:
        """Produces a dictionary mirroring the Protobuf Widget message."""
        return {
            "type": self.widget_type,
            "props": dict(self.props),
            "children": [c.to_ir_dict() for c in self.children],
            "callback_id": self.callback_id,
        }


class QtSignal:
    """
    Qt/PySide-style Signal for connecting callbacks and event handling.
    Enables `widget.signal.connect(handler)`, `.disconnect(handler)`, and `.emit(*args)`.
    """

    def __init__(
        self,
        owner: Widget,
        callback_prop: str = "callback_id",
        value_converter: Optional[Callable[[Any], Any]] = None,
    ):
        self.owner = owner
        self.callback_prop = callback_prop
        self.value_converter = value_converter
        self._slots: list[Callable] = []
        self._installed = False

    def connect(self, slot: Callable) -> QtSignal:
        """Connects a callback function (slot) to this signal. Returns self."""
        if slot not in self._slots:
            self._slots.append(slot)
        self._ensure_registered()
        return self

    def disconnect(self, slot: Optional[Callable] = None) -> QtSignal:
        """Disconnects a specific slot, or all slots if none specified. Returns self."""
        if slot is None:
            self._slots.clear()
        elif slot in self._slots:
            self._slots.remove(slot)
        return self

    def emit(self, *args: Any, **kwargs: Any) -> None:
        """Dispatches this signal immediately to all connected slots."""
        self._dispatch(*args, **kwargs)

    def _ensure_registered(self) -> None:
        if self._installed:
            return
        self._installed = True

        def _dispatcher(*args: Any, **kwargs: Any):
            if self.value_converter is not None:
                if args:
                    try:
                        args = (self.value_converter(args[0]), *args[1:])
                    except Exception:
                        pass
                elif "value" in kwargs:
                    try:
                        kwargs = dict(kwargs)
                        kwargs["value"] = self.value_converter(kwargs["value"])
                    except Exception:
                        pass
            self._dispatch(*args, **kwargs)

        cid = _register_callback(_dispatcher)
        if self.callback_prop == "callback_id":
            self.owner.callback_id = cid
        else:
            self.owner.props[self.callback_prop] = cid

    def _dispatch(self, *args: Any, **kwargs: Any) -> None:
        for slot in list(self._slots):
            try:
                _call_callable(slot, *args, **kwargs)
            except Exception as e:
                from pyflutter.core.logger import logger
                logger.error(f"Error executing slot {slot} for signal {self.callback_prop}: {e}", exc_info=True)

    def __call__(self, *args: Any, **kwargs: Any) -> None:
        self.emit(*args, **kwargs)


class Component(Widget):
    """
    Pythonic component base class (equivalent to Flutter's StatelessWidget / PyQt's QMainWindow).
    
    Supports both Declarative (`build(self) -> Widget`) and Imperative PyQt-style programming:
        self.layout = Column()
        self.layout.add_widget(Text("Hello"))
        self.btn = Button("Click")
        self.btn.clicked.connect(self.on_click)
        self.layout.add_widget(self.btn)
    """
    widget_type: str = "Component"

    def _ensure_layout(self) -> Widget:
        if getattr(self, "_central_widget", None) is None:
            from pyflutter.widgets.widgets import Column
            self._central_widget = Column()
        return self._central_widget

    @property
    def central_widget(self) -> Optional[Widget]:
        """Returns the central widget or layout of this component."""
        return getattr(self, "_central_widget", None)

    @central_widget.setter
    def central_widget(self, widget: Widget) -> None:
        self._central_widget = widget

    @property
    def layout(self) -> Optional[Widget]:
        """Returns the central layout of this component (Qt-style alias for central_widget)."""
        return getattr(self, "_central_widget", None)

    @layout.setter
    def layout(self, widget: Widget) -> None:
        self._central_widget = widget

    def set_central_widget(self, widget: Widget) -> Component:
        """Sets the central widget (Qt QMainWindow.setCentralWidget). Returns self."""
        self._central_widget = widget
        return self

    def set_layout(self, layout: Widget) -> Component:
        """Sets the central layout (Qt QWidget.setLayout). Returns self."""
        self._central_widget = layout
        return self

    setCentralWidget = set_central_widget
    setLayout = set_layout

    def add_widget(self, child: Widget) -> Component:
        """Appends a child widget to the central layout. Returns self."""
        layout = self._ensure_layout()
        layout.add_widget(child)
        return self

    def add(self, child: Widget) -> Component:
        """Appends a child widget to the central layout. Returns self."""
        return self.add_widget(child)

    def add_widgets(self, *children: Widget) -> Component:
        """Appends multiple child widgets to the central layout. Returns self."""
        layout = self._ensure_layout()
        layout.add_widgets(*children)
        return self

    def add_layout(self, child_layout: Widget) -> Component:
        """Appends a child layout (Qt addLayout). Returns self."""
        layout = self._ensure_layout()
        layout.add_layout(child_layout)
        return self

    def add_spacing(self, size: float = 8.0) -> Component:
        """Appends spacing to the central layout. Returns self."""
        layout = self._ensure_layout()
        layout.add_spacing(size)
        return self

    def add_stretch(self, flex: int = 1) -> Component:
        """Appends a flexible spacer to the central layout. Returns self."""
        layout = self._ensure_layout()
        layout.add_stretch(flex)
        return self

    def add_divider(
        self,
        height: Optional[float] = 16.0,
        thickness: Optional[float] = 1.0,
        color: Optional[str] = None,
    ) -> Component:
        """Appends a divider to the central layout. Returns self."""
        layout = self._ensure_layout()
        layout.add_divider(height=height, thickness=thickness, color=color)
        return self

    addWidget = add_widget
    addWidgets = add_widgets
    addLayout = add_layout
    addSpacing = add_spacing
    addStretch = add_stretch
    addSpacer = add_stretch
    addDivider = add_divider

    def build(self) -> Widget:
        """
        Builds the widget subtree.
        If not explicitly overridden, automatically synthesizes the UI tree
        from self.central_widget, self.layout, self.column, self.row, or self._central_widget,
        and wraps with a Scaffold if self.app_bar, self.drawer, self.fab, etc. are defined.
        """
        central = (
            getattr(self, "_central_widget", None)
            or getattr(self, "central_widget", None)
            or getattr(self, "layout", None)
            or getattr(self, "root", None)
            or getattr(self, "body", None)
            or getattr(self, "column", None)
            or getattr(self, "row", None)
        )

        app_bar = (
            getattr(self, "app_bar", None)
            or getattr(self, "appbar", None)
            or getattr(self, "app_bar_widget", None)
        )
        drawer = getattr(self, "drawer", None)
        fab = (
            getattr(self, "floating_action_button", None)
            or getattr(self, "fab", None)
        )
        bottom_bar = (
            getattr(self, "bottom_navigation_bar", None)
            or getattr(self, "bottom_bar", None)
        )

        if central is None:
            raise NotImplementedError(
                f"Component '{self.__class__.__name__}' must implement 'build(self) -> Widget' "
                f"or define an imperative layout attribute (e.g. self.column, self.layout, "
                f"self.set_central_widget(w), or self.add_widget(w))."
            )

        # Wrap in Scaffold if app-level elements are provided
        if app_bar is not None or drawer is not None or fab is not None or bottom_bar is not None:
            from pyflutter.widgets.widgets import Scaffold, AppBar
            effective_bar = AppBar(title=app_bar) if isinstance(app_bar, str) else app_bar
            return Scaffold(
                body=central,
                app_bar=effective_bar,
                drawer=drawer,
                floating_action_button=fab,
                bottom_navigation_bar=bottom_bar,
            )

        return central

    def update(self) -> None:
        """
        Triggers an immediate asynchronous UI update.
        Pushes the re-rendered widget tree to the connected device.
        """
        from pyflutter.app import update
        update()

    def show_snack_bar(
        self,
        message: str,
        *,
        duration: Any = None,
        action: Optional[str] = None,
        on_action: Optional[Callable[[], None]] = None,
        background_color: Optional[str] = None,
    ) -> None:
        """Displays a native SnackBar notification."""
        from pyflutter.plugins.overlay import show_snack_bar
        from pyflutter.core.style import Duration
        d = duration if duration is not None else Duration(seconds=4)
        show_snack_bar(
            message,
            duration=d,
            action=action,
            on_action=on_action,
            background_color=background_color,
        )

    def show_dialog(
        self,
        title: str,
        content: str,
        *,
        confirm_label: Optional[str] = "OK",
        cancel_label: Optional[str] = None,
        on_confirm: Optional[Callable[[], None]] = None,
        on_cancel: Optional[Callable[[], None]] = None,
    ) -> None:
        """Displays a native Material 3 AlertDialog."""
        from pyflutter.plugins.overlay import show_dialog
        show_dialog(
            title=title,
            content=content,
            confirm_label=confirm_label,
            cancel_label=cancel_label,
            on_confirm=on_confirm,
            on_cancel=on_cancel,
        )

    @property
    def navigator(self):
        """Returns the application Navigator for multi-page screen transitions."""
        from pyflutter.core.navigation import Navigator
        return Navigator


# Idiomatic Flutter alias for developers coming from Flutter
StatelessWidget = Component

# Modern Python OOP alias for screen/window root component
MainWindow = Component


def new_widget_id() -> str:
    return f"w{next(_id_counter)}"


_id_counter = itertools.count()
