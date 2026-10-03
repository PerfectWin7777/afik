"""
PyFlutter Share plugin (share_plus).
Provides native sharing dialogs for text, links, and files.
"""

from __future__ import annotations

from typing import Optional
from pyflutter.plugins.manager import call_plugin


def share(
    text: str,
    subject: Optional[str] = None,
    title: Optional[str] = None,
) -> bool:
    """Shares text content via system share sheet."""
    args = {"text": str(text)}
    if subject:
        args["subject"] = str(subject)
    if title:
        args["title"] = str(title)

    res = call_plugin("share_plus", "share", args)
    return bool(isinstance(res, dict) and res.get("success", True))


def share_files(
    paths: list[str],
    text: Optional[str] = None,
    subject: Optional[str] = None,
) -> bool:
    """Shares local files via system share sheet."""
    args = {"paths": ",".join(str(p) for p in paths)}
    if text:
        args["text"] = str(text)
    if subject:
        args["subject"] = str(subject)

    res = call_plugin("share_plus", "shareFiles", args)
    return bool(isinstance(res, dict) and res.get("success", True))


def share_uri(uri: str) -> bool:
    """Shares a URI via system share sheet."""
    res = call_plugin("share_plus", "shareUri", {"uri": str(uri)})
    return bool(isinstance(res, dict) and res.get("success", True))
