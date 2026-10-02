"""
PyFlutter Storage / SharedPreferences plugin.
Provides persistent Key-Value storage across application runs.
"""

from __future__ import annotations

from typing import Any, Optional
from pyflutter.plugins.manager import call_plugin


def set_string(key: str, value: str) -> bool:
    """Stores a string value persistently."""
    return bool(call_plugin("storage", "setString", {"key": key, "value": str(value)}))


def get_string(key: str, default: Optional[str] = None) -> Optional[str]:
    """Retrieves a persistent string value."""
    res = call_plugin("storage", "getString", {"key": key})
    return str(res) if res is not None else default


def set_int(key: str, value: int) -> bool:
    """Stores an integer value persistently."""
    return bool(call_plugin("storage", "setInt", {"key": key, "value": str(value)}))


def get_int(key: str, default: Optional[int] = None) -> Optional[int]:
    """Retrieves a persistent integer value."""
    res = call_plugin("storage", "getInt", {"key": key})
    if res is not None:
        try:
            return int(res)
        except (ValueError, TypeError):
            pass
    return default


def set_bool(key: str, value: bool) -> bool:
    """Stores a boolean value persistently."""
    return bool(call_plugin("storage", "setBool", {"key": key, "value": "true" if value else "false"}))


def get_bool(key: str, default: Optional[bool] = None) -> Optional[bool]:
    """Retrieves a persistent boolean value."""
    res = call_plugin("storage", "getBool", {"key": key})
    if res is not None:
        return True if str(res).lower() in ("true", "1") else False
    return default


def set_double(key: str, value: float) -> bool:
    """Stores a float value persistently."""
    return bool(call_plugin("storage", "setDouble", {"key": key, "value": str(value)}))


def get_double(key: str, default: Optional[float] = None) -> Optional[float]:
    """Retrieves a persistent float value."""
    res = call_plugin("storage", "getDouble", {"key": key})
    if res is not None:
        try:
            return float(res)
        except (ValueError, TypeError):
            pass
    return default


def remove(key: str) -> bool:
    """Removes a key from persistent storage."""
    return bool(call_plugin("storage", "remove", {"key": key}))


def clear() -> bool:
    """Clears all entries in persistent storage."""
    return bool(call_plugin("storage", "clear", {}))


def get_all() -> dict[str, Any]:
    """Returns a dictionary of all stored key-value pairs."""
    res = call_plugin("storage", "getAll", {})
    return dict(res) if isinstance(res, dict) else {}
