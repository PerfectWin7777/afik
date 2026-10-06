"""
PyFlutter PathProvider plugin.
Provides system directory locations (documents, temp, downloads).
"""

from __future__ import annotations

from typing import Optional

from pyflutter.plugins.manager import call_plugin


def get_app_documents_directory() -> str:
    """Returns the path to the directory where the application may place data that is user-generated."""
    return str(call_plugin("path_provider", "getApplicationDocumentsDirectory", {}) or "")


def get_temporary_directory() -> str:
    """Returns the path to the directory where the application may place temporary files."""
    return str(call_plugin("path_provider", "getTemporaryDirectory", {}) or "")


def get_app_support_directory() -> str:
    """Returns the path to a directory where the application may place application support files."""
    return str(call_plugin("path_provider", "getApplicationSupportDirectory", {}) or "")


def get_downloads_directory() -> Optional[str]:
    """Returns the path to the directory for user downloads."""
    res = call_plugin("path_provider", "getDownloadsDirectory", {})
    return str(res) if res else None
