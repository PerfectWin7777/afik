"""
Frame scheduler: the single UI thread of a Afik application.

Everything that touches application state runs on ONE thread, the way Flutter runs on its UI
thread:

* user callbacks (button clicks, text changes, plugin events) are posted with :meth:`post`,
* ``pf.update()`` / signal writes only mark the tree dirty (:meth:`request_frame`),
* the scheduler drains the posted tasks first, then builds and sends the tree **once**, at
  most every ``min_interval`` seconds, however many updates were requested meanwhile.

So a callback never runs while the tree is being built, a thousand signal writes cost one
build, and user code needs no locks. Threads of the application (timers, network workers)
call :func:`afik.run_on_ui` to hand their work to this thread.
"""

from __future__ import annotations

import queue
import threading
import time
from typing import Any, Callable, Optional

from afik.core.logger import logger

UI_THREAD_NAME = "afik-ui"


class FrameScheduler:
    def __init__(self, render: Callable[[], None], min_interval: float = 1 / 60):
        self._render = render
        self._min_interval = min_interval
        self._tasks: "queue.Queue[Callable[[], None]]" = queue.Queue()
        self._wake = threading.Event()
        self._dirty = False
        self._lock = threading.Lock()
        self._stopping = False
        self._thread: Optional[threading.Thread] = None
        self._last_frame = 0.0
        self.frames_rendered = 0

    # ----------------------------------------------------------------- lifecycle
    @property
    def running(self) -> bool:
        return self._thread is not None and self._thread.is_alive()

    def is_ui_thread(self) -> bool:
        return threading.current_thread() is self._thread

    def start(self) -> None:
        if self.running:
            return
        self._stopping = False
        self._thread = threading.Thread(target=self._loop, name=UI_THREAD_NAME, daemon=True)
        self._thread.start()

    def stop(self, timeout: float = 2.0) -> None:
        self._stopping = True
        self._wake.set()
        thread = self._thread
        if thread is not None and thread is not threading.current_thread():
            thread.join(timeout)

    # ----------------------------------------------------------------- requests (any thread)
    def request_frame(self) -> None:
        """Marks the tree dirty; one build will happen soon, whatever the number of requests."""
        with self._lock:
            self._dirty = True
        self._wake.set()

    def post(self, task: Callable[[], None]) -> None:
        """Runs ``task`` on the UI thread, before the next frame."""
        self._tasks.put(task)
        self._wake.set()

    def call(self, fn: Callable[[], Any], timeout: Optional[float] = 30.0) -> Any:
        """Runs ``fn`` on the UI thread and returns its result (or raises its exception).

        Called from the UI thread itself, it simply runs ``fn``.
        """
        if self.is_ui_thread() or not self.running:
            return fn()
        done = threading.Event()
        box: dict[str, Any] = {}

        def task() -> None:
            try:
                box["value"] = fn()
            except BaseException as e:  # noqa: BLE001 - re-raised in the caller
                box["error"] = e
            finally:
                done.set()

        self.post(task)
        if not done.wait(timeout):
            raise TimeoutError("The UI thread did not run the task in time.")
        if "error" in box:
            raise box["error"]
        return box.get("value")

    # ----------------------------------------------------------------- the loop
    def run_pending(self) -> None:
        """Drains the posted tasks and renders if the tree is dirty, on the calling thread.

        For tests and for code that must be synchronous while the scheduler is not running.
        """
        self._drain_tasks()
        self._render_if_dirty(wait_for_interval=False)

    def _drain_tasks(self) -> None:
        while True:
            try:
                task = self._tasks.get_nowait()
            except queue.Empty:
                return
            try:
                task()
            except Exception as e:  # a failing callback must not stop the UI thread
                logger.opt(exception=True).error("UI task failed: {}", e)

    def _render_if_dirty(self, wait_for_interval: bool) -> None:
        with self._lock:
            dirty = self._dirty
        if not dirty:
            return
        if wait_for_interval:
            delay = self._last_frame + self._min_interval - time.monotonic()
            if delay > 0:
                # Let the updates of this frame arrive, but keep serving callbacks.
                self._wake.wait(delay)
                self._drain_tasks()
        with self._lock:
            self._dirty = False
        try:
            self._render()
        except Exception as e:
            logger.opt(exception=True).error("Frame failed: {}", e)
        self._last_frame = time.monotonic()
        self.frames_rendered += 1

    def _loop(self) -> None:
        while not self._stopping:
            self._wake.wait()
            if self._stopping:
                break
            self._wake.clear()
            self._drain_tasks()
            self._render_if_dirty(wait_for_interval=True)
            # work posted while we rendered must not be lost
            if not self._tasks.empty() or self._dirty:
                self._wake.set()
