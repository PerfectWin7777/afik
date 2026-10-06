"""How slots and callbacks are called: Qt-like (extra values dropped) and tolerant to Flutter events."""

from __future__ import annotations

import functools
import unittest

import pyflutter as pf
from pyflutter.core import widget_base as wb
from pyflutter.core.widget_base import _call_callable


def record(fn_factory, *args, **kwargs):
    seen = []
    fn = fn_factory(seen)
    _call_callable(fn, *args, **kwargs)
    return seen


class TestQtStyleSlots(unittest.TestCase):
    """PyQt: a slot may accept fewer arguments than the signal emits."""

    def test_slot_without_parameters_ignores_the_emitted_values(self):
        self.assertEqual(record(lambda s: (lambda: s.append("called")), 1, 2, 3), ["called"])

    def test_slot_takes_the_first_values_only(self):
        self.assertEqual(record(lambda s: (lambda a: s.append(a)), 1, 2, 3), [1])
        self.assertEqual(record(lambda s: (lambda a, b: s.append((a, b))), 1, 2, 3), [(1, 2)])

    def test_star_args_slot_gets_everything(self):
        self.assertEqual(record(lambda s: (lambda *a: s.append(a)), 1, 2, 3), [(1, 2, 3)])

    def test_bound_methods_work(self):
        class Window:
            def __init__(self):
                self.got = []

            def on_changed(self, value):
                self.got.append(value)

        w = Window()
        _call_callable(w.on_changed, "text")
        self.assertEqual(w.got, ["text"])

    def test_default_parameters_are_kept(self):
        self.assertEqual(record(lambda s: (lambda a, b=7: s.append((a, b))), 1), [(1, 7)])

    def test_partial_and_callable_objects(self):
        seen = []
        _call_callable(functools.partial(lambda tag, v: seen.append((tag, v)), "t"), 5)
        self.assertEqual(seen, [("t", 5)])

        class Handler:
            def __call__(self, v):
                seen.append(("obj", v))

        _call_callable(Handler(), 9)
        self.assertEqual(seen[-1], ("obj", 9))

    def test_emit_through_a_signal_keeps_working(self):
        button = pf.Button("x")
        got = []
        button.clicked.connect(lambda: got.append("no-arg"))
        button.clicked.connect(lambda checked: got.append(("checked", checked)))
        button.clicked.emit(True)
        self.assertEqual(got, ["no-arg", ("checked", True)])


class TestFlutterEvents(unittest.TestCase):
    """Event data arrives as named strings."""

    def test_no_data_and_no_parameters(self):
        self.assertEqual(record(lambda s: (lambda: s.append(1))), [1])

    def test_a_parameter_named_like_the_data(self):
        self.assertEqual(record(lambda s: (lambda value: s.append(value)), value="x"), ["x"])

    def test_any_parameter_name_receives_the_main_value(self):
        self.assertEqual(record(lambda s: (lambda text: s.append(text)), value="x"), ["x"])
        self.assertEqual(record(lambda s: (lambda v: s.append(v)), value="y", extra="z"), ["y"])

    def test_a_required_parameter_without_data_gets_none_instead_of_a_type_error(self):
        self.assertEqual(record(lambda s: (lambda e: s.append(e))), [None])
        self.assertEqual(record(lambda s: (lambda a, b: s.append((a, b)))), [(None, None)])

    def test_kwargs_handler_receives_the_named_data(self):
        self.assertEqual(record(lambda s: (lambda **kw: s.append(kw)), value="z", a="1"), [{"value": "z", "a": "1"}])

    def test_several_named_parameters_are_matched_by_name(self):
        self.assertEqual(record(lambda s: (lambda a, b: s.append((a, b))), b="2", a="1"), [("1", "2")])

    def test_named_and_kwargs_mixed(self):
        self.assertEqual(
            record(lambda s: (lambda value, **rest: s.append((value, rest))), value="v", other="o"),
            [("v", {"other": "o"})],
        )

    def test_keyword_only_parameters(self):
        self.assertEqual(record(lambda s: (lambda *, value: s.append(value)), value="k"), ["k"])
        self.assertEqual(record(lambda s: (lambda *, value: s.append(value))), [None])

    def test_positional_value_wins_over_a_named_value_of_the_same_parameter(self):
        # QtSignal passes the converted value positionally AND the raw event data by name
        self.assertEqual(record(lambda s: (lambda value: s.append(value)), True, value="true"), [True])

    def test_star_args_and_kwargs_get_everything(self):
        self.assertEqual(
            record(lambda s: (lambda *a, **k: s.append((a, k))), 1, value="x"),
            [((1,), {"value": "x"})],
        )

    def test_star_args_handler_used_by_the_overlay_helpers(self):
        seen = []
        _call_callable(lambda *_, **__: seen.append("ok"), value="x")
        self.assertEqual(seen, ["ok"])

    def test_builtins_without_a_signature(self):
        _call_callable(print)       # must not raise


class TestWidgetEventsEndToEnd(unittest.TestCase):
    def test_widgets_deliver_typed_values(self):
        got = []
        slider = pf.Slider(0.0, on_change=lambda v: got.append(("slider", v)))
        checkbox = pf.Checkbox(False, on_change=lambda v: got.append(("checkbox", v)))
        field = pf.TextField("", on_change=lambda v: got.append(("text", v)))
        wb.invoke_callback(slider.callback_id, {"value": "0.5"})
        wb.invoke_callback(checkbox.callback_id, {"value": "false"})
        wb.invoke_callback(field.callback_id, {"value": "abc"})
        self.assertEqual(got, [("slider", 0.5), ("checkbox", False), ("text", "abc")])

    def test_button_handler_taking_an_event_argument_works(self):
        got = []
        button = pf.Button("go", on_click=lambda e: got.append(e))
        wb.invoke_callback(button.callback_id, {})
        self.assertEqual(got, [None])


if __name__ == "__main__":
    unittest.main()
