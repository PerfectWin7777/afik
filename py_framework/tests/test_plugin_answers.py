"""Plugin wrappers must never turn a missing or malformed platform answer into a success."""

from __future__ import annotations

import unittest
from unittest.mock import patch

from afik.plugins import (
    audioplayers,
    camera,
    chewie,
    connectivity_plus,
    flutter_local_notifications,
    image_picker,
    pdfx,
    printing,
    share_plus,
    video_player,
    webview_flutter,
)
from afik.plugins.manager import PluginError

BAD = [None, {}, "ok", [], {"success": "true"}]


class _Patched:
    """Makes every call_plugin of ``module`` answer ``answer``."""

    def __init__(self, module, answer):
        self.patch = patch.object(module, "call_plugin", return_value=answer)

    def __enter__(self):
        return self.patch.__enter__()

    def __exit__(self, *exc):
        return self.patch.__exit__(*exc)


class TestWrappersRefuseBadAnswers(unittest.TestCase):
    def test_share(self):
        for answer in BAD:
            with _Patched(share_plus, answer):
                self.assertFalse(share_plus.share("x"), answer)
                self.assertFalse(share_plus.share_files(["a"]), answer)
                self.assertFalse(share_plus.share_uri("https://x"), answer)

    def test_share_is_true_only_when_the_user_picked_a_target(self):
        with _Patched(share_plus, {"success": False, "status": "dismissed"}):
            self.assertFalse(share_plus.share("x"))
        with _Patched(share_plus, {"success": True, "status": "success"}):
            self.assertTrue(share_plus.share("x"))

    def test_connectivity_reads_offline_on_bad_answer(self):
        for answer in BAD:
            with _Patched(connectivity_plus, answer):
                self.assertEqual(connectivity_plus.check_connectivity(), connectivity_plus.ConnectivityResult.NONE, answer)
                self.assertFalse(connectivity_plus.is_connected(), answer)

    def test_connectivity_multiple_results(self):
        with _Patched(connectivity_plus, {"status": "wifi", "results": ["wifi", "vpn"]}):
            self.assertEqual(
                connectivity_plus.check_connectivity_all(),
                [connectivity_plus.ConnectivityResult.WIFI, connectivity_plus.ConnectivityResult.VPN],
            )
        with _Patched(connectivity_plus, {"status": "none", "results": []}):
            self.assertFalse(connectivity_plus.is_connected())

    def test_notifications(self):
        plugin = flutter_local_notifications.FlutterLocalNotificationsPlugin()
        for answer in BAD:
            with _Patched(flutter_local_notifications, answer):
                self.assertFalse(plugin.initialize(), answer)
                self.assertFalse(plugin.show(1, "t", "b"), answer)
                self.assertFalse(plugin.cancel(1), answer)
                self.assertFalse(plugin.cancel_all(), answer)

    def test_audio(self):
        player = audioplayers.AudioPlayer("p")
        for answer in BAD:
            with _Patched(audioplayers, answer):
                self.assertFalse(player.play("http://x/a.mp3"), answer)
                self.assertFalse(player.pause(), answer)
                self.assertFalse(player.resume(), answer)
                self.assertFalse(player.stop(), answer)
                self.assertFalse(player.seek(1.0), answer)
                self.assertFalse(player.set_volume(0.5), answer)
                self.assertIsNone(player.get_duration(), answer)
                self.assertIsNone(player.get_position(), answer)

    def test_audio_state_follows_the_platform(self):
        player = audioplayers.AudioPlayer("p")
        with _Patched(audioplayers, {"state": "playing"}):
            self.assertTrue(player.play("http://x/a.mp3"))
            self.assertEqual(player.state, audioplayers.PlayerState.PLAYING)
        with _Patched(audioplayers, {"state": "paused"}):
            self.assertFalse(player.play("http://x/a.mp3"))  # asked to play, platform says paused

    def test_camera(self):
        for answer in BAD:
            with _Patched(camera, answer):
                self.assertEqual(camera.available_cameras(), [], answer)
                controller = camera.CameraController("0")
                self.assertFalse(controller.initialize(), answer)
                self.assertFalse(controller.is_initialized, answer)
                self.assertIsNone(controller.take_picture(), answer)
                self.assertFalse(controller.start_video_recording(), answer)
                self.assertFalse(controller.is_recording(), answer)
                self.assertFalse(controller.set_flash_mode("off"), answer)
                self.assertIsNone(controller.set_zoom_level(2.0), answer)

    def test_video_player_refuses_creation_without_confirmation(self):
        for answer in BAD:
            with _Patched(video_player, answer):
                with self.assertRaises(PluginError):
                    video_player.VideoPlayerController.network("http://x/v.mp4")

    def test_video_player_controls(self):
        with _Patched(video_player, {"created": True}):
            controller = video_player.VideoPlayerController.network("http://x/v.mp4")
        for answer in BAD:
            with _Patched(video_player, answer):
                self.assertFalse(controller.initialize(), answer)
                self.assertFalse(controller.play(), answer)
                self.assertFalse(controller.pause(), answer)
                self.assertFalse(controller.seek_to(1.0), answer)
                self.assertFalse(controller.set_volume(1.0), answer)
                self.assertFalse(controller.set_looping(True), answer)
        self.assertIsNone(controller.duration)
        with _Patched(video_player, {"initialized": True, "duration": 12.5, "aspectRatio": 1.5}):
            self.assertTrue(controller.initialize())
            self.assertEqual(controller.duration, 12.5)
        with _Patched(video_player, {"isPlaying": True}):
            self.assertTrue(controller.play())
            self.assertFalse(controller.pause())  # platform says it is still playing

    def test_chewie_requires_confirmation(self):
        with _Patched(video_player, {"created": True}):
            video = video_player.VideoPlayerController.network("http://x/v.mp4")
        for answer in BAD:
            with _Patched(chewie, answer):
                with self.assertRaises(PluginError):
                    chewie.ChewieController(video)

    def test_webview(self):
        controller = webview_flutter.WebViewController("about:blank", view_id="w")
        for answer in BAD:
            with _Patched(webview_flutter, answer):
                self.assertFalse(controller.load_url("https://x"), answer)
                self.assertFalse(controller.load_html("<p/>"), answer)
                self.assertFalse(controller.reload(), answer)
                self.assertFalse(controller.go_back(), answer)
                self.assertFalse(controller.go_forward(), answer)
                self.assertFalse(controller.can_go_back(), answer)
                self.assertFalse(controller.can_go_forward(), answer)

    def test_printing(self):
        for answer in BAD:
            with _Patched(printing, answer):
                self.assertFalse(printing.Printing.print_pdf("a.pdf"), answer)
                self.assertFalse(printing.Printing.share_pdf("a.pdf"), answer)
                self.assertFalse(printing.Printing.layout_pdf("a.pdf"), answer)

    def test_pdfx_does_not_invent_documents(self):
        for answer in BAD:
            with _Patched(pdfx, answer):
                with self.assertRaises(PluginError):
                    pdfx.PdfDocument.open_file("a.pdf")
        document = pdfx.PdfDocument("doc_1", 3, "a.pdf")
        for answer in BAD:
            with _Patched(pdfx, answer):
                with self.assertRaises(PluginError):
                    document.render_page(1)
                self.assertFalse(document.close(), answer)

    def test_image_picker_cancel_is_none(self):
        picker = image_picker.ImagePicker()
        for answer in (None, {}, [], "", {"cancelled": True}):
            with _Patched(image_picker, answer):
                self.assertIsNone(picker.pick_image(), answer)
                self.assertIsNone(picker.pick_video(), answer)
        with _Patched(image_picker, None):
            self.assertEqual(picker.pick_multi_image(), [])


class TestPdfControllersTravelAsProps(unittest.TestCase):
    def test_syncfusion_controller_state_is_sent_to_the_widget(self):
        from afik.plugins.syncfusion_flutter_pdfviewer import PdfViewerController, SfPdfViewer
        controller = PdfViewerController()
        controller.jump_to_page(3)
        controller.set_zoom_level(2.0)
        props = SfPdfViewer("a.pdf", controller=controller).props
        self.assertEqual((props["page"], props["zoom"]), ("3", "2.0"))

    def test_pdfx_and_pdfview_use_their_controller(self):
        from afik.plugins.flutter_pdfview import PDFView, PDFViewController
        from afik.plugins.pdfx import PdfController, PdfDocument, PdfView
        document = PdfDocument("d", 5, "/x/a.pdf")
        props = PdfView(PdfController(2, document)).props
        self.assertEqual((props["path"], props["page"]), ("/x/a.pdf", "2"))
        self.assertEqual(PDFView("b.pdf", controller=PDFViewController(4)).props["page"], "4")


if __name__ == "__main__":
    unittest.main()
