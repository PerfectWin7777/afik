"""
Afik share backward-compatibility alias for share_plus.
"""

from __future__ import annotations

from afik.plugins.share_plus import (
    share,
    share_files,
    share_uri,
)

__all__ = [
    "share",
    "share_files",
    "share_uri",
]
