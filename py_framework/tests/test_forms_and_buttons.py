"""
Unit test suite for PyFlutter Forms, Controllers, Validators, Dropdowns, and Buttons.
"""

from __future__ import annotations

import unittest

from pyflutter.core.form import (
    Form,
    FormKey,
    OutlineInputBorder,
    TextEditingController,
    Validators,
)
from pyflutter.core.render import render_tree_frame
from pyflutter.core.widget_base import invoke_callback
from pyflutter.widgets.widgets import (
    Column,
    DropdownButton,
    DropdownMenu,
    ElevatedButton,
    OutlinedButton,
    Row,
    TextButton,
    TextFormField,
)


class TestTextEditingController(unittest.TestCase):
    def test_controller_text_and_listener(self):
        controller = TextEditingController(text="Initial")
        self.assertEqual(controller.text, "Initial")
        self.assertFalse(controller.is_empty)

        notifications = []
        listener = lambda: notifications.append(controller.text)
        controller.add_listener(listener)

        controller.text = "Updated"
        self.assertEqual(controller.text, "Updated")
        self.assertEqual(notifications, ["Updated"])

        controller.clear()
        self.assertEqual(controller.text, "")
        self.assertTrue(controller.is_empty)
        self.assertEqual(notifications, ["Updated", ""])

        controller.remove_listener(listener)
        controller.text = "After Remove"
        self.assertEqual(len(notifications), 2)


class TestValidators(unittest.TestCase):
    def test_required(self):
        v = Validators.required("Required field")
        self.assertEqual(v(""), "Required field")
        self.assertEqual(v("   "), "Required field")
        self.assertIsNone(v("valid text"))

    def test_email(self):
        v = Validators.email("Invalid email")
        self.assertIsNone(v(""))  # Optional if empty
        self.assertEqual(v("plainaddress"), "Invalid email")
        self.assertEqual(v("missing@domain"), "Invalid email")
        self.assertIsNone(v("user@example.com"))
        self.assertIsNone(v("user.name+tag@company.co.uk"))

    def test_min_and_max_length(self):
        min_v = Validators.min_length(5, "Too short")
        self.assertEqual(min_v("abc"), "Too short")
        self.assertIsNone(min_v("abcde"))
        self.assertIsNone(min_v("abcdef"))

        max_v = Validators.max_length(5, "Too long")
        self.assertIsNone(max_v("abc"))
        self.assertIsNone(max_v("abcde"))
        self.assertEqual(max_v("abcdef"), "Too long")

    def test_numeric(self):
        v = Validators.numeric("Not a number")
        self.assertEqual(v("abc"), "Not a number")
        self.assertIsNone(v("123"))
        self.assertIsNone(v("123.45"))
        self.assertIsNone(v("-42"))

    def test_matches(self):
        c1 = TextEditingController(text="password123")
        v = Validators.matches(c1, "Passwords must match")
        self.assertEqual(v("wrong"), "Passwords must match")
        self.assertIsNone(v("password123"))

    def test_compose(self):
        v = Validators.compose(
            Validators.required("Field is required"),
            Validators.email("Invalid email address"),
            Validators.min_length(8, "Email too short"),
        )
        self.assertEqual(v(""), "Field is required")
        self.assertEqual(v("bad"), "Invalid email address")
        self.assertEqual(v("a@b.c"), "Email too short")
        self.assertIsNone(v("user@example.com"))


