"""
Base classes for the PyFlutter widget tree.
Lightweight, zero-dependency, and fully typed for IDE autocomplete and embedded runtimes.
"""

from __future__ import annotations

import itertools
import threading
import uuid
from collections import OrderedDict
from typing import Any, Callable, Optional


_callback_registry: dict[str, Callable] = {}
_registry_lock = threading.RLock()

# Callbacks that are not attached to any widget (SnackBar action, dialog buttons).
# They survive frame sweeps, are one-shot (invoking one removes its whole group)
# and the oldest ones are evicted past _MAX_PINNED so they can never leak.
_pinned_callbacks: "OrderedDict[str, Optional[str]]" = OrderedDict()
_MAX_PINNED = 64


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

    with _registry_lock:
        _callback_registry[callback_id] = target_fn
    return callback_id


def _register_pinned_callback(
    callback_id: str,
    fn: Callable,
    group: Optional[str] = None,
) -> str:
    """Registers a one-shot callback that is not tied to a widget of the tree.

    All callbacks sharing the same `group` are discarded as soon as one of them fires.
    """
    with _registry_lock:
        _callback_registry[callback_id] = fn
        _pinned_callbacks[callback_id] = group
        while len(_pinned_callbacks) > _MAX_PINNED:
            old_id, _ = _pinned_callbacks.popitem(last=False)
            _callback_registry.pop(old_id, None)
    return callback_id


def _call_callable(target: Callable, *args: Any, **kwargs: Any) -> Any:
    """Calls a slot / callback with the arguments it can take, like a Qt slot.

    ``args`` are positional values (a Qt signal's arguments, ``QtSignal.emit(1, 2)``), ``kwargs`` are
    named values (the event data sent by Flutter, ``{"value": "abc"}``). The slot may take fewer
    arguments than are available - extra positional values are dropped, as with PyQt - and the
    rules are:

    1. positional values fill the slot's positional parameters first;
    2. remaining parameters are filled by name from ``kwargs``;
    3. a required parameter nobody names gets the event's main value (``kwargs["value"]``, else the
       first value) once, and ``None`` after that, so ``on_click=lambda e: ...`` works when a button
       sends no data instead of failing with a TypeError;
    4. ``**kwargs`` collects the named values left; ``*args`` collects all positional values.
    """
    import inspect

    try:
        sig = inspect.signature(target)
    except (ValueError, TypeError):
        # builtins without a signature: try the richest call first
        for attempt in ((args, kwargs), (args, {}), ((), kwargs)):
            if attempt == ((), {}):
                continue
            try:
                return target(*attempt[0], **attempt[1])
            except TypeError:
                continue
        return target()

    params = list(sig.parameters.values())
    var_pos = any(p.kind is p.VAR_POSITIONAL for p in params)
    var_kw = any(p.kind is p.VAR_KEYWORD for p in params)
    positional = [p for p in params if p.kind in (p.POSITIONAL_ONLY, p.POSITIONAL_OR_KEYWORD)]
    keyword_only = [p for p in params if p.kind is p.KEYWORD_ONLY]

    if var_pos:
        call_args = list(args)
    else:
        call_args = list(args[: len(positional)])
    bound = {p.name for p in positional[: len(call_args)]}
    unused = {k: v for k, v in kwargs.items() if k not in bound}

    call_kwargs: dict[str, Any] = {}
    waiting = [p for p in positional[len(call_args):] + keyword_only]
    for p in waiting:                                     # by name
        if p.name in unused:
            call_kwargs[p.name] = unused.pop(p.name)
    main_given = False
    for p in waiting:                                     # required and still unnamed
        if p.name in call_kwargs or p.default is not p.empty:
            continue
        if unused and not main_given:
            key = "value" if "value" in unused else next(iter(unused))
            call_kwargs[p.name] = unused.pop(key)
            main_given = True
        else:
            call_kwargs[p.name] = None
    if var_kw:
        call_kwargs.update(unused)

    # a POSITIONAL_ONLY parameter cannot be passed by name: move those into the positional list
    for p in positional[len(call_args):]:
        if p.kind is p.POSITIONAL_ONLY and p.name in call_kwargs:
            call_args.append(call_kwargs.pop(p.name))
    return target(*call_args, **call_kwargs)


