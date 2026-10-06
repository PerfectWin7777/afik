"""
PyFlutter high-level application runner and builder.
Enables running and building PyFlutter apps directly with `python script.py`
or programmatically via `pf.run(App(), build="apk", mode="debug")`.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Optional


_active_runner: Optional[Any] = None


def set_active_runner(runner: Any) -> None:
    global _active_runner
    _active_runner = runner


def get_active_runner() -> Optional[Any]:
    return _active_runner


def update() -> None:
    """
    Requests an immediate UI re-render and sends the updated tree to the Flutter device.
    Useful for background network fetches, timers, or WebSocket events.
    """
    if _active_runner is not None:
        _active_runner.push_update()


def run_on_ui(fn: Any) -> None:
    """Runs ``fn()`` on the application's UI thread, where all state must be touched.

    Call it from your own threads (timers, network workers) instead of changing widgets or
    signals directly. Without a running application it simply calls ``fn()``.
    """
    runner = _active_runner
    if runner is not None and getattr(runner, "scheduler", None) is not None and runner.scheduler.running:
        runner.scheduler.post(fn)
    else:
        fn()


def run(
    app: Any = None,
    *,
    build: Optional[str | bool] = None,
    mode: str = "debug",
    target: Optional[str] = None,
    device: Optional[str] = None,
    port: int = 7879,
    attach: bool = False,
    split_per_abi: bool = False,
) -> Any:
    """
    Launches or builds the PyFlutter application.
    
    Usage:
        import pyflutter as pf

        class App:
            def build(self):
                return pf.Center(pf.Text("Hello World"))

        if __name__ == "__main__":
            # Run interactively (default: debug):
            pf.run(App())

            # Or build standalone package directly in Python:
            # pf.run(App(), build="apk", mode="debug")
            # pf.run(App(), build="appbundle", mode="release")
            # pf.run(App(), build="windows", mode="release")
    """
    # Auto-detect calling script file
    caller_file = sys._getframe(1).f_code.co_filename
    entrypoint_path = (
        Path(caller_file).resolve()
        if caller_file and caller_file != "<stdin>"
        else Path.cwd() / "main.py"
    )

    # Check for CLI arguments invocation: `python main.py build [target] [--release|--debug]`
    cli_build = False
    cli_target = None
    cli_mode = None
    cli_split = False

    if len(sys.argv) > 1 and sys.argv[1] == "build":
        cli_build = True
        # Check if target specified (e.g. python main.py build apk)
        if len(sys.argv) > 2 and not sys.argv[2].startswith("-"):
            cli_target = sys.argv[2]
        if "--release" in sys.argv:
            cli_mode = "release"
        elif "--debug" in sys.argv:
            cli_mode = "debug"
        if "--split-per-abi" in sys.argv:
            cli_split = True

    should_build = (build is not None and build is not False) or cli_build

    if should_build:
        from pyflutter.cli.builder import PyFlutterBuilder

        # Resolve build target (default: apk)
        build_target = "apk"
        if isinstance(build, str):
            build_target = build.lower()
        elif target:
            build_target = target.lower()
        elif cli_target:
            build_target = cli_target.lower()

        # Resolve build mode (default: debug)
        build_mode = "debug"
        if cli_mode:
            build_mode = cli_mode
        elif mode:
            build_mode = mode.lower()

        split = split_per_abi or cli_split

        builder = PyFlutterBuilder(
            target=build_target,
            entrypoint=str(entrypoint_path),
            release=(build_mode == "release"),
            split_per_abi=split,
        )
        return builder.build()

    from pyflutter.cli.runner import PyFlutterRunner

    runner = PyFlutterRunner(
        entrypoint=entrypoint_path,
        device_id=device,
        port=port,
        attach_only=attach,
    )

    # If app instance was directly passed, reuse it
    if app is not None:
        runner.app = app

    set_active_runner(runner)
    runner.start()
