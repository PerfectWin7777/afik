"""
PyFlutter Native Plugin Manager.
Dispatches duplex RPC method calls from Python to the Rust bridge and Dart runtime.
Provides package installation tools for adding Flutter native packages and local fallback execution.
"""

from __future__ import annotations

import itertools
import json
import os
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


class PluginError(RuntimeError):
    """Raised when a native plugin call fails on the Dart side or cannot be delivered."""


class PluginTimeoutError(PluginError, TimeoutError):
    """Raised when the connected Dart runtime does not answer a plugin call in time."""


_rpc_lock = threading.Lock()

def require(res: Any, key: str, what: str) -> dict:
    """Returns ``res`` if it is a dict whose ``key`` is exactly True, else raises ``PluginError``.

    A plugin answer that is missing or malformed must never read as a success.
    """
    if isinstance(res, dict) and res.get(key) is True:
        return res
    raise PluginError(f"{what} failed: unexpected answer {res!r}")


# Calls that wait for a human (biometric prompt, permission dialog, pickers).
INTERACTIVE_TIMEOUT = 120.0
DEFAULT_TIMEOUT = 3.0

# Time the Dart side may take, per (plugin, method); ("plugin", "*") covers every other method
# of that plugin. Anything not listed gets DEFAULT_TIMEOUT. An explicit ``timeout=`` always wins.
PLUGIN_TIMEOUTS: dict[tuple[str, str], float] = {
    # a human answers
    ("local_auth", "authenticate"): INTERACTIVE_TIMEOUT,
    ("permission_handler", "requestPermission"): INTERACTIVE_TIMEOUT,
    ("file_picker", "pickFiles"): INTERACTIVE_TIMEOUT,
    ("file_picker", "getDirectoryPath"): INTERACTIVE_TIMEOUT,
    ("file_picker", "saveFile"): INTERACTIVE_TIMEOUT,
    ("image_picker", "pickImage"): INTERACTIVE_TIMEOUT,
    ("image_picker", "pickVideo"): INTERACTIVE_TIMEOUT,
    ("image_picker", "pickMultiImage"): INTERACTIVE_TIMEOUT,
    ("share_plus", "share"): INTERACTIVE_TIMEOUT,
    ("share_plus", "shareFiles"): INTERACTIVE_TIMEOUT,
    ("share_plus", "shareUri"): INTERACTIVE_TIMEOUT,
    ("printing", "printPdf"): INTERACTIVE_TIMEOUT,
    ("printing", "sharePdf"): INTERACTIVE_TIMEOUT,
    ("printing", "layoutPdf"): INTERACTIVE_TIMEOUT,
    ("camera", "initialize"): INTERACTIVE_TIMEOUT,          # camera permission prompt
    ("flutter_local_notifications", "initialize"): INTERACTIVE_TIMEOUT,  # notification permission
    # slow, but nobody to wait for
    ("camera", "takePicture"): 30.0,
    ("camera", "stopVideoRecording"): 30.0,
    ("pdfx", "*"): 30.0,
    ("video_player", "initialize"): 60.0,
}


def timeout_for(plugin_name: str, method: str) -> float:
    """The default wait for ``plugin_name.method`` (see :data:`PLUGIN_TIMEOUTS`)."""
    return PLUGIN_TIMEOUTS.get(
        (plugin_name, method), PLUGIN_TIMEOUTS.get((plugin_name, "*"), DEFAULT_TIMEOUT)
    )


def cancel_pending_calls(reason: str = "bridge closed") -> None:
    """Wakes every call waiting for an answer; each one raises ``PluginError(reason)``.

    Called when the bridge goes away (quit, Dart disconnected) so that nothing keeps waiting for
    an answer that can no longer arrive.
    """
    for call_id, event in list(_pending_rpc_calls.items()):
        _rpc_results[call_id] = (None, reason)
        event.set()


def _runtime_is_connected(runner: Any) -> bool:
    return bool(runner and runner.session and runner.session.process and runner.is_running)


def invoke_plugin_method(plugin_name: str, method: str, args: dict[str, Any]) -> None:
    """
    Invokes a fire-and-forget method on a native Flutter plugin shim.
    Never waits for the Dart answer, so it is safe to call from any callback.
    """
    call_plugin(plugin_name, method, args, wait=False)


