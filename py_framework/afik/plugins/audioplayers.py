"""
Afik AudioPlayers plugin (matches pub.dev package: audioplayers).
Provides sound effects and audio playback capabilities.
"""

from __future__ import annotations

import itertools
from enum import Enum
from typing import Optional

from afik.plugins.manager import call_plugin


class PlayerState(str, Enum):
    STOPPED = "stopped"
    PLAYING = "playing"
    PAUSED = "paused"
    COMPLETED = "completed"


_player_id_counter = itertools.count()


class AudioPlayer:
    """Manages one audio playback session (audioplayers).

    ``url`` may be an http(s) URL, a local file path, or ``asset:<path>`` for a bundled asset.
    Every method reports what the platform answered; nothing is assumed to have worked.
    """

    def __init__(self, player_id: Optional[str] = None):
        self.player_id = player_id or f"player_{next(_player_id_counter)}"
        self._state: PlayerState = PlayerState.STOPPED

    def _call(self, method: str, extra: Optional[dict] = None, timeout: float = 3.0) -> dict:
        args = {"playerId": self.player_id}
        if extra:
            args.update(extra)
        res = call_plugin("audioplayers", method, args, timeout=timeout)
        return res if isinstance(res, dict) else {}

    def _track_state(self, res: dict) -> bool:
        try:
            self._state = PlayerState(res["state"])
            return True
        except (KeyError, ValueError):
            return False

    def play(self, url: str, volume: float = 1.0, position: float = 0.0) -> bool:
        """Plays audio; True once the platform confirms playback started."""
        res = self._call("play", {"url": str(url), "volume": str(volume), "position": str(position)}, timeout=30.0)
        return self._track_state(res) and self._state == PlayerState.PLAYING

    def pause(self) -> bool:
        """Pauses playback."""
        return self._track_state(self._call("pause")) and self._state == PlayerState.PAUSED

    def resume(self) -> bool:
        """Resumes paused playback."""
        return self._track_state(self._call("resume")) and self._state == PlayerState.PLAYING

    def stop(self) -> bool:
        """Stops playback and resets the position."""
        return self._track_state(self._call("stop")) and self._state == PlayerState.STOPPED

    def seek(self, position_seconds: float) -> bool:
        """Seeks to a timestamp in seconds."""
        return "position" in self._call("seek", {"position": str(position_seconds)})

    def set_volume(self, volume: float) -> bool:
        """Sets the volume between 0.0 (silent) and 1.0 (max)."""
        return "volume" in self._call("setVolume", {"volume": str(max(0.0, min(1.0, volume)))})

    def get_duration(self) -> Optional[float]:
        """Total duration in seconds, or None while the platform does not know it yet."""
        value = self._call("getDuration").get("duration")
        return float(value) if isinstance(value, (int, float)) else None

    def get_position(self) -> Optional[float]:
        """Playhead position in seconds, or None when unknown."""
        value = self._call("getPosition").get("position")
        return float(value) if isinstance(value, (int, float)) else None

    @property
    def state(self) -> PlayerState:
        """Current playback state as reported by the platform."""
        self._track_state(self._call("getState"))
        return self._state

    def dispose(self) -> bool:
        """Releases the native player."""
        return self._call("dispose").get("disposed") is True


__all__ = [
    "AudioPlayer",
    "PlayerState",
]
