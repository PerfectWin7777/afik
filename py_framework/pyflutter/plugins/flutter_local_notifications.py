"""
PyFlutter FlutterLocalNotifications alias module.
"""

from pyflutter.plugins.local_notifications import (
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
