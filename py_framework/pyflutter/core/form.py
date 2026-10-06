"""
Forms, validation, and text editing controllers for PyFlutter.
Provides a reactive, typed, Flutter-standard Form API.
"""

from __future__ import annotations

import re
from typing import Any, Callable, Optional, Sequence

from pyflutter.core.widget_base import Widget
from pyflutter.core.logger import logger


class TextEditingController:
    """
    Controls the text being edited in a TextField or TextFormField.
    
    Equivalent to Flutter's TextEditingController.
    Allows reading/updating text, clearing, and listening to text changes.
    """

    def __init__(self, text: str = ""):
        self._text: str = str(text) if text is not None else ""
        self._listeners: list[Callable[[], None]] = []

    @property
    def text(self) -> str:
        return self._text

    @text.setter
    def text(self, new_text: str) -> None:
        val = str(new_text) if new_text is not None else ""
        if self._text != val:
            self._text = val
            self._notify_listeners()

    @property
    def is_empty(self) -> bool:
        return len(self._text) == 0

    def clear(self) -> None:
        """Clears the controller's text content."""
        self.text = ""

    def add_listener(self, listener: Callable[[], None]) -> None:
        """Registers a listener callback invoked whenever the text changes."""
        if listener not in self._listeners:
            self._listeners.append(listener)

    def remove_listener(self, listener: Callable[[], None]) -> None:
        """Removes a previously registered listener callback."""
        if listener in self._listeners:
            self._listeners.remove(listener)

    def _notify_listeners(self) -> None:
        for listener in list(self._listeners):
            try:
                listener()
            except Exception as e:
                logger.error("Error in TextEditingController listener: {}", e)

    def __repr__(self) -> str:
        return f"TextEditingController(text={self._text!r})"


class InputBorder:
    """Border styles for text fields."""
    NONE = "none"
    OUTLINE = "outline"
    UNDERLINE = "underline"


class OutlineInputBorder:
    """An outline border around a text field with customizable corner radius."""
    def __init__(
        self,
        *,
        border_radius: float = 8.0,
        border_color: Optional[str] = None,
        border_width: float = 1.0,
    ):
        self.type = "outline"
        self.border_radius = border_radius
        self.border_color = border_color
        self.border_width = border_width


class UnderlineInputBorder:
    """A single underline border beneath a text field."""
    def __init__(
        self,
        *,
        border_color: Optional[str] = None,
        border_width: float = 1.0,
    ):
        self.type = "underline"
        self.border_color = border_color
        self.border_width = border_width


class Validators:
    """
    Standard collection of form field validators.
    Each validator returns None when validation succeeds, or an error string when it fails.
    """

    @staticmethod
    def required(error_message: str = "This field is required") -> Callable[[str], Optional[str]]:
        def validate(value: str) -> Optional[str]:
            if value is None or str(value).strip() == "":
                return error_message
            return None
        return validate

    @staticmethod
    def email(error_message: str = "Please enter a valid email address") -> Callable[[str], Optional[str]]:
        pattern = re.compile(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")
        def validate(value: str) -> Optional[str]:
            if not value or str(value).strip() == "":
                return None  # Combine with required() if field cannot be empty
            if not pattern.match(str(value).strip()):
                return error_message
            return None
        return validate

    @staticmethod
    def min_length(length: int, error_message: Optional[str] = None) -> Callable[[str], Optional[str]]:
        msg = error_message or f"Must be at least {length} characters"
        def validate(value: str) -> Optional[str]:
            if value and len(str(value)) < length:
                return msg
            return None
        return validate

    @staticmethod
    def max_length(length: int, error_message: Optional[str] = None) -> Callable[[str], Optional[str]]:
        msg = error_message or f"Must be at most {length} characters"
        def validate(value: str) -> Optional[str]:
            if value and len(str(value)) > length:
                return msg
            return None
        return validate

    @staticmethod
    def numeric(error_message: str = "Please enter a valid number") -> Callable[[str], Optional[str]]:
        def validate(value: str) -> Optional[str]:
            if not value or str(value).strip() == "":
                return None
            try:
                float(str(value).strip())
                return None
            except ValueError:
                return error_message
        return validate

    @staticmethod
    def regex(pattern: str, error_message: str = "Invalid format") -> Callable[[str], Optional[str]]:
        compiled = re.compile(pattern)
        def validate(value: str) -> Optional[str]:
            if not value or str(value).strip() == "":
                return None
            if not compiled.match(str(value).strip()):
                return error_message
            return None
        return validate

    @staticmethod
    def matches(
        other: TextEditingController | Callable[[], str] | str,
        error_message: str = "Values do not match",
    ) -> Callable[[str], Optional[str]]:
        def validate(value: str) -> Optional[str]:
            if isinstance(other, TextEditingController):
                target = other.text
            elif callable(other):
                target = other()
            else:
                target = str(other)
            if str(value or "") != str(target or ""):
                return error_message
            return None
        return validate

    @staticmethod
    def compose(*validators: Callable[[str], Optional[str]]) -> Callable[[str], Optional[str]]:
        """Composes multiple validators into one, running sequentially and returning the first failure."""
        def validate(value: str) -> Optional[str]:
            for v in validators:
                err = v(value)
                if err:
                    return err
            return None
        return validate


class FormKey:
    """
    Manages the state and validation of a Form and its child FormFields.
    Equivalent to Flutter's GlobalKey<FormState>().
    """

    def __init__(self):
        self._fields: list[Any] = []

    def register(self, field: Any) -> None:
        if field not in self._fields:
            self._fields.append(field)

    def unregister(self, field: Any) -> None:
        if field in self._fields:
            self._fields.remove(field)

    def validate(self) -> bool:
        """
        Validates all registered form fields.
        Returns True if all fields are valid, False otherwise.
        Sets error messages on invalid fields and triggers UI update.
        """
        is_valid = True
        for field in list(self._fields):
            if hasattr(field, "validate_field"):
                valid = field.validate_field()
                if not valid:
                    is_valid = False
        from pyflutter.app import update
        update()
        return is_valid

    def reset(self) -> None:
        """Resets all registered fields to their initial values and clears errors."""
        for field in list(self._fields):
            if hasattr(field, "reset_field"):
                field.reset_field()
        from pyflutter.app import update
        update()

    def save(self) -> None:
        """Invokes on_saved on all registered form fields."""
        for field in list(self._fields):
            if hasattr(field, "save_field"):
                field.save_field()

    def get_values(self) -> dict[str, str]:
        """Returns a dictionary of all named fields with their current values."""
        values = {}
        for field in self._fields:
            name = getattr(field, "name", None)
            if name:
                values[name] = getattr(field, "value", "")
        return values


class Form(Widget):
    """
    Container for grouping multiple form fields (e.g. TextFormField).
    
    Parameters:
        child: The widget tree containing the form fields.
        form_key: Optional FormKey to control validation, resetting, and saving.
        key: Alias for form_key.
    """
    widget_type = "Form"

    def __init__(
        self,
        child: Widget,
        *,
        form_key: Optional[FormKey] = None,
        key: Optional[FormKey] = None,
        raw_props: Optional[dict[str, Any]] = None,
    ):
        super().__init__(raw_props=raw_props)
        self.children = [child]
        self.form_key = form_key or key
        if self.form_key:
            self._auto_register(child)

    def _auto_register(self, widget: Any) -> None:
        if hasattr(widget, "_register_with_form_key") and callable(widget._register_with_form_key):
            widget._register_with_form_key(self.form_key)
        for c in getattr(widget, "children", []):
            self._auto_register(c)
