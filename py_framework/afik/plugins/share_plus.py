"""
Afik Share plugin (matches pub.dev package: share_plus).
Provides native sharing dialogs for text, links, and files.

Every function returns True only when the platform reports that the user picked a target.
"""

from __future__ import annotations

import json
from typing import Optional

from afik.plugins.manager import call_plugin


def _shared(res: object) -> bool:
    return isinstance(res, dict) and res.get("success") is True


def share(
    text: str,
    subject: Optional[str] = None,
    title: Optional[str] = None,
) -> bool:
    """Shares text content via the system share sheet."""
    args = {"text": str(text)}
    if subject:
        args["subject"] = str(subject)
    if title:
        args["title"] = str(title)
    return _shared(call_plugin("share_plus", "share", args))


def share_files(
    paths: list[str],
    text: Optional[str] = None,
    subject: Optional[str] = None,
) -> bool:
    """Shares local files via the system share sheet."""
    args = {"paths": json.dumps([str(p) for p in paths])}
    if text:
        args["text"] = str(text)
    if subject:
        args["subject"] = str(subject)
    return _shared(call_plugin("share_plus", "shareFiles", args))


def share_uri(uri: str) -> bool:
    """Shares a URI via the system share sheet."""
    return _shared(call_plugin("share_plus", "shareUri", {"uri": str(uri)}))


__all__ = [
    "share",
    "share_files",
    "share_uri",
]