def invoke_callback(callback_id: str, event_data: dict[str, str]) -> None:
    """Invokes a registered callback with optional event data."""
    with _registry_lock:
        fn = _callback_registry.get(callback_id)
        if callback_id in _pinned_callbacks:
            group = _pinned_callbacks.pop(callback_id)
            _callback_registry.pop(callback_id, None)
            if group is not None:
                for cid in [c for c, g in _pinned_callbacks.items() if g == group]:
                    _pinned_callbacks.pop(cid, None)
                    _callback_registry.pop(cid, None)
    if fn is None:
        from pyflutter.core.logger import logger
        logger.debug("Ignoring event for unknown or expired callback {}", callback_id)
        return
    try:
        if event_data:
            _call_callable(fn, **event_data)
        else:
            _call_callable(fn)
    except Exception as e:
        from pyflutter.core.logger import logger
        logger.opt(exception=True).error("Error inside callback {}: {}", callback_id, e)


def clear_callbacks() -> None:
    """Clears all registered callbacks (used during hot reload/restart)."""
    with _registry_lock:
        _callback_registry.clear()
        _pinned_callbacks.clear()
        _active_callback_generations.clear()


_active_callback_generations: list[set[str]] = []


def collect_active_callback_ids(widget: Any) -> set[str]:
    """Recursively collects all callback IDs currently present in a widget tree."""
    ids: set[str] = set()
    cb_id = getattr(widget, "callback_id", "")
    if cb_id:
        ids.add(cb_id)
    props = getattr(widget, "props", {})
    if isinstance(props, dict):
        for k, v in props.items():
            if (k.endswith("_callback_id") or k == "callback_id") and isinstance(v, str) and v:
                ids.add(v)
    for child in getattr(widget, "children", []):
        ids.update(collect_active_callback_ids(child))
    return ids


