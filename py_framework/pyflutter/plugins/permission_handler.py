"""
PyFlutter PermissionHandler plugin (permission_handler).
Checks and requests runtime permissions on Android, iOS, and desktop.
"""

from __future__ import annotations

from enum import Enum
from typing import Union
from pyflutter.plugins.manager import call_plugin


class Permission(str, Enum):
    CAMERA = "camera"
    MICROPHONE = "microphone"
    STORAGE = "storage"
    PHOTOS = "photos"
    LOCATION = "location"
    LOCATION_ALWAYS = "locationAlways"
    LOCATION_WHEN_IN_USE = "locationWhenInUse"
    NOTIFICATION = "notification"
    BLUETOOTH = "bluetooth"
    CONTACTS = "contacts"


class PermissionStatus(str, Enum):
    GRANTED = "granted"
    DENIED = "denied"
    RESTRICTED = "restricted"
    LIMITED = "limited"
    PERMANENTLY_DENIED = "permanentlyDenied"

    @property
    def is_granted(self) -> bool:
        return self == PermissionStatus.GRANTED

    @property
    def is_denied(self) -> bool:
        return self == PermissionStatus.DENIED

    @property
    def is_permanently_denied(self) -> bool:
        return self == PermissionStatus.PERMANENTLY_DENIED


def check_permission(permission: Union[Permission, str]) -> PermissionStatus:
    """Checks the current authorization status of a permission."""
    perm_val = permission.value if isinstance(permission, Permission) else str(permission)
    res = call_plugin("permission_handler", "checkPermission", {"permission": perm_val})
    status_str = res.get("status", "granted") if isinstance(res, dict) else "granted"
    try:
        return PermissionStatus(status_str.lower())
    except ValueError:
        return PermissionStatus.GRANTED


def request_permission(permission: Union[Permission, str]) -> PermissionStatus:
    """Prompts the user to grant a permission."""
    perm_val = permission.value if isinstance(permission, Permission) else str(permission)
    res = call_plugin("permission_handler", "requestPermission", {"permission": perm_val})
    status_str = res.get("status", "granted") if isinstance(res, dict) else "granted"
    try:
        return PermissionStatus(status_str.lower())
    except ValueError:
        return PermissionStatus.GRANTED


def open_app_settings() -> bool:
    """Opens system settings for the current application."""
    res = call_plugin("permission_handler", "openAppSettings", {})
    return bool(isinstance(res, dict) and res.get("opened", True))
