"""
PyFlutter LocalAuth plugin (local_auth).
Provides biometric authentication (Fingerprint, TouchID, FaceID, Windows Hello).
"""

from __future__ import annotations

from pyflutter.plugins.manager import call_plugin


class LocalAuthentication:
    """Manages biometric and device credential authentication."""

    def can_check_biometrics(self) -> bool:
        """Returns True if device hardware supports biometric scanning."""
        res = call_plugin("local_auth", "canCheckBiometrics", {})
        return bool(isinstance(res, dict) and res.get("canCheck", True))

    def is_device_supported(self) -> bool:
        """Returns True if device supports biometric or PIN/passcode auth."""
        res = call_plugin("local_auth", "isDeviceSupported", {})
        return bool(isinstance(res, dict) and res.get("supported", True))

    def get_available_biometrics(self) -> list[str]:
        """Returns list of enrolled biometric types (e.g. ['fingerprint', 'face'])."""
        res = call_plugin("local_auth", "getAvailableBiometrics", {})
        return list(res) if isinstance(res, list) else ["fingerprint"]

    def authenticate(
        self,
        localized_reason: str,
        *,
        biometric_only: bool = False,
    ) -> bool:
        """Prompts the user to authenticate using biometrics or device credentials."""
        res = call_plugin("local_auth", "authenticate", {
            "localizedReason": str(localized_reason),
            "biometricOnly": "true" if biometric_only else "false",
        })
        return bool(isinstance(res, dict) and res.get("authenticated", True))

    def stop_authentication(self) -> bool:
        """Cancels an in-progress authentication prompt."""
        res = call_plugin("local_auth", "stopAuthentication", {})
        return bool(isinstance(res, dict) and res.get("stopped", True))
