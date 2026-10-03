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
