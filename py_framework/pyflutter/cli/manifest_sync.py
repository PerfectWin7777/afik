"""
PyFlutter Zero-Code Platform Manifest Synchronizer.
Automatically synchronizes declarative permissions and app metadata from
pyflutter.yaml into AndroidManifest.xml and iOS Info.plist.
Developers never have to touch native XML or Plist files manually.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Sequence
from xml.sax.saxutils import escape, quoteattr

from pyflutter.core.config import PyFlutterConfig
from pyflutter.core.logger import logger

PERMISSION_MAP_ANDROID: dict[str, list[str]] = {
    # Core & Connectivity
    "internet": ["android.permission.INTERNET"],
    "network_state": ["android.permission.ACCESS_NETWORK_STATE"],
    "wifi_state": [
        "android.permission.ACCESS_WIFI_STATE",
        "android.permission.CHANGE_WIFI_STATE",
    ],

    # Camera & Media
    "camera": ["android.permission.CAMERA"],
    "record_audio": ["android.permission.RECORD_AUDIO"],
    "microphone": [
        "android.permission.RECORD_AUDIO",
        "android.permission.MODIFY_AUDIO_SETTINGS",
    ],
    "storage": [
        "android.permission.READ_EXTERNAL_STORAGE",
        "android.permission.WRITE_EXTERNAL_STORAGE",
        "android.permission.READ_MEDIA_IMAGES",
        "android.permission.READ_MEDIA_VIDEO",
        "android.permission.READ_MEDIA_AUDIO",
    ],
    "photo_library": [
        "android.permission.READ_MEDIA_IMAGES",
        "android.permission.READ_MEDIA_VIDEO",
        "android.permission.READ_EXTERNAL_STORAGE",
    ],

    # Voice & Speech Recognition
    "speech_recognition": [
        "android.permission.RECORD_AUDIO",
        "android.permission.INTERNET",
    ],
    "speech": [
        "android.permission.RECORD_AUDIO",
        "android.permission.INTERNET",
    ],

    # Geolocation
    "location": [
        "android.permission.ACCESS_FINE_LOCATION",
        "android.permission.ACCESS_COARSE_LOCATION",
    ],
    "location_when_in_use": [
        "android.permission.ACCESS_FINE_LOCATION",
        "android.permission.ACCESS_COARSE_LOCATION",
    ],
    "location_always": [
        "android.permission.ACCESS_FINE_LOCATION",
        "android.permission.ACCESS_COARSE_LOCATION",
        "android.permission.ACCESS_BACKGROUND_LOCATION",
    ],

    # Notifications & Hardware
    "notifications": ["android.permission.POST_NOTIFICATIONS"],
    "notification": ["android.permission.POST_NOTIFICATIONS"],
    "vibrate": ["android.permission.VIBRATE"],
    "wake_lock": ["android.permission.WAKE_LOCK"],

    # Bluetooth & NFC
    "bluetooth": [
        "android.permission.BLUETOOTH",
        "android.permission.BLUETOOTH_ADMIN",
        "android.permission.BLUETOOTH_CONNECT",
        "android.permission.BLUETOOTH_SCAN",
        "android.permission.BLUETOOTH_ADVERTISE",
    ],
    "nfc": ["android.permission.NFC"],

    # Contacts, Phone & Calendar
    "contacts": [
        "android.permission.READ_CONTACTS",
        "android.permission.WRITE_CONTACTS",
    ],
    "phone": [
        "android.permission.CALL_PHONE",
        "android.permission.READ_PHONE_STATE",
    ],
    "sms": [
        "android.permission.SEND_SMS",
        "android.permission.RECEIVE_SMS",
        "android.permission.READ_SMS",
    ],
    "calendar": [
        "android.permission.READ_CALENDAR",
        "android.permission.WRITE_CALENDAR",
    ],
    "calendars": [
        "android.permission.READ_CALENDAR",
        "android.permission.WRITE_CALENDAR",
    ],

    # Security & Sensors
    "biometrics": [
        "android.permission.USE_BIOMETRIC",
        "android.permission.USE_FINGERPRINT",
    ],
    "fingerprint": [
        "android.permission.USE_BIOMETRIC",
        "android.permission.USE_FINGERPRINT",
    ],
    "sensors": [
        "android.permission.ACTIVITY_RECOGNITION",
        "android.permission.BODY_SENSORS",
    ],
}

PERMISSION_MAP_IOS: dict[str, tuple[str, str]] = {
    # Camera & Media
    "camera": ("NSCameraUsageDescription", "This app requires camera access."),
    "record_audio": ("NSMicrophoneUsageDescription", "This app requires microphone access."),
    "microphone": ("NSMicrophoneUsageDescription", "This app requires microphone access."),
    "photo_library": ("NSPhotoLibraryUsageDescription", "This app requires photo library access."),
    "storage": ("NSPhotoLibraryUsageDescription", "This app requires access to your photo library and files."),
    "media_library": ("NSAppleMusicUsageDescription", "This app requires access to your media library."),

    # Speech Recognition
    "speech_recognition": ("NSSpeechRecognitionUsageDescription", "This app requires speech recognition to transcribe your voice."),
    "speech": ("NSSpeechRecognitionUsageDescription", "This app requires speech recognition to transcribe your voice."),

    # Geolocation
    "location": ("NSLocationWhenInUseUsageDescription", "This app requires location access."),
    "location_when_in_use": ("NSLocationWhenInUseUsageDescription", "This app requires location access while in use."),
    "location_always": ("NSLocationAlwaysAndWhenInUseUsageDescription", "This app requires background location access."),

    # Bluetooth & NFC
    "bluetooth": ("NSBluetoothAlwaysUsageDescription", "This app requires Bluetooth access."),
    "nfc": ("NFCReaderUsageDescription", "This app requires NFC tag reading."),

    # Contacts, Calendar & Reminders
    "contacts": ("NSContactsUsageDescription", "This app requires contacts access."),
    "calendar": ("NSCalendarsUsageDescription", "This app requires calendar access."),
    "calendars": ("NSCalendarsUsageDescription", "This app requires calendar access."),
    "reminders": ("NSRemindersUsageDescription", "This app requires reminders access."),

    # Security & Sensors
    "biometrics": ("NSFaceIDUsageDescription", "This app requires Face ID authentication for secure access."),
    "face_id": ("NSFaceIDUsageDescription", "This app requires Face ID authentication for secure access."),
    "sensors": ("NSMotionUsageDescription", "This app requires motion sensor access."),
    "tracking": ("NSUserTrackingUsageDescription", "This identifier will be used to deliver personalized services."),
}

# Android <queries> intent declarations needed for services like speech recognition
QUERIES_MAP_ANDROID: dict[str, str] = {
    "speech_recognition": '<intent><action android:name="android.speech.RecognitionService"/></intent>',
    "speech": '<intent><action android:name="android.speech.RecognitionService"/></intent>',
}


ANDROID_BEGIN = "<!-- pyflutter:permissions:begin (generated, do not edit) -->"
ANDROID_END = "<!-- pyflutter:permissions:end -->"
QUERIES_BEGIN = "<!-- pyflutter:queries:begin (generated, do not edit) -->"
QUERIES_END = "<!-- pyflutter:queries:end -->"
PLIST_BEGIN = "<!-- pyflutter:permissions:begin (generated, do not edit) -->"
PLIST_END = "<!-- pyflutter:permissions:end -->"


def _strip_block(text: str, begin: str, end: str) -> str:
    """Removes a managed block (and the line break before it) from ``text``."""
    pattern = r"[ \t]*" + re.escape(begin) + r".*?" + re.escape(end) + r"[ \t]*\n?"
    return re.sub(pattern, "", text, flags=re.S)


def android_permission_names(permissions: Sequence[str]) -> list[str]:
    """Android permission names for the permission keys of pyflutter.yaml / plugins."""
    names: list[str] = []
    for p in permissions:
        key = p.lower().strip()
        if key in PERMISSION_MAP_ANDROID:
            found = PERMISSION_MAP_ANDROID[key]
        elif key.startswith("android.permission."):
            found = [p.strip()]
        elif key in PERMISSION_MAP_IOS:
            found = []  # iOS-only key
        else:
            logger.warning("Unknown permission '{}' in pyflutter.yaml (ignored).", p)
            found = []
        for name in found:
            if name not in names:
                names.append(name)
    return names


def sync_android_manifest(
    manifest_path: Path,
    permissions: Sequence[str],
    app_title: str | None = None,
    extra_queries: Sequence[str] = (),
) -> bool:
    """
    Writes the permissions (and <queries> entries) the project needs into AndroidManifest.xml.

    They live in generated blocks that are rewritten on every sync, so a permission removed
    from pyflutter.yaml (or a plugin that is uninstalled) disappears from the manifest.
    Permissions the manifest declares outside the blocks are left alone and not duplicated.
    """
    if not manifest_path.exists():
        return False

    original = manifest_path.read_text(encoding="utf-8")
    content = _strip_block(_strip_block(original, ANDROID_BEGIN, ANDROID_END), QUERIES_BEGIN, QUERIES_END)

    # 1. app label
    if app_title:
        content = re.sub(r'android:label="[^"]*"', lambda _m: f"android:label={quoteattr(app_title)}", content, count=1)

    # 2. permissions block, right after <manifest ...>
    wanted = [n for n in android_permission_names(permissions) if f'android:name="{n}"' not in content]
    if wanted:
        tag = re.search(r"<manifest[^>]*>", content)
        if tag:
            lines = [f"    {ANDROID_BEGIN}"] + [f'    <uses-permission android:name="{n}"/>' for n in wanted] + [f"    {ANDROID_END}"]
            content = content[: tag.end()] + "\n" + "\n".join(lines) + content[tag.end():]

    # 3. queries block, right after <queries>
    snippets = list(extra_queries)
    for p in permissions:
        snippet = QUERIES_MAP_ANDROID.get(p.lower().strip())
        if snippet and snippet not in snippets:
            snippets.append(snippet)
    if snippets:
        opened = re.search(r"<queries>", content)
        if opened:
            lines = [f"        {QUERIES_BEGIN}"] + [f"        {sn}" for sn in snippets] + [f"        {QUERIES_END}"]
            content = content[: opened.end()] + "\n" + "\n".join(lines) + content[opened.end():]
        else:
            logger.warning("AndroidManifest.xml has no <queries> section: package visibility entries were not written.")

    if content == original:
        return False
    manifest_path.write_text(content, encoding="utf-8")
    logger.debug("[sync] Updated {}: {}", manifest_path.name, wanted)
    return True


def sync_ios_plist(plist_path: Path, permissions: Sequence[str], app_title: str | None = None) -> bool:
    """Writes the usage descriptions the project needs into Info.plist (generated block)."""
    if not plist_path.exists():
        return False

    original = plist_path.read_text(encoding="utf-8")
    content = _strip_block(original, PLIST_BEGIN, PLIST_END)

    if app_title and "<key>CFBundleDisplayName</key>" in content:
        safe_title = escape(app_title)
        content = re.sub(
            r"(<key>CFBundleDisplayName</key>\s*<string>)[^<]*(</string>)",
            lambda m: f"{m.group(1)}{safe_title}{m.group(2)}",
            content,
        )

    entries: list[tuple[str, str]] = []
    for p in permissions:
        item = PERMISSION_MAP_IOS.get(p.lower().strip())
        if item and item not in entries and f"<key>{item[0]}</key>" not in content:
            entries.append(item)
    if entries:
        root = re.search(r"<dict>", content)
        if root:
            lines = [f"\t{PLIST_BEGIN}"]
            for key, description in entries:
                lines += [f"\t<key>{key}</key>", f"\t<string>{escape(description)}</string>"]
            lines.append(f"\t{PLIST_END}")
            content = content[: root.end()] + "\n" + "\n".join(lines) + content[root.end():]

    if content == original:
        return False
    plist_path.write_text(content, encoding="utf-8")
    logger.debug("[sync] Updated {}", plist_path.name)
    return True


def sync_platform_metadata(
    runtime_dir: Path,
    config: PyFlutterConfig,
    extra_permissions: Sequence[str] = (),
    extra_queries: Sequence[str] = (),
) -> None:
    """Syncs pyflutter.yaml permissions and branding into the Android / iOS files of a runtime copy."""
    runtime_dir = Path(runtime_dir)
    if not runtime_dir.is_dir():
        return

    app_title = config.name.replace("_", " ").title() if config.name else None
    perms = list(dict.fromkeys([*config.permissions, *extra_permissions]))

    android_manifest = runtime_dir / "android" / "app" / "src" / "main" / "AndroidManifest.xml"
    if sync_android_manifest(android_manifest, perms, app_title, extra_queries):
        logger.info("Synced native permissions to the Android manifest ({} permission key(s))", len(perms))

    ios_plist = runtime_dir / "ios" / "Runner" / "Info.plist"
    if sync_ios_plist(ios_plist, perms, app_title):
        logger.info("Synced native permissions to iOS Info.plist")
