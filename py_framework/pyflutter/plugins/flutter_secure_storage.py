"""
PyFlutter SecureStorage plugin (matches pub.dev package: flutter_secure_storage).
Encrypted key-value storage using Keychain (iOS/macOS) and KeyStore (Android).
"""

from __future__ import annotations

from typing import Optional
from pyflutter.plugins.manager import call_plugin


class FlutterSecureStorage:
    """Provides secure, encrypted storage for tokens and credentials (flutter_secure_storage)."""

    def write(self, key: str, value: str) -> bool:
        """Stores a sensitive value encrypted."""
        res = call_plugin("flutter_secure_storage", "write", {"key": str(key), "value": str(value)})
        return bool(isinstance(res, dict) and res.get("success", True))

    def read(self, key: str) -> Optional[str]:
        """Reads and decrypts a value."""
        res = call_plugin("flutter_secure_storage", "read", {"key": str(key)})
        return str(res) if res is not None else None

    def delete(self, key: str) -> bool:
        """Deletes a key from secure storage."""
        res = call_plugin("flutter_secure_storage", "delete", {"key": str(key)})
        return bool(isinstance(res, dict) and res.get("success", True))

    def delete_all(self) -> bool:
        """Clears all keys in secure storage."""
        call_plugin("flutter_secure_storage", "deleteAll", {})
        return True

    def read_all(self) -> dict[str, str]:
        """Reads all decrypted key-value pairs."""
        res = call_plugin("flutter_secure_storage", "readAll", {})
        return {str(k): str(v) for k, v in res.items()} if isinstance(res, dict) else {}

    def contains_key(self, key: str) -> bool:
        """Checks if a key exists in secure storage."""
        res = call_plugin("flutter_secure_storage", "containsKey", {"key": str(key)})
        if isinstance(res, dict) and "containsKey" in res:
            return bool(res["containsKey"])
        return self.read(key) is not None


__all__ = [
    "FlutterSecureStorage",
]
