"""
PyFlutter Hive plugin.
Lightweight and blazing-fast key-value database ("boxes").
"""

from __future__ import annotations

from typing import Any, Optional
from pyflutter.plugins.manager import call_plugin


class Box:
    """Represents an open Hive database storage box."""

    def __init__(self, name: str):
        self.name = str(name)
        self.is_open: bool = True

    def put(self, key: str, value: Any) -> bool:
        """Stores a key-value entry in the box."""
        res = call_plugin("hive", "put", {"boxName": self.name, "key": str(key), "value": value})
        return bool(isinstance(res, dict) and res.get("success", True))

    def get(self, key: str, default: Any = None) -> Any:
        """Retrieves a stored value by key."""
        res = call_plugin("hive", "get", {"boxName": self.name, "key": str(key), "defaultValue": default})
        if isinstance(res, dict) and "value" in res:
            val = res["value"]
            return val if val is not None else default
        return default

    def delete(self, key: str) -> bool:
        """Deletes a key from the box."""
        res = call_plugin("hive", "delete", {"boxName": self.name, "key": str(key)})
        return bool(isinstance(res, dict) and res.get("success", True))

    def clear(self) -> bool:
        """Clears all entries in the box."""
        res = call_plugin("hive", "clear", {"boxName": self.name})
        return bool(isinstance(res, dict) and res.get("cleared", True))

    def contains_key(self, key: str) -> bool:
        """Checks if a key exists in the box."""
        val = self.get(key)
        return val is not None

    def get_all(self) -> dict[str, Any]:
        """Returns all entries in the box as a dict."""
        res = call_plugin("hive", "getAll", {"boxName": self.name})
        return dict(res) if isinstance(res, dict) else {}

    def keys(self) -> list[str]:
        return list(self.get_all().keys())

    def values(self) -> list[Any]:
        return list(self.get_all().values())

    def items(self) -> list[tuple[str, Any]]:
        return list(self.get_all().items())

    def close(self) -> bool:
        """Closes the box."""
        call_plugin("hive", "close", {"boxName": self.name})
        self.is_open = False
        return True

    def __getitem__(self, key: str) -> Any:
        val = self.get(key)
        if val is None:
            raise KeyError(key)
        return val

    def __setitem__(self, key: str, value: Any) -> None:
        self.put(key, value)

    def __delitem__(self, key: str) -> None:
        self.delete(key)

    def __contains__(self, key: str) -> bool:
        return self.contains_key(key)


_opened_boxes: dict[str, Box] = {}


def open_box(name: str) -> Box:
    """Opens a Hive box by name and returns the Box reference."""
    call_plugin("hive", "openBox", {"boxName": str(name)})
    if name not in _opened_boxes:
        _opened_boxes[name] = Box(name)
    return _opened_boxes[name]


def box(name: str) -> Box:
    """Returns an already opened box or opens it if not yet loaded."""
    return open_box(name)
