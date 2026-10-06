"""
Reactive State Management for PyFlutter.
Provides Signals, Computed values, Effects, Batched updates,
and Flutter-standard StatefulComponent / State architecture.
"""

from __future__ import annotations

import contextvars
import threading
import weakref
from typing import Any, Callable, Generic, Optional, TypeVar, Union

from pyflutter.core.logger import logger
from pyflutter.core.widget_base import Component, Widget

T = TypeVar("T")

_UNSET = object()
_batch_depth: int = 0
_batched_listeners: set[Callable[[], None]] = set()
_batch_lock = threading.RLock()
_flushing_batch: bool = False          # True while the listeners of a finished batch run
_MUTABLE_CONTAINERS = (list, dict, set, bytearray)


def _same(a: Any, b: Any) -> bool:
    """Value equality that never raises and copes with array-likes (numpy, pandas)."""
    if a is b:
        return True
    try:
        result = a == b
        return bool(result.all()) if hasattr(result, "all") else bool(result)
    except Exception:
        return False
_active_signal_tracker: contextvars.ContextVar[Optional[Callable[[Signal[Any]], None]]] = (
    contextvars.ContextVar("_active_signal_tracker", default=None)
)

_state_registry: dict[Any, State] = {}
_call_site_counters: dict[tuple[str, int], int] = {}


def reset_call_site_counters() -> None:
    """Resets call-site counters at the start of a frame build."""
    _call_site_counters.clear()


def infer_call_site_key(cls: type) -> str:
    """Infers a deterministic, stable key for a stateful widget based on its caller code location."""
    import inspect
    caller = inspect.currentframe().f_back
    while caller:
        module_name = caller.f_globals.get("__name__", "")
        if not (module_name == "pyflutter" or module_name.startswith("pyflutter.")):
            break
        caller = caller.f_back
    if caller:
        base_name = caller.f_code.co_filename.replace("\\", "/").split("/")[-1]
        line = caller.f_lineno
        loc = (base_name, line)
        idx = _call_site_counters.get(loc, 0)
        _call_site_counters[loc] = idx + 1
        return f"{cls.__name__}@{base_name}:{line}#{idx}"
    return f"{cls.__name__}#auto"


# --- State lifecycle: mark and sweep ------------------------------------------------------
#
# Every full resolution of the tree is a "frame". A State that was reached during the frame is
# marked with its number; at the end of the frame the states that were not reached are
# disposed and forgotten, because their widget left the tree (a removed branch, a popped page).
# A page that is only covered by another one in the Navigator is not rebuilt either, but its
# states must survive until the page is popped, as in Flutter.

_frame_id = 0
ROOT_PAGE = "root"
_current_owner: contextvars.ContextVar[Any] = contextvars.ContextVar("_current_owner", default=None)


def begin_frame() -> None:
    """Starts a new frame: states reached from now on belong to it."""
    global _frame_id
    _frame_id += 1


def current_frame() -> int:
    return _frame_id


def page_owner_token(page: Any) -> Any:
    """Identifies the Navigator page the widgets under ``page`` belong to."""
    from pyflutter.core.navigation import Navigator
    if not Navigator.can_pop():
        return ROOT_PAGE
    return id(page)


def _covered_owners() -> set:
    """Owners whose states must be kept although their page was not rebuilt (covered pages)."""
    from pyflutter.core.navigation import Navigator
    stack = Navigator._stack
    if len(stack) <= 1:
        return set()
    return {ROOT_PAGE} | {id(page) for page in stack[1:]}


def dispose_state(state: "State") -> None:
    """Calls ``state.dispose()`` once, logging (not raising) what it raises."""
    if getattr(state, "_disposed", False):
        return
    state._disposed = True
    try:
        state.dispose()
    except Exception:
        logger.opt(exception=True).error("Error during state disposal of {}", type(state).__name__)


def sweep_states() -> list["State"]:
    """Disposes the states that were not reached during the current frame. Returns them."""
    covered = _covered_owners()
    removed: list[State] = []
    for key, state in list(_state_registry.items()):
        if state._last_seen_frame == _frame_id:
            continue
        if state._owner_token is not None and state._owner_token in covered:
            continue
        _state_registry.pop(key, None)
        removed.append(state)
    for state in removed:
        dispose_state(state)
    return removed


def clear_state_registry() -> None:
    """Disposes and forgets every cached State (used during hot restart)."""
    reset_call_site_counters()
    states = list(_state_registry.values())
    _state_registry.clear()
    for state in states:
        dispose_state(state)