def call_plugin(
    plugin_name: str,
    method: str,
    args: Optional[dict[str, Any]] = None,
    timeout: Optional[float] = None,
    wait: bool = True,
) -> Any:
    """
    Invokes an RPC method on a native Flutter plugin and returns the result.

    - Connected Dart runtime: the call goes over the bridge. A Dart-side error
      raises `PluginError`, a missing answer raises `PluginTimeoutError`. A failed
      call is never replaced by simulated data.
    - No runtime (unit tests, scripts, offline development): the local platform
      fallback is used. It is a simulation: the first call of each plugin logs a warning, and
      the security plugins (see :data:`OFFLINE_REFUSED`) refuse unless
      ``PYFLUTTER_ALLOW_INSECURE_MOCKS=1``.

    ``timeout`` defaults to :func:`timeout_for` (``PLUGIN_TIMEOUTS``): 3 s for ordinary calls,
    120 s for the ones that wait for a person.
    """
    args = args or {}
    if timeout is None:
        timeout = timeout_for(plugin_name, method)
    runner = get_active_runner()

    if not _runtime_is_connected(runner):
        _check_offline_allowed(plugin_name, method)
        return _dispatch_local_fallback(plugin_name, method, args)

    if wait and threading.current_thread() is getattr(runner, "_event_thread", None):
        raise PluginError(
            f"{plugin_name}.{method} was called from the bridge reader thread; "
            "the answer could never be read. Call it from a callback or a worker thread."
        )

    call_id = f"c_{next(_rpc_counter)}"
    event = threading.Event()
    if wait:
        _pending_rpc_calls[call_id] = event
    try:
        try:
            payload = f"{plugin_name}\x00{method}\x00{call_id}\x00{json.dumps(args)}".encode("utf-8")
        except (TypeError, ValueError) as e:
            raise PluginError(f"Arguments of {plugin_name}.{method} are not JSON serializable: {e}") from e
        header = struct.pack(">BI", MSG_PLUGIN_CALL, len(payload))
        try:
            with _rpc_lock:
                runner.session.process.stdin.write(header + payload)
                runner.session.process.stdin.flush()
        except (BrokenPipeError, OSError, ValueError) as e:
            raise PluginError(f"Bridge unavailable while calling {plugin_name}.{method}: {e}") from e
        logger.debug(f"[plugin rpc] Dispatched {plugin_name}.{method} (call_id: {call_id})")

        if not wait:
            return None
        if not event.wait(timeout=timeout):
            raise PluginTimeoutError(f"{plugin_name}.{method} timed out after {timeout}s")
        res, err = _rpc_results.pop(call_id, (None, None))
        if err:
            raise PluginError(f"Error in {plugin_name}.{method}: {err}")
        return res
    finally:
        _pending_rpc_calls.pop(call_id, None)
        if not wait:
            _rpc_results.pop(call_id, None)


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


# Plugins whose answer people rely on for security decisions: a simulated "authenticated",
# "granted" or secret store would be a lie, so they refuse when no Flutter runtime is connected.
OFFLINE_REFUSED = frozenset({
    "local_auth", "permission_handler", "flutter_secure_storage", "secure_storage",
})
# Offline answers that are real or explicit enough not to need a warning.
_OFFLINE_NO_WARNING = frozenset({"__method_channel__", "path_provider"})
_offline_warned: set[str] = set()


def _check_offline_allowed(plugin_name: str, method: str) -> None:
    """Refuses security plugins offline, and warns once per plugin that the answer is simulated."""
    if plugin_name in OFFLINE_REFUSED and os.environ.get("PYFLUTTER_ALLOW_INSECURE_MOCKS") != "1":
        raise PluginError(
            f"{plugin_name}.{method} is unavailable offline: no Flutter runtime is connected, and "
            "a simulated answer would not be trustworthy. Run the app on a device, or set "
            "PYFLUTTER_ALLOW_INSECURE_MOCKS=1 for tests."
        )
    if plugin_name not in _OFFLINE_NO_WARNING and plugin_name not in _offline_warned:
        _offline_warned.add(plugin_name)
        logger.warning("[offline] {} is simulated (no Flutter runtime connected)", plugin_name)


def _dispatch_local_fallback(plugin_name: str, method: str, args: dict[str, Any]) -> Any:
    """Safe local fallback for offline development, CLI operations, and unit tests."""
    # MethodChannel Universal Fallback
    if plugin_name == "__method_channel__":
        channel_name = str(args.get("channel", ""))
        method_name = str(args.get("method", method))
        arguments = args.get("arguments")
        from pyflutter.core.channel import get_mock_method_call_handler, MethodCall
        mock = get_mock_method_call_handler(channel_name)
        if mock is not None:
            return mock(MethodCall(method_name, arguments))
        logger.debug(f"[MethodChannel fallback] {channel_name}.{method_name} invoked offline.")
        return None

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
            return {"status": "wifi", "results": ["wifi"]}

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

    # Local Notifications
    elif plugin_name in ("flutter_local_notifications", "local_notifications"):
        if method == "initialize":
            return {"initialized": True}
        elif method == "show":
            return {"shown": True, "id": args.get("id", "0")}
        elif method == "cancel":
            return {"cancelled": True, "id": args.get("id", "0")}
        elif method == "cancelAll":
            return {"cancelled": True}
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

    # PDF & Printing Suite (Syncfusion, PDFX, Printing, FlutterPdfView)
    elif plugin_name in ("pdf", "printing", "syncfusion_flutter_pdfviewer", "syncfusion_pdfviewer", "pdfx", "flutter_pdfview"):
        if method == "openPdf":
            return {"documentId": "doc_1", "pageCount": 10, "path": args.get("path", "doc.pdf")}
        elif method == "getPageCount":
            return {"pageCount": 10}
        elif method == "renderPage":
            p = int(args.get("pageNumber", 1))
            return {"pageNumber": p, "width": 595, "height": 842, "rendered": True}
        elif method == "printPdf":
            return {"printed": True, "name": args.get("name", "doc.pdf")}
        elif method == "sharePdf":
            return {"shared": True, "path": args.get("path", "")}
        elif method == "layoutPdf":
            return {"completed": True}

    return None





def add_flutter_package(package_name: str) -> bool:
    """Adds a Flutter package to the project in the current directory (`pyflutter add`)."""
    from pyflutter.cli import plugins_cmd

    return plugins_cmd.add(package_name)


def remove_flutter_package(package_name: str) -> bool:
    """Removes a Flutter package from the project in the current directory (`pyflutter remove`)."""
    from pyflutter.cli import plugins_cmd

    return plugins_cmd.remove(package_name)
