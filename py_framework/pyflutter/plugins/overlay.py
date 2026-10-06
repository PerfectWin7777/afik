"""
PyFlutter Native Overlays and User Feedback Module.
Provides high-level APIs for SnackBars, Alert Dialogs, and Modal BottomSheets.
"""

from __future__ import annotations

import uuid
from typing import Any, Callable, Optional, Union

from pyflutter.core.style import Duration
from pyflutter.core.widget_base import _register_pinned_callback
from pyflutter.plugins.manager import invoke_plugin_method


def show_snack_bar(
    message: str,
    *,
    duration: Union[Duration, float, int] = Duration(seconds=4),
    action: Optional[str] = None,
    on_action: Optional[Callable[[], None]] = None,
    background_color: Optional[str] = None,
) -> None:
    """
    Displays a native floating SnackBar notification at the bottom of the screen.
    
    Parameters:
        message: The textual notification to display.
        duration: How long the SnackBar remains visible (default: 4 seconds).
        action: Optional label for an action button (e.g. "Undo", "Cancel").
        on_action: Callback executed when the user clicks the action button.
        background_color: Optional custom background hex color.
    
    Example:
        pf.show_snack_bar(
            "Article ajouté au panier",
            duration=pf.Duration(seconds=3),
            action="Annuler",
            on_action=self.undo_add,
        )
    """
    duration_ms = 4000
    if isinstance(duration, Duration):
        duration_ms = duration.in_milliseconds
    elif isinstance(duration, (int, float)):
        duration_ms = int(duration * 1000) if duration < 100 else int(duration)

    action_id = ""
    if action and on_action:
        action_id = f"cb_snackbar_{uuid.uuid4().hex[:8]}"
        _register_pinned_callback(action_id, lambda *_, **__: on_action())

    args: dict[str, Any] = {
        "message": str(message),
        "duration_ms": duration_ms,
    }
    if action:
        args["action"] = str(action)
    if action_id:
        args["action_id"] = action_id
    if background_color:
        args["background_color"] = str(background_color)

    invoke_plugin_method("overlay", "show_snack_bar", args)


def show_dialog(
    title: str,
    content: str,
    *,
    confirm_label: Optional[str] = "OK",
    cancel_label: Optional[str] = None,
    on_confirm: Optional[Callable[[], None]] = None,
    on_cancel: Optional[Callable[[], None]] = None,
) -> None:
    """
    Displays a native Material 3 AlertDialog.
    
    Parameters:
        title: Dialog headline.
        content: Main explanatory message.
        confirm_label: Label for confirmation button (default: "OK").
        cancel_label: Optional label for dismissal button (e.g. "Annuler").
        on_confirm: Callback executed when the confirm button is pressed.
        on_cancel: Callback executed when the cancel button is pressed.
    
    Example:
        pf.show_dialog(
            title="Confirmer la suppression",
            content="Voulez-vous vraiment vider votre panier ?",
            confirm_label="Supprimer",
            cancel_label="Annuler",
            on_confirm=self.clear_cart,
        )
    """
    group = f"dialog_{uuid.uuid4().hex[:8]}"
    confirm_id = ""
    if confirm_label and on_confirm:
        confirm_id = f"cb_dialog_confirm_{uuid.uuid4().hex[:8]}"
        _register_pinned_callback(confirm_id, lambda *_, **__: on_confirm(), group)

    cancel_id = ""
    if cancel_label and on_cancel:
        cancel_id = f"cb_dialog_cancel_{uuid.uuid4().hex[:8]}"
        _register_pinned_callback(cancel_id, lambda *_, **__: on_cancel(), group)

    args: dict[str, Any] = {
        "title": str(title),
        "content": str(content),
    }
    if confirm_label:
        args["confirm_label"] = str(confirm_label)
    if confirm_id:
        args["confirm_id"] = confirm_id
    if cancel_label:
        args["cancel_label"] = str(cancel_label)
    if cancel_id:
        args["cancel_id"] = cancel_id

    invoke_plugin_method("overlay", "show_dialog", args)
