"""
Afik device_info backward-compatibility alias for device_info_plus.
"""

from __future__ import annotations

from afik.plugins.device_info_plus import (
    DeviceInfoPlugin,
    get_device_info,
    get_platform,
)

__all__ = [
    "DeviceInfoPlugin",
    "get_device_info",
    "get_platform",
]
