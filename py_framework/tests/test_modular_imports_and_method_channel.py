"""
Unit tests for PyFlutter modular imports architecture and generic MethodChannel.
Verifies that:
1. Root `pyflutter` namespace is pure and unpolluted (no monolithic plugin dumping in __all__).
2. Plugins are imported modularly from `pyflutter.plugins.*`, including their dedicated widgets.
3. MethodChannel invokes platform methods, handles arguments, catches PlatformException,
   and enables mock handlers for offline unit testing.
"""

from __future__ import annotations

import unittest
import pyflutter as pf
from pyflutter.core.channel import (
    MethodChannel,
    EventChannel,
    MethodCall,
    PlatformException,
    set_mock_method_call_handler,
)


class TestModularImports(unittest.TestCase):
    def test_root_namespace_is_pure(self):
        """Root __all__ must not contain raw plugin classes."""
        self.assertNotIn("ImagePicker", pf.__all__)
        self.assertNotIn("CameraController", pf.__all__)
        self.assertNotIn("WebViewController", pf.__all__)
        self.assertNotIn("VideoPlayerController", pf.__all__)
        self.assertNotIn("Box", pf.__all__)
        self.assertNotIn("Database", pf.__all__)
        self.assertNotIn("FlutterLocalNotificationsPlugin", pf.__all__)
        self.assertNotIn("FlutterSecureStorage", pf.__all__)
        self.assertNotIn("LocalAuthentication", pf.__all__)

        # Platform communication channels must be present
        self.assertIn("MethodChannel", pf.__all__)
        self.assertIn("EventChannel", pf.__all__)
        self.assertIn("MethodCall", pf.__all__)
        self.assertIn("PlatformException", pf.__all__)

    def test_plugins_module_access(self):
        """Plugins are accessed under pyflutter.plugins."""
        from pyflutter.plugins import (
            image_picker,
            camera,
            connectivity,
            audioplayer,
            video_player,
            share,
            webview,
            chewie,
            hive,
            sqflite,
            local_notifications,
            permission_handler,
            secure_storage,
            local_auth,
            pdf,
        )
        self.assertTrue(hasattr(image_picker, "ImagePicker"))
        self.assertTrue(hasattr(camera, "CameraController"))
        self.assertTrue(hasattr(connectivity, "check_connectivity"))
        self.assertTrue(hasattr(audioplayer, "AudioPlayer"))
        self.assertTrue(hasattr(video_player, "VideoPlayerController"))
        self.assertTrue(hasattr(share, "share"))
        self.assertTrue(hasattr(webview, "WebViewController"))
        self.assertTrue(hasattr(chewie, "ChewieController"))
        self.assertTrue(hasattr(hive, "open_box"))
        self.assertTrue(hasattr(sqflite, "open_database"))
        self.assertTrue(hasattr(local_notifications, "FlutterLocalNotificationsPlugin"))
        self.assertTrue(hasattr(permission_handler, "check_permission"))
        self.assertTrue(hasattr(secure_storage, "FlutterSecureStorage"))
        self.assertTrue(hasattr(local_auth, "LocalAuthentication"))
        self.assertTrue(hasattr(pdf, "PdfDocument"))

    def test_plugin_dedicated_widgets_import(self):
        """Widgets tied to plugins are importable directly from their plugin module."""
        from pyflutter.plugins.camera import CameraPreview, CameraController
        from pyflutter.plugins.webview import WebView, WebViewController
        from pyflutter.plugins.video_player import VideoPlayer, VideoPlayerController
        from pyflutter.plugins.chewie import Chewie, ChewieController
        from pyflutter.plugins.pdf import SfPdfViewer, PdfView, PdfViewPinch, PDFView

        self.assertEqual(CameraPreview(CameraController("0")).widget_type, "CameraPreview")
        self.assertEqual(WebView("https://flutter.dev").widget_type, "WebView")
        self.assertEqual(VideoPlayer("video.mp4").widget_type, "VideoPlayer")
        self.assertEqual(SfPdfViewer.file("test.pdf").widget_type, "SfPdfViewer")
        self.assertEqual(PdfView("test.pdf").widget_type, "PdfView")
        self.assertEqual(PdfViewPinch("test.pdf").widget_type, "PdfViewPinch")
        self.assertEqual(PDFView("test.pdf").widget_type, "PDFView")

    def test_deprecated_root_fallback(self):
        """Accessing legacy root exports still resolves gracefully via __getattr__ without crashing."""
        self.assertIsNotNone(pf.ImagePicker)
        self.assertIsNotNone(pf.CameraController)
        self.assertIsNotNone(pf.CameraPreview)
        self.assertIsNotNone(pf.WebView)
        self.assertIsNotNone(pf.VideoPlayer)
        self.assertIsNotNone(pf.Chewie)
        self.assertIsNotNone(pf.SfPdfViewer)


class TestMethodChannel(unittest.TestCase):
    def setUp(self):
        set_mock_method_call_handler("test.channel/battery", None)
        set_mock_method_call_handler("test.channel/error", None)

    def tearDown(self):
        set_mock_method_call_handler("test.channel/battery", None)
        set_mock_method_call_handler("test.channel/error", None)

    def test_method_channel_init(self):
        channel = pf.MethodChannel("com.example.app/test")
        self.assertEqual(channel.name, "com.example.app/test")
        self.assertIn("com.example.app/test", repr(channel))

        with self.assertRaises(ValueError):
            pf.MethodChannel("")

    def test_invoke_method_with_mock_handler(self):
        received_calls = []

        def mock_battery_handler(call: MethodCall):
            received_calls.append(call)
            if call.method == "getBatteryLevel":
                return 88
            elif call.method == "isCharging":
                return True
            return None

        set_mock_method_call_handler("test.channel/battery", mock_battery_handler)
        channel = pf.MethodChannel("test.channel/battery")

        level = channel.invoke_method("getBatteryLevel")
        self.assertEqual(level, 88)

        charging = channel.invoke_method("isCharging", {"fast": True})
        self.assertTrue(charging)

        self.assertEqual(len(received_calls), 2)
        self.assertEqual(received_calls[0].method, "getBatteryLevel")
        self.assertEqual(received_calls[1].method, "isCharging")
        self.assertEqual(received_calls[1].arguments, {"fast": True})

    def test_platform_exception_handling(self):
        def mock_error_handler(call: MethodCall):
            return {
                "platform_error": {
                    "code": "BATTERY_NOT_AVAILABLE",
                    "message": "Device has no battery sensor",
                    "details": {"sensor_id": 0},
                }
            }

        set_mock_method_call_handler("test.channel/error", mock_error_handler)
        channel = pf.MethodChannel("test.channel/error")

        with self.assertRaises(PlatformException) as ctx:
            channel.invoke_method("getBatteryStatus")

        ex = ctx.exception
        self.assertEqual(ex.code, "BATTERY_NOT_AVAILABLE")
        self.assertEqual(ex.message, "Device has no battery sensor")
        self.assertEqual(ex.details, {"sensor_id": 0})
        self.assertIn("BATTERY_NOT_AVAILABLE", repr(ex))

    def test_event_channel(self):
        channel = pf.EventChannel("test.channel/events")
        self.assertEqual(channel.name, "test.channel/events")
        self.assertIn("test.channel/events", repr(channel))

        received = []
        channel.listen(lambda val: received.append(val))
        self.assertIsNotNone(channel._listener)

        channel.cancel()
        self.assertIsNone(channel._listener)


if __name__ == "__main__":
    unittest.main()
