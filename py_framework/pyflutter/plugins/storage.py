"""
PyFlutter storage backward-compatibility alias for shared_preferences.
"""

from __future__ import annotations

from pyflutter.plugins.shared_preferences import (
    SharedPreferences,
    clear,
    get_all,
    get_bool,
    get_double,
    get_int,
    get_string,
    remove,
    set_bool,
    set_double,
    set_int,
    set_string,
)

__all__ = [
    "SharedPreferences",
    "set_string",
    "get_string",
    "set_int",
    "get_int",
    "set_bool",
    "get_bool",
    "set_double",
    "get_double",
    "remove",
    "clear",
    "get_all",
]
