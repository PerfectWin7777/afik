"""
Afik Camera plugin.
Provides camera hardware discovery, capture control, and viewfinder integration.
"""

from __future__ import annotations

from typing import Any, Optional

from afik.plugins.image_picker import XFile
from afik.plugins.manager import call_plugin


class CameraDescription:
    """Description of a hardware camera device."""

    def __init__(self, camera_id: str, name: str, lens_facing: str = "back", sensor_orientation: int = 90):
        self.id = str(camera_id)
        self.name = str(name)
        self.lens_facing = str(lens_facing)
        self.sensor_orientation = int(sensor_orientation)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> CameraDescription:
        return cls(
            camera_id=str(data.get("id", "0")),
            name=str(data.get("name", "Camera")),
            lens_facing=str(data.get("lensFacing", "back")),
            sensor_orientation=int(data.get("sensorOrientation", 90)),
        )

    def __repr__(self) -> str:
        return f"<CameraDescription id={self.id!r} name={self.name!r} lens={self.lens_facing!r}>"


def available_cameras() -> list[CameraDescription]:
    """Returns a list of available cameras on the device."""
    res = call_plugin("camera", "availableCameras", {})
    if isinstance(res, list):
        return [CameraDescription.from_dict(item) for item in res if isinstance(item, dict)]
    return []


class CameraController:
    """Controls an active camera session."""

    def __init__(
        self,
        camera: CameraDescription | str,
        resolution: str = "high",
    ):
        self.camera_id = camera.id if isinstance(camera, CameraDescription) else str(camera)
        self.resolution = resolution
        self.is_initialized: bool = False
        self._is_recording: bool = False

    def initialize(self) -> bool:
        """Initializes the camera hardware for preview and capture."""
        res = call_plugin(
            "camera", "initialize", {"cameraId": self.camera_id, "resolution": self.resolution}
        )
        self.is_initialized = isinstance(res, dict) and res.get("initialized") is True
        return self.is_initialized

    def take_picture(self) -> Optional[XFile]:
        """Captures a still image from the camera."""
        res = call_plugin("camera", "takePicture", {"cameraId": self.camera_id})
        if isinstance(res, dict) and "path" in res:
            return XFile(res["path"], res.get("name"), int(res.get("size", 0)))
        return None

    def start_video_recording(self) -> bool:
        """Starts recording video."""
        res = call_plugin("camera", "startVideoRecording", {"cameraId": self.camera_id})
        self._is_recording = isinstance(res, dict) and res.get("recording") is True
        return self._is_recording

    def stop_video_recording(self) -> Optional[XFile]:
        """Stops recording video and returns the captured video file."""
        res = call_plugin("camera", "stopVideoRecording", {"cameraId": self.camera_id})
        self._is_recording = False
        if isinstance(res, dict) and "path" in res:
            return XFile(res["path"], res.get("name"), int(res.get("size", 0)))
        return None

    def is_recording(self) -> bool:
        """Checks if video is actively recording."""
        res = call_plugin("camera", "isRecording", {"cameraId": self.camera_id})
        return isinstance(res, dict) and res.get("isRecording") is True

    def set_flash_mode(self, mode: str) -> bool:
        """Sets flash mode ('off', 'auto', 'always', 'torch'). True if the platform applied it."""
        res = call_plugin("camera", "setFlashMode", {"cameraId": self.camera_id, "mode": mode})
        return isinstance(res, dict) and res.get("flashMode") == mode

    def set_zoom_level(self, zoom: float) -> Optional[float]:
        """Sets the zoom; returns the zoom actually applied (clamped to the camera's range)."""
        res = call_plugin("camera", "setZoomLevel", {"cameraId": self.camera_id, "zoom": str(zoom)})
        value = res.get("zoom") if isinstance(res, dict) else None
        return float(value) if isinstance(value, (int, float)) else None

    def dispose(self) -> bool:
        """Releases the camera device."""
        res = call_plugin("camera", "dispose", {"cameraId": self.camera_id})
        self.is_initialized = False
        return isinstance(res, dict) and res.get("disposed") is True


from afik.widgets.widgets import CameraPreview  # noqa: E402  (re-export; widgets import this module)

__all__ = [
    "CameraDescription",
    "available_cameras",
    "CameraController",
    "CameraPreview",
    "XFile",
]

