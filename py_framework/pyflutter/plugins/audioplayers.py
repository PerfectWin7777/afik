"""
PyFlutter AudioPlayers plugin (matches pub.dev package: audioplayers).
Provides sound effects and audio playback capabilities.
"""

from __future__ import annotations

import itertools
from enum import Enum
from typing import Optional
from pyflutter.plugins.manager import call_plugin


class PlayerState(str, Enum):
    STOPPED = "stopped"
    PLAYING = "playing"
    PAUSED = "paused"
    COMPLETED = "completed"


_player_id_counter = itertools.count()


class AudioPlayer:
    """Manages audio playback sessions (audioplayers)."""

    def __init__(self, player_id: Optional[str] = None):
        self.player_id = player_id or f"player_{next(_player_id_counter)}"
        self._state: PlayerState = PlayerState.STOPPED

    def play(self, url: str, volume: float = 1.0, position: float = 0.0) -> bool:
        """Plays audio from an HTTP URL or local file path."""
        res = call_plugin("audioplayers", "play", {
            "playerId": self.player_id,
            "url": str(url),
            "volume": str(volume),
            "position": str(position),
        })
        self._state = PlayerState.PLAYING
        return True

    def pause(self) -> bool:
        """Pauses current audio playback."""
        res = call_plugin("audioplayers", "pause", {"playerId": self.player_id})
        self._state = PlayerState.PAUSED
        return True

    def resume(self) -> bool:
        """Resumes paused audio playback."""
        res = call_plugin("audioplayers", "resume", {"playerId": self.player_id})
        self._state = PlayerState.PLAYING
        return True

    def stop(self) -> bool:
        """Stops audio playback and resets position."""
        res = call_plugin("audioplayers", "stop", {"playerId": self.player_id})
        self._state = PlayerState.STOPPED
        return True

    def seek(self, position_seconds: float) -> bool:
        """Seeks to a specific timestamp in seconds."""
        call_plugin("audioplayers", "seek", {
            "playerId": self.player_id,
            "position": str(position_seconds),
        })
        return True

    def set_volume(self, volume: float) -> bool:
        """Sets playback volume between 0.0 (silent) and 1.0 (max)."""
        call_plugin("audioplayers", "setVolume", {
            "playerId": self.player_id,
            "volume": str(max(0.0, min(1.0, volume))),
        })
        return True

    def get_duration(self) -> float:
        """Returns total duration of current track in seconds."""
        res = call_plugin("audioplayers", "getDuration", {"playerId": self.player_id})
        if isinstance(res, dict) and "duration" in res:
            try:
                return float(res["duration"])
            except (ValueError, TypeError):
                pass
        return 180.0

    def get_position(self) -> float:
        """Returns current playhead position in seconds."""
        res = call_plugin("audioplayers", "getPosition", {"playerId": self.player_id})
        if isinstance(res, dict) and "position" in res:
            try:
                return float(res["position"])
            except (ValueError, TypeError):
                pass
        return 0.0

    @property
    def state(self) -> PlayerState:
        """Returns current playback state."""
        res = call_plugin("audioplayers", "getState", {"playerId": self.player_id})
        if isinstance(res, dict) and "state" in res:
            try:
                self._state = PlayerState(res["state"])
            except ValueError:
                pass
        return self._state


__all__ = [
    "AudioPlayer",
    "PlayerState",
]
