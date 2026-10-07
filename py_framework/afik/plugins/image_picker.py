"""
Afik ImagePicker plugin.
Provides image and video selection from device gallery or camera.
"""

from __future__ import annotations

import os
from enum import Enum
from pathlib import Path
from typing import Any, Optional

from afik.plugins.manager import call_plugin


class ImageSource(str, Enum):
    GALLERY = "gallery"
    CAMERA = "camera"


class XFile:
    """Represents a cross-platform file picked from gallery or camera."""

    def __init__(self, path: str, name: Optional[str] = None, size: int = 0):
        self.path = str(path)
        self.name = name or Path(path).name
        self.size = size or (os.path.getsize(path) if os.path.exists(path) else 0)

    def read_bytes(self) -> bytes:
        with open(self.path, "rb") as f:
            return f.read()

    def read_text(self, encoding: str = "utf-8") -> str:
        with open(self.path, "r", encoding=encoding, errors="replace") as f:
            return f.read()

    def __repr__(self) -> str:
        return f"<XFile path={self.path!r} name={self.name!r} size={self.size}>"

    def __str__(self) -> str:
        return self.path


class ImagePicker:
    """ImagePicker client for picking media."""

    def pick_image(
        self,
        source: ImageSource | str = ImageSource.GALLERY,
        *,
        max_width: Optional[float] = None,
        max_height: Optional[float] = None,
        image_quality: Optional[int] = None,
    ) -> Optional[XFile]:
        """Prompts the user to pick an image from gallery or take a picture with camera."""
        source_val = source.value if isinstance(source, ImageSource) else str(source)
        args: dict[str, Any] = {"source": source_val}
        if max_width is not None:
            args["maxWidth"] = str(max_width)
        if max_height is not None:
            args["maxHeight"] = str(max_height)
        if image_quality is not None:
            args["imageQuality"] = str(image_quality)

        res = call_plugin("image_picker", "pickImage", args)
        if isinstance(res, dict) and "path" in res:
            return XFile(res["path"], res.get("name"), int(res.get("size", 0)))
        return None

    def pick_video(
        self,
        source: ImageSource | str = ImageSource.GALLERY,
    ) -> Optional[XFile]:
        """Prompts the user to pick a video from gallery or record with camera."""
        source_val = source.value if isinstance(source, ImageSource) else str(source)
        res = call_plugin("image_picker", "pickVideo", {"source": source_val})
        if isinstance(res, dict) and "path" in res:
            return XFile(res["path"], res.get("name"), int(res.get("size", 0)))
        return None

    def pick_multi_image(self) -> list[XFile]:
        """Prompts the user to pick multiple images."""
        res = call_plugin("image_picker", "pickMultiImage", {})
        if isinstance(res, list):
            items = []
            for item in res:
                if isinstance(item, dict) and "path" in item:
                    items.append(XFile(item["path"], item.get("name"), int(item.get("size", 0))))
            return items
        return []


# Module-level convenience functions
_default_picker = ImagePicker()
pick_image = _default_picker.pick_image
pick_video = _default_picker.pick_video
pick_multi_image = _default_picker.pick_multi_image
