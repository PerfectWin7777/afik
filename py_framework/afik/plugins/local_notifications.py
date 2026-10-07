"""
Afik local_notifications backward-compatibility alias for flutter_local_notifications.
"""

from __future__ import annotations

from afik.plugins.flutter_local_notifications import (
    FlutterLocalNotificationsPlugin,
    cancel,
    cancel_all,
    get_active_notifications,
    initialize,
    show,
)

__all__ = [
    "FlutterLocalNotificationsPlugin",
    "initialize",
    "show",
    "cancel",
    "cancel_all",
    "get_active_notifications",
]
