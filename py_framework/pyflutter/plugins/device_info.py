"""
PyFlutter DeviceInfo plugin.
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
    res = call_plugin("device_info", "getDeviceInfo", {})
    return dict(res) if isinstance(res, dict) else {}


def get_platform() -> str:
    """Returns the current operating system name (e.g. 'android', 'windows')."""
    info = get_device_info()
    return str(info.get("platform", ""))
