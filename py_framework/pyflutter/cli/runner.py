"""
PyFlutter CLI Runner.
Orchestrates Flutter runtime, Rust bridge relay, Python event loop, and developer hot reload (r/R/q).
"""

from __future__ import annotations

import atexit
import importlib
import importlib.util
import os
import queue
import secrets
import shutil
import socket
import subprocess
import sys
import threading
import time
from pathlib import Path
from typing import Any, Optional

from pyflutter.core.logger import logger
from pyflutter.cli.devices import select_device, setup_adb_port_forward
from pyflutter.core.bridge import BridgeSession, RESYNC_CALLBACK_ID
from pyflutter.core.widget_base import invoke_callback, clear_callbacks


def find_workspace_root() -> Path:
    """Finds the root directory containing dart_runtime and rust_bridge."""
    current = Path.cwd().resolve()
    for parent in [current, *current.parents]:
        if (parent / "dart_runtime").exists() and (parent / "rust_bridge").exists():
            return parent
    # Default fallback to parent of py_framework
    return Path(__file__).resolve().parents[3]


def find_bridge_binary(root: Path) -> Path:
    """Finds the compiled pyflutter-bridge binary."""
    ext = ".exe" if sys.platform == "win32" else ""
    candidates = [
        root / "rust_bridge" / "target" / "release" / f"pyflutter-bridge{ext}",
        root / "rust_bridge" / "target" / "debug" / f"pyflutter-bridge{ext}",
    ]
    for c in candidates:
        if c.exists():
            return c
    raise FileNotFoundError(
        f"pyflutter-bridge binary not found in {root / 'rust_bridge' / 'target'}. "
        "Please build it with `cargo build` in rust_bridge/."
    )