class Signal(Generic[T]):
    """
    Reactive state primitive holding a value of type T.
    
    Usage:
        count = pf.Signal(0)
        
        # Read:
        print(count.value)    # or count()
        
        # Write:
        count.value = 5       # or count(5)
        
        # Transform:
        count.update(lambda c: c + 1)
        
        # Listen:
        count.add_listener(lambda: print("Value changed!"))
    """

    def __init__(
        self,
        initial_value: T,
        *,
        auto_update: bool = True,
        equals: Optional[Callable[[Any, Any], bool]] = None,
    ):
        self._value: T = initial_value
        self._listeners: list[Callable[[], None]] = []
        self._auto_update = auto_update
        self._equals: Callable[[Any, Any], bool] = equals or _same

    @property
    def value(self) -> T:
        tracker = _active_signal_tracker.get()
        if tracker is not None:
            tracker(self)
        return self._value

    @value.setter
    def value(self, new_value: T) -> None:
        if not self._equals(self._value, new_value):
            self._value = new_value
            self._notify_listeners()

    def get(self) -> T:
        return self.value

    def set(self, new_value: T) -> None:
        self.value = new_value

    def update(self, fn: Callable[[T], T]) -> None:
        """Sets the value to ``fn(current)``; ``fn`` must RETURN the new value.

        To change a list / dict / set in place use :meth:`mutate` instead: ``update(lambda l:
        l.append(x))`` would store ``None``, so it raises a TypeError.
        """
        new_value = fn(self._value)
        if new_value is None and isinstance(self._value, _MUTABLE_CONTAINERS):
            raise TypeError(
                "Signal.update() must return the new value (the function returned None). "
                "Use Signal.mutate() to change a list, dict or set in place."
            )
        self.value = new_value

    def mutate(self, fn: Callable[[T], Any]) -> None:
        """Changes the current value IN PLACE with ``fn(value)`` and always notifies the listeners.

            todos = pf.Signal([])
            todos.mutate(lambda items: items.append("buy milk"))
        """
        fn(self._value)
        self._notify_listeners()

    def add_listener(self, listener: Callable[[], None]) -> None:
        """Registers a listener callback invoked whenever the value changes."""
        if listener not in self._listeners:
            self._listeners.append(listener)

    def remove_listener(self, listener: Callable[[], None]) -> None:
        """Removes a previously registered listener callback."""
        if listener in self._listeners:
            self._listeners.remove(listener)

    def subscribe(self, listener: Callable[[T], None]) -> Callable[[], None]:
        """
        Subscribes to value changes, invoking listener(new_val) on each change.
        Returns an unsubscribe handle.
        """
        def _wrapper():
            listener(self._value)

        self.add_listener(_wrapper)
        return lambda: self.remove_listener(_wrapper)

    def _notify_listeners(self) -> None:
        with _batch_lock:
            if _batch_depth > 0:
                _batched_listeners.update(self._listeners)
                if self._auto_update:
                    _batched_listeners.add(_request_update)
                return
            flushing = _flushing_batch

        for l in list(self._listeners):
            try:
                l()
            except Exception as e:
                logger.error("Error in Signal listener: {}", e)

        # while a finished batch is flushed, the batch asks for the single frame itself
        if self._auto_update and not flushing:
            _request_update()

    def __call__(self, new_value: Any = _UNSET) -> T:
        """Calling signal() reads the value; calling signal(val) sets it."""
        if new_value is not _UNSET:
            self.value = new_value
        return self.value

    def __str__(self) -> str:
        return str(self.value)

    def __repr__(self) -> str:
        return f"Signal({self._value!r})"


# Flutter-native alias for developers coming from Flutter
ValueNotifier = Signal


class Computed(Signal[T]):
    """
    A reactive signal derived from other signals.
    Automatically tracks dependencies and updates when any dependency changes.
    """

    def __init__(self, compute_fn: Callable[[], T], *, auto_update: bool = True):
        self._compute_fn = compute_fn
        self._dependencies: set[Signal[Any]] = set()
        initial_val = self._recompute()
        super().__init__(initial_val, auto_update=auto_update)

    def _recompute(self) -> T:
        def _track(sig: Signal[Any]):
            if sig not in self._dependencies:
                self._dependencies.add(sig)
                sig.add_listener(self._on_dependency_changed)

        prev = _active_signal_tracker.get()
        _active_signal_tracker.set(_track)
        try:
            return self._compute_fn()
        finally:
            _active_signal_tracker.set(prev)

    def _on_dependency_changed(self) -> None:
        new_val = self._recompute()
        if not self._equals(self._value, new_val):
            self.value = new_val

    def __repr__(self) -> str:
        return f"Computed({self._value!r})"


