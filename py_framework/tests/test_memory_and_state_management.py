"""
Tests for Afik memory leak prevention, State Management,
single-pass component resolution, and callback garbage collection.
"""

import unittest

from afik import Button, Column, Component, Signal, SignalBuilder, State, StatefulWidget, Text, TextField
from afik.core import render, state, widget_base


class TestMemoryAndStateManagement(unittest.TestCase):

    def setUp(self):
        widget_base.clear_callbacks()
        state.clear_state_registry()

    def test_single_pass_component_resolution_and_nid(self):
        """Verifies that Component.build() is called exactly once per render pass and children have valid _nid."""
        build_counts = {"count": 0}

        class MyCard(Component):
            def build(self):
                build_counts["count"] += 1
                return Column([Text("Hello"), Button("Click", on_click=lambda: None)])

        class App(Component):
            def build(self):
                return Column([MyCard()])

        app = App()
        tree = render.resolve_tree(app)
        render.assign_node_ids(tree)
        snapshot = render.widget_to_snapshot(tree)

        # build() must be called only once
        self.assertEqual(build_counts["count"], 1)

        # Children inside component must have non-empty deterministic _nid
        card_col = snapshot["children"][0]
        self.assertEqual(card_col["_nid"], "root.0")
        self.assertEqual(card_col["children"][0]["_nid"], "root.0.0")
        self.assertEqual(card_col["children"][1]["_nid"], "root.0.1")

    def test_callback_garbage_collection(self):
        """Verifies that stale callbacks from abandoned widgets are swept from memory."""
        btn_a = Button("A", on_click=lambda: "A")
        col_a = Column([btn_a])

        # Frame 1: button A
        render.render_tree_frame(col_a)
        self.assertIn(btn_a.callback_id, widget_base._callback_registry)

        # Frame 2: button B
        btn_b = Button("B", on_click=lambda: "B")
        col_b = Column([btn_b])
        render.render_tree_frame(col_b)
        self.assertIn(btn_b.callback_id, widget_base._callback_registry)

        # Frame 3: button C (retains generations=2, so frame 1 callback should now be pruned)
        btn_c = Button("C", on_click=lambda: "C")
        col_c = Column([btn_c])
        render.render_tree_frame(col_c)

        self.assertNotIn(btn_a.callback_id, widget_base._callback_registry)
        self.assertIn(btn_b.callback_id, widget_base._callback_registry)
        self.assertIn(btn_c.callback_id, widget_base._callback_registry)

    def test_signal_builder_listener_deduplication(self):
        """Verifies that repeatedly rebuilding a SignalBuilder does not accumulate duplicate listeners."""
        count = Signal(0, auto_update=False)

        class Parent(Component):
            def build(self):
                return Column([
                    SignalBuilder(count, lambda v: Text(f"Value: {v}"))
                ])

        parent = Parent()
        for _ in range(10):
            tree = render.resolve_tree(parent)
            render.assign_node_ids(tree)

        # Listeners must be deduplicated (at most 1)
        self.assertLessEqual(len(count._listeners), 1)

    def test_stateful_widget_retains_state_without_explicit_key(self):
        """Verifies that a StatefulWidget without an explicit key retains its state across rebuilds."""
        init_calls = {"count": 0}

        class CounterWidget(StatefulWidget):
            def create_state(self):
                return CounterState()

        class CounterState(State):
            def init_state(self):
                init_calls["count"] += 1
                self.counter = 0

            def build(self):
                return Text(f"Count: {self.counter}")

        class Screen(Component):
            def build(self):
                return Column([CounterWidget()])

        screen = Screen()

        # Frame 1
        tree1 = render.resolve_tree(screen)
        first_text = tree1.children[0]
        self.assertEqual(first_text.props["value"], "Count: 0")
        self.assertEqual(init_calls["count"], 1)

        # Simulate state mutation
        state_inst = list(state._state_registry.values())[0]
        state_inst.counter = 99

        # Frame 2
        tree2 = render.resolve_tree(screen)
        second_text = tree2.children[0]
        self.assertEqual(second_text.props["value"], "Count: 99")
        # init_state must NOT have been called again!
        self.assertEqual(init_calls["count"], 1)

    def test_text_field_key_parameter(self):
        """Verifies that TextField accepts a key parameter and sets it in props."""
        tf = TextField(value="test", key="custom_tf_key")
        self.assertEqual(tf.props.get("key"), "custom_tf_key")


if __name__ == "__main__":
    unittest.main()
