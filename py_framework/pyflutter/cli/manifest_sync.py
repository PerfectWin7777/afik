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


def sync_android_manifest(manifest_path: Path, permissions: Sequence[str], app_title: str | None = None) -> bool:
    """
    Injects required uses-permission tags into AndroidManifest.xml idempotently.
    """
    if not manifest_path.exists():
        return False

    content = manifest_path.read_text(encoding="utf-8")
    modified = False

    # 1. Update app label if title provided
    if app_title:
        label_pattern = r'android:label="[^"]*"'
        new_label = f'android:label="{app_title}"'
        if re.search(label_pattern, content):
            new_content = re.sub(label_pattern, new_label, content, count=1)
            if new_content != content:
                content = new_content
                modified = True

    # 2. Gather Android permissions
    android_perms: list[str] = []
    for p in permissions:
        key = p.lower().strip()
        if key in PERMISSION_MAP_ANDROID:
            android_perms.extend(PERMISSION_MAP_ANDROID[key])
        elif key.startswith("android.permission."):
            android_perms.append(key)

    # 3. Inject missing permissions
    for perm in android_perms:
        perm_tag = f'<uses-permission android:name="{perm}"/>'
        if perm not in content:
            # Insert right after <manifest ...>
            manifest_tag_match = re.search(r"<manifest[^>]*>", content)
            if manifest_tag_match:
                insert_pos = manifest_tag_match.end()
                content = content[:insert_pos] + f"\n    {perm_tag}" + content[insert_pos:]
                modified = True

    # 4. Inject queries intents (e.g. speech recognition)
    for p in permissions:
        key = p.lower().strip()
        if key in QUERIES_MAP_ANDROID:
            intent_snippet = QUERIES_MAP_ANDROID[key]
            if "android.speech.RecognitionService" not in content and "<queries>" in content:
                queries_match = re.search(r"<queries>", content)
                if queries_match:
                    insert_pos = queries_match.end()
                    content = content[:insert_pos] + f"\n        {intent_snippet}" + content[insert_pos:]
                    modified = True

    if modified:
        manifest_path.write_text(content, encoding="utf-8")
        logger.debug(f"[sync] Updated {manifest_path.name} with permissions: {android_perms}")

    return modified


def sync_ios_plist(plist_path: Path, permissions: Sequence[str], app_title: str | None = None) -> bool:
    """
    Injects required permission descriptions into iOS Info.plist idempotently.
    """
    if not plist_path.exists():
        return False

    content = plist_path.read_text(encoding="utf-8")
    modified = False

    # 1. Update display name if provided
    if app_title:
        if "<key>CFBundleDisplayName</key>" in content:
            pattern = r"(<key>CFBundleDisplayName</key>\s*<string>)[^<]*(</string>)"
            new_content = re.sub(pattern, rf"\g<1>{app_title}\g<2>", content)
            if new_content != content:
                content = new_content
                modified = True

    # 2. Gather iOS permissions
    for p in permissions:
        key = p.lower().strip()
        if key in PERMISSION_MAP_IOS:
            plist_key, default_desc = PERMISSION_MAP_IOS[key]
            if f"<key>{plist_key}</key>" not in content:
                snippet = f"\t<key>{plist_key}</key>\n\t<string>{default_desc}</string>\n"
                # Insert inside the root <dict>
                dict_match = re.search(r"<dict>", content)
                if dict_match:
                    insert_pos = dict_match.end()
                    content = content[:insert_pos] + "\n" + snippet + content[insert_pos:]
                    modified = True

    if modified:
        plist_path.write_text(content, encoding="utf-8")
        logger.debug(f"[sync] Updated {plist_path.name}")

    return modified


def sync_platform_metadata(workspace_root: Path, config: PyFlutterConfig) -> None:
    """
    Main entry point: syncs pyflutter.yaml permissions and branding to Android and iOS.
    """
    dart_runtime_dir = workspace_root / "dart_runtime"
    if not dart_runtime_dir.exists():
        return

    app_title = config.name.replace("_", " ").title() if config.name else None
    perms = config.permissions

    # Android
    android_manifest = dart_runtime_dir / "android" / "app" / "src" / "main" / "AndroidManifest.xml"
    if android_manifest.exists():
        if sync_android_manifest(android_manifest, perms, app_title):
            logger.info(f"Auto-synced native permissions to Android manifest ({len(perms)} permission(s))")

    # iOS
    ios_plist = dart_runtime_dir / "ios" / "Runner" / "Info.plist"
    if ios_plist.exists():
        if sync_ios_plist(ios_plist, perms, app_title):
            logger.info(f"Auto-synced native permissions to iOS Info.plist")
