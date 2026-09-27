"""
PyFlutter high-level application runner.
Enables running PyFlutter apps directly with `python script.py` or the VS Code "Run" button.
"""

from __future__ import annotations

import inspect
from pathlib import Path
from typing import Any, Callable, Optional


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


def run(
    app: Any = None,
    *,
    target: Optional[Callable[[], Any]] = None,
    device: Optional[str] = None,
    port: int = 7879,
    attach: bool = False,
):
    """
    Launches the PyFlutter application.
    
    Usage:
        import pyflutter as pf

        class App:
            def build(self):
                return pf.Center(pf.Text("Hello World"))

        if __name__ == "__main__":
            pf.run(App())
    """
    from pyflutter.cli.runner import PyFlutterRunner

    # Auto-detect calling script file
    caller_frame = inspect.stack()[1]
    caller_file = caller_frame.filename
    entrypoint_path = Path(caller_file).resolve() if caller_file and caller_file != "<stdin>" else Path.cwd() / "main.py"

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
