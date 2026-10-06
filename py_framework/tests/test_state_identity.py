"""T-03 part 2: a State is found again by its place in the tree, not by source line numbers."""

from __future__ import annotations

import unittest

import pyflutter as pf
from pyflutter.core import state as st
from pyflutter.core.render import resolve_tree


class Counter(pf.State):
    def init_state(self):
        self.n = 0

    def build(self):
        return pf.Text(f"{self.widget.label}:{self.n}")


class CounterWidget(pf.StatefulComponent):
    def __init__(self, label="", **kw):
        super().__init__(**kw)
        self.label = label

    def create_state(self):
        return Counter()


def texts(tree):
    return [c.props["text"] for c in tree.children]


def bump(label, tree):
    """Increments the state shown as ``label`` (finds it through the registry)."""
    for state in st._state_registry.values():
        if state.widget.label == label:
            state.n += 1


class TestStructuralIdentity(unittest.TestCase):
    def setUp(self):
        st.clear_state_registry()

    def tearDown(self):
        st.clear_state_registry()

    def test_same_structure_built_from_different_code_keeps_the_state(self):
        # Two functions = two different "call sites" (what an edit that moves lines produces).
        def screen_v1():
            return pf.Column([CounterWidget("a")])

        def screen_v2():

            # more code above, other line numbers
            return pf.Column([CounterWidget("a")])

        tree = resolve_tree(screen_v1())
        bump("a", tree)
        tree = resolve_tree(screen_v2())
        self.assertEqual(texts(tree), ["a:1"])

    def test_siblings_of_the_same_class_have_separate_states(self):
        tree = resolve_tree(pf.Column([CounterWidget("a"), CounterWidget("b")]))
        bump("a", tree)
        tree = resolve_tree(pf.Column([CounterWidget("a"), CounterWidget("b")]))
        self.assertEqual(texts(tree), ["a:1", "b:0"])

    def test_same_widget_built_in_a_loop_gets_one_state_per_position(self):
        build = lambda: pf.Column([CounterWidget(str(i)) for i in range(3)])
        resolve_tree(build())
        bump("1", None)
        self.assertEqual(texts(resolve_tree(build())), ["0:0", "1:1", "2:0"])
        self.assertEqual(len(st._state_registry), 3)

    def test_unkeyed_state_follows_the_position(self):
        resolve_tree(pf.Column([CounterWidget("a"), CounterWidget("b")]))
        bump("a", None)
        # Inserting something in front shifts positions, like Flutter without keys.
        tree = resolve_tree(pf.Column([pf.Text("new"), CounterWidget("a"), CounterWidget("b")]))
        self.assertEqual(texts(tree)[0], "new")
        self.assertEqual(texts(tree)[1:], ["a:0", "b:0"])

    def test_keyed_state_follows_the_key_when_the_list_is_reordered(self):
        def items(order):
            return pf.Column([CounterWidget(k, key=k) for k in order])

        resolve_tree(items(["a", "b", "c"]))
        bump("c", None)
        tree = resolve_tree(items(["c", "a", "b"]))
        self.assertEqual(texts(tree), ["c:1", "a:0", "b:0"])
        self.assertEqual(len(st._state_registry), 3)

    def test_keyed_state_survives_the_removal_of_its_neighbours(self):
        def items(order):
            return pf.Column([CounterWidget(k, key=k) for k in order])

        resolve_tree(items(["a", "b", "c"]))
        bump("c", None)
        tree = resolve_tree(items(["c"]))
        self.assertEqual(texts(tree), ["c:1"])
        self.assertEqual(len(st._state_registry), 1)

    def test_the_same_key_under_different_parents_is_not_shared(self):
        tree = resolve_tree(pf.Column([
            pf.Row([CounterWidget("left", key="k")]),
            pf.Row([CounterWidget("right", key="k")]),
        ]))
        self.assertEqual(len(st._state_registry), 2)
        bump("left", None)
        tree = resolve_tree(pf.Column([
            pf.Row([CounterWidget("left", key="k")]),
            pf.Row([CounterWidget("right", key="k")]),
        ]))
        self.assertEqual([r.children[0].props["text"] for r in tree.children], ["left:1", "right:0"])

    def test_a_component_returning_a_stateful_component_keeps_both_states(self):
        class Wrapper(pf.Component):
            def build(self):
                return CounterWidget("inner")

        outer = lambda: pf.Column([CounterWidget("outer"), Wrapper()])
        resolve_tree(outer())
        bump("inner", None)
        self.assertEqual(texts(resolve_tree(outer())), ["outer:0", "inner:1"])

    def test_a_stateful_component_nested_in_a_state_build(self):
        class Inner(pf.State):
            def init_state(self):
                self.n = 0

            def build(self):
                return pf.Text(f"inner:{self.n}")

        class InnerWidget(pf.StatefulComponent):
            def create_state(self):
                return Inner()

        class Outer(pf.State):
            def build(self):
                return pf.Column([InnerWidget()])

        class OuterWidget(pf.StatefulComponent):
            def create_state(self):
                return Outer()

        resolve_tree(OuterWidget())
        for state in st._state_registry.values():
            if isinstance(state, Inner):
                state.n = 7
        tree = resolve_tree(OuterWidget())
        self.assertEqual(tree.children[0].props["text"], "inner:7")

    def test_a_direct_build_outside_a_tree_keeps_the_state_on_the_instance(self):
        w = CounterWidget("solo")
        w.build()
        w._state.n = 3
        self.assertEqual(w.build().props["text"], "solo:3")
        self.assertEqual(len(st._state_registry), 0)


if __name__ == "__main__":
    unittest.main()
