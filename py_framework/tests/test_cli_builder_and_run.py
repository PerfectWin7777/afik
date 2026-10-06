"""
Unit tests for PyFlutter CLI Builder and pf.run() build parameters.
Verifies target defaults (apk debug), mode flags, and canonical plugin naming.
"""

from __future__ import annotations

import sys
import unittest
from unittest.mock import patch

import pyflutter as pf
from pyflutter.cli.builder import PyFlutterBuilder
from pyflutter.cli.main import parse_args
from pyflutter.plugins import (
    audioplayer,
    audioplayers,
    connectivity,
    connectivity_plus,
    device_info,
    device_info_plus,
    flutter_local_notifications,
    flutter_pdfview,
    flutter_secure_storage,
    local_notifications,
    pdfx,
    printing,
    secure_storage,
    share,
    share_plus,
    shared_preferences,
    storage,
    syncfusion_flutter_pdfviewer,
    syncfusion_pdfviewer,
    webview,
    webview_flutter,
)


class TestCliBuilderAndRun(unittest.TestCase):
    def test_builder_defaults(self):
        """Default target must be 'apk' and default mode must be debug (release=False)."""
        builder = PyFlutterBuilder()
        self.assertEqual(builder.target, "apk")
        self.assertFalse(builder.release)  # Debug by default

    def test_builder_target_normalization(self):
        """Target aliases like 'bundle' or 'ios' normalize correctly."""
        b_bundle = PyFlutterBuilder(target="bundle")
        self.assertEqual(b_bundle.target, "appbundle")

        b_ios = PyFlutterBuilder(target="ios")
        self.assertEqual(b_ios.target, "ipa")

        b_win = PyFlutterBuilder(target="windows", release=True)
        self.assertEqual(b_win.target, "windows")
        self.assertTrue(b_win.release)

    def test_cli_parse_args_defaults(self):
        """CLI `pyflutter build` defaults to target='apk' and debug mode."""
        args = parse_args(["build"])
        self.assertEqual(args.target, "apk")
        self.assertFalse(args.release)
        self.assertFalse(args.profile)
        self.assertFalse(args.release)

    def test_cli_parse_args_release(self):
        """CLI `pyflutter build appbundle --release` parses target and release."""
        args = parse_args(["build", "appbundle", "--release"])
        self.assertEqual(args.target, "appbundle")
        self.assertTrue(args.release)

    @patch.object(PyFlutterBuilder, "build", return_value=True)
    def test_run_with_build_param(self, mock_build):
        """Calling pf.run(App(), build='apk', mode='debug') invokes the builder."""
        class DummyApp:
            def build(self):
                return pf.Text("test")

        res = pf.run(DummyApp(), build="apk", mode="debug")
        self.assertTrue(res)
        mock_build.assert_called_once()

    @patch.object(PyFlutterBuilder, "build", return_value=True)
    def test_run_cli_forwarding_build(self, mock_build):
        """`python main.py build apk --debug` forwards automatically into builder."""
        class DummyApp:
            def build(self):
                return pf.Text("test")

        original_argv = sys.argv
        try:
            sys.argv = ["main.py", "build", "apk", "--debug"]
            res = pf.run(DummyApp())
            self.assertTrue(res)
            mock_build.assert_called_once()
        finally:
            sys.argv = original_argv

    def test_canonical_plugin_equivalences(self):
        """Verify that every pub.dev package has a matching canonical Python module and alias."""
        # Audio
        self.assertIs(audioplayers.AudioPlayer, audioplayer.AudioPlayer)
        # Connectivity
        self.assertIs(connectivity_plus.ConnectivityResult, connectivity.ConnectivityResult)
        # Share
        self.assertIs(share_plus.share, share.share)
        # WebView
        self.assertIs(webview_flutter.WebViewController, webview.WebViewController)
        # Notifications
        self.assertIs(flutter_local_notifications.FlutterLocalNotificationsPlugin, local_notifications.FlutterLocalNotificationsPlugin)
        # Secure Storage
        self.assertIs(flutter_secure_storage.FlutterSecureStorage, secure_storage.FlutterSecureStorage)
        # Storage
        self.assertIs(shared_preferences.set_string, storage.set_string)
        # Device Info
        self.assertIs(device_info_plus.get_device_info, device_info.get_device_info)
        # Syncfusion PDF
        self.assertIs(syncfusion_flutter_pdfviewer.SfPdfViewer, syncfusion_pdfviewer.SfPdfViewer)
        # PDFX
        self.assertTrue(hasattr(pdfx, "PdfDocument"))
        # Printing
        self.assertTrue(hasattr(printing, "Printing"))
        # Flutter PDFView
        self.assertTrue(hasattr(flutter_pdfview, "PDFView"))


if __name__ == "__main__":
    unittest.main()
