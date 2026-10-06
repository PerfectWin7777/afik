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
            res = manager.call_plugin("connectivity_plus", "checkConnectivity", {})
            self.assertEqual(res, {"status": "wifi", "results": ["wifi"]})


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


class TestSqflite(unittest.TestCase):
    def test_real_rows_and_identifier_validation(self):
        from pyflutter.plugins import sqflite
        db = sqflite.open_database(":memory:")
        db.execute("CREATE TABLE items (id INTEGER PRIMARY KEY, name TEXT)")
        self.assertEqual(db.insert("items", {"name": "a"}), 1)
        self.assertEqual(db.insert("items", {"name": "b"}), 2)
        self.assertEqual([r["name"] for r in db.query("items", order_by="id")], ["a", "b"])
        with self.assertRaises(ValueError):
            db.insert("items; DROP TABLE items", {"name": "x"})
        with self.assertRaises(Exception):
            db.insert("missing_table", {"name": "x"})


class TestSecurityPluginsRefuseByDefault(unittest.TestCase):
    """A missing, unknown or malformed platform answer must never read as a success."""

    BAD_ANSWERS = [None, {}, "ok", [], {"authenticated": "true"}, {"status": "weird"}]

    def _with_answer(self, answer):
        return patch("pyflutter.plugins.manager.call_plugin", return_value=answer)

    def test_local_auth_refuses(self):
        from pyflutter.plugins import local_auth
        for answer in self.BAD_ANSWERS:
            with patch.object(local_auth, "call_plugin", return_value=answer):
                auth = local_auth.LocalAuthentication()
                self.assertFalse(auth.authenticate("why"), answer)
                self.assertFalse(auth.can_check_biometrics(), answer)
                self.assertFalse(auth.is_device_supported(), answer)
                self.assertFalse(auth.stop_authentication(), answer)
                self.assertEqual(auth.get_available_biometrics(), [], answer)

    def test_local_auth_accepts_only_explicit_true(self):
        from pyflutter.plugins import local_auth
        with patch.object(local_auth, "call_plugin", return_value={"authenticated": True}):
            self.assertTrue(local_auth.LocalAuthentication().authenticate("why"))
        # the wait for the person is decided by the central table
        self.assertEqual(manager.timeout_for("local_auth", "authenticate"), manager.INTERACTIVE_TIMEOUT)

    def test_permission_handler_refuses(self):
        from pyflutter.plugins import permission_handler as ph
        for answer in self.BAD_ANSWERS:
            with patch.object(ph, "call_plugin", return_value=answer):
                self.assertEqual(ph.check_permission("camera"), ph.PermissionStatus.DENIED, answer)
                self.assertEqual(ph.request_permission(ph.Permission.CAMERA), ph.PermissionStatus.DENIED, answer)
                self.assertFalse(ph.open_app_settings(), answer)

    def test_permission_handler_reads_real_statuses(self):
        from pyflutter.plugins import permission_handler as ph
        for raw, expected in (("granted", ph.PermissionStatus.GRANTED),
                              ("permanentlyDenied", ph.PermissionStatus.PERMANENTLY_DENIED),
                              ("limited", ph.PermissionStatus.LIMITED)):
            with patch.object(ph, "call_plugin", return_value={"status": raw}):
                self.assertEqual(ph.check_permission("camera"), expected)

    def test_secure_storage_refuses(self):
        from pyflutter.plugins import flutter_secure_storage as fss
        for answer in self.BAD_ANSWERS:
            with patch.object(fss, "call_plugin", return_value=answer):
                vault = fss.FlutterSecureStorage()
                self.assertFalse(vault.write("k", "v"), answer)
                self.assertFalse(vault.delete("k"), answer)
                self.assertFalse(vault.delete_all(), answer)


class TestHiveBoxesPersist(unittest.TestCase):
    def setUp(self):
        import shutil
        import tempfile
        from pyflutter.plugins import hive
        self.hive = hive
        self.dir = tempfile.mkdtemp()
        hive.init(self.dir)
        self.addCleanup(shutil.rmtree, self.dir, ignore_errors=True)
        self.addCleanup(hive._opened_boxes.clear)

    def test_values_survive_closing_and_reopening(self):
        box = self.hive.open_box("prefs")
        box.put("user", {"name": "ada", "tags": [1, 2]})
        box.close()
        again = self.hive.open_box("prefs")
        self.assertEqual(again.get("user"), {"name": "ada", "tags": [1, 2]})

    def test_non_serialisable_value_is_rejected_and_box_untouched(self):
        box = self.hive.open_box("prefs")
        box.put("a", 1)
        with self.assertRaises(TypeError):
            box.put("b", object())
        self.assertEqual(box.get_all(), {"a": 1})

    def test_missing_keys_and_closed_box(self):
        box = self.hive.open_box("prefs")
        self.assertIsNone(box.get("nope"))
        self.assertFalse(box.delete("nope"))
        with self.assertRaises(KeyError):
            box["nope"]
        box.close()
        with self.assertRaises(ValueError):
            box.get("x")

    def test_contains_key_is_true_for_stored_none(self):
        box = self.hive.open_box("prefs")
        box.put("k", None)
        self.assertIn("k", box)
