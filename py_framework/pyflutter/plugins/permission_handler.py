"""
PyFlutter PermissionHandler plugin (permission_handler).
Checks and requests runtime permissions on Android, iOS, and desktop.
"""

from __future__ import annotations

from enum import Enum
from typing import Union
from pyflutter.plugins.manager import INTERACTIVE_TIMEOUT, call_plugin


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


def _parse_status(res: object) -> PermissionStatus:
    """Anything missing, unknown or malformed is a refusal, never a grant."""
    raw = res.get("status") if isinstance(res, dict) else None
    try:
        return PermissionStatus(str(raw))
    except ValueError:
        return PermissionStatus.DENIED


def _permission_name(permission: Union[Permission, str]) -> str:
    return permission.value if isinstance(permission, Permission) else str(permission)


def check_permission(permission: Union[Permission, str]) -> PermissionStatus:
    """Checks the current authorization status of a permission."""
    res = call_plugin("permission_handler", "checkPermission", {"permission": _permission_name(permission)})
    return _parse_status(res)


def request_permission(permission: Union[Permission, str]) -> PermissionStatus:
    """Prompts the user to grant a permission (waits for the user's answer)."""
    res = call_plugin(
        "permission_handler", "requestPermission", {"permission": _permission_name(permission)},
        timeout=INTERACTIVE_TIMEOUT,
    )
    return _parse_status(res)


def open_app_settings() -> bool:
    """Opens system settings for the current application."""
    res = call_plugin("permission_handler", "openAppSettings", {})
    return isinstance(res, dict) and res.get("opened") is True
