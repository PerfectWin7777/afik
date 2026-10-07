"""
Forms, validation, and text editing controllers for Afik.
Provides a reactive, typed, Flutter-standard Form API.
"""

from __future__ import annotations

import re
import weakref
from typing import Any, Callable, Optional

from afik.core.logger import logger
from afik.core.widget_base import Widget


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

    The key outlives the widgets: a ``TextFormField`` is recreated on every build, so the
    values typed by the user and the validation errors are stored **here**, indexed by the
    field ``name``, and every new field with the same name starts from them. Give a ``name`` to
    every field whose value must survive a rebuild (fields without a name keep working but
    restart from their own initial value each time the screen is rebuilt).
    """

    def __init__(self):
        # Live fields only: a rebuilt field replaces the previous one of the same name, and
        # fields nobody references any more disappear on their own.
        self._fields: "weakref.WeakSet[Any]" = weakref.WeakSet()
        self._by_name: dict[str, "weakref.ReferenceType[Any]"] = {}
        self._values: dict[str, str] = {}
        self._errors: dict[str, str] = {}

    # -- registration ------------------------------------------------------------------

    def register(self, field: Any) -> None:
        """Adds a field and makes it start from the value and error the key remembers."""
        self._fields.add(field)
        name = getattr(field, "name", None)
        if not name:
            return
        previous = self._by_name.get(name)
        old = previous() if previous is not None else None
        if old is not None and old is not field:
            self._fields.discard(old)
        self._by_name[name] = weakref.ref(field)

        if getattr(field, "controller", None) is not None:
            # The controller belongs to the user and already holds the typed text.
            self._values[name] = field.value
        elif name in self._values:
            field.props["value"] = self._values[name]
        else:
            self._values[name] = str(field.props.get("value", ""))

        if name in self._errors:
            field.props["error_text"] = self._errors[name]

    def unregister(self, field: Any) -> None:
        self._fields.discard(field)
        name = getattr(field, "name", None)
        ref = self._by_name.get(name) if name else None
        if ref is not None and ref() is field:
            del self._by_name[name]

    # -- values ------------------------------------------------------------------------

    def set_value(self, name: str, text: Any) -> None:
        """Sets the value of a named field, in the store and in its live widget."""
        self.set_values({name: text})

    def set_values(self, values: dict[str, Any]) -> None:
        """Sets several named values at once (for example to load a record into the form)."""
        for name, text in values.items():
            text = "" if text is None else str(text)
            self._values[name] = text
            ref = self._by_name.get(name)
            field = ref() if ref is not None else None
            if field is not None:
                field.set_value(text, auto_update=False)
        from afik.app import update
        update()

    def _store_value(self, name: str, text: Any) -> None:
        self._values[name] = "" if text is None else str(text)

    def _store_error(self, name: str, error: Optional[str]) -> None:
        if error:
            self._errors[name] = str(error)
        else:
            self._errors.pop(name, None)

    def get_values(self) -> dict[str, str]:
        """Returns a dictionary of all named fields with their current values."""
        values = dict(self._values)
        for name, ref in self._by_name.items():
            field = ref()
            if field is not None:
                values[name] = field.value
        return values

    # -- Form operations -----------------------------------------------------------------

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
        from afik.app import update
        update()
        return is_valid

    def reset(self) -> None:
        """Resets all registered fields to their initial values and clears errors."""
        for field in list(self._fields):
            if hasattr(field, "reset_field"):
                field.reset_field()
        self._errors.clear()
        from afik.app import update
        update()

    def save(self) -> None:
        """Invokes on_saved on all registered form fields."""
        for field in list(self._fields):
            if hasattr(field, "save_field"):
                field.save_field()


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
