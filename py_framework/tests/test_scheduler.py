"""One UI thread: callbacks and builds are serialised and updates are coalesced."""

from __future__ import annotations

import json
import struct
import threading
import time
import unittest
from pathlib import Path
from unittest.mock import patch

import afik as pf
from afik import app as app_module
from afik.cli.runner import AfikRunner
from afik.core.scheduler import UI_THREAD_NAME, FrameScheduler
from afik.plugins import manager


def wait_until(predicate, timeout=2.0):
    end = time.time() + timeout
    while time.time() < end:
        if predicate():
            return True
        time.sleep(0.005)
    return predicate()


class TestFrameScheduler(unittest.TestCase):
    def setUp(self):
        self.frames = []
        self.scheduler = FrameScheduler(lambda: self.frames.append(threading.current_thread().name))
        self.scheduler.start()
        self.addCleanup(self.scheduler.stop)

    def test_many_requests_cost_one_frame(self):
        for _ in range(1000):
            self.scheduler.request_frame()
        self.assertTrue(wait_until(lambda: len(self.frames) >= 1))
        time.sleep(0.1)
        self.assertLessEqual(len(self.frames), 2)

    def test_everything_runs_on_the_ui_thread(self):
        names = []
        self.scheduler.post(lambda: names.append(threading.current_thread().name))
        self.scheduler.request_frame()
        self.assertTrue(wait_until(lambda: names and self.frames))
        self.assertEqual(names, [UI_THREAD_NAME])
        self.assertEqual(self.frames, [UI_THREAD_NAME])

    def test_tasks_run_before_the_frame_they_triggered(self):
        order = []
        scheduler = FrameScheduler(lambda: order.append("frame"))
        scheduler.start()
        self.addCleanup(scheduler.stop)
        scheduler.post(lambda: order.append("task"))
        scheduler.request_frame()
        self.assertTrue(wait_until(lambda: "frame" in order))
        self.assertEqual(order[:2], ["task", "frame"])

    def test_a_failing_task_does_not_stop_the_loop(self):
        done = []
        self.scheduler.post(lambda: 1 / 0)
        self.scheduler.post(lambda: done.append(1))
        self.assertTrue(wait_until(lambda: done))

    def test_a_failing_frame_does_not_stop_the_loop(self):
        calls = []

        def render():
            calls.append(1)
            if len(calls) == 1:
                raise RuntimeError("boom")

        scheduler = FrameScheduler(render)
        scheduler.start()
        self.addCleanup(scheduler.stop)
        scheduler.request_frame()
        self.assertTrue(wait_until(lambda: len(calls) == 1))
        time.sleep(0.05)
        scheduler.request_frame()
        self.assertTrue(wait_until(lambda: len(calls) == 2))

    def test_call_returns_the_result_or_raises(self):
        self.assertEqual(self.scheduler.call(lambda: threading.current_thread().name), UI_THREAD_NAME)
        with self.assertRaises(ZeroDivisionError):
            self.scheduler.call(lambda: 1 / 0)

    def test_call_from_the_ui_thread_does_not_deadlock(self):
        result = []
        self.scheduler.post(lambda: result.append(self.scheduler.call(lambda: 7)))
        self.assertTrue(wait_until(lambda: result == [7]))

    def test_run_pending_without_a_thread(self):
        frames = []
        scheduler = FrameScheduler(lambda: frames.append(1))
        ran = []
        scheduler.post(lambda: ran.append(1))
        scheduler.request_frame()
        scheduler.run_pending()
        self.assertEqual((ran, frames), ([1], [1]))


class FakeSession:
    """Collects the trees the runner sends, and answers plugin calls like Dart would."""

    def __init__(self):
        self.sent = []
        self.process = self
        self.stdin = self

    def send_tree(self, tree, force_full=False, resolved=False):
        self.sent.append((tree, force_full))

    def reset_snapshot(self):
        pass

    # the process.stdin interface used by call_plugin
    def write(self, data):
        msg_type, length = struct.unpack(">BI", data[:5])
        if msg_type == 0x03:
            _, _, call_id, _ = data[5:5 + length].decode().split("\x00", 3)
            body = json.dumps({"call_id": call_id, "result": {"ok": True}, "error": None}).encode()
            threading.Thread(target=manager.handle_plugin_response, args=(body,)).start()

    def flush(self):
        pass


