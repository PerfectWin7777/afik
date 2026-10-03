"""
PyFlutter local_notifications backward-compatibility alias for flutter_local_notifications.
"""

from __future__ import annotations

from pyflutter.plugins.flutter_local_notifications import (
    FlutterLocalNotificationsPlugin,
    initialize,
    show,
    cancel,
    cancel_all,
    get_active_notifications,
)

__all__ = [
    "FlutterLocalNotificationsPlugin",
    "initialize",
    "show",
    "cancel",
    "cancel_all",
    "get_active_notifications",
]