def is_port_in_use(port: int) -> bool:
    """Checks if a local TCP port is already open/in use."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.3)
        return s.connect_ex(("127.0.0.1", port)) == 0


def _pids_listening_on(port: int) -> list[int]:
    """Returns the PIDs listening on a local TCP port (best effort)."""
    pids: list[int] = []
    if sys.platform == "win32":
        output = subprocess.check_output(
            ["netstat", "-ano", "-p", "TCP"], text=True, errors="ignore"
        )
        for line in output.splitlines():
            parts = line.split()
            if len(parts) >= 5 and parts[1].endswith(f":{port}") and parts[3] == "LISTENING":
                pids.append(int(parts[4]))
    else:
        for cmd in (["lsof", "-t", f"-iTCP:{port}", "-sTCP:LISTEN"], ["fuser", f"{port}/tcp"]):
            if shutil.which(cmd[0]) is None:
                continue
            out = subprocess.run(cmd, capture_output=True, text=True).stdout
            pids = [int(tok) for tok in out.split() if tok.isdigit()]
            if pids:
                break
    return [pid for pid in pids if pid != os.getpid() and pid > 0]


def _process_name(pid: int) -> str:
    try:
        if sys.platform == "win32":
            out = subprocess.check_output(
                ["tasklist", "/FI", f"PID eq {pid}", "/FO", "CSV", "/NH"], text=True, errors="ignore"
            )
            return out.split(",")[0].strip('"').lower()
        return subprocess.check_output(["ps", "-p", str(pid), "-o", "comm="], text=True).strip().lower()
    except Exception:
        return ""


def ensure_port_free(port: int) -> None:
    """Frees the bridge port from a stale *pyflutter-bridge* process.

    Only processes whose name is `pyflutter-bridge` are terminated; any other
    program using the port is left alone and reported with an actionable error.
    """
    if not is_port_in_use(port):
        return
    logger.info("Port {} is occupied. Looking for a stale bridge process...", port)
    try:
        pids = _pids_listening_on(port)
    except Exception as e:
        logger.debug("Could not inspect port {}: {}", port, e)
        pids = []

    foreign: list[tuple[int, str]] = []
    for pid in pids:
        name = _process_name(pid)
        if "pyflutter-bridge" in name:
            logger.info("Terminating stale bridge (PID {}) on port {}...", pid, port)
            try:
                if sys.platform == "win32":
                    subprocess.run(["taskkill", "/F", "/PID", str(pid)], capture_output=True)
                else:
                    os.kill(pid, 15)
            except Exception as e:
                logger.debug("Could not terminate PID {}: {}", pid, e)
        else:
            foreign.append((pid, name or "unknown"))

    time.sleep(0.5)
    if is_port_in_use(port):
        detail = ", ".join(f"{name} (PID {pid})" for pid, name in foreign) or "an unknown process"
        logger.error(
            "Port {} is used by {}. Free it or choose another port with `pyflutter run -p <port>`.",
            port, detail,
        )
        sys.exit(1)


def load_app_from_file(file_path: str | Path, prefer_class: Optional[str] = None):
    """Dynamically loads the Python app module and instantiates the App class."""
    file_path = Path(file_path).resolve()
    # Namespaced so an entrypoint named random.py / json.py / logging.py can never
    # replace a standard-library module in sys.modules.
    module_name = f"pyflutter_app_{file_path.stem}"
    spec = importlib.util.spec_from_file_location(module_name, str(file_path))
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load module from {file_path}")

    # Auto-discover local py_framework if running from development repository
    workspace = find_workspace_root()
    dev_framework = workspace / "py_framework"
    if dev_framework.exists() and str(dev_framework) not in sys.path:
        sys.path.insert(0, str(dev_framework))

    # Ensure the script's directory is on sys.path
    script_dir = str(file_path.parent.resolve())
    if script_dir not in sys.path:
        sys.path.insert(0, script_dir)

    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)

    # Find the App class or callable
    from pyflutter.core.widget_base import Component, MainWindow
    app_instance = None

    # 0. On reload, keep the class of the running app (the one given to pf.run)
    if prefer_class:
        attr = getattr(module, prefer_class, None)
        if isinstance(attr, type) and getattr(attr, "__module__", "") == module_name:
            try:
                app_instance = attr()
            except Exception as e:
                logger.debug(f"Failed to instantiate {prefer_class}: {e}")

    # 1. Explicit 'App' in module
    if app_instance is None and hasattr(module, "App"):
        app_cls = getattr(module, "App")
        try:
            app_instance = app_cls() if isinstance(app_cls, type) else app_cls
        except Exception as e:
            logger.debug(f"Failed to instantiate App: {e}")

    # 2. Subclass of MainWindow (PyQt / PySide OOP style)
    if app_instance is None:
        for attr_name in dir(module):
            attr = getattr(module, attr_name, None)
            if (
                isinstance(attr, type)
                and issubclass(attr, MainWindow)
                and attr is not MainWindow
                and getattr(attr, "__module__", "") == module_name
            ):
                try:
                    app_instance = attr()
                    break
                except Exception as e:
                    logger.debug(f"Could not instantiate MainWindow {attr_name}: {e}")

    # 3. User-defined class ending with 'App' or 'Window'
    if app_instance is None:
        for attr_name in dir(module):
            if (attr_name.endswith("App") or attr_name.endswith("Window")) and attr_name not in ("MaterialApp", "App", "MainWindow"):
                attr = getattr(module, attr_name, None)
                if isinstance(attr, type) and getattr(attr, "__module__", "") == module_name:
                    try:
                        app_instance = attr()
                        break
                    except Exception as e:
                        logger.debug(f"Could not instantiate {attr_name}: {e}")

    # 4. User-defined class inheriting from Component that takes 0 arguments
    if app_instance is None:
        for attr_name in dir(module):
            attr = getattr(module, attr_name, None)
            if (
                isinstance(attr, type)
                and issubclass(attr, Component)
                and attr not in (Component, MainWindow)
                and getattr(attr, "__module__", "") == module_name
            ):
                try:
                    app_instance = attr()
                    break
                except TypeError:
                    continue
                except Exception as e:
                    logger.debug(f"Could not instantiate {attr_name}: {e}")

    # 5. User-defined class with a build() method
    if app_instance is None:
        for attr_name in dir(module):
            attr = getattr(module, attr_name, None)
            if (
                isinstance(attr, type)
                and hasattr(attr, "build")
                and getattr(attr, "__module__", "") == module_name
            ):
                try:
                    app_instance = attr()
                    break
                except TypeError:
                    continue

    # 6. Fallback: search for top-level build() function
    if app_instance is None and hasattr(module, "build") and callable(getattr(module, "build")):
        class FunctionalApp:
            def build(self):
                return module.build()
        app_instance = FunctionalApp()

    if app_instance is None:
        raise AttributeError(
            f"No Component, App class, or build() function found in {file_path}. "
            "Please define a `Component` subclass or a `build(self)` method."
        )

    return module, app_instance


class GradleSpinner:
    """Animated CLI spinner for Gradle build and install steps."""

    def __init__(self):
        self.running = False
        self.thread = None
        self.start_time = 0.0
        self.message = ""

    def start(self, message: str = "Building APK with Gradle"):
        if self.running:
            return
        self.running = True
        self.message = message
        self.start_time = time.perf_counter()
        self.thread = threading.Thread(target=self._spin, daemon=True)
        self.thread.start()

    def _spin(self):
        frames = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
        idx = 0
        while self.running:
            elapsed = int(time.perf_counter() - self.start_time)
            frame = frames[idx % len(frames)]
            msg = f"\r  \033[36m{frame}\033[0m {self.message}... ({elapsed}s)   "
            try:
                sys.stdout.write(msg)
                sys.stdout.flush()
            except Exception:
                pass
            idx += 1
            time.sleep(0.08)

    def stop(self, success_msg: Optional[str] = None):
        if not self.running:
            return
        self.running = False
        elapsed = time.perf_counter() - self.start_time
        try:
            sys.stdout.write("\r" + " " * 80 + "\r")
            sys.stdout.flush()
        except Exception:
            pass
        if success_msg:
            logger.success(f"{success_msg} in {elapsed:.1f}s")


class PyFlutterRunner:
    """Manages the full lifecycle of a pyflutter run session."""

    def __init__(
        self,
        entrypoint: str | Path,
        device_id: Optional[str] = None,
        port: int = 7879,
        attach_only: bool = False,
        debug_banner: Optional[bool] = None,
    ):
        self.entrypoint = Path(entrypoint).resolve()
        self.preferred_device_id = device_id
        self.port = port
        self.attach_only = attach_only
        self.debug_banner = debug_banner
        self.root = find_workspace_root()
        self.bridge_bin = find_bridge_binary(self.root)
        self.dart_runtime_dir = self.root / "dart_runtime"

        self.session: Optional[BridgeSession] = None
        self.flutter_process: Optional[subprocess.Popen] = None
        self.app_module = None
        self.app = None
        self.is_running = False
        self.tree_lock = threading.RLock()
        self._building = False
        self._rebuild_requested = False
        self._event_thread: Optional[threading.Thread] = None
        self._callback_queue: queue.Queue = queue.Queue()
        self._callback_thread: Optional[threading.Thread] = None
        atexit.register(self.quit, exit_sys=False)

        # Load project configuration if pyflutter.yaml exists
        from pyflutter.core.config import PyFlutterConfig
        self.config = PyFlutterConfig.find_and_load(self.entrypoint.parent)
        if self.config.config_path:
            logger.info(f"Loaded project manifest: {self.config.config_path.name} ({self.config.name} v{self.config.version})")

    def _build_and_tag_tree(self):
        """Builds the UI tree and applies app-level configurations like debug_banner."""
        if hasattr(self.app, "build") and callable(self.app.build):
            tree = self.app.build()
        else:
            tree = self.app
        show_banner = False
        if hasattr(self.app, "debug_banner"):
            show_banner = bool(self.app.debug_banner)
        elif self.debug_banner is not None:
            show_banner = bool(self.debug_banner)
        if hasattr(tree, "props") and isinstance(tree.props, dict):
            tree.props["debug_banner"] = "true" if show_banner else "false"
        return tree

    def start(self):
        """Main execution flow for `pyflutter run`."""
        if not self.entrypoint.exists():
            logger.error(f"Entrypoint file not found: {self.entrypoint}")
            sys.exit(1)

        # 0. Sync declarative permissions to native Android and iOS manifests
        from pyflutter.plugins.catalog import CatalogError, prepare_runtime
        try:
            prepare_runtime(self.root, self.config)
        except CatalogError as e:
            logger.error("{}", e)
            sys.exit(1)

        # 1. Device selection
        logger.info("Discovering target devices...")
        device = select_device(self.preferred_device_id)
        if not device:
            logger.error("No supported Flutter devices found. Please connect a device or start an emulator.")
            sys.exit(1)

        dev_name = device.get("name", "Unknown")
        dev_id = device.get("id", "")
        dev_platform = device.get("targetPlatform", "")
        logger.success(f"Selected device: {dev_name} ({dev_id}) [{dev_platform}]")

        # 2. Android ADB port reverse
        if "android" in dev_platform.lower() and dev_id:
            logger.info(f"Setting up ADB port forward for Android (tcp:{self.port} <-> tcp:{self.port})...")
            if setup_adb_port_forward(dev_id, self.port):
                logger.success("ADB port forward configured successfully.")
            else:
                logger.warning("Failed to configure ADB reverse automatically. Run `adb reverse tcp:7879 tcp:7879` if needed.")

        # 3. Load Python app
        if self.app is None:
            logger.info(f"Loading Python entrypoint: {self.entrypoint.name}...")
            self.app_module, self.app = load_app_from_file(self.entrypoint)
            logger.success(f"Loaded {self.app.__class__.__name__} successfully.")
        else:
            logger.success(f"Using {self.app.__class__.__name__} application instance.")

        # 4. Start Rust Bridge relay
        ensure_port_free(self.port)
        logger.info(f"Starting Rust Bridge relay on port {self.port}...")
        # Shared secret between the bridge and the Flutter app we launch ourselves, so
        # no other local process can read the UI tree or inject events. With --attach
        # the Flutter app is started by hand and cannot receive the token.
        self.token = None if self.attach_only else secrets.token_hex(16)
        bridge_args = ["--dart-port", str(self.port)]
        if self.token:
            bridge_args += ["--token", self.token]
        self.session = BridgeSession(str(self.bridge_bin), extra_args=bridge_args)

        # 5. Start Flutter runtime if not attach_only
        if not self.attach_only:
            logger.info(f"Launching Flutter app on {dev_name}...")
            self._start_flutter(dev_id)

        # 6. Initial tree push
        self.is_running = True
        logger.info("Waiting for Flutter client to connect and request initial tree...")
        initial_tree = self._build_and_tag_tree()
        with self.tree_lock:
            self.session.send_tree(initial_tree)
        logger.success("Initial UI tree sent to Bridge.")

        # 7. Start threads: Event receiver & Keypress handler
        self._callback_thread = threading.Thread(target=self._callback_worker, daemon=True)
        self._callback_thread.start()
        self._event_thread = threading.Thread(target=self._event_loop, daemon=True)
        self._event_thread.start()

        self._print_banner(dev_name)
        self._interactive_keyboard_loop()

    def _start_flutter(self, device_id: str):
        """Spawns flutter run in dart_runtime."""
        flutter_bin = shutil.which("flutter") or shutil.which("flutter.bat")
        if flutter_bin:
            lockfile = Path(flutter_bin).parent / "cache" / "lockfile"
            if lockfile.exists():
                try:
                    lockfile.unlink()
                except Exception:
                    pass

        cmd = ["flutter", "run", "-d", device_id, f"--dart-define=PYFLUTTER_PORT={self.port}"]
        if getattr(self, "token", None):
            cmd.append(f"--dart-define=PYFLUTTER_TOKEN={self.token}")
        self.flutter_process = subprocess.Popen(
            cmd,
            cwd=str(self.dart_runtime_dir),
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
            bufsize=1,
            shell=(sys.platform == "win32"),
        )

        # Background thread to stream Flutter stdout with animated Gradle spinner
        spinner = GradleSpinner()

        def stream_output():
            if not self.flutter_process or not self.flutter_process.stdout:
                return
            try:
                for line in iter(self.flutter_process.stdout.readline, ""):
                    line_str = line.strip()
                    if not line_str:
                        continue

                    if "Running Gradle task" in line_str:
                        spinner.start("Building APK with Gradle (assembleDebug)")
                        continue
                    elif "Built build" in line_str:
                        spinner.stop("Gradle assembleDebug completed")
                        continue
                    elif "Installing build" in line_str:
                        spinner.stop()
                        logger.info("📦 Installing APK onto device...")
                        continue
                    elif "Syncing files to device" in line_str:
                        spinner.stop()
                        logger.info(f"⚡ {line_str}")
                        continue
                    elif "Flutter run key commands" in line_str or "To hot reload changes" in line_str:
                        continue
                    elif "For a more detailed help message" in line_str or "Application finished." in line_str:
                        continue
                    # Always stream the authentic Flutter log so developers see the complete native diagnostics
                    logger.info(f"[flutter] {line_str}")

                    # When a layout overflow occurs, append actionable English guidance for the Python developer
                    if "A RenderFlex overflowed by" in line_str or ("overflowed by" in line_str and "pixels" in line_str):
                        logger.warning(
                            "\n💡 [PyFlutter Developer Guidance]\n"
                            f"   Flutter layout overflow: {line_str}\n"
                            "   Children widgets exceeded the parent constraints. How to resolve in Python:\n"
                            "   1. Replace `Row(...)` with `Wrap(children=[...], spacing=8, run_spacing=8)` to auto-wrap items onto new lines.\n"
                            "   2. Wrap children in `Expanded(child)` or `Flexible(child, fit=FlexFit.LOOSE)` so they share available space.\n"
                            "   3. Wrap the Row in `SingleChildScrollView(child, scroll_direction=Axis.HORIZONTAL)` to enable horizontal scrolling.\n"
                            "   4. Wrap in `FittedBox(child, fit=BoxFit.SCALE_DOWN)` to scale down child contents automatically to fit."
                        )
            except Exception as e:
                logger.debug(f"Stream output stopped: {e}")

        threading.Thread(target=stream_output, daemon=True).start()

    def _event_loop(self):
        """Listens for incoming frames (CallbackEvents and PluginResponses) from Flutter."""
        from pyflutter.core.render import MSG_CALLBACK_EVENT, MSG_PLUGIN_RESPONSE
        from pyflutter.plugins.manager import handle_plugin_response

        while self.is_running and self.session:
            try:
                event_pair = self.session.next_event()
            except Exception as e:
                if self.is_running:
                    logger.error(f"Bridge stream error: {e}")
                break

            if event_pair is None:
                if self.is_running:
                    logger.warning("Bridge stream ended or Flutter disconnected.")
                break

            msg_type, event = event_pair

            if msg_type == MSG_PLUGIN_RESPONSE:
                try:
                    handle_plugin_response(event)
                except Exception as e:
                    logger.error(f"Error handling plugin response: {e}")
                continue

            if msg_type == MSG_CALLBACK_EVENT and event:
                # Never run user code on this thread: it must keep reading the
                # bridge so plugin answers (called from callbacks) can arrive.
                self._callback_queue.put(event)

        self._callback_queue.put(None)

    def _callback_worker(self):
        """Runs user callbacks sequentially, then re-renders the tree."""
        while True:
            event = self._callback_queue.get()
            if event is None or not self.is_running:
                break
            try:
                if event.callback_id == RESYNC_CALLBACK_ID:
                    # A Dart client (re)connected and its tree is outdated.
                    logger.debug("Dart client requested a full tree resync")
                    if self.session:
                        self.session.reset_snapshot()
                    self._render_and_send(force_full=True)
                    continue
                logger.debug("Event received: {}", event.callback_id)
                invoke_callback(event.callback_id, dict(event.event_data))
                self.push_update()
            except Exception as e:
                if self.is_running:
                    logger.opt(exception=True).error("Error handling callback event {}: {}", event.callback_id, e)

    def _render_and_send(self, force_full: bool = False) -> None:
        """Builds and sends the tree. Updates requested during a build are coalesced
        into one extra rebuild instead of re-entering (and deadlocking on) the lock."""
        with self.tree_lock:
            if self._building:
                self._rebuild_requested = True
                return
            self._building = True
            try:
                while True:
                    self._rebuild_requested = False
                    tree = self._build_and_tag_tree()
                    self.session.send_tree(tree, force_full=force_full)
                    force_full = False
                    if not self._rebuild_requested:
                        break
            finally:
                self._building = False

    def push_update(self):
        """Pushes an asynchronous tree update to the bridge and connected device."""
        if self.session and self.app:
            try:
                self._render_and_send()
            except Exception as e:
                logger.opt(exception=True).error("Failed to push async update: {}", e)

    def hot_reload(self):
        """Performs a fast Hot Reload (reloads Python module while preserving state, pushes diff patch)."""
        logger.info("\n⚡ [PyFlutter] Hot Reloading UI...")
        start_time = time.perf_counter()
        try:
            # Reload module from disk to capture new build logic without resetting state
            self.app_module, new_app = load_app_from_file(
                self.entrypoint, prefer_class=type(self.app).__name__ if self.app is not None else None
            )
            if new_app is not None and self.app is not None:
                if hasattr(self.app, "__dict__") and hasattr(new_app, "__dict__"):
                    for k, v in self.app.__dict__.items():
                        if not k.startswith("_") and k in new_app.__dict__:
                            setattr(new_app, k, v)
                self.app = new_app

            # Rebuild tree and push diff
            if self.session and self.app:
                with self.tree_lock:
                    tree = self._build_and_tag_tree()
                    self.session.send_tree(tree)

            # Forward reload to Flutter engine if active
            if self.flutter_process and self.flutter_process.stdin:
                try:
                    self.flutter_process.stdin.write("r\n")
                    self.flutter_process.stdin.flush()
                except Exception:
                    pass

            elapsed_ms = (time.perf_counter() - start_time) * 1000
            logger.success(f"⚡ [PyFlutter] Hot Reload completed in {elapsed_ms:.1f}ms!")
        except Exception as e:
            logger.error(f"Hot Reload failed: {e}")

    def hot_restart(self):
        """Performs a Hot Restart (resets app state, clears callbacks, and resets Flutter)."""
        logger.info("\n🔄 [PyFlutter] Hot Restarting app...")
        try:
            from pyflutter.core.state import clear_state_registry
            clear_callbacks()
            clear_state_registry()

            if self.session:
                self.session.reset_snapshot()

            prefer = type(self.app).__name__ if self.app is not None else None
            self.app_module, self.app = load_app_from_file(self.entrypoint, prefer_class=prefer)

            if self.session and self.app:
                with self.tree_lock:
                    tree = self._build_and_tag_tree()
                    self.session.send_tree(tree, force_full=True)

            if self.flutter_process and self.flutter_process.stdin:
                try:
                    self.flutter_process.stdin.write("R\n")
                    self.flutter_process.stdin.flush()
                except Exception:
                    pass

            logger.success("🔄 [PyFlutter] Hot Restart completed!")
        except Exception as e:
            logger.error(f"Hot Restart failed: {e}")

    def quit(self, exit_sys: bool = True):
        """Shuts down all processes cleanly."""
        if not self.is_running and self.session is None and self.flutter_process is None:
            return
        logger.info("\n👋 [PyFlutter] Quitting...")
        self.is_running = False

        if self.flutter_process:
            try:
                if self.flutter_process.stdin:
                    self.flutter_process.stdin.write("q\n")
                    self.flutter_process.stdin.flush()
                self.flutter_process.terminate()
            except Exception:
                pass
            self.flutter_process = None

        if self.session:
            try:
                self.session.close()
            except Exception:
                pass
            self.session = None

        logger.info("Session ended cleanly.")
        if exit_sys:
            try:
                sys.exit(0)
            except SystemExit:
                pass

    def _print_banner(self, device_name: str):
        banner = f"""
