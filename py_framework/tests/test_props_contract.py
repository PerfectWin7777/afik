"""T-11: the props contract, the validation of props in Python, and the consistency check."""

from __future__ import annotations

import os
import subprocess
import sys
import unittest
from enum import Enum
from pathlib import Path
from unittest.mock import patch

import pyflutter as pf
from pyflutter.core import contract

ROOT = Path(__file__).resolve().parents[2]


class TestContractFile(unittest.TestCase):
    def test_contract_loads_and_describes_the_core_widgets(self):
        data = contract.load()
        self.assertGreater(len(data), 60)
        for widget_type in ("Text", "Column", "Row", "TextField", "Tooltip", "Positioned", "CircularProgressIndicator"):
            self.assertIn(widget_type, data)
        self.assertIn("wait_duration_ms", data["Tooltip"]["props"])
        self.assertIn("stroke_width", data["CircularProgressIndicator"]["props"])
        self.assertIn("width", data["Positioned"]["props"])

    def test_every_prop_has_a_known_type(self):
        allowed = {"string", "number", "bool", "color", "icon", "callback", "enum"}
        for widget_type, entry in contract.load().items():
            for name, spec in entry["props"].items():
                kind = spec["type"] if isinstance(spec, dict) else spec
                self.assertIn(kind, allowed, f"{widget_type}.{name}")
                if kind == "enum":
                    self.assertTrue(spec["values"], f"{widget_type}.{name}")


class TestStrictValidation(unittest.TestCase):
    def test_strict_mode_is_on_in_the_test_suite(self):
        self.assertTrue(contract.strict())

    def test_a_known_prop_is_accepted(self):
        pf.Tooltip("hello", pf.Text("x"), wait_duration_ms=500)

    def test_an_unknown_prop_raises_in_strict_mode(self):
        text = pf.Text("x")
        with self.assertRaisesRegex(ValueError, "no prop 'bogus'"):
            text.props["bogus"] = "1"

    def test_an_unknown_constructor_prop_raises(self):
        class Typo(pf.Widget):
            widget_type = "Tooltip"

        with self.assertRaisesRegex(ValueError, "no prop 'mesage'"):
            Typo(mesage="oops")

    def test_a_bad_enum_value_raises(self):
        with self.assertRaisesRegex(ValueError, "not one of"):
            pf.Column([], main_axis_alignment="sideways")

    def test_enum_members_are_sent_as_their_value(self):
        col = pf.Column([], main_axis_alignment=pf.MainAxisAlignment.SPACE_BETWEEN)
        self.assertEqual(col.props["main_axis_alignment"], "space_between")

    def test_framework_props_and_callback_ids_are_always_allowed(self):
        text = pf.Text("x")
        for name in ("key", "slot", "_nid", "visible", "enabled", "tooltip", "my_callback_id"):
            text.props[name] = "v"

    def test_raw_props_are_an_escape_hatch(self):
        text = pf.Text("x", raw_props={"anything_goes": "yes"})
        self.assertEqual(text.props["anything_goes"], "yes")

    def test_types_outside_the_contract_are_not_checked(self):
        class Custom(pf.Widget):
            widget_type = "MyOwnWidget"

        Custom(whatever="1").props["other"] = "2"


class TestValueTypes(unittest.TestCase):
    def test_callables_and_containers_are_rejected(self):
        for bad in (lambda: 1, [1, 2], {"a": 1}, (1, 2), {1}):
            with self.assertRaises(TypeError, msg=repr(bad)):
                pf.Text("x", color=bad)

    def test_the_error_names_the_widget_and_the_prop(self):
        with self.assertRaisesRegex(TypeError, r"Text\.color"):
            pf.Text("x", color=lambda: 1)

    def test_numbers_bools_and_none_still_work(self):
        text = pf.Text("x", font_size=14, soft_wrap=False, color=None)
        self.assertEqual(text.props["font_size"], "14")
        self.assertEqual(text.props["soft_wrap"], "false")
        self.assertNotIn("color", text.props)

    def test_custom_enum_is_turned_into_its_value(self):
        class Mode(Enum):
            CLIP = "clip"

        self.assertEqual(pf.Text("x", overflow=Mode.CLIP).props["overflow"], "clip")


class TestLenientMode(unittest.TestCase):
    def test_outside_strict_mode_an_unknown_prop_warns_once(self):
        contract._warned.clear()
        with patch.dict(os.environ, {"PYFLUTTER_STRICT_PROPS": "0"}), \
                patch("pyflutter.core.logger.logger.warning") as warning:
            text = pf.Text("x")
            text.props["bogus"] = "1"
            text.props["bogus"] = "2"
            pf.Text("y").props["bogus"] = "3"
        self.assertEqual(warning.call_count, 1)
        self.assertEqual(text.props["bogus"], "2")          # still stored: lenient mode never drops data


class TestQtSettersOnAnyWidget(unittest.TestCase):
    def test_tooltip_and_background_color_on_a_label(self):
        label = pf.Label("x") if hasattr(pf, "Label") else pf.Text("x")
        label.setToolTip("help", auto_update=False)
        label.setBackgroundColor("#00FF00", auto_update=False)
        self.assertEqual(label.props["tooltip"], "help")
        self.assertEqual(label.props["background_color"], "#00FF00")


class TestConsistencyCheck(unittest.TestCase):
    @unittest.skipUnless((ROOT / "tools" / "check_contract.py").exists(), "repository checkout only")
    def test_python_dart_and_contract_agree(self):
        proc = subprocess.run(
            [sys.executable, str(ROOT / "tools" / "check_contract.py")],
            capture_output=True, text=True,
        )
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)


if __name__ == "__main__":
    unittest.main()
