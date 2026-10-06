"""
PyFlutter Connectivity plugin (matches pub.dev package: connectivity_plus).
Checks the device network state (WiFi, mobile, ethernet, ...).
"""

from __future__ import annotations

from enum import Enum

from pyflutter.plugins.manager import call_plugin


class ConnectivityResult(str, Enum):
    WIFI = "wifi"
    MOBILE = "mobile"
    ETHERNET = "ethernet"
    BLUETOOTH = "bluetooth"
    VPN = "vpn"
    OTHER = "other"
    NONE = "none"


def _parse(name: object) -> ConnectivityResult:
    try:
        return ConnectivityResult(str(name).lower())
    except ValueError:
        return ConnectivityResult.OTHER


def check_connectivity_all() -> list[ConnectivityResult]:
    """Every active connection type reported by the platform (empty list means offline).

    A missing or malformed answer reads as offline, never as connected.
    """
    res = call_plugin("connectivity", "checkConnectivity", {})
    if isinstance(res, dict) and isinstance(res.get("results"), list):
        found = [_parse(r) for r in res["results"]]
    elif isinstance(res, dict) and "status" in res:
        found = [_parse(res["status"])]
    else:
        found = []
    return [r for r in found if r != ConnectivityResult.NONE]


def check_connectivity() -> ConnectivityResult:
    """The first active connection type, or ``ConnectivityResult.NONE`` when offline."""
    active = check_connectivity_all()
    return active[0] if active else ConnectivityResult.NONE


def is_connected() -> bool:
    """True if the device reports at least one active network connection."""
    return bool(check_connectivity_all())


__all__ = [
    "ConnectivityResult",
    "check_connectivity",
    "check_connectivity_all",
    "is_connected",
]