+------------------------------------------------------------+
|                  PyFlutter Interactive Dev                 |
+------------------------------------------------------------+
|  Device: {device_name[:30]:<49} |
|  Bridge Port: {self.port:<44} |
+------------------------------------------------------------+
|  Keyboard shortcuts:                                       |
|    r : Hot Reload UI & Python code                         |
|    R : Hot Restart (reset state)                           |
|    h : Show help                                           |
|    q : Quit                                                |
+------------------------------------------------------------+
"""
        print(banner)

    def _interactive_keyboard_loop(self):
        """Reads keyboard inputs interactively (instant single-key press on Windows/Unix)."""
        if sys.platform == "win32" and sys.stdin.isatty():
            import msvcrt
            while self.is_running:
                try:
                    ch = msvcrt.getch()
                    if ch in (b"\x00", b"\xe0"):
                        msvcrt.getch()
                        continue
                    key = ch.decode("utf-8", errors="ignore")
                    if key:
                        self._handle_key(key)
                except (KeyboardInterrupt, EOFError):
                    self.quit()
                    break
        elif sys.platform != "win32" and sys.stdin.isatty():
            import select
            import termios
            import tty
            fd = sys.stdin.fileno()
            old_settings = termios.tcgetattr(fd)
            try:
                tty.setraw(fd)
                while self.is_running:
                    rlist, _, _ = select.select([sys.stdin], [], [], 0.1)
                    if rlist:
                        key = sys.stdin.read(1)
                        if key == "\x03":
                            break
                        self._handle_key(key)
            except Exception:
                pass
            finally:
                termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        else:
            # Fallback for piped stdin (CI, scripts, non-tty)
            while self.is_running:
                try:
                    line = sys.stdin.readline()
                    if not line:
                        break
                    for ch in line.strip():
                        if ch:
                            self._handle_key(ch)
                except (KeyboardInterrupt, EOFError):
                    self.quit()
                    break

    def _handle_key(self, key: str):
        if key == "r":
            self.hot_reload()
        elif key == "R":
            self.hot_restart()
        elif key in ("q", "Q"):
            self.quit()
        elif key in ("h", "H", "?"):
            self._print_banner(self.preferred_device_id or "Active Device")
