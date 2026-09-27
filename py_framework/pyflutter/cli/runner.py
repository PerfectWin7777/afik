"""
PyFlutter CLI Runner.
Orchestrates Flutter runtime, Rust bridge relay, Python event loop, and developer hot reload (r/R/q).
"""

from __future__ import annotations

import importlib
import importlib.util
import os
import queue
import shutil
import subprocess
import sys
import threading
import time
from pathlib import Path
from typing import Any, Optional

from pyflutter.core.logger import logger
from pyflutter.cli.devices import select_device, setup_adb_port_forward
from pyflutter.core.bridge import BridgeSession
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


def load_app_from_file(file_path: Path):
    """Dynamically loads the Python app module and instantiates the App class."""
    module_name = file_path.stem
    spec = importlib.util.spec_from_file_location(module_name, str(file_path))
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load module from {file_path}")

    # Ensure the script's directory is on sys.path
    script_dir = str(file_path.parent.resolve())
    if script_dir not in sys.path:
        sys.path.insert(0, script_dir)

    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)

    # Find the App class or callable
    app_instance = None
    if hasattr(module, "App"):
        app_cls = getattr(module, "App")
        app_instance = app_cls() if isinstance(app_cls, type) else app_cls
    else:
        # Search for any class ending with 'App'
        for attr_name in dir(module):
            if attr_name.endswith("App") and attr_name != "App":
                attr = getattr(module, attr_name)
                if isinstance(attr, type):
                    app_instance = attr()
                    break

    if app_instance is None and hasattr(module, "build"):
        class FunctionalApp:
            def build(self):
                return module.build()
        app_instance = FunctionalApp()

    if app_instance is None:
        raise AttributeError(
            f"No App class or build() function found in {file_path}. "
            "Please define `class App:` with a `build(self)` method."
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
        self.tree_lock = threading.Lock()

    def _build_and_tag_tree(self):
        """Builds the UI tree and applies app-level configurations like debug_banner."""
        tree = self.app.build()
        show_banner = False
        if hasattr(self.app, "debug_banner"):
            show_banner = bool(self.app.debug_banner)
        elif self.debug_banner is not None:
            show_banner = bool(self.debug_banner)
        tree.props["debug_banner"] = "true" if show_banner else "false"
        return tree

    def start(self):
        """Main execution flow for `pyflutter run`."""
        if not self.entrypoint.exists():
            logger.error(f"Entrypoint file not found: {self.entrypoint}")
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
        logger.info(f"Loading Python entrypoint: {self.entrypoint.name}...")
        self.app_module, self.app = load_app_from_file(self.entrypoint)
        logger.success(f"Loaded {self.app.__class__.__name__} successfully.")

        # 4. Start Rust Bridge relay
        logger.info(f"Starting Rust Bridge relay on port {self.port}...")
        self.session = BridgeSession(
            str(self.bridge_bin),
            extra_args=["--dart-port", str(self.port)],
        )

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
        event_thread = threading.Thread(target=self._event_loop, daemon=True)
        event_thread.start()

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

        cmd = ["flutter", "run", "-d", device_id]
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

                    logger.info(f"[flutter] {line_str}")
            except Exception as e:
                logger.debug(f"Stream output stopped: {e}")

        threading.Thread(target=stream_output, daemon=True).start()

    def _event_loop(self):
        """Listens for incoming CallbackEvents from Flutter."""
        while self.is_running and self.session:
            try:
                event = self.session.next_event()
                if event is None:
                    if self.is_running:
                        logger.warning("Bridge stream ended or Flutter disconnected.")
                    break

                logger.debug(f"Event received: {event.callback_id}")
                invoke_callback(event.callback_id, dict(event.event_data))

                # Rebuild and send new tree
                with self.tree_lock:
                    new_tree = self._build_and_tag_tree()
                    self.session.send_tree(new_tree)
            except Exception as e:
                if self.is_running:
                    logger.error(f"Error in event loop: {e}")
                break

    def push_update(self):
        """Pushes an asynchronous tree update to the bridge and connected device."""
        if self.session and self.app:
            try:
                with self.tree_lock:
                    tree = self._build_and_tag_tree()
                    self.session.send_tree(tree)
            except Exception as e:
                logger.error(f"Failed to push async update: {e}")

    def hot_reload(self):
        """Performs a fast Hot Reload (reloads Python module and re-renders tree)."""
        logger.info("\n⚡ [PyFlutter] Hot Reloading UI...")
        start_time = time.perf_counter()
        try:
            # Clear previous callbacks to prevent memory leaks
            clear_callbacks()

            # Reload module from disk
            self.app_module, self.app = load_app_from_file(self.entrypoint)

            # Rebuild tree and push
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
        """Performs a Hot Restart (resets app state and resets Flutter)."""
        logger.info("\n🔄 [PyFlutter] Hot Restarting app...")
        try:
            clear_callbacks()
            self.app_module, self.app = load_app_from_file(self.entrypoint)

            if self.session and self.app:
                with self.tree_lock:
                    tree = self._build_and_tag_tree()
                    self.session.send_tree(tree)

            if self.flutter_process and self.flutter_process.stdin:
                try:
                    self.flutter_process.stdin.write("R\n")
                    self.flutter_process.stdin.flush()
                except Exception:
                    pass

            logger.success("🔄 [PyFlutter] Hot Restart completed!")
        except Exception as e:
            logger.error(f"Hot Restart failed: {e}")

    def quit(self):
        """Shuts down all processes cleanly."""
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

        if self.session:
            try:
                self.session.close()
            except Exception:
                pass

        logger.info("Session ended cleanly.")
        sys.exit(0)

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
