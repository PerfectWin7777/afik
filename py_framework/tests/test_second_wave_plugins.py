"""
Unit tests for the second wave of essential Flutter packages:
- chewie
- hive
- sqflite
- flutter_local_notifications
- permission_handler
- flutter_secure_storage
- local_auth
"""

import os
import unittest

import pyflutter as pf
from pyflutter.plugins import (
    chewie,
    hive,
    sqflite,
    local_notifications,
    flutter_local_notifications,
    permission_handler,
    secure_storage,
    flutter_secure_storage,
    local_auth,
    video_player,
)


_previous_mock_setting = os.environ.get("PYFLUTTER_ALLOW_INSECURE_MOCKS")


def setUpModule():
    # These tests exercise the offline simulation of the security plugins, which is refused
    # by default (see tests/test_plugin_timeouts_offline.py).
    os.environ["PYFLUTTER_ALLOW_INSECURE_MOCKS"] = "1"


def tearDownModule():
    if _previous_mock_setting is None:
        os.environ.pop("PYFLUTTER_ALLOW_INSECURE_MOCKS", None)
    else:
        os.environ["PYFLUTTER_ALLOW_INSECURE_MOCKS"] = _previous_mock_setting


class TestChewiePluginAndWidget(unittest.TestCase):
    def test_chewie_controller(self):
        vctrl = video_player.VideoPlayerController.network("https://example.com/stream.mp4")
        cctrl = chewie.ChewieController(
            vctrl,
            auto_play=True,
            looping=True,
            aspect_ratio=16 / 9,
        )
        self.assertTrue(cctrl.auto_play)
        self.assertTrue(cctrl.looping)
        self.assertTrue(cctrl.enter_full_screen())
        self.assertTrue(cctrl.is_full_screen)
        self.assertTrue(cctrl.exit_full_screen())
        self.assertFalse(cctrl.is_full_screen)
        cctrl.dispose()

    def test_chewie_widget(self):
        vctrl = video_player.VideoPlayerController.file("film.mp4")
        cctrl = chewie.ChewieController(vctrl)
        w = pf.Chewie(cctrl, width=400, height=225)
        self.assertEqual(w.widget_type, "Chewie")
        self.assertEqual(w.props["url"], "film.mp4")
        self.assertEqual(float(w.props["width"]), 400)

        # Signal connection
        called = []
        w.event.connect(lambda data: called.append(data))
        self.assertTrue(hasattr(w, "_event_signal"))


class TestHivePlugin(unittest.TestCase):
    def setUp(self):
        import tempfile
        self._dir = tempfile.mkdtemp()
        hive.init(self._dir)

    def tearDown(self):
        import shutil
        hive._opened_boxes.clear()
        shutil.rmtree(self._dir, ignore_errors=True)

    def test_hive_box_operations(self):
        box = hive.open_box("settings")
        self.assertTrue(box.is_open)

        box.put("theme", "dark")
        self.assertEqual(box.get("theme"), "dark")
        self.assertTrue(box.contains_key("theme"))

        # Dict syntax
        box["volume"] = 80
        self.assertEqual(box["volume"], 80)
        self.assertIn("volume", box)

        self.assertIn("theme", box.keys())
        self.assertEqual(len(box.get_all()), 2)

        del box["theme"]
        self.assertNotIn("theme", box)

        box.clear()
        self.assertEqual(len(box.get_all()), 0)
        box.close()


class TestSqflitePlugin(unittest.TestCase):
    def test_sqflite_database_crud(self):
        db = sqflite.open_database(":memory:")
        self.assertTrue(db.execute("CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT, email TEXT)"))

        row_id = db.insert("users", {"name": "Alice", "email": "alice@example.com"})
        self.assertGreaterEqual(row_id, 1)

        users = db.query("users")
        self.assertIsInstance(users, list)
        self.assertTrue(any(u.get("name") == "Alice" for u in users))

        updated = db.update("users", {"name": "Alice Cooper"}, where="name = ?", where_args=["Alice"])
        self.assertGreaterEqual(updated, 1)

        deleted = db.delete("users", where="name = ?", where_args=["Alice Cooper"])
        self.assertGreaterEqual(deleted, 1)

        db.close()


class TestLocalNotificationsPlugin(unittest.TestCase):
    def test_notifications_lifecycle(self):
        self.assertTrue(local_notifications.initialize())

        shown = local_notifications.show(
            101,
            title="Download Complete",
            body="Your file is ready to view.",
            payload="/downloads/file.pdf",
        )
        self.assertTrue(shown)

        active = local_notifications.get_active_notifications()
        self.assertIsInstance(active, list)

        self.assertTrue(local_notifications.cancel(101))
        self.assertTrue(local_notifications.cancel_all())

    def test_alias(self):
        plugin = flutter_local_notifications.FlutterLocalNotificationsPlugin()
        self.assertTrue(plugin.initialize())


class TestPermissionHandlerPlugin(unittest.TestCase):
    def test_check_and_request_permissions(self):
        status = permission_handler.check_permission(permission_handler.Permission.CAMERA)
        self.assertIsInstance(status, permission_handler.PermissionStatus)
        self.assertTrue(status.is_granted)

        req_status = permission_handler.request_permission(permission_handler.Permission.LOCATION)
        self.assertIsInstance(req_status, permission_handler.PermissionStatus)
        self.assertTrue(req_status.is_granted)

        self.assertTrue(permission_handler.open_app_settings())


class TestSecureStoragePlugin(unittest.TestCase):
    def test_secure_storage_crud(self):
        vault = secure_storage.FlutterSecureStorage()
        vault.delete_all()

        self.assertIsNone(vault.read("auth_token"))
        self.assertFalse(vault.contains_key("auth_token"))

        self.assertTrue(vault.write("auth_token", "super_secret_jwt_token"))
        self.assertEqual(vault.read("auth_token"), "super_secret_jwt_token")
        self.assertTrue(vault.contains_key("auth_token"))

        all_keys = vault.read_all()
        self.assertIn("auth_token", all_keys)
        self.assertEqual(all_keys["auth_token"], "super_secret_jwt_token")

        self.assertTrue(vault.delete("auth_token"))
        self.assertIsNone(vault.read("auth_token"))

    def test_alias(self):
        vault = flutter_secure_storage.FlutterSecureStorage()
        self.assertIsNotNone(vault)


class TestLocalAuthPlugin(unittest.TestCase):
    def test_biometrics_authentication(self):
        auth = local_auth.LocalAuthentication()
        self.assertTrue(auth.can_check_biometrics())
        self.assertTrue(auth.is_device_supported())

        biometrics = auth.get_available_biometrics()
        self.assertIsInstance(biometrics, list)
        self.assertTrue(len(biometrics) > 0)

        authenticated = auth.authenticate("Please authenticate to access your bank account")
        self.assertTrue(authenticated)

        self.assertTrue(auth.stop_authentication())


if __name__ == "__main__":
    unittest.main()
