"""
PyFlutter FilePicker plugin.
Provides native file selection dialogs.
"""

from __future__ import annotations

import base64
from typing import Any, Optional
from pyflutter.plugins.manager import INTERACTIVE_TIMEOUT, call_plugin


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

    res = call_plugin("file_picker", "pickFiles", args, timeout=INTERACTIVE_TIMEOUT)
    return list(res) if isinstance(res, list) else []


def get_directory_path(*, initial_directory: Optional[str] = None) -> Optional[str]:
    """Prompts the user to pick a directory. Returns its path, or None if cancelled."""
    args: dict[str, Any] = {}
    if initial_directory:
        args["initial_directory"] = str(initial_directory)
    res = call_plugin("file_picker", "getDirectoryPath", args, timeout=INTERACTIVE_TIMEOUT)
    return str(res) if isinstance(res, str) and res else None


def save_file(
    file_name: str,
    data: bytes,
    *,
    initial_directory: Optional[str] = None,
) -> Optional[str]:
    """Asks the user where to save ``data`` under ``file_name``. Returns the saved location,
    or None if the dialog was cancelled."""
    args: dict[str, Any] = {
        "file_name": str(file_name),
        "data": base64.b64encode(bytes(data)).decode("ascii"),
    }
    if initial_directory:
        args["initial_directory"] = str(initial_directory)
    res = call_plugin("file_picker", "saveFile", args, timeout=INTERACTIVE_TIMEOUT)
    return str(res) if isinstance(res, str) and res else None
