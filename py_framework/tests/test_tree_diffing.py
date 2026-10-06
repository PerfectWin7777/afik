"""
Unit tests for PyFlutter Tree Diffing and Granular Patch generation.
Validates O(N) recursive tree diffing, node ID addressing, and patch formatting.
"""

import unittest

from pyflutter import Button, Column, Container, Row, Text
from pyflutter.core.render import (
    MSG_TREE_PATCH,
    assign_node_ids,
    diff_snapshots,
    tree_patch_frame,
    widget_to_snapshot,
)


class TestTreeDiffing(unittest.TestCase):
    """Validates granular diff generation between tree snapshots."""

    def test_node_id_assignment(self):
        col = Column([
            Text("First", key="txt1"),
            Button("Click"),
            Row([Text("Nested")]),
        ])
        assign_node_ids(col)

        self.assertEqual(col.props["_nid"], "root")
        self.assertEqual(col.children[0].props["_nid"], "root.0[txt1]")
        self.assertEqual(col.children[1].props["_nid"], "root.1")
        self.assertEqual(col.children[2].props["_nid"], "root.2")
        self.assertEqual(col.children[2].children[0].props["_nid"], "root.2.0")

    def test_identical_trees_produce_empty_diff(self):
        t1 = Column([Text("Hello"), Button("OK")])
        t2 = Column([Text("Hello"), Button("OK")])
        assign_node_ids(t1)
        assign_node_ids(t2)

        s1 = widget_to_snapshot(t1)
        s2 = widget_to_snapshot(t2)

        diff = diff_snapshots(s1, s2)
        self.assertIsNotNone(diff)
        self.assertEqual(len(diff), 0)

    def test_single_property_change_produces_targeted_patch(self):
        t1 = Column([Text("Hello"), Button("Count: 0")])
        t2 = Column([Text("Hello"), Button("Count: 1")])
        assign_node_ids(t1)
        assign_node_ids(t2)

        s1 = widget_to_snapshot(t1)
        s2 = widget_to_snapshot(t2)

        diff = diff_snapshots(s1, s2)
        self.assertIsNotNone(diff)
        self.assertEqual(len(diff), 1)
        self.assertEqual(diff[0]["id"], "root.1")
        self.assertEqual(diff[0]["props"]["label"], "Count: 1")

    def test_structural_change_falls_back_to_none(self):
        # Adding a child is a structural change -> requires full RenderTree
        t1 = Column([Text("A")])
        t2 = Column([Text("A"), Text("B")])
        assign_node_ids(t1)
        assign_node_ids(t2)

        s1 = widget_to_snapshot(t1)
        s2 = widget_to_snapshot(t2)

        diff = diff_snapshots(s1, s2)
        self.assertIsNone(diff)

    def test_widget_type_change_falls_back_to_none(self):
        t1 = Container(child=Text("A"))
        t2 = Container(child=Button("A"))
        assign_node_ids(t1)
        assign_node_ids(t2)

        s1 = widget_to_snapshot(t1)
        s2 = widget_to_snapshot(t2)

        diff = diff_snapshots(s1, s2)
        self.assertIsNone(diff)

    def test_tree_patch_frame_encoding(self):
        patch = [{"id": "root.0", "props": {"text": "Updated"}}]
        frame = tree_patch_frame(patch)
        self.assertEqual(frame[0], MSG_TREE_PATCH)
        self.assertIn(b'"text": "Updated"', frame)


if __name__ == "__main__":
    unittest.main()
