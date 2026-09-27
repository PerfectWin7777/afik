"""
PyFlutter native plugins package.
"""

from __future__ import annotations

from pyflutter.plugins import url_launcher
from pyflutter.plugins.manager import add_flutter_package, invoke_plugin_method

__all__ = [
    "url_launcher",
    "add_flutter_package",
    "invoke_plugin_method",
]
