"""FormKey keeps what the user typed: the widgets are recreated on every build, the key is not."""

from __future__ import annotations

import gc
import unittest

import pyflutter as pf
from pyflutter.core import widget_base as wb


def build(form_key, seen=None):
    """What a screen's build() does: brand-new widgets every time."""
    return pf.Form(
        form_key=form_key,
        child=pf.Column([
            pf.TextFormField(name="email", validator=pf.Validators.required("email?"),
                             on_change=(lambda v: seen.append(v)) if seen is not None else None),
            pf.TextFormField(name="age", initial_value="18", validator=pf.Validators.numeric("number?")),
        ]),
    )


def fields(form):
    return {f.name: f for f in form.children[0].children}


class TestFormKeyStore(unittest.TestCase):
    def test_typed_values_survive_a_rebuild(self):
        key = pf.FormKey()
        form = build(key)
        f = fields(form)
        wb.invoke_callback(f["email"].callback_id, {"value": "a@b.co"})
        wb.invoke_callback(f["age"].callback_id, {"value": "42"})

        rebuilt = fields(build(key))
        self.assertEqual(rebuilt["email"].value, "a@b.co")
        self.assertEqual(rebuilt["age"].value, "42")
        self.assertEqual(key.get_values(), {"email": "a@b.co", "age": "42"})

    def test_values_are_read_from_the_store_not_from_the_initial_value(self):
        key = pf.FormKey()
        f = fields(build(key))
        wb.invoke_callback(f["email"].callback_id, {"value": "typed"})
        fields(build(key))                       # a rebuild whose field has initial_value ""
        self.assertEqual(key.get_values()["email"], "typed")

    def test_user_handler_runs_after_the_store_is_updated(self):
        key = pf.FormKey()
        seen = []
        f = fields(build(key, seen))
        wb.invoke_callback(f["email"].callback_id, {"value": "x"})
        self.assertEqual(seen, ["x"])
        self.assertEqual(key._values["email"], "x")

    def test_stale_fields_do_not_pile_up(self):
        key = pf.FormKey()
        for _ in range(50):
            build(key)
        gc.collect()
        self.assertLessEqual(len(key._fields), 2)
        self.assertEqual(len(key._by_name), 2)

    def test_validation_errors_reach_the_rebuilt_field(self):
        key = pf.FormKey()
        build(key)
        self.assertFalse(key.validate())
        rebuilt = fields(build(key))
        self.assertEqual(rebuilt["email"].props.get("error_text"), "email?")
        self.assertNotIn("error_text", rebuilt["age"].props)

        wb.invoke_callback(rebuilt["email"].callback_id, {"value": "ok@ok.io"})
        self.assertTrue(key.validate())
        self.assertNotIn("error_text", fields(build(key))["email"].props)

    def test_validate_uses_the_typed_value_of_the_current_field(self):
        key = pf.FormKey()
        build(key)
        current = fields(build(key))
        wb.invoke_callback(current["email"].callback_id, {"value": "z"})
        wb.invoke_callback(current["age"].callback_id, {"value": "abc"})
        self.assertFalse(key.validate())
        self.assertNotIn("error_text", current["email"].props)
        self.assertEqual(current["age"].props.get("error_text"), "number?")

    def test_reset_restores_initial_values_and_clears_errors(self):
        key = pf.FormKey()
        f = fields(build(key))
        wb.invoke_callback(f["age"].callback_id, {"value": "abc"})
        key.validate()
        key.reset()
        rebuilt = fields(build(key))
        self.assertEqual(rebuilt["age"].value, "18")
        self.assertNotIn("error_text", rebuilt["age"].props)
        self.assertEqual(rebuilt["email"].value, "")

    def test_set_values_loads_a_record(self):
        key = pf.FormKey()
        f = fields(build(key))
        key.set_values({"email": "loaded@x.io", "age": 30})
        self.assertEqual(f["email"].value, "loaded@x.io")
        self.assertEqual(fields(build(key))["age"].value, "30")

    def test_controller_stays_the_source_of_truth(self):
        key = pf.FormKey()
        controller = pf.TextEditingController("a")
        pf.Form(form_key=key, child=pf.TextFormField(name="n", controller=controller))
        controller.text = "b"
        self.assertEqual(key.get_values()["n"], "b")
        again = pf.TextFormField(name="n", controller=controller)
        again._register_with_form_key(key)
        self.assertEqual(again.value, "b")

    def test_fields_without_a_name_still_validate_and_save(self):
        key = pf.FormKey()
        saved = []
        field = pf.TextFormField(initial_value="v", validator=pf.Validators.required("r"),
                                 on_saved=saved.append)
        pf.Form(form_key=key, child=field)
        self.assertTrue(key.validate())
        key.save()
        self.assertEqual(saved, ["v"])
        self.assertEqual(key.get_values(), {})


if __name__ == "__main__":
    unittest.main()
