"""T-10: a patch tells apart "prop is now empty" from "prop no longer exists"."""

from __future__ import annotations

import unittest

import pyflutter as pf
from pyflutter.core.render import assign_node_ids, diff_snapshots, resolve_tree, widget_to_snapshot


def snap(widget):
    tree = resolve_tree(widget)
    assign_node_ids(tree)
    return widget_to_snapshot(tree)


class TestPatchProps(unittest.TestCase):
    def test_a_cleared_text_is_a_value_not_a_removal(self):
        old = snap(pf.TextField("hello", label="Name"))
        new = snap(pf.TextField("", label="Name"))
        (op,) = diff_snapshots(old, new)
        self.assertEqual(op["props"], {"value": ""})
        self.assertNotIn("remove", op)

    def test_a_dropped_prop_is_listed_in_remove(self):
        old = snap(pf.TextField("a", label="Name", helper_text="help"))
        new = snap(pf.TextField("a", label="Name"))
        (op,) = diff_snapshots(old, new)
        self.assertEqual(op["remove"], ["helper_text"])
        self.assertNotIn("props", op)

    def test_change_and_removal_together(self):
        old = snap(pf.TextField("a", helper_text="help"))
        new = snap(pf.TextField("b"))
        (op,) = diff_snapshots(old, new)
        self.assertEqual(op["props"], {"value": "b"})
        self.assertEqual(op["remove"], ["helper_text"])

    def test_identical_trees_produce_no_operation(self):
        self.assertEqual(diff_snapshots(snap(pf.Text("x")), snap(pf.Text("x"))), [])

    def test_an_error_text_cleared_by_the_app_is_removed_not_emptied(self):
        old = snap(pf.TextField("a", error_text="bad"))
        new = snap(pf.TextField("a"))
        (op,) = diff_snapshots(old, new)
        self.assertEqual(op["remove"], ["error_text"])


if __name__ == "__main__":
    unittest.main()
