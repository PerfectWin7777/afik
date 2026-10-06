"""
PyFlutter LocalNotifications plugin (matches pub.dev package: flutter_local_notifications).
Displays scheduled, ongoing, or immediate system notifications.
"""

from __future__ import annotations

from typing import Any, Optional
from pyflutter.plugins.manager import call_plugin


class FlutterLocalNotificationsPlugin:
    """Manages system local notifications (flutter_local_notifications)."""

    def initialize(self) -> bool:
        """Initializes notification channels and settings."""
        res = call_plugin("flutter_local_notifications", "initialize", {})
        return isinstance(res, dict) and res.get("initialized") is True

    def show(
        self,
        notification_id: int,
        title: str,
        body: str,
        payload: Optional[str] = None,
        *,
        channel_id: str = "default_channel",
        channel_name: str = "General",
    ) -> bool:
        """Displays an immediate notification."""
        args: dict[str, Any] = {
            "id": str(notification_id),
            "title": str(title),
            "body": str(body),
            "channelId": str(channel_id),
            "channelName": str(channel_name),
        }
        if payload:
            args["payload"] = str(payload)

        res = call_plugin("flutter_local_notifications", "show", args)
        return isinstance(res, dict) and res.get("shown") is True

    def cancel(self, notification_id: int) -> bool:
        """Cancels a notification by ID."""
        res = call_plugin("flutter_local_notifications", "cancel", {"id": str(notification_id)})
        return isinstance(res, dict) and res.get("cancelled") is True

    def cancel_all(self) -> bool:
        """Cancels all active notifications."""
        res = call_plugin("flutter_local_notifications", "cancelAll", {})
        return isinstance(res, dict) and res.get("cancelled") is True

    def get_active_notifications(self) -> list[dict[str, Any]]:
        """Returns the list of currently active notifications."""
        res = call_plugin("flutter_local_notifications", "getActiveNotifications", {})
        return list(res) if isinstance(res, list) else []


# Module singleton & conveniences
_notifications = FlutterLocalNotificationsPlugin()
initialize = _notifications.initialize
show = _notifications.show
cancel = _notifications.cancel
cancel_all = _notifications.cancel_all
get_active_notifications = _notifications.get_active_notifications

__all__ = [
    "FlutterLocalNotificationsPlugin",
    "initialize",
    "show",
    "cancel",
    "cancel_all",
    "get_active_notifications",
]
