"""
PyFlutter VideoPlayer plugin.
Provides video playback controllers and streaming capabilities.
"""

from __future__ import annotations

import itertools
from typing import Optional

from pyflutter.plugins.manager import call_plugin, require

_video_counter = itertools.count()


class VideoPlayerController:
    """Controls video playback, seeking and properties (video_player)."""

    def __init__(self, url: str, is_asset: bool = False, controller_id: Optional[str] = None):
        self.url = str(url)
        self.is_asset = is_asset
        self.controller_id = controller_id or f"vid_{next(_video_counter)}"
        self.is_initialized: bool = False
        self._is_playing: bool = False
        self._is_looping: bool = False
        self._duration: Optional[float] = None
        self.aspect_ratio: Optional[float] = None

        require(call_plugin("video_player", "create", {
            "controllerId": self.controller_id,
            "url": self.url,
            "isAsset": "true" if is_asset else "false",
        }), "created", "VideoPlayerController.create")

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
        """Opens the video and reads its metadata. True once the platform confirms it."""
        res = call_plugin("video_player", "initialize", {"controllerId": self.controller_id})
        self.is_initialized = isinstance(res, dict) and res.get("initialized") is True
        if self.is_initialized:
            if isinstance(res.get("duration"), (int, float)):
                self._duration = float(res["duration"])
            if isinstance(res.get("aspectRatio"), (int, float)):
                self.aspect_ratio = float(res["aspectRatio"])
        return self.is_initialized

    def _playing_from(self, res: object) -> bool:
        if isinstance(res, dict) and isinstance(res.get("isPlaying"), bool):
            self._is_playing = res["isPlaying"]
            return True
        return False

    def play(self) -> bool:
        """Starts playback. True if the platform reports the video is now playing."""
        res = call_plugin("video_player", "play", {"controllerId": self.controller_id})
        return self._playing_from(res) and self._is_playing

    def pause(self) -> bool:
        """Pauses playback. True if the platform reports the video is now paused."""
        res = call_plugin("video_player", "pause", {"controllerId": self.controller_id})
        return self._playing_from(res) and not self._is_playing

    def seek_to(self, position_seconds: float) -> bool:
        """Moves the playhead."""
        res = call_plugin("video_player", "seekTo", {
            "controllerId": self.controller_id,
            "position": str(position_seconds),
        })
        return isinstance(res, dict) and "position" in res

    def set_volume(self, volume: float) -> bool:
        """Sets the volume between 0.0 and 1.0."""
        res = call_plugin("video_player", "setVolume", {
            "controllerId": self.controller_id,
            "volume": str(max(0.0, min(1.0, volume))),
        })
        return isinstance(res, dict) and "volume" in res

    def set_looping(self, looping: bool) -> bool:
        """Turns looping on or off."""
        res = call_plugin("video_player", "setLooping", {
            "controllerId": self.controller_id,
            "looping": "true" if looping else "false",
        })
        if isinstance(res, dict) and isinstance(res.get("isLooping"), bool):
            self._is_looping = res["isLooping"]
            return True
        return False

    def is_playing(self) -> bool:
        """Whether the video is playing right now, asked to the platform."""
        res = call_plugin("video_player", "getState", {"controllerId": self.controller_id})
        if isinstance(res, dict) and isinstance(res.get("isPlaying"), bool):
            self._is_playing = res["isPlaying"]
        return self._is_playing

    def position(self) -> float:
        """Current playhead position in seconds (0.0 if the platform cannot tell)."""
        res = call_plugin("video_player", "getPosition", {"controllerId": self.controller_id})
        value = res.get("position") if isinstance(res, dict) else None
        return float(value) if isinstance(value, (int, float)) else 0.0

    @property
    def duration(self) -> Optional[float]:
        """Total duration in seconds, known after :meth:`initialize`; None before."""
        return self._duration

    def dispose(self) -> None:
        """Releases the video stream."""
        call_plugin("video_player", "dispose", {"controllerId": self.controller_id})
        self.is_initialized = False
        self._is_playing = False


from pyflutter.widgets.widgets import VideoPlayer  # noqa: E402  (re-export; widgets import this module)

__all__ = [
    "VideoPlayerController",
    "VideoPlayer",
]

