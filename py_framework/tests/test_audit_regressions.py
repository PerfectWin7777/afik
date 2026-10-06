"""Regression tests for bugs found during the framework audit."""

from __future__ import annotations

import json
import queue
import struct
import threading
import time
import unittest
from unittest.mock import patch

import pyflutter as pf
from pyflutter.core import widget_base as wb
from pyflutter.core.render import (
    assign_node_ids,
    diff_snapshots,
    resolve_tree,
    widget_to_snapshot,
)
from pyflutter.plugins import manager


class _FakeStdin:
    def __init__(self, inbox: "queue.Queue", mode: str):
        self.inbox, self.mode = inbox, mode

    def write(self, data: bytes) -> None:
        msg_type, length = struct.unpack(">BI", data[:5])
        if msg_type != 0x03:
            return
        _, _, call_id, _ = data[5:5 + length].decode().split("\x00", 3)
        if self.mode == "silent":
            return
        body = {"call_id": call_id, "result": {"ok": True}, "error": None}
        if self.mode == "error":
            body = {"call_id": call_id, "result": None, "error": "boom"}
        manager.handle_plugin_response(json.dumps(body).encode())

    def flush(self) -> None:
        pass


class _FakeRunner:
    def __init__(self, mode: str):
        inbox: "queue.Queue" = queue.Queue()
        self.is_running = True
        self._event_thread = None
        self.session = type("S", (), {"process": type("P", (), {"stdin": _FakeStdin(inbox, mode)})()})()


class TestPluginRpc(unittest.TestCase):
    def _with_runner(self, mode):
        return patch.object(manager, "get_active_runner", return_value=_FakeRunner(mode))

    def test_dart_answer_is_returned(self):
        with self._with_runner("ok"):
            self.assertEqual(manager.call_plugin("local_auth", "authenticate", {}), {"ok": True})

    def test_dart_error_is_raised_not_replaced_by_fallback(self):
        with self._with_runner("error"):
            with self.assertRaises(manager.PluginError):
                manager.call_plugin("local_auth", "authenticate", {})

    def test_timeout_raises_instead_of_simulating_success(self):
        with self._with_runner("silent"):
            with self.assertRaises(manager.PluginTimeoutError):
                manager.call_plugin("local_auth", "authenticate", {}, timeout=0.05)

    def test_fire_and_forget_does_not_wait(self):
        with self._with_runner("silent"):
            start = time.time()
            manager.invoke_plugin_method("overlay", "show_snack_bar", {"message": "x"})
            self.assertLess(time.time() - start, 0.5)

    def test_offline_fallback_still_works_without_runtime(self):
        with patch.object(manager, "get_active_runner", return_value=None):
            self.assertEqual(manager.call_plugin("local_auth", "authenticate", {}), {"authenticated": True})


class TestPinnedCallbacks(unittest.TestCase):
    def test_pinned_callback_survives_sweeps_and_is_one_shot(self):
        fired = []
        wb._register_pinned_callback("pin_a", lambda: fired.append("a"), group="g")
        wb._register_pinned_callback("pin_b", lambda: fired.append("b"), group="g")
        for _ in range(3):
            wb.sweep_stale_callbacks(set())
        wb.invoke_callback("pin_a", {})
        wb.invoke_callback("pin_b", {})  # same group: already discarded
        self.assertEqual(fired, ["a"])


class TestTreeResolution(unittest.TestCase):
    def test_cached_layout_keeps_rebuilding_components(self):
        class Badge(pf.Component):
            count = 0

            def build(self):
                Badge.count += 1
                return pf.Text(f"build#{Badge.count}")

        layout = pf.Column()
        layout.add_widget(Badge())
        first = resolve_tree(layout).children[0].props["text"]
        second = resolve_tree(layout).children[0].props["text"]
        self.assertNotEqual(first, second)
        self.assertIsInstance(layout.children[0], Badge)

    def test_keyed_reorder_forces_full_tree(self):
        def snap(keys):
            tree = pf.Column([pf.Text(k.upper(), key=k) for k in keys])
            assign_node_ids(tree)
            return widget_to_snapshot(tree)

        self.assertIsNone(diff_snapshots(snap(["a", "b"]), snap(["b", "a"])))

    def test_stateful_keys_independent_of_user_file_name(self):
        class S(pf.State):
            def build(self):
                return pf.Text("x")

        class W(pf.StatefulComponent):
            def create_state(self):
                return S()

        a, b = W(), W()
        self.assertNotEqual(a.key, b.key)


class TestWatchListeners(unittest.TestCase):
    def test_dead_watch_listeners_are_removed_on_next_change(self):
        sig = pf.Signal(0, auto_update=False)
        for _ in range(20):
            resolve_tree(pf.Watch(lambda: pf.Text(str(sig.value))))
        import gc
        gc.collect()
        sig.value = 1
        self.assertLessEqual(len(sig._listeners), 1)


class TestErrorLogging(unittest.TestCase):
    def test_braces_in_exception_message_do_not_break_callback_error_handling(self):
        def bad():
            raise KeyError("{id}")

        wb._callback_registry["bad_cb"] = bad
        wb.invoke_callback("bad_cb", {})  # must not raise


class TestConfigRobustness(unittest.TestCase):
    def _load(self, text):
        import pathlib
        import tempfile
        from pyflutter.core.config import PyFlutterConfig
        path = pathlib.Path(tempfile.mkdtemp()) / "pyflutter.yaml"
        path.write_text(text)
        return PyFlutterConfig.from_file(path)

    def test_null_sections_and_bad_values_do_not_crash(self):
        self.assertEqual(self._load("dependencies:\n").flutter_dependencies, {})
        self.assertEqual(self._load("- a\n- b\n").name, "pyflutter_app")
        self.assertEqual(self._load("pyflutter:\n  port: abc\n").port, 7879)


class TestBuildFlags(unittest.TestCase):
    def test_release_flag_is_honoured(self):
        from pyflutter.cli import main as cli

        captured = {}

        class FakeBuilder:
            def __init__(self, **kwargs):
                captured.update(kwargs)

            def build(self):
                return True

        with patch("pyflutter.cli.builder.PyFlutterBuilder", FakeBuilder):
            with self.assertRaises(SystemExit):
                cli.main(["build", "apk", "--release"])
        self.assertTrue(captured["release"])

    def test_remove_command_target_exists(self):
        from pyflutter.plugins.manager import remove_flutter_package
        self.assertTrue(callable(remove_flutter_package))


if __name__ == "__main__":
    unittest.main()