class Effect:
    """
    Runs a side-effect function immediately and re-executes it whenever any
    accessed Signal changes.
    """

    def __init__(self, effect_fn: Callable[[], Optional[Callable[[], None]]]):
        self._effect_fn = effect_fn
        self._cleanup_fn: Optional[Callable[[], None]] = None
        self._dependencies: set[Signal[Any]] = set()
        self._is_disposed = False
        self._run()

    def _run(self) -> None:
        if self._is_disposed:
            return
        if self._cleanup_fn is not None:
            try:
                self._cleanup_fn()
            except Exception as e:
                logger.error(f"Error in effect cleanup: {e}")
            self._cleanup_fn = None

        def _track(sig: Signal[Any]):
            if sig not in self._dependencies:
                self._dependencies.add(sig)
                sig.add_listener(self._on_dependency_changed)

        prev = _active_signal_tracker.get()
        _active_signal_tracker.set(_track)
        try:
            res = self._effect_fn()
            if callable(res):
                self._cleanup_fn = res
        finally:
            _active_signal_tracker.set(prev)

    def _on_dependency_changed(self) -> None:
        if not self._is_disposed:
            self._run()

    def dispose(self) -> None:
        """Stops the effect and runs any cleanup handler."""
        self._is_disposed = True
        for sig in self._dependencies:
            sig.remove_listener(self._on_dependency_changed)
        self._dependencies.clear()
        if self._cleanup_fn is not None:
            try:
                self._cleanup_fn()
            except Exception:
                pass
            self._cleanup_fn = None


def _request_update() -> None:
    from pyflutter.app import update
    update()


class _BatchContext:
    def __enter__(self):
        global _batch_depth
        with _batch_lock:
            _batch_depth += 1
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        global _batch_depth, _flushing_batch
        with _batch_lock:
            _batch_depth -= 1
            if _batch_depth > 0:
                return False
            pending = list(_batched_listeners)
            _batched_listeners.clear()
            _flushing_batch = True
        # The signals did change even if the block raised, so listeners always run; the exception
        # (if any) then propagates unchanged.
        try:
            wants_frame = False
            for listener in pending:
                if listener is _request_update:
                    wants_frame = True
                    continue
                try:
                    listener()
                except Exception as e:
                    logger.error("Error in batched listener: {}", e)
            if wants_frame:
                _request_update()
        finally:
            with _batch_lock:
                _flushing_batch = False
        return False


def batch(fn: Optional[Callable[[], Any]] = None):
    """
    Batches multiple signal mutations into a single listener notification
    and single UI re-render.
    
    Can be used as a function or as a context manager:
        with pf.batch():
            user.value = "John"
            age.value = 30
            
        pf.batch(lambda: [user.set("John"), age.set(30)])
    """
    ctx = _BatchContext()
    if fn is not None:
        with ctx:
            return fn()
    return ctx


class Watch(Component):
    """
    A reactive widget that automatically observes all Signals accessed within its builder.
    Whenever any observed Signal changes, Watch triggers an immediate update.
    """

    widget_type = "Watch"

    def __init__(self, builder: Callable[[], Widget]):
        super().__init__()
        self.builder = builder
        self._tracked_signals: set[Signal[Any]] = set()

    def build(self) -> Widget:
        # A new Watch is created at every parent rebuild. The listener only holds a
        # weak reference to it and unregisters itself once the Watch is gone, so
        # signals never accumulate listeners (and rebuilds) across frames.
        self_ref = weakref.ref(self)

        def _track(signal: Signal[Any]):
            if signal not in self._tracked_signals:
                self._tracked_signals.add(signal)

                def _listener() -> None:
                    watch = self_ref()
                    if watch is None:
                        signal.remove_listener(_listener)
                    else:
                        watch._on_signal_changed()

                signal.add_listener(_listener)

        prev_listener = _active_signal_tracker.get()
        _active_signal_tracker.set(_track)
        try:
            return self.builder()
        finally:
            _active_signal_tracker.set(prev_listener)

    def _on_signal_changed(self) -> None:
        self.update()


