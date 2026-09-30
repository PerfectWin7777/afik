"""
Unit test suite for PyFlutter Reactive State Management (Signals, Computed, Effects, Batch, Watch, StatefulComponent).
"""

from __future__ import annotations

import unittest
from pyflutter.core.state import (
    Signal,
    ValueNotifier,
    Computed,
    Effect,
    batch,
    Watch,
    SignalBuilder,
    ValueListenableBuilder,
    StatefulComponent,
    State,
    clear_state_registry,
)
from pyflutter.widgets.widgets import Column, Text, Button
from pyflutter.core.render import render_tree_frame, resolve_widget


class TestSignal(unittest.TestCase):
    def test_signal_read_write_update(self):
        count = Signal(10, auto_update=False)
        self.assertEqual(count.value, 10)
        self.assertEqual(count(), 10)
        self.assertEqual(count.get(), 10)

        # Setting via property
        count.value = 20
        self.assertEqual(count.value, 20)

        # Setting via call
        count(30)
        self.assertEqual(count.value, 30)

        # Update via lambda
        count.update(lambda c: c + 5)
        self.assertEqual(count.value, 35)

    def test_signal_listeners_and_subscribe(self):
        sig = Signal("hello", auto_update=False)
        history = []

        unsub = sig.subscribe(lambda val: history.append(val))

        sig.value = "world"
        sig.value = "pyflutter"
        self.assertEqual(history, ["world", "pyflutter"])

        unsub()
        sig.value = "ignored"
        self.assertEqual(history, ["world", "pyflutter"])


class TestComputed(unittest.TestCase):
    def test_computed_single_and_multi_dependency(self):
        first_name = Signal("Ada", auto_update=False)
        last_name = Signal("Lovelace", auto_update=False)

        full_name = Computed(lambda: f"{first_name.value} {last_name.value}", auto_update=False)
        self.assertEqual(full_name.value, "Ada Lovelace")

        history = []
        full_name.subscribe(lambda val: history.append(val))

        first_name.value = "Augusta"
        self.assertEqual(full_name.value, "Augusta Lovelace")
        self.assertEqual(history, ["Augusta Lovelace"])

        last_name.value = "King"
        self.assertEqual(full_name.value, "Augusta King")
        self.assertEqual(history, ["Augusta Lovelace", "Augusta King"])


class TestEffect(unittest.TestCase):
    def test_effect_execution_and_cleanup(self):
        count = Signal(1, auto_update=False)
        runs = []
        cleanups = []

        def side_effect():
            current = count.value
            runs.append(current)
            return lambda: cleanups.append(f"clean_{current}")

        effect = Effect(side_effect)
        self.assertEqual(runs, [1])
        self.assertEqual(cleanups, [])

        count.value = 2
        self.assertEqual(runs, [1, 2])
        self.assertEqual(cleanups, ["clean_1"])

        effect.dispose()
        self.assertEqual(cleanups, ["clean_1", "clean_2"])

        count.value = 3
        # No more executions after dispose
        self.assertEqual(runs, [1, 2])


class TestBatch(unittest.TestCase):
    def test_batched_mutations(self):
        a = Signal(1, auto_update=False)
        b = Signal(10, auto_update=False)
        notifications = []

        a.add_listener(lambda: notifications.append("a"))
        b.add_listener(lambda: notifications.append("b"))

        with batch():
            a.value = 2
            a.value = 3
            b.value = 20
            b.value = 30
            # Listeners should not have run yet inside the batch
            self.assertEqual(len(notifications), 0)

        # After exiting batch, each listener is triggered once
        self.assertEqual(sorted(notifications), ["a", "b"])


class TestWatchAndSignalBuilder(unittest.TestCase):
    def test_watch_reactive_rebuild(self):
        sig = Signal("alpha", auto_update=False)
        widget = Watch(lambda: Text(f"Val: {sig.value}"))

        resolved = resolve_widget(widget)
        self.assertEqual(resolved.props.get("value"), "Val: alpha")

        sig.value = "beta"
        resolved = resolve_widget(widget)
        self.assertEqual(resolved.props.get("value"), "Val: beta")

    def test_signal_builder(self):
        count = ValueNotifier(5, auto_update=False)
        builder_widget = SignalBuilder(
            signal=count,
            builder=lambda val: Text(f"Count: {val}"),
        )
        resolved = resolve_widget(builder_widget)
        self.assertEqual(resolved.props.get("value"), "Count: 5")

        count.value = 15
        resolved = resolve_widget(builder_widget)
        self.assertEqual(resolved.props.get("value"), "Count: 15")


class TestStatefulComponent(unittest.TestCase):
    def setUp(self):
        clear_state_registry()

    def test_state_lifecycle_and_mutation(self):
        lifecycle = []

        class CounterState(State):
            def __init__(self):
                super().__init__()
                self.count = 0

            def init_state(self):
                lifecycle.append("init_state")

            def did_update_widget(self, old_widget):
                lifecycle.append(f"did_update_widget from step {old_widget.step}")

            def increment(self):
                with self.set_state():
                    self.count += self.widget.step

            def build(self):
                return Button(f"Count: {self.count}", on_pressed=self.increment)

        class CounterWidget(StatefulComponent):
            def __init__(self, step=1, key="counter_1"):
                super().__init__(key=key)
                self.step = step

            def create_state(self):
                return CounterState()

        # First mount
        w1 = CounterWidget(step=1)
        btn1 = resolve_widget(w1)
        self.assertEqual(btn1.props.get("label"), "Count: 0")
        self.assertEqual(lifecycle, ["init_state"])

        # Mutate state
        state = w1.get_or_create_state()
        state.increment()
        btn1_after = resolve_widget(w1)
        self.assertEqual(btn1_after.props.get("label"), "Count: 1")

        # Parent rebuilds with new widget instance having step=5 and same key
        w2 = CounterWidget(step=5)
        btn2 = resolve_widget(w2)
        # Preserves accumulated count=1
        self.assertEqual(btn2.props.get("label"), "Count: 1")
        self.assertIn("did_update_widget from step 1", lifecycle)

        # Mutate again with new step=5
        state2 = w2.get_or_create_state()
        state2.increment()
        btn2_after = resolve_widget(w2)
        self.assertEqual(btn2_after.props.get("label"), "Count: 6")


class TestStateSerialization(unittest.TestCase):
    def test_tree_with_state_and_signals_to_proto(self):
        score = Signal(99, auto_update=False)

        class GameScreen(StatefulComponent):
            def create_state(self):
                class _GameState(State):
                    def build(self):
                        return Column([
                            Text(score),
                            Watch(lambda: Text(f"Score is {score.value}")),
                        ])
                return _GameState()

        frame = render_tree_frame(GameScreen())
        self.assertIsInstance(frame, bytes)
        self.assertEqual(frame[0], 0x01)  # MSG_RENDER_TREE byte


if __name__ == "__main__":
    unittest.main()
