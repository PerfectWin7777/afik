"""
PyFlutter Native Plugin Manager.
Dispatches RPC method calls from Python to the Rust bridge and Dart runtime.
Provides package installation tools for adding Flutter native packages.
"""

from __future__ import annotations

import json
import shutil
import struct
import subprocess
import sys
from pathlib import Path
from typing import Any

from pyflutter.app import get_active_runner
from pyflutter.core.logger import logger

MSG_PLUGIN_CALL = 0x03


def invoke_plugin_method(plugin_name: str, method: str, args: dict[str, Any]) -> None:
    """
    Invokes a method on a native Flutter plugin shim.
    Serializes arguments and routes them through the active Rust bridge session.
    """
    runner = get_active_runner()
    if runner and runner.session and runner.session.process:
        try:
            payload = f"{plugin_name}\x00{method}\x00{json.dumps(args)}".encode("utf-8")
            header = struct.pack(">BI", MSG_PLUGIN_CALL, len(payload))
            runner.session.process.stdin.write(header + payload)
            runner.session.process.stdin.flush()
            logger.debug(f"[plugin call] {plugin_name}.{method}({args}) dispatched.")
        except Exception as e:
            logger.error(f"[plugin error] Failed to dispatch {plugin_name}.{method}: {e}")
    else:
        logger.warning(f"[plugin warning] No active bridge session to dispatch {plugin_name}.{method}")


def add_flutter_package(package_name: str) -> bool:
    """
    Installs a Flutter package into the PyFlutter runtime using `flutter pub add`.
    """
    # Locate dart_runtime directory
    current = Path(__file__).resolve()
    # Path is: py_framework/pyflutter/plugins/manager.py -> repo root is 3 levels up
    repo_root = current.parents[3]
    dart_runtime_dir = repo_root / "dart_runtime"

    if not dart_runtime_dir.exists():
        logger.error(f"Cannot find dart_runtime at: {dart_runtime_dir}")
        return False

    flutter_bin = shutil.which("flutter") or shutil.which("flutter.bat")
    if not flutter_bin:
        logger.error("Flutter binary not found in PATH.")
        return False

    logger.info(f"📦 Installing native Flutter package '{package_name}' into {dart_runtime_dir.name}...")
    try:
        proc = subprocess.run(
            ["flutter", "pub", "add", package_name],
            cwd=str(dart_runtime_dir),
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
            shell=(sys.platform == "win32"),
        )
        logger.success(f"✅ Successfully installed '{package_name}' into dart_runtime!")

        # Sync with pyflutter.yaml
        from pyflutter.core.config import PyFlutterConfig
        config = PyFlutterConfig.find_and_load()
        config.add_flutter_dependency(package_name)
        logger.info(f"📝 Recorded '{package_name}' in pyflutter.yaml.")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to install package '{package_name}':\n{e.stdout}")
        return False


def remove_flutter_package(package_name: str) -> bool:
    """
    Removes a Flutter package from the PyFlutter runtime using `flutter pub remove`
    and updates pyflutter.yaml.
    """
    current = Path(__file__).resolve()
    repo_root = current.parents[3]
    dart_runtime_dir = repo_root / "dart_runtime"

    if not dart_runtime_dir.exists():
        logger.error(f"Cannot find dart_runtime at: {dart_runtime_dir}")
        return False

    logger.info(f"🗑️  Removing Flutter package '{package_name}'...")
    try:
        subprocess.run(
            ["flutter", "pub", "remove", package_name],
            cwd=str(dart_runtime_dir),
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            shell=(sys.platform == "win32"),
        )
        logger.success(f"✅ Successfully removed '{package_name}'.")

        from pyflutter.core.config import PyFlutterConfig
        config = PyFlutterConfig.find_and_load()
        config.remove_flutter_dependency(package_name)
        logger.info(f"📝 Removed '{package_name}' from pyflutter.yaml.")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to remove package '{package_name}':\n{e.stdout}")
        return False