class TestFormAndFormKey(unittest.TestCase):
    def test_form_validation_and_lifecycle(self):
        form_key = FormKey()
        email_controller = TextEditingController()
        saved_data = {}

        def save_email(val):
            saved_data["email"] = val

        field_email = TextFormField(
            name="email",
            controller=email_controller,
            label="Email Address",
            validator=Validators.compose(
                Validators.required("Email is required"),
                Validators.email("Invalid email"),
            ),
            on_saved=save_email,
        )

        field_name = TextFormField(
            name="name",
            initial_value="",
            label="Full Name",
            validator=Validators.required("Name is required"),
            on_saved=lambda v: saved_data.update({"name": v}),
        )

        # Wrap in Form container
        Form(
            form_key=form_key,
            child=Column([
                field_email,
                field_name,
            ])
        )

        # Initially both are empty -> validate should fail
        self.assertFalse(form_key.validate())
        self.assertEqual(field_email.props.get("error_text"), "Email is required")
        self.assertEqual(field_name.props.get("error_text"), "Name is required")

        # Fill invalid email
        email_controller.text = "invalid_email_format"
        self.assertFalse(form_key.validate())
        self.assertEqual(field_email.props.get("error_text"), "Invalid email")

        # Fix email and fill name
        email_controller.text = "developer@pyflutter.org"
        field_name.set_value("PyFlutter Developer")
        self.assertTrue(form_key.validate())
        self.assertNotIn("error_text", field_email.props)
        self.assertNotIn("error_text", field_name.props)

        # Test save
        form_key.save()
        self.assertEqual(saved_data["email"], "developer@pyflutter.org")
        self.assertEqual(saved_data["name"], "PyFlutter Developer")

        # Test get_values
        values = form_key.get_values()
        self.assertEqual(values["email"], "developer@pyflutter.org")
        self.assertEqual(values["name"], "PyFlutter Developer")

        # Test reset
        form_key.reset()
        self.assertEqual(field_name.value, "")
        self.assertNotIn("error_text", field_name.props)


class TestDropdownButtonAndMenu(unittest.TestCase):
    def test_dropdown_button(self):
        selected = []
        dropdown = DropdownButton(
            items=["Apple", "Banana", "Cherry"],
            value="Banana",
            hint="Choose a fruit",
            on_changed=lambda v: selected.append(v),
        )
        self.assertEqual(dropdown.props["value"], "Banana")
        self.assertEqual(len(dropdown.children), 3)
        self.assertEqual(dropdown.children[0].props["value"], "Apple")
        self.assertEqual(dropdown.children[1].props["value"], "Banana")

        # Trigger callback from Dart bridge event
        invoke_callback(dropdown.callback_id, {"value": "Cherry"})
        self.assertEqual(dropdown.props["value"], "Cherry")
        self.assertEqual(selected, ["Cherry"])

    def test_dropdown_menu(self):
        menu = DropdownMenu(
            entries=["Light", "Dark", "System"],
            label="Theme",
            initial_selection="System",
        )
        self.assertEqual(menu.props["label"], "Theme")
        self.assertEqual(menu.props["initial_selection"], "System")
        self.assertEqual(len(menu.children), 3)


class TestButtons(unittest.TestCase):
    def test_elevated_outlined_and_text_buttons(self):
        clicks = []

        btn1 = ElevatedButton("Elevated", on_pressed=lambda: clicks.append("elevated"), background_color="#1877F2")
        btn2 = OutlinedButton("Outlined", on_pressed=lambda: clicks.append("outlined"), border_color="#1877F2")
        btn3 = TextButton("Text", on_pressed=lambda: clicks.append("text"), color="#1877F2")

        self.assertEqual(btn1.widget_type, "Button")
        self.assertEqual(btn2.widget_type, "OutlinedButton")
        self.assertEqual(btn3.widget_type, "TextButton")

        invoke_callback(btn1.callback_id, {})
        invoke_callback(btn2.callback_id, {})
        invoke_callback(btn3.callback_id, {})

        self.assertEqual(clicks, ["elevated", "outlined", "text"])


class TestProtobufSerialization(unittest.TestCase):
    def test_render_tree_serialization(self):
        controller = TextEditingController(text="hello")
        tree = Form(
            child=Column([
                TextFormField(
                    controller=controller,
                    label="Username",
                    border=OutlineInputBorder(border_radius=12.0, border_color="#1877F2"),
                ),
                DropdownButton(
                    items=["Option 1", "Option 2"],
                    value="Option 1",
                ),
                Row([
                    OutlinedButton("Cancel"),
                    ElevatedButton("Submit"),
                ]),
            ])
        )

        frame = render_tree_frame(tree)
        self.assertIsInstance(frame, bytes)
        self.assertGreater(len(frame), 10)
        # Type tag 0x01 for RenderTree
        self.assertEqual(frame[0], 0x01)


if __name__ == "__main__":
    unittest.main()
