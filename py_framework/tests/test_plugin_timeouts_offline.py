"""T-08: per-plugin timeouts, explicit offline simulation, wake-up of waiting calls."""

from __future__ import annotations

import os
import threading
import time
import unittest
from unittest.mock import patch

from pyflutter.plugins import manager
from tests.test_audit_regressions import _FakeRunner  # silent / error / ok fake bridge


class TestTimeoutTable(unittest.TestCase):
    def test_interactive_calls_wait_for_the_person(self):
        for plugin, method in [
            ("local_auth", "authenticate"), ("permission_handler", "requestPermission"),
            ("file_picker", "pickFiles"), ("image_picker", "pickImage"),
            ("share_plus", "share"), ("printing", "printPdf"), ("camera", "initialize"),
        ]:
            self.assertEqual(manager.timeout_for(plugin, method), manager.INTERACTIVE_TIMEOUT, (plugin, method))

    def test_slow_and_ordinary_calls(self):
        self.assertEqual(manager.timeout_for("camera", "takePicture"), 30.0)
        self.assertEqual(manager.timeout_for("pdfx", "renderPage"), 30.0)      # plugin-wide entry
        self.assertEqual(manager.timeout_for("video_player", "initialize"), 60.0)
        self.assertEqual(manager.timeout_for("shared_preferences", "getString"), manager.DEFAULT_TIMEOUT)
        self.assertEqual(manager.timeout_for("local_auth", "isDeviceSupported"), manager.DEFAULT_TIMEOUT)

    def test_call_plugin_uses_the_table_unless_a_timeout_is_given(self):
        waits = []

        class Spy(threading.Event):
            def wait(self, timeout=None):
                waits.append(timeout)
                return True

        with patch.object(manager.threading, "Event", Spy), \
                patch.object(manager, "get_active_runner", return_value=_FakeRunner("ok")):
            manager.call_plugin("local_auth", "authenticate", {})
            manager.call_plugin("local_auth", "authenticate", {}, timeout=1.5)
            manager.call_plugin("url_launcher", "canLaunch", {})
        self.assertEqual(waits, [manager.INTERACTIVE_TIMEOUT, 1.5, manager.DEFAULT_TIMEOUT])


class TestOfflineSimulation(unittest.TestCase):
    def setUp(self):
        self._env = os.environ.pop("PYFLUTTER_ALLOW_INSECURE_MOCKS", None)
        manager._offline_warned.clear()

    def tearDown(self):
        if self._env is not None:
            os.environ["PYFLUTTER_ALLOW_INSECURE_MOCKS"] = self._env
        else:
            os.environ.pop("PYFLUTTER_ALLOW_INSECURE_MOCKS", None)

    def _offline(self):
        return patch.object(manager, "get_active_runner", return_value=None)

    def test_security_plugins_refuse_without_a_runtime(self):
        with self._offline():
            for plugin, method in [
                ("local_auth", "authenticate"), ("local_auth", "isDeviceSupported"),
                ("permission_handler", "requestPermission"), ("permission_handler", "checkPermission"),
                ("flutter_secure_storage", "write"), ("flutter_secure_storage", "read"),
            ]:
                with self.assertRaises(manager.PluginError, msg=(plugin, method)):
                    manager.call_plugin(plugin, method, {})

    def test_the_environment_variable_allows_the_simulation(self):
        os.environ["PYFLUTTER_ALLOW_INSECURE_MOCKS"] = "1"
        with self._offline():
            self.assertEqual(manager.call_plugin("local_auth", "authenticate", {}), {"authenticated": True})

    def test_first_call_of_a_simulated_plugin_warns_once(self):
        with self._offline(), patch.object(manager.logger, "warning") as warning:
            manager.call_plugin("connectivity_plus", "checkConnectivity", {})
            manager.call_plugin("connectivity_plus", "checkConnectivity", {})
            manager.call_plugin("device_info_plus", "getDeviceInfo", {})
        self.assertEqual(warning.call_count, 2)
        self.assertIn("connectivity_plus", warning.call_args_list[0].args[1:])

    def test_real_local_answers_do_not_warn(self):
        with self._offline(), patch.object(manager.logger, "warning") as warning:
            manager.call_plugin("path_provider", "getTemporaryDirectory", {})
        warning.assert_not_called()

    def test_a_connected_runtime_never_uses_the_simulation(self):
        with patch.object(manager, "get_active_runner", return_value=_FakeRunner("error")):
            with self.assertRaises(manager.PluginError):
                manager.call_plugin("local_auth", "authenticate", {})


class TestCancelPendingCalls(unittest.TestCase):
    def test_waiting_calls_wake_up_when_the_bridge_closes(self):
        errors = []

        def waiter():
            try:
                manager.call_plugin("local_auth", "authenticate", {})
            except manager.PluginError as e:
                errors.append(str(e))

        with patch.object(manager, "get_active_runner", return_value=_FakeRunner("silent")):
            thread = threading.Thread(target=waiter)
            thread.start()
            deadline = time.time() + 2
            while not manager._pending_rpc_calls and time.time() < deadline:
                time.sleep(0.01)
            started = time.time()
            manager.cancel_pending_calls("bridge closed")
            thread.join(2)
        self.assertFalse(thread.is_alive())
        self.assertLess(time.time() - started, 1.0)       # not the 120 s of the interactive wait
        self.assertEqual(len(errors), 1)
        self.assertIn("bridge closed", errors[0])
        self.assertEqual(manager._pending_rpc_calls, {})


if __name__ == "__main__":
    unittest.main()
