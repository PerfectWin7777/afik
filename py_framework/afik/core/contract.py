"""The props contract: which props each widget type may send to the Flutter shell.

``afik/contract/widgets.json`` lists, for every ``widget_type``, its props and their types
(``string | number | bool | color | icon | callback``, or ``{"type": "enum", "values": [...]}``).
Python checks what it sends against it; ``tools/check_contract.py`` checks it against the Dart
builder. A prop outside the contract is almost always a typo, or a prop the Dart side ignores.

* default: an unknown prop or a bad enum value logs one warning per (widget, prop);
* ``AFIK_STRICT_PROPS=1`` (used by the test-suite): the same problems raise ``ValueError``.

Widget types that are not in the contract (user-defined widgets, third-party plugins) and props
passed through ``raw_props=`` are never checked.
"""

from __future__ import annotations

import json
import os
from enum import Enum
from pathlib import Path
from typing import Any, Optional

CONTRACT_PATH = Path(__file__).resolve().parent.parent / "contract" / "widgets.json"

# Props every widget may carry: set by the framework or read for every widget by the shell.
COMMON_PROPS = frozenset({"key", "slot", "_nid", "visible", "enabled", "tooltip", "debug_banner"})

_contract: Optional[dict[str, Any]] = None
_warned: set[tuple[str, str]] = set()


def load() -> dict[str, Any]:
    global _contract
    if _contract is None:
        try:
            _contract = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            _contract = {}          # no contract available: nothing is checked
    return _contract


def strict() -> bool:
    return os.environ.get("AFIK_STRICT_PROPS") == "1"


def normalize(widget_type: str, name: str, value: Any) -> Any:
    """Turns an Enum into its value and rejects what cannot be sent as a text prop."""
    if isinstance(value, Enum):
        return value.value
    if callable(value) or isinstance(value, (list, dict, set, tuple, frozenset)):
        raise TypeError(
            f"{widget_type}.{name}: unsupported value of type {type(value).__name__}; props are "
            "text, numbers or booleans (use raw_props= for custom data, and the on_* parameters "
            "for callbacks)"
        )
    return value


def problem(widget_type: str, name: str, value: Any) -> Optional[str]:
    """Why ``widget_type.name = value`` is not in the contract, or None."""
    entry = load().get(widget_type)
    if entry is None or name in COMMON_PROPS or name.endswith("callback_id"):
        return None
    spec = entry["props"].get(name)
    if spec is None:
        prefixes = tuple(entry.get("prefixes", ()))
        if prefixes and name.startswith(prefixes):
            return None
        return f"{widget_type} has no prop '{name}' in the contract (typo, or a prop Dart does not read)"
    if isinstance(spec, dict) and spec.get("type") == "enum":
        text = _text(value)
        if text not in spec["values"]:
            return f"{widget_type}.{name} = {text!r} is not one of {spec['values']}"
    return None


def _text(value: Any) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    return str(value)


def validate(widget_type: str, name: str, value: Any) -> None:
    """Checks one prop; raises in strict mode, otherwise warns once per widget and prop."""
    why = problem(widget_type, name, value)
    if why is None:
        return
    if strict():
        raise ValueError(why)
    key = (widget_type, name)
    if key not in _warned:
        _warned.add(key)
        from afik.core.logger import logger
        logger.warning("{}", why)


class Props(dict):
    """The ``props`` dict of a widget: every assignment goes through the contract check."""

    __slots__ = ("_widget_type",)

    def __init__(self, widget_type: str):
        super().__init__()
        self._widget_type = widget_type

    def __setitem__(self, key: str, value: Any) -> None:
        validate(self._widget_type, key, value)
        super().__setitem__(key, value)

    def update(self, *args: Any, **kwargs: Any) -> None:       # type: ignore[override]
        for key, value in dict(*args, **kwargs).items():
            self[key] = value

    def setdefault(self, key: str, default: Any = None) -> Any:
        if key not in self:
            self[key] = default
        return self[key]
