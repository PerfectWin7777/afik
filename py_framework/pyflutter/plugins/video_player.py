"""
PyFlutter VideoPlayer plugin.
Provides video playback controllers and streaming capabilities.
"""

from __future__ import annotations

import itertools
from typing import Optional
from pyflutter.plugins.manager import call_plugin


_video_counter = itertools.count()


class VideoPlayerController:
    """Controls video playback, seeking, and properties."""

    def __init__(self, url: str, is_asset: bool = False, controller_id: Optional[str] = None):
        self.url = str(url)
        self.is_asset = is_asset
        self.controller_id = controller_id or f"vid_{next(_video_counter)}"
        self.is_initialized: bool = False
        self._is_playing: bool = False
        self._is_looping: bool = False
        self._duration: float = 300.0

        call_plugin("video_player", "create", {
            "controllerId": self.controller_id,
            "url": self.url,
            "isAsset": "true" if is_asset else "false",
        })

    @classmethod
    def network(cls, url: str) -> VideoPlayerController:
        """Constructs a controller from a network video URL."""
        return cls(url, is_asset=False)

    @classmethod
    def asset(cls, asset_name: str) -> VideoPlayerController:
        """Constructs a controller from an application asset."""
        return cls(asset_name, is_asset=True)

    @classmethod
    def file(cls, path: str) -> VideoPlayerController:
        """Constructs a controller from a local file path."""
        return cls(path, is_asset=False)

    def initialize(self) -> bool:
        """Initializes video decoding and fetches metadata."""
        res = call_plugin("video_player", "initialize", {"controllerId": self.controller_id})
        self.is_initialized = True
        if isinstance(res, dict) and "duration" in res:
            try:
                self._duration = float(res["duration"])
            except (ValueError, TypeError):
                pass
        return True

    def play(self) -> bool:
        """Starts video playback."""
        call_plugin("video_player", "play", {"controllerId": self.controller_id})
        self._is_playing = True
        return True

    def pause(self) -> bool:
        """Pauses video playback."""
        call_plugin("video_player", "pause", {"controllerId": self.controller_id})
        self._is_playing = False
        return True

    def seek_to(self, position_seconds: float) -> bool:
        """Seeks to a specific timestamp in seconds."""
        call_plugin("video_player", "seekTo", {
            "controllerId": self.controller_id,
            "position": str(position_seconds),
        })
        return True

    def set_volume(self, volume: float) -> bool:
        """Sets audio volume from 0.0 to 1.0."""
        call_plugin("video_player", "setVolume", {
            "controllerId": self.controller_id,
            "volume": str(max(0.0, min(1.0, volume))),
        })
        return True

    def set_looping(self, looping: bool) -> bool:
        """Sets whether playback should automatically loop."""
        self._is_looping = looping
        call_plugin("video_player", "setLooping", {
            "controllerId": self.controller_id,
            "looping": "true" if looping else "false",
        })
        return True

    def is_playing(self) -> bool:
        """Checks if video is currently playing."""
        return self._is_playing

    def position(self) -> float:
        """Returns current playhead position in seconds."""
        res = call_plugin("video_player", "getPosition", {"controllerId": self.controller_id})
        if isinstance(res, dict) and "position" in res:
            try:
                return float(res["position"])
            except (ValueError, TypeError):
                pass
        return 0.0

    @property
    def duration(self) -> float:
        """Returns total duration of video in seconds."""
        return self._duration

    def dispose(self) -> None:
        """Disposes resources and releases the video stream."""
        call_plugin("video_player", "dispose", {"controllerId": self.controller_id})
        self.is_initialized = False
        self._is_playing = False
