"""
Afik connectivity backward-compatibility alias for connectivity_plus.
"""

from __future__ import annotations

from afik.plugins.connectivity_plus import (
    ConnectivityResult,
    check_connectivity,
    is_connected,
)

__all__ = [
    "ConnectivityResult",
    "check_connectivity",
    "is_connected",
]
