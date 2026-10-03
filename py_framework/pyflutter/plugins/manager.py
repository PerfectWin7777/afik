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

    # ImagePicker
    elif plugin_name == "image_picker":
        img_path = str(Path(tempfile.gettempdir()) / "pyflutter_sample_image.png")
        if not Path(img_path).exists():
            with open(img_path, "wb") as f:
                f.write(b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82")
        vid_path = str(Path(tempfile.gettempdir()) / "pyflutter_sample_video.mp4")
        if not Path(vid_path).exists():
            with open(vid_path, "w") as f:
                f.write("sample video")

        if method == "pickImage":
            return {"path": img_path, "name": "sample.png", "size": 1024}
        elif method == "pickVideo":
            return {"path": vid_path, "name": "sample.mp4", "size": 2048}
        elif method == "pickMultiImage":
            return [{"path": img_path, "name": "sample.png", "size": 1024}]

    # Camera
    elif plugin_name == "camera":
        img_path = str(Path(tempfile.gettempdir()) / "pyflutter_cam.jpg")
        if not Path(img_path).exists():
            with open(img_path, "wb") as f:
                f.write(b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00\xff\xd9")
        vid_path = str(Path(tempfile.gettempdir()) / "pyflutter_vid.mp4")
        if not Path(vid_path).exists():
            with open(vid_path, "w") as f:
                f.write("sample cam video")

        if method == "availableCameras":
            return [
                {"id": "0", "name": "Back Camera", "lensFacing": "back", "sensorOrientation": 90},
                {"id": "1", "name": "Front Camera", "lensFacing": "front", "sensorOrientation": 270},
            ]
        elif method == "initialize":
            return {"cameraId": args.get("cameraId", "0"), "initialized": True}
        elif method == "takePicture":
            return {"path": img_path, "name": "pyflutter_cam.jpg", "size": 1024}
        elif method == "startVideoRecording":
            return {"recording": True}
        elif method == "stopVideoRecording":
            return {"path": vid_path, "name": "pyflutter_vid.mp4", "size": 2048}
        elif method == "setFlashMode":
            return {"flashMode": args.get("mode", "off")}
        elif method == "setZoomLevel":
            return {"zoom": float(args.get("zoom", 1.0))}
        elif method == "isRecording":
            return {"isRecording": False}
        elif method == "dispose":
            return {"disposed": True}

    # Connectivity
    elif plugin_name in ("connectivity", "connectivity_plus"):
        if method == "checkConnectivity":
            return {"status": "wifi"}

    # AudioPlayers
    elif plugin_name in ("audioplayers", "audioplayer"):
        pid = args.get("playerId", "default")
        if method == "play":
            _local_storage_cache[f"_audio_state_{pid}"] = "playing"
            return {"state": "playing"}
        elif method == "pause":
            _local_storage_cache[f"_audio_state_{pid}"] = "paused"
            return {"state": "paused"}
        elif method == "resume":
            _local_storage_cache[f"_audio_state_{pid}"] = "playing"
            return {"state": "playing"}
        elif method == "stop":
            _local_storage_cache[f"_audio_state_{pid}"] = "stopped"
            return {"state": "stopped"}
        elif method == "seek":
            return {"position": float(args.get("position", 0.0))}
        elif method == "setVolume":
            return {"volume": float(args.get("volume", 1.0))}
        elif method == "getDuration":
            return {"duration": 180.0}
        elif method == "getPosition":
            return {"position": 0.0}
        elif method == "getState":
            return {"state": _local_storage_cache.get(f"_audio_state_{pid}", "stopped")}

    # VideoPlayer
    elif plugin_name == "video_player":
        if method == "create":
            return {"created": True}
        elif method == "initialize":
            return {"initialized": True, "duration": 300.0, "aspectRatio": 1.777}
        elif method == "play":
            return {"isPlaying": True}
        elif method == "pause":
            return {"isPlaying": False}
        elif method == "seekTo":
            return {"position": float(args.get("position", 0.0))}
        elif method == "setVolume":
            return {"volume": float(args.get("volume", 1.0))}
        elif method == "setLooping":
            return {"isLooping": args.get("looping") == "true"}
        elif method == "getPosition":
            return {"position": 0.0}
        elif method == "dispose":
            return {"disposed": True}

    # Share
    elif plugin_name in ("share_plus", "share"):
        if method == "share":
            return {"success": True}
        elif method == "shareFiles":
            return {"success": True, "count": 1}
        elif method == "shareUri":
            return {"success": True}

    # WebView
    elif plugin_name in ("webview", "webview_flutter"):
        vid = args.get("viewId", "default")
        if method == "loadUrl":
            _local_storage_cache[f"_web_url_{vid}"] = str(args.get("url", "about:blank"))
            return {"url": _local_storage_cache[f"_web_url_{vid}"]}
        elif method == "loadHtml":
            _local_storage_cache[f"_web_url_{vid}"] = "data:text/html;charset=utf-8,..."
            return {"success": True}
        elif method == "reload":
            return {"reloaded": True}
        elif method == "goBack":
            return {"success": True}
        elif method == "goForward":
            return {"success": True}
        elif method == "canGoBack":
            return {"canGoBack": False}
        elif method == "canGoForward":
            return {"canGoForward": False}
        elif method == "evaluateJavascript":
            return "eval_result"
        elif method == "currentUrl":
            return {"url": _local_storage_cache.get(f"_web_url_{vid}", "about:blank")}

    # Chewie
    elif plugin_name == "chewie":
        cid = args.get("controllerId", "default")
        if method == "createChewieController":
            return {"controllerId": cid, "configured": True}
        elif method == "enterFullScreen":
            return {"controllerId": cid, "isFullScreen": True}
        elif method == "exitFullScreen":
            return {"controllerId": cid, "isFullScreen": False}
        elif method == "getConfig":
            return {"controllerId": cid, "configured": True}

    # Hive
    elif plugin_name == "hive":
        bname = args.get("boxName", "default")
        if method == "openBox":
            return {"boxName": bname, "opened": True}
        elif method == "put":
            k = str(args.get("key", ""))
            _local_storage_cache[f"_hive_{bname}_{k}"] = args.get("value")
            return {"boxName": bname, "key": k, "success": True}
        elif method == "get":
            k = str(args.get("key", ""))
            val = _local_storage_cache.get(f"_hive_{bname}_{k}")
            return {"boxName": bname, "key": k, "value": val if val is not None else args.get("defaultValue")}
        elif method == "delete":
            k = str(args.get("key", ""))
            _local_storage_cache.pop(f"_hive_{bname}_{k}", None)
            return {"boxName": bname, "key": k, "success": True}
        elif method == "clear":
            prefix = f"_hive_{bname}_"
            for k in list(_local_storage_cache.keys()):
                if k.startswith(prefix):
                    del _local_storage_cache[k]
            return {"boxName": bname, "cleared": True}
        elif method == "getAll":
            prefix = f"_hive_{bname}_"
            res = {}
            for k, v in _local_storage_cache.items():
                if k.startswith(prefix):
                    res[k[len(prefix):]] = v
            return res
        elif method == "close":
            return {"boxName": bname, "closed": True}

    # Sqflite
    elif plugin_name == "sqflite":
        dbname = args.get("db", "main.db")
        if method == "openDatabase":
            return {"db": dbname, "opened": True}
        elif method == "execute":
            return {"db": dbname, "executed": True}
        elif method == "insert":
            return {"db": dbname, "inserted": True, "id": 1}
        elif method == "query":
            return []
        elif method == "update":
            return {"db": dbname, "updated": 1}
        elif method == "delete":
            return {"db": dbname, "deleted": 1}
        elif method == "close":
            return {"db": dbname, "closed": True}

    # Local Notifications
    elif plugin_name in ("flutter_local_notifications", "local_notifications"):
        if method == "initialize":
            return {"initialized": True}
        elif method == "show":
            return {"shown": True, "id": args.get("id", "0")}
        elif method == "cancel":
            return {"cancelled": True, "id": args.get("id", "0")}
        elif method == "cancelAll":
            return {"cancelledCount": 1}
        elif method == "getActiveNotifications":
            return [{"id": 0, "title": "Notification", "body": "Body"}]

    # Permission Handler
    elif plugin_name == "permission_handler":
        perm = args.get("permission", "camera")
        if method == "checkPermission":
            return {"permission": perm, "status": "granted"}
        elif method == "requestPermission":
            return {"permission": perm, "status": "granted"}
        elif method == "openAppSettings":
            return {"opened": True}

    # Secure Storage
    elif plugin_name in ("flutter_secure_storage", "secure_storage"):
        if method == "write":
            k = str(args.get("key", ""))
            _local_storage_cache[f"_sec_{k}"] = str(args.get("value", ""))
            return {"key": k, "success": True}
        elif method == "read":
            k = str(args.get("key", ""))
            return _local_storage_cache.get(f"_sec_{k}")
        elif method == "delete":
            k = str(args.get("key", ""))
            _local_storage_cache.pop(f"_sec_{k}", None)
            return {"key": k, "success": True}
        elif method == "deleteAll":
            for k in list(_local_storage_cache.keys()):
                if k.startswith("_sec_"):
                    del _local_storage_cache[k]
            return {"cleared": True}
        elif method == "readAll":
            prefix = "_sec_"
            return {k[len(prefix):]: str(v) for k, v in _local_storage_cache.items() if k.startswith(prefix)}
        elif method == "containsKey":
            k = str(args.get("key", ""))
            return {"containsKey": f"_sec_{k}" in _local_storage_cache}

    # Local Auth
    elif plugin_name == "local_auth":
        if method == "canCheckBiometrics":
            return {"canCheck": True}
        elif method == "isDeviceSupported":
            return {"supported": True}
        elif method == "getAvailableBiometrics":
            return ["fingerprint", "face"]
        elif method == "authenticate":
            return {"authenticated": True}
        elif method == "stopAuthentication":
            return {"stopped": True}

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
