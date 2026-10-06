"""
Unit tests for PyFlutter native plugins and RPC architecture.
Tests storage, path_provider, device_info, file_picker, and RPC dispatching.
"""

import json
import threading
import unittest

from pyflutter.plugins import (
    device_info,
    file_picker,
    path_provider,
    shared_preferences,
    storage,
)
from pyflutter.plugins.manager import (
    _pending_rpc_calls,
    _rpc_results,
    handle_plugin_response,
)


class TestPluginsStorage(unittest.TestCase):
    def setUp(self):
        storage.clear()

    def test_string_operations(self):
        self.assertIsNone(storage.get_string("test_key"))
        self.assertEqual(storage.get_string("test_key", default="fallback"), "fallback")

        success = storage.set_string("test_key", "hello_world")
        self.assertTrue(success)
        self.assertEqual(storage.get_string("test_key"), "hello_world")

    def test_int_operations(self):
        self.assertIsNone(storage.get_int("int_key"))
        storage.set_int("int_key", 42)
        self.assertEqual(storage.get_int("int_key"), 42)

    def test_bool_operations(self):
        self.assertIsNone(storage.get_bool("bool_key"))
        storage.set_bool("bool_key", True)
        self.assertTrue(storage.get_bool("bool_key"))
        storage.set_bool("bool_key", False)
        self.assertFalse(storage.get_bool("bool_key"))

    def test_double_operations(self):
        self.assertIsNone(storage.get_double("double_key"))
        storage.set_double("double_key", 3.14159)
        self.assertAlmostEqual(storage.get_double("double_key"), 3.14159, places=4)

    def test_remove_and_clear(self):
        storage.set_string("k1", "v1")
        storage.set_string("k2", "v2")
        self.assertEqual(len(storage.get_all()), 2)

        storage.remove("k1")
        self.assertIsNone(storage.get_string("k1"))
        self.assertEqual(storage.get_string("k2"), "v2")

        storage.clear()
        self.assertEqual(len(storage.get_all()), 0)

    def test_shared_preferences_alias(self):
        shared_preferences.set_string("pref_key", "pref_val")
        self.assertEqual(shared_preferences.get_string("pref_key"), "pref_val")
        self.assertEqual(storage.get_string("pref_key"), "pref_val")


class TestPluginsPathProvider(unittest.TestCase):
    def test_paths(self):
        docs = path_provider.get_app_documents_directory()
        self.assertIsInstance(docs, str)
        self.assertTrue(len(docs) > 0)

        temp = path_provider.get_temporary_directory()
        self.assertIsInstance(temp, str)
        self.assertTrue(len(temp) > 0)

        support = path_provider.get_app_support_directory()
        self.assertIsInstance(support, str)
        self.assertTrue(len(support) > 0)

        downloads = path_provider.get_downloads_directory()
        self.assertIsInstance(downloads, str)


class TestPluginsDeviceInfo(unittest.TestCase):
    def test_device_info(self):
        info = device_info.get_device_info()
        self.assertIsInstance(info, dict)
        self.assertIn("platform", info)
        self.assertIn("version", info)

        platform = device_info.get_platform()
        self.assertIsInstance(platform, str)
        self.assertTrue(len(platform) > 0)


class TestPluginsFilePicker(unittest.TestCase):
    def test_file_picker_fallback(self):
        res = file_picker.pick_files(allow_multiple=False)
        self.assertIsInstance(res, list)


class TestPluginRPCResponseHandling(unittest.TestCase):
    def test_handle_plugin_response_success(self):
        call_id = "test_call_123"
        evt = threading.Event()
        _pending_rpc_calls[call_id] = evt

        payload = json.dumps({
            "call_id": call_id,
            "result": {"status": "ok", "value": 999},
            "error": None,
        }).encode("utf-8")

        handle_plugin_response(payload)

        self.assertTrue(evt.is_set())
        res, err = _rpc_results.pop(call_id, (None, None))
        self.assertEqual(res, {"status": "ok", "value": 999})
        self.assertIsNone(err)

    def test_handle_plugin_response_error(self):
        call_id = "test_call_err"
        evt = threading.Event()
        _pending_rpc_calls[call_id] = evt

        payload = json.dumps({
            "call_id": call_id,
            "result": None,
            "error": "PluginMethodNotImplemented",
        }).encode("utf-8")

        handle_plugin_response(payload)

        self.assertTrue(evt.is_set())
        res, err = _rpc_results.pop(call_id, (None, None))
        self.assertIsNone(res)
        self.assertEqual(err, "PluginMethodNotImplemented")


if __name__ == "__main__":
    unittest.main()