class SignalBuilder(Component):
    """
    Builds a widget tree based on the value of a Signal or ValueNotifier.
    Equivalent to Flutter's ValueListenableBuilder.
    """

    widget_type = "SignalBuilder"

    def __init__(
        self,
        signal: Signal[Any],
        builder: Callable[[Any], Widget],
        *,
        value_listenable: Optional[Signal[Any]] = None,
    ):
        super().__init__()
        self.signal = signal or value_listenable
        if self.signal is None:
            raise ValueError("SignalBuilder requires a signal or value_listenable argument.")
        self.builder = builder
        from pyflutter.app import update
        if not getattr(self.signal, "_auto_update", True):
            self.signal.add_listener(update)

    def build(self) -> Widget:
        return self.builder(self.signal.value)

    def _on_signal_changed(self) -> None:
        self.update()


# Flutter-native alias
ValueListenableBuilder = SignalBuilder


class State:
    """
    The logic and internal state for a StatefulComponent.
    Equivalent to Flutter's State<T>.
    """

    # Class-level defaults: a subclass that overrides __init__ without calling super() still works.
    _widget: Optional["StatefulComponent"] = None
    _last_seen_frame: int = -1
    _owner_token: Any = None
    _disposed: bool = False

    def __init__(self):
        self._widget: Optional[StatefulComponent] = None

    @property
    def widget(self) -> StatefulComponent:
        """The current configuration widget."""
        if self._widget is None:
            raise RuntimeError("State.widget accessed before state was initialized.")
        return self._widget

    def init_state(self) -> None:
        """Called when this state object is inserted into the tree."""
        pass

    def did_update_widget(self, old_widget: StatefulComponent) -> None:
        """Called whenever the parent component rebuilds and provides a new widget."""
        pass

    def dispose(self) -> None:
        """Called once when the widget leaves the tree for good (removed branch, popped page,
        hot restart). Stop timers, threads and subscriptions here."""
        pass

    def set_state(self, fn: Optional[Callable[[], None]] = None):
        """
        Notifies the framework that the internal state of this object has changed.
        Can be used as a function or as a context manager:
        
        Example:
            self.set_state(lambda: setattr(self, "counter", self.counter + 1))
            
            # Or with context manager:
            with self.set_state():
                self.counter += 1
        """

        class _SetStateContext:
            def __enter__(inner_self):
                pass

            def __exit__(inner_self, exc_type, exc_val, exc_tb):
                if exc_type is None:
                    from pyflutter.app import update
                    update()

        if fn is not None:
            fn()
            from pyflutter.app import update
            update()
            return None
        return _SetStateContext()

    def build(self) -> Widget:
        raise NotImplementedError("State subclasses must implement the build() method.")


class StatefulComponent(Component):
    """
    A component that has mutable state.
    Equivalent to Flutter's StatefulWidget.
    
    Subclasses implement create_state() -> State.
    """

    widget_type = "StatefulComponent"

    def __init__(self, *, key: Optional[Any] = None, **props: Any):
        super().__init__(**props)
        self.key = key if key is not None else infer_call_site_key(self.__class__)
        self._state: Optional[State] = None

    def create_state(self) -> State:
        raise NotImplementedError("StatefulComponent must implement create_state()")

    def get_or_create_state(self) -> State:
        if self.key is not None:
            registry_key = (self.__class__, self.key)
            if registry_key in _state_registry:
                existing_state = _state_registry[registry_key]
                existing_state._last_seen_frame = _frame_id
                existing_state._owner_token = _current_owner.get()
                old_w = existing_state._widget
                existing_state._widget = self
                if old_w is not None and old_w is not self:
                    existing_state.did_update_widget(old_w)
                self._state = existing_state
                return existing_state
            else:
                new_state = self.create_state()
                new_state._widget = self
                new_state._last_seen_frame = _frame_id
                new_state._owner_token = _current_owner.get()
                _state_registry[registry_key] = new_state
                new_state.init_state()
                self._state = new_state
                return new_state

        if self._state is None:
            self._state = self.create_state()
            self._state._widget = self
            self._state.init_state()
        else:
            old_w = self._state._widget
            self._state._widget = self
            if old_w is not None and old_w is not self:
                self._state.did_update_widget(old_w)
        return self._state

    def build(self) -> Widget:
        state = self.get_or_create_state()
        return state.build()


# Idiomatic Flutter alias
StatefulWidget = StatefulComponent
