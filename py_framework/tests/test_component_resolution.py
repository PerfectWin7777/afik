"""T-12: Component.build() only takes widgets, and says clearly when it has nothing to show."""

from __future__ import annotations

import unittest
from unittest.mock import patch

import pyflutter as pf
from pyflutter.core import widget_base as wb


def texts(widget):
    out = []
    stack = [widget]
    while stack:
        w = stack.pop()
        if w.widget_type == "Text":
            out.append(w.props.get("text"))
        stack.extend(getattr(w, "children", []))
    return out


class TestComponentPicksWidgetsOnly(unittest.TestCase):
    def test_a_string_named_body_is_ignored(self):
        class Page(pf.Component):
            def __init__(self):
                super().__init__()
                self.body = "just some text"
                self.layout = pf.Column([pf.Text("real")])

        tree = Page().build()
        self.assertEqual(texts(tree), ["real"])

    def test_non_widget_attributes_with_alias_names_do_not_break_the_build(self):
        class Page(pf.Component):
            def __init__(self):
                super().__init__()
                self.root = {"path": "/"}
                self.row = 3
                self.fab = "plus"
                self.drawer = ["a", "b"]
                self.set_central_widget(pf.Text("ok"))

        tree = Page().build()
        self.assertEqual(tree.widget_type, "Text")     # no Scaffold built from the junk

    def test_a_method_with_an_alias_name_is_not_taken_as_the_root(self):
        class Page(pf.Component):
            def column(self):          # a user method, not a widget
                return 1

            def __init__(self):
                super().__init__()
                self.add_widget(pf.Text("x"))

        self.assertEqual(texts(Page().build()), ["x"])

    def test_app_bar_may_still_be_a_string(self):
        class Page(pf.Component):
            def __init__(self):
                super().__init__()
                self.app_bar = "Title"
                self.layout = pf.Column()

        self.assertEqual(Page().build().widget_type, "Scaffold")

    def test_layout_wins_over_the_old_aliases(self):
        class Page(pf.Component):
            def __init__(self):
                super().__init__()
                self.column = pf.Column([pf.Text("old")])
                self.layout = pf.Column([pf.Text("new")])

        self.assertEqual(texts(Page().build()), ["new"])


class TestDeprecatedAliases(unittest.TestCase):
    def test_old_alias_still_works_and_warns_once(self):
        wb._warned_component_aliases.clear()

        class Legacy(pf.Component):
            def __init__(self):
                super().__init__()
                self.column = pf.Column([pf.Text("legacy")])

        with patch("pyflutter.core.logger.logger.warning") as warning:
            self.assertEqual(texts(Legacy().build()), ["legacy"])
            Legacy().build()
        self.assertEqual(warning.call_count, 1)
        self.assertIn("self.layout", warning.call_args.args[-1])

    def test_current_names_do_not_warn(self):
        wb._warned_component_aliases.clear()

        class Modern(pf.Component):
            def __init__(self):
                super().__init__()
                self.layout = pf.Column([pf.Text("m")])
                self.floating_action_button = pf.FloatingActionButton(pf.Icon("add"))

        with patch("pyflutter.core.logger.logger.warning") as warning:
            Modern().build()
        warning.assert_not_called()


class TestEmptyComponentError(unittest.TestCase):
    def test_message_names_the_class_and_shows_both_ways(self):
        class Empty(pf.Component):
            pass

        with self.assertRaises(NotImplementedError) as ctx:
            Empty().build()
        message = str(ctx.exception)
        self.assertIn("Empty", message)
        self.assertIn("def build(self)", message)
        self.assertIn("self.layout = Column()", message)


class TestShadowingStaysHarmless(unittest.TestCase):
    def test_instance_attributes_named_like_widget_methods_work(self):
        class Counter(pf.Component):
            def __init__(self):
                super().__init__()
                self.count = 0
                self.text = "label"
                self.value = 5
                self.layout = pf.Column([pf.Text(f"{self.text}: {self.count} / {self.value}")])

        self.assertEqual(texts(Counter().build()), ["label: 0 / 5"])


if __name__ == "__main__":
    unittest.main()
