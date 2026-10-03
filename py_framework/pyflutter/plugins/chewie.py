"""
PyFlutter Chewie plugin.
Provides enhanced video playback controllers and full-screen Material UI wrapper.
"""

from __future__ import annotations

from typing import Any, Optional
from pyflutter.plugins.manager import call_plugin
from pyflutter.plugins.video_player import VideoPlayerController


class ChewieController:
    """Controls advanced Chewie playback properties on top of a VideoPlayerController."""

    def __init__(
        self,
        video_player_controller: VideoPlayerController,
        *,
        auto_play: bool = False,
        looping: bool = False,
        show_controls: bool = True,
        aspect_ratio: float = 16.0 / 9.0,
        full_screen_by_default: bool = False,
    ):
        self.video_player_controller = video_player_controller
        self.auto_play = auto_play
        self.looping = looping
        self.show_controls = show_controls
        self.aspect_ratio = aspect_ratio
        self.is_full_screen = full_screen_by_default

        call_plugin("chewie", "createChewieController", {
            "controllerId": video_player_controller.controller_id,
            "autoPlay": "true" if auto_play else "false",
            "looping": "true" if looping else "false",
            "showControls": "true" if show_controls else "false",
            "aspectRatio": str(aspect_ratio),
        })

    def enter_full_screen(self) -> bool:
        """Transitions video display into full-screen mode."""
        self.is_full_screen = True
        call_plugin("chewie", "enterFullScreen", {
            "controllerId": self.video_player_controller.controller_id,
        })
        return True

    def exit_full_screen(self) -> bool:
        """Exits full-screen mode."""
        self.is_full_screen = False
        call_plugin("chewie", "exitFullScreen", {
            "controllerId": self.video_player_controller.controller_id,
        })
        return True

    def dispose(self) -> None:
        """Disposes the controller resources."""
        self.video_player_controller.dispose()


from pyflutter.widgets.widgets import Chewie

__all__ = [
    "ChewieController",
    "Chewie",
]

