"""
PyFlutter Connectivity plugin (connectivity_plus).
Checks device network connectivity states (WiFi, Mobile, Ethernet, None).
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
    NONE = "none"


def check_connectivity() -> ConnectivityResult:
    """Checks the current network connectivity status of the device."""
    res = call_plugin("connectivity", "checkConnectivity", {})
    if isinstance(res, dict):
        status = res.get("status", "none")
    elif isinstance(res, str):
        status = res
    else:
        status = "wifi"

    try:
        return ConnectivityResult(status.lower())
    except ValueError:
        return ConnectivityResult.NONE


def is_connected() -> bool:
    """Convenience method returning True if device has any active internet connection."""
    return check_connectivity() != ConnectivityResult.NONE
