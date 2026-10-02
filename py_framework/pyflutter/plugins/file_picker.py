"""
PyFlutter FilePicker plugin.
Provides native file selection dialogs.
"""

from __future__ import annotations

from typing import Any, Optional
from pyflutter.plugins.manager import call_plugin


def pick_files(
    *,
    initial_directory: Optional[str] = None,
    allowed_extensions: Optional[list[str]] = None,
    allow_multiple: bool = False,
) -> list[dict[str, Any]]:
    """
    Prompts the user to pick one or more files from disk.
    Returns a list of dicts with 'name', 'path', and 'size'.
    """
    args: dict[str, Any] = {
        "allow_multiple": "true" if allow_multiple else "false",
    }
    if initial_directory:
        args["initial_directory"] = str(initial_directory)
    if allowed_extensions:
        args["allowed_extensions"] = ",".join(allowed_extensions)

    res = call_plugin("file_picker", "pickFiles", args)
    return list(res) if isinstance(res, list) else []
