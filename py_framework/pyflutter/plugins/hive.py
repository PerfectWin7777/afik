"""
PyFlutter Hive-style key-value boxes, implemented in Python.

This is not a binding to the Dart `hive` package: the app's Python code already runs in the
same process as its files, so persistence is done here and no extra Flutter package is
needed. The API follows Hive's (`open_box`, `put`, `get`, `delete`, `clear`, ...); each box
is one JSON file, written atomically, so values must be JSON-serialisable (str, int, float,
bool, None, list, dict).

Storage location: ``$PYFLUTTER_DATA_DIR/hive``, else the app support directory reported by
the path_provider plugin, else ``~/.pyflutter/hive``. Call :func:`init` to choose another.
"""

from __future__ import annotations

import json
import os
import tempfile
import threading
from pathlib import Path
from typing import Any, Iterator, Optional

_directory: Optional[Path] = None
_lock = threading.RLock()


def init(path: str | os.PathLike[str]) -> None:
    """Sets the directory that holds the box files (created if missing)."""
    global _directory
    _directory = Path(path)
    _directory.mkdir(parents=True, exist_ok=True)


def _storage_dir() -> Path:
    if _directory is not None:
        return _directory
    env = os.environ.get("PYFLUTTER_DATA_DIR")
    if env:
        base = Path(env) / "hive"
    else:
        base = None
        try:
            from pyflutter.plugins import path_provider

            support = path_provider.get_app_support_directory()
            if support:
                base = Path(support) / "hive"
        except Exception:
            base = None
        if base is None:
            base = Path.home() / ".pyflutter" / "hive"
    base.mkdir(parents=True, exist_ok=True)
    return base


class Box:
    """A named, persistent key-value store."""

    def __init__(self, name: str, directory: Path):
        self.name = str(name)
        self._file = directory / f"{self.name}.json"
        self.is_open: bool = True
        self._data: dict[str, Any] = {}
        if self._file.exists():
            try:
                loaded = json.loads(self._file.read_text(encoding="utf-8"))
            except (OSError, ValueError) as e:
                raise ValueError(f"Hive box '{self.name}' is corrupted ({self._file}): {e}") from e
            if isinstance(loaded, dict):
                self._data = loaded

    # -- persistence
    def _save(self) -> None:
        text = json.dumps(self._data, ensure_ascii=False)
        fd, tmp = tempfile.mkstemp(dir=self._file.parent, prefix=self.name + ".", suffix=".tmp")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                f.write(text)
            os.replace(tmp, self._file)
        except BaseException:
            if os.path.exists(tmp):
                os.unlink(tmp)
            raise

    def _check_open(self) -> None:
        if not self.is_open:
            raise ValueError(f"Hive box '{self.name}' is closed.")

    # -- Hive API
    def put(self, key: str, value: Any) -> bool:
        """Stores a value. Raises TypeError if it is not JSON-serialisable."""
        self.put_all({key: value})
        return True

    def put_all(self, entries: dict[str, Any]) -> None:
        with _lock:
            self._check_open()
            json.dumps(entries)  # fail before touching the box
            self._data.update({str(k): v for k, v in entries.items()})
            self._save()

    def get(self, key: str, default: Any = None) -> Any:
        with _lock:
            self._check_open()
            return self._data.get(str(key), default)

    def delete(self, key: str) -> bool:
        """Deletes a key. Returns False if it was not in the box."""
        with _lock:
            self._check_open()
            if str(key) not in self._data:
                return False
            del self._data[str(key)]
            self._save()
            return True

    def clear(self) -> bool:
        with _lock:
            self._check_open()
            self._data.clear()
            self._save()
            return True

    def contains_key(self, key: str) -> bool:
        with _lock:
            self._check_open()
            return str(key) in self._data

    def get_all(self) -> dict[str, Any]:
        with _lock:
            self._check_open()
            return dict(self._data)

    def keys(self) -> list[str]:
        return list(self.get_all().keys())

    def values(self) -> list[Any]:
        return list(self.get_all().values())

    def items(self) -> list[tuple[str, Any]]:
        return list(self.get_all().items())

    @property
    def length(self) -> int:
        return len(self.get_all())

    def close(self) -> bool:
        with _lock:
            self.is_open = False
            _opened_boxes.pop(self.name, None)
        return True

    # -- dict style
    def __getitem__(self, key: str) -> Any:
        data = self.get_all()
        if str(key) not in data:
            raise KeyError(key)
        return data[str(key)]

    def __setitem__(self, key: str, value: Any) -> None:
        self.put(key, value)

    def __delitem__(self, key: str) -> None:
        if not self.delete(key):
            raise KeyError(key)

    def __contains__(self, key: object) -> bool:
        return self.contains_key(str(key))

    def __len__(self) -> int:
        return self.length

    def __iter__(self) -> Iterator[str]:
        return iter(self.keys())


_opened_boxes: dict[str, Box] = {}


def open_box(name: str) -> Box:
    """Opens (or returns the already opened) box ``name``."""
    with _lock:
        existing = _opened_boxes.get(name)
        if existing is not None and existing.is_open:
            return existing
        box_ = Box(name, _storage_dir())
        _opened_boxes[name] = box_
        return box_


def box(name: str) -> Box:
    """Returns an already opened box, opening it if needed."""
    return open_box(name)


def delete_box_from_disk(name: str) -> bool:
    """Closes the box and deletes its file. Returns False if there was no such box."""
    with _lock:
        existing = _opened_boxes.pop(name, None)
        if existing is not None:
            existing.is_open = False
        file = _storage_dir() / f"{name}.json"
        if file.exists():
            file.unlink()
            return True
        return False


__all__ = ["Box", "init", "open_box", "box", "delete_box_from_disk"]
