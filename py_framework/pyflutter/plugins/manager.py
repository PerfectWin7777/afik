"""
PyFlutter Native Plugin Manager.
Dispatches duplex RPC method calls from Python to the Rust bridge and Dart runtime.
Provides package installation tools for adding Flutter native packages and local fallback execution.
"""

from __future__ import annotations

import itertools
import json
import shutil
import struct
import subprocess
import sys
import tempfile
import threading
from pathlib import Path
from typing import Any, Optional

from pyflutter.app import get_active_runner
from pyflutter.core.logger import logger

MSG_PLUGIN_CALL = 0x03
MSG_PLUGIN_RESPONSE = 0x05

_pending_rpc_calls: dict[str, threading.Event] = {}
_rpc_results: dict[str, tuple[Any, Optional[str]]] = {}
_rpc_counter = itertools.count()
_local_storage_cache: dict[str, Any] = {}


def invoke_plugin_method(plugin_name: str, method: str, args: dict[str, Any]) -> None:
    """
    Invokes a fire-and-forget method on a native Flutter plugin shim.
    """
    call_plugin(plugin_name, method, args)


def call_plugin(
    plugin_name: str,
    method: str,
    args: Optional[dict[str, Any]] = None,
    timeout: float = 3.0,
) -> Any:
    """
    Invokes an RPC method on a native Flutter plugin and returns the result.
    If a connected Dart runtime is active, dispatches over the bridge.
    Otherwise, seamlessly executes using the local platform fallback.
    """
    args = args or {}
    runner = get_active_runner()

    if runner and runner.session and runner.session.process and runner.is_running:
        call_id = f"c_{next(_rpc_counter)}"
        event = threading.Event()
        _pending_rpc_calls[call_id] = event
        try:
            payload = f"{plugin_name}\x00{method}\x00{call_id}\x00{json.dumps(args)}".encode("utf-8")
            header = struct.pack(">BI", MSG_PLUGIN_CALL, len(payload))
            runner.session.process.stdin.write(header + payload)
            runner.session.process.stdin.flush()
            logger.debug(f"[plugin rpc] Dispatched {plugin_name}.{method} (call_id: {call_id})")

            if event.wait(timeout=timeout):
                res, err = _rpc_results.pop(call_id, (None, None))
                if err:
                    raise RuntimeError(f"Error in {plugin_name}.{method}: {err}")
                return res
            else:
                logger.warning(f"[plugin timeout] {plugin_name}.{method} timed out. Using fallback.")
        except Exception as e:
            logger.debug(f"[plugin call error] {e}")
        finally:
            _pending_rpc_calls.pop(call_id, None)

    return _dispatch_local_fallback(plugin_name, method, args)


def handle_plugin_response(payload: bytes) -> None:
    """Handles an incoming MSG_PLUGIN_RESPONSE from Dart."""
    try:
        data = json.loads(payload.decode("utf-8"))
        call_id = data.get("call_id")
        result = data.get("result")
        error = data.get("error")
        if call_id and call_id in _pending_rpc_calls:
            _rpc_results[call_id] = (result, error)
            event = _pending_rpc_calls.pop(call_id)
            event.set()
    except Exception as e:
        logger.error(f"Error decoding plugin response: {e}")


def _dispatch_local_fallback(plugin_name: str, method: str, args: dict[str, Any]) -> Any:
    """Safe local fallback for offline development, CLI operations, and unit tests."""
    # Storage / SharedPreferences
    if plugin_name in ("storage", "shared_preferences"):
        key = args.get("key", "")
        if method in ("setString", "set_string"):
            _local_storage_cache[key] = str(args.get("value", ""))
            return True
        elif method in ("getString", "get_string"):
            return _local_storage_cache.get(key)
        elif method in ("setInt", "set_int"):
            try:
                _local_storage_cache[key] = int(args.get("value", 0))
            except (ValueError, TypeError):
                _local_storage_cache[key] = 0
            return True
        elif method in ("getInt", "get_int"):
            return _local_storage_cache.get(key)
        elif method in ("setBool", "set_bool"):
            val = args.get("value")
            _local_storage_cache[key] = True if str(val).lower() in ("true", "1") else False
            return True
        elif method in ("getBool", "get_bool"):
            return _local_storage_cache.get(key)
        elif method in ("setDouble", "set_double"):
            try:
                _local_storage_cache[key] = float(args.get("value", 0.0))
            except (ValueError, TypeError):
                _local_storage_cache[key] = 0.0
            return True
        elif method in ("getDouble", "get_double"):
            return _local_storage_cache.get(key)
        elif method in ("remove",):
            _local_storage_cache.pop(key, None)
            return True
        elif method in ("clear",):
            _local_storage_cache.clear()
            return True
        elif method in ("getAll", "get_all"):
            return dict(_local_storage_cache)

    # PathProvider
    elif plugin_name == "path_provider":
        if method in ("getApplicationDocumentsDirectory", "get_app_documents_directory", "get_documents_dir"):
            return str(Path.home() / "Documents")
        elif method in ("getTemporaryDirectory", "get_temporary_directory", "get_temp_dir"):
            return tempfile.gettempdir()
        elif method in ("getApplicationSupportDirectory", "get_app_support_directory"):
            return str(Path.home() / ".pyflutter")
        elif method in ("getDownloadsDirectory", "get_downloads_directory"):
            return str(Path.home() / "Downloads")

    # DeviceInfo
    elif plugin_name in ("device_info", "device_info_plus"):
        return {
            "platform": sys.platform,
            "version": sys.version.split()[0],
            "hostname": "localhost",
            "numberOfProcessors": 4,
            "localeName": "en_US",
            "isPhysicalDevice": False,
        }

    # FilePicker
    elif plugin_name == "file_picker":
        return []

    return None


def add_flutter_package(package_name: str) -> bool:
    """Installs a Flutter package into the PyFlutter runtime using `flutter pub add`."""
    current = Path(__file__).resolve()
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
        subprocess.run(
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
        from pyflutter.core.config import PyFlutterConfig
        config = PyFlutterConfig.find_and_load()
        config.add_flutter_dependency(package_name)
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to install package '{package_name}':\n{e.stdout}")
        return False