def sweep_stale_callbacks(active_ids: set[str], retain_generations: int = 2) -> None:
    """Retains callbacks from recent frames while purging unreferenced stale callbacks to prevent memory leaks."""
    global _active_callback_generations
    with _registry_lock:
        _active_callback_generations.append(set(active_ids))
        if len(_active_callback_generations) > retain_generations:
            _active_callback_generations = _active_callback_generations[-retain_generations:]

        surviving_ids = set().union(*_active_callback_generations) if _active_callback_generations else set()
        stale_keys = [
            cid for cid in _callback_registry
            if cid not in surviving_ids and cid not in _pinned_callbacks
        ]
        for cid in stale_keys:
            _callback_registry.pop(cid, None)


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

    def _notify_dirty(self) -> None:
        """Triggers an immediate reactive update if an app runner is active."""
        try:
            from pyflutter.app import update
            update()
        except Exception:
            pass

    def set_enabled(self, enabled: bool = True, *, auto_update: bool = True) -> Widget:
        """Enables or disables the widget (Qt QWidget.setEnabled())."""
        self.props["enabled"] = "true" if enabled else "false"
        if auto_update:
            self._notify_dirty()
        return self

    def is_enabled(self) -> bool:
        """Returns True if the widget is enabled (Qt QWidget.isEnabled())."""
        return self.props.get("enabled", "true") != "false"

    def set_visible(self, visible: bool = True, *, auto_update: bool = True) -> Widget:
        """Shows or hides the widget (Qt QWidget.setVisible())."""
        self.props["visible"] = "true" if visible else "false"
        if auto_update:
            self._notify_dirty()
        return self

    def is_visible(self) -> bool:
        """Returns True if the widget is visible (Qt QWidget.isVisible())."""
        return self.props.get("visible", "true") != "false"

    def set_text(self, text: Any, *, auto_update: bool = True) -> Widget:
        """Updates text/label content (Qt QLabel.setText() / QPushButton.setText())."""
        val_str = str(text.value if hasattr(text, "value") else text)
        self.props["text"] = val_str
        self.props["value"] = val_str
        self.props["label"] = val_str
        if auto_update:
            self._notify_dirty()
        return self

    def text(self) -> str:
        """Returns the current text or label (Qt QLabel.text())."""
        return self.props.get("text") or self.props.get("value") or self.props.get("label") or ""

    def set_value(self, value: Any, *, auto_update: bool = True) -> Widget:
        """Updates numeric or boolean value (Qt QSlider.setValue / QCheckBox.setChecked)."""
        val = value.value if hasattr(value, "value") else value
        if isinstance(val, bool):
            self.props["value"] = "true" if val else "false"
        else:
            self.props["value"] = str(val)
        if auto_update:
            self._notify_dirty()
        return self

    def value(self) -> str:
        """Returns the current value property."""
        return self.props.get("value", "")

    def set_color(self, color: str, *, auto_update: bool = True) -> Widget:
        """Sets the primary foreground or text color."""
        self.props["color"] = color
        if auto_update:
            self._notify_dirty()
        return self

    def set_background_color(self, color: str, *, auto_update: bool = True) -> Widget:
        """Sets the background color."""
        self.props["background_color"] = color
        if auto_update:
            self._notify_dirty()
        return self

    def set_tooltip(self, message: str, *, auto_update: bool = True) -> Widget:
        """Sets a hover tooltip on this widget (Qt QWidget.setToolTip())."""
        self.props["tooltip"] = message
        if auto_update:
            self._notify_dirty()
        return self

    # Qt-style camelCase aliases
    setEnabled = set_enabled
    isEnabled = is_enabled
    setVisible = set_visible
    isVisible = is_visible
    setText = set_text
    setValue = set_value
    setColor = set_color
    setBackgroundColor = set_background_color
    setToolTip = set_tooltip
    setTooltip = set_tooltip

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
            extracted_val = None
            if args:
                extracted_val = args[0]
            elif "value" in kwargs:
                extracted_val = kwargs["value"]
            elif "text" in kwargs:
                extracted_val = kwargs["text"]
            elif "checked" in kwargs:
                extracted_val = kwargs["checked"]

            if extracted_val is not None and self.value_converter is not None:
                try:
                    extracted_val = self.value_converter(extracted_val)
                except Exception:
                    pass

            if extracted_val is not None:
                self._dispatch(extracted_val, *args[1:], **kwargs)
            else:
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
                logger.opt(exception=True).error("Error executing slot {} for signal {}: {}", slot, self.callback_prop, e)

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

    def set_menu_bar(self, menu_bar: Widget) -> Component:
        """Sets the menu bar (Qt QMainWindow.setMenuBar). Returns self."""
        self._menu_bar = menu_bar
        return self

    def set_status_bar(self, status_bar: Widget) -> Component:
        """Sets the status bar (Qt QMainWindow.setStatusBar). Returns self."""
        self._status_bar = status_bar
        return self

    def add_tool_bar(self, tool_bar: Widget) -> Component:
        """Adds a toolbar to this window (Qt QMainWindow.addToolBar). Returns self."""
        if not hasattr(self, "_tool_bars"):
            self._tool_bars = []
        self._tool_bars.append(tool_bar)
        return self

    setMenuBar = set_menu_bar
    setStatusBar = set_status_bar
    addToolBar = add_tool_bar

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

        menu_bar = getattr(self, "_menu_bar", None)
        tool_bars = getattr(self, "_tool_bars", [])
        status_bar = getattr(self, "_status_bar", None)

        if menu_bar is not None or tool_bars or status_bar is not None:
            from pyflutter.widgets.widgets import Column
            body_items: list[Widget] = []
            if menu_bar is not None:
                body_items.append(menu_bar)
            for tb in tool_bars:
                body_items.append(tb)
            body_items.append(central.expanded())
            if status_bar is not None:
                body_items.append(status_bar)
            central = Column(children=body_items)

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
        duration_ms: Optional[int] = None,
        action: Optional[str] = None,
        on_action: Optional[Callable[[], None]] = None,
        background_color: Optional[str] = None,
    ) -> None:
        """Displays a native SnackBar notification (`duration` in seconds or a Duration)."""
        from pyflutter.plugins.overlay import show_snack_bar
        show_snack_bar(
            message,
            duration=duration,
            duration_ms=duration_ms,
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