class Counter(pf.Component):
    def __init__(self):
        super().__init__()
        self.builds = 0
        self.inside_build = False
        self.inside_callback = False
        self.overlap = False

    def build(self):
        self.inside_build = True
        if self.inside_callback:
            self.overlap = True
        self.builds += 1
        time.sleep(0.002)
        self.inside_build = False
        return pf.Text(str(self.builds))


class TestRunnerUsesTheUiThread(unittest.TestCase):
    def setUp(self):
        with patch("afik.cli.runner.find_bridge_binary", return_value=Path("bridge")), \
             patch("afik.cli.runner.atexit.register"):
            self.runner = AfikRunner(entrypoint=Path(__file__))
        self.session = FakeSession()
        self.runner.session = self.session
        self.runner.app = Counter()
        self.runner.is_running = True
        app_module.set_active_runner(self.runner)
        self.runner.scheduler.start()
        self.addCleanup(app_module.set_active_runner, None)
        self.addCleanup(self.runner.scheduler.stop)

    def test_a_thousand_updates_are_one_build(self):
        for _ in range(1000):
            pf.update()
        self.assertTrue(wait_until(lambda: self.session.sent))
        time.sleep(0.1)
        self.assertLessEqual(len(self.session.sent), 2)

    def test_update_from_a_worker_thread_is_a_frame(self):
        threading.Thread(target=pf.update).start()
        self.assertTrue(wait_until(lambda: self.session.sent))

    def test_a_callback_with_three_updates_sends_once(self):
        def handler():
            pf.update()
            pf.update()
            pf.update()

        from afik.core.widget_base import _register_callback
        callback_id = _register_callback(handler)
        event = type("E", (), {"callback_id": callback_id, "event_data": {}})()
        self.runner.scheduler.post(lambda: self.runner._handle_callback_event(event))
        self.assertTrue(wait_until(lambda: self.session.sent))
        time.sleep(0.1)
        self.assertEqual(len(self.session.sent), 1)

    def test_callbacks_and_builds_never_overlap(self):
        app = self.runner.app
        from afik.core.widget_base import _register_callback

        def handler():
            app.inside_callback = True
            if app.inside_build:
                app.overlap = True
            time.sleep(0.003)
            pf.update()
            app.inside_callback = False

        callback_id = _register_callback(handler)
        event = type("E", (), {"callback_id": callback_id, "event_data": {}})()
        stop = threading.Event()

        def spam():
            while not stop.is_set():
                pf.update()
                pf.run_on_ui(lambda: None)

        spammers = [threading.Thread(target=spam) for _ in range(3)]
        for t in spammers:
            t.start()
        for _ in range(40):
            self.runner.scheduler.post(lambda: self.runner._handle_callback_event(event))
            time.sleep(0.002)
        stop.set()
        for t in spammers:
            t.join()
        time.sleep(0.2)
        self.assertFalse(app.overlap)
        self.assertGreater(app.builds, 0)

    def test_run_on_ui_runs_on_the_ui_thread(self):
        names = []
        pf.run_on_ui(lambda: names.append(threading.current_thread().name))
        self.assertTrue(wait_until(lambda: names))
        self.assertEqual(names, [UI_THREAD_NAME])

    def test_run_on_ui_without_an_application_just_calls(self):
        app_module.set_active_runner(None)
        names = []
        pf.run_on_ui(lambda: names.append(threading.current_thread().name))
        self.assertEqual(names, [threading.current_thread().name])

    def test_plugin_call_from_a_callback_gets_its_answer(self):
        answers = []
        from afik.core.widget_base import _register_callback

        def handler():
            answers.append(manager.call_plugin("local_auth", "authenticate", {}, timeout=2.0))

        callback_id = _register_callback(handler)
        event = type("E", (), {"callback_id": callback_id, "event_data": {}})()
        start = time.time()
        self.runner.scheduler.post(lambda: self.runner._handle_callback_event(event))
        self.assertTrue(wait_until(lambda: answers))
        self.assertEqual(answers, [{"ok": True}])
        self.assertLess(time.time() - start, 1.0)

    def test_resync_request_forces_a_full_tree(self):
        from afik.core.bridge import RESYNC_CALLBACK_ID
        event = type("E", (), {"callback_id": RESYNC_CALLBACK_ID, "event_data": {}})()
        self.runner.scheduler.post(lambda: self.runner._handle_callback_event(event))
        self.assertTrue(wait_until(lambda: self.session.sent))
        self.assertTrue(self.session.sent[0][1])


if __name__ == "__main__":
    unittest.main()
