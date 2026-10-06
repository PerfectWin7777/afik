"""
PyFlutter LocalAuth plugin (local_auth).
Provides biometric authentication (Fingerprint, TouchID, FaceID, Windows Hello).
"""

from __future__ import annotations

from pyflutter.plugins.manager import INTERACTIVE_TIMEOUT, call_plugin


class LocalAuthentication:
    """Manages biometric and device credential authentication."""

    def can_check_biometrics(self) -> bool:
        """Returns True if device hardware supports biometric scanning."""
        res = call_plugin("local_auth", "canCheckBiometrics", {})
        return isinstance(res, dict) and res.get("canCheck") is True

    def is_device_supported(self) -> bool:
        """Returns True if device supports biometric or PIN/passcode auth."""
        res = call_plugin("local_auth", "isDeviceSupported", {})
        return isinstance(res, dict) and res.get("supported") is True

    def get_available_biometrics(self) -> list[str]:
        """Returns list of enrolled biometric types (e.g. ['fingerprint', 'face'])."""
        res = call_plugin("local_auth", "getAvailableBiometrics", {})
        return [str(b) for b in res] if isinstance(res, list) else []

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
        }, timeout=INTERACTIVE_TIMEOUT)
        # Only an explicit `authenticated: true` from the platform counts as success.
        return isinstance(res, dict) and res.get("authenticated") is True

    def stop_authentication(self) -> bool:
        """Cancels an in-progress authentication prompt."""
        res = call_plugin("local_auth", "stopAuthentication", {})
        return isinstance(res, dict) and res.get("stopped") is True
