"""
PyFlutter DeviceInfo plugin (matches pub.dev package: device_info_plus).
Provides operating system, hardware, and device information.
"""

from __future__ import annotations

from typing import Any

from pyflutter.plugins.manager import call_plugin


def get_device_info() -> dict[str, Any]:
    """
    Returns a dictionary of platform and device properties:
    - platform: 'android', 'ios', 'windows', 'macos', 'linux'
    - version: OS version
    - hostname: local machine/device name
    - numberOfProcessors: CPU cores
    - localeName: e.g. 'en_US'
    - isPhysicalDevice: bool
    """
    res = call_plugin("device_info_plus", "getDeviceInfo", {})
    return dict(res) if isinstance(res, dict) else {}


def get_platform() -> str:
    """Returns the current operating system name (e.g. 'android', 'windows')."""
    info = get_device_info()
    return str(info.get("platform", ""))


class DeviceInfoPlugin:
    """Class interface matching Flutter's DeviceInfoPlugin API."""

    get_device_info = staticmethod(get_device_info)
    get_platform = staticmethod(get_platform)


__all__ = [
    "DeviceInfoPlugin",
    "get_device_info",
    "get_platform",
]
