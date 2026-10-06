"""
Device discovery and selection for PyFlutter CLI.
Uses Flutter's native device engine (flutter devices --machine).
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any, Optional


def list_devices() -> list[dict[str, Any]]:
    """Discovers available devices by querying `flutter devices --machine`."""
    try:
        raw = subprocess.check_output(
            ["flutter", "devices", "--machine"],
            stderr=subprocess.DEVNULL,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=45,
            shell=(sys.platform == "win32"),
        )
        # Find JSON array in stdout
        start = raw.find("[")
        end = raw.rfind("]")
        if start != -1 and end != -1:
            raw = raw[start : end + 1]
        data = json.loads(raw)
        return [d for d in data if d.get("isSupported", True)]
    except Exception:
        return []


def setup_adb_port_forward(device_id: str, port: int = 7879) -> bool:
    """Configures adb reverse port forwarding for Android devices."""
    try:
        subprocess.run(
            ["adb", "-s", device_id, "reverse", f"tcp:{port}", f"tcp:{port}"],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="replace",
            shell=(sys.platform == "win32"),
        )
        return True
    except Exception:
        return False


CONFIG_DIR = Path.home() / ".pyflutter"
CONFIG_FILE = CONFIG_DIR / "config.json"


def get_last_device_id() -> Optional[str]:
    """Retrieves the last selected device ID from user config."""
    try:
        if CONFIG_FILE.exists():
            data = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
            return data.get("last_device_id")
    except Exception:
        pass
    return None


def save_last_device_id(device_id: str) -> None:
    """Saves the last selected device ID to user config."""
    try:
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        data = {}
        if CONFIG_FILE.exists():
            try:
                data = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
            except Exception:
                pass
        data["last_device_id"] = device_id
        CONFIG_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")
    except Exception:
        pass


def select_device(preferred_id: Optional[str] = None) -> Optional[dict[str, Any]]:
    """
    Selects a target device:
    - If preferred_id is provided, immediately targets that device (fast path).
    - If only 1 device is found, selects it automatically.
    - If multiple devices are found, prioritizes the last-used device as [1] default.
    """
    if preferred_id:
        # Prefer what Flutter reports; only guess when it cannot be queried.
        known = next(
            (d for d in list_devices() if preferred_id in (d.get("id"), d.get("name"))),
            None,
        )
        if known is not None:
            selected = known
        else:
            lowered = preferred_id.lower()
            guessed = (
                "android-arm64"
                if lowered.startswith("emulator-") or "android" in lowered
                else lowered
            )
            selected = {"name": preferred_id, "id": preferred_id, "targetPlatform": guessed}
        if "android" in selected.get("targetPlatform", "").lower():
            setup_adb_port_forward(selected.get("id", preferred_id))
        save_last_device_id(selected.get("id", preferred_id))
        return selected

    devices = list_devices()
    if not devices:
        return None

    # Check if there is a previously used device
    last_id = get_last_device_id()
    if last_id:
        # Move last used device to the first position
        match_idx = next((i for i, d in enumerate(devices) if d.get("id") == last_id), None)
        if match_idx is not None and match_idx > 0:
            devices.insert(0, devices.pop(match_idx))

    selected = None
    if len(devices) == 1:
        selected = devices[0]
    else:
        # Multiple devices: prompt user
        print("\nAvailable devices:")
        for idx, d in enumerate(devices, start=1):
            target = d.get("targetPlatform", "")
            name = d.get("name", "Unknown")
            dev_id = d.get("id", "")
            sdk = d.get("sdk", "")
            tag = " [Last used]" if last_id and dev_id == last_id else ""
            print(f"  [{idx}]: {name} ({dev_id}){tag} | {target} | {sdk}")

        default_name = devices[0].get("name", "1")
        while True:
            try:
                prompt = f"\nPlease choose a device (1-{len(devices)}) [default: 1 ({default_name})]: "
                choice = input(prompt).strip()
                if not choice:
                    selected = devices[0]
                    break
                choice_num = int(choice)
                if 1 <= choice_num <= len(devices):
                    selected = devices[choice_num - 1]
                    break
            except ValueError:
                pass
            except (EOFError, KeyboardInterrupt):
                print("\nAborted: no device chosen. Pass one with `-d <device>`.")
                sys.exit(1)
            print(f"Invalid choice. Please enter a number between 1 and {len(devices)}.")

    if selected:
        platform = selected.get("targetPlatform", "").lower()
        dev_id = selected.get("id", "")
        if "android" in platform and dev_id:
            setup_adb_port_forward(dev_id)
        if dev_id:
            save_last_device_id(dev_id)

    return selected
