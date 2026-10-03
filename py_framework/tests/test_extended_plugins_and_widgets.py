"""
Unit tests for the 7 top Flutter packages and corresponding widgets in PyFlutter:
- image_picker (pick_image, pick_video, pick_multi_image, XFile)
- camera (available_cameras, CameraController, CameraPreview widget)
- connectivity_plus (check_connectivity, is_connected, ConnectivityResult)
- audioplayers (AudioPlayer, PlayerState)
- video_player (VideoPlayerController, VideoPlayer widget)
- share_plus (share, share_files, share_uri)
- webview_flutter (WebViewController, WebView widget)
"""

import unittest

import pyflutter as pf
from pyflutter.plugins import (
    image_picker,
    camera,
    connectivity,
    connectivity_plus,
    audioplayer,
    audioplayers,
    video_player,
    share,
    share_plus,
    webview,
    webview_flutter,
)


class TestImagePickerPlugin(unittest.TestCase):
    def test_pick_image(self):
        file = image_picker.pick_image(image_picker.ImageSource.GALLERY)
        self.assertIsNotNone(file)
        self.assertIsInstance(file, image_picker.XFile)
        self.assertTrue(len(file.path) > 0)
        self.assertTrue(len(file.name) > 0)
        self.assertIsInstance(file.read_bytes(), bytes)

    def test_pick_video(self):
        vid = image_picker.pick_video(image_picker.ImageSource.CAMERA)
        self.assertIsNotNone(vid)
        self.assertIsInstance(vid, image_picker.XFile)

    def test_pick_multi_image(self):
        files = image_picker.pick_multi_image()
        self.assertIsInstance(files, list)
        if files:
            self.assertIsInstance(files[0], image_picker.XFile)


class TestCameraPlugin(unittest.TestCase):
    def test_available_cameras(self):
        cams = camera.available_cameras()
        self.assertIsInstance(cams, list)
        self.assertTrue(len(cams) >= 1)
        self.assertEqual(cams[0].lens_facing, "back")

    def test_camera_controller_lifecycle(self):
        cams = camera.available_cameras()
        ctrl = camera.CameraController(cams[0])
        self.assertFalse(ctrl.is_initialized)

        ctrl.initialize()
        self.assertTrue(ctrl.is_initialized)

        ctrl.set_flash_mode("auto")
        ctrl.set_zoom_level(1.5)

        pic = ctrl.take_picture()
        self.assertIsNotNone(pic)
        self.assertIsInstance(pic, image_picker.XFile)

        self.assertTrue(ctrl.start_video_recording())
        vid = ctrl.stop_video_recording()
        self.assertIsNotNone(vid)
        self.assertIsInstance(vid, image_picker.XFile)

        ctrl.dispose()
        self.assertFalse(ctrl.is_initialized)


class TestConnectivityPlugin(unittest.TestCase):
    def test_connectivity(self):
        result = connectivity.check_connectivity()
        self.assertIsInstance(result, connectivity.ConnectivityResult)
        self.assertTrue(connectivity.is_connected())

    def test_alias(self):
        res = connectivity_plus.check_connectivity()
        self.assertIsInstance(res, connectivity_plus.ConnectivityResult)


class TestAudioPlayerPlugin(unittest.TestCase):
    def test_audio_player_controls(self):
        player = audioplayer.AudioPlayer()
        self.assertEqual(player.state, audioplayer.PlayerState.STOPPED)

        player.play("https://example.com/audio.mp3", volume=0.7)
        self.assertEqual(player.state, audioplayer.PlayerState.PLAYING)

        player.pause()
        self.assertEqual(player.state, audioplayer.PlayerState.PAUSED)

        player.resume()
        self.assertEqual(player.state, audioplayer.PlayerState.PLAYING)

        player.seek(30.0)
        player.set_volume(0.5)

        self.assertGreater(player.get_duration(), 0)
        self.assertIsInstance(player.get_position(), float)

        player.stop()
        self.assertEqual(player.state, audioplayer.PlayerState.STOPPED)

    def test_alias(self):
        player = audioplayers.AudioPlayer()
        self.assertIsNotNone(player)


class TestVideoPlayerPlugin(unittest.TestCase):
    def test_video_controller_controls(self):
        ctrl = video_player.VideoPlayerController.network("https://example.com/stream.mp4")
        self.assertFalse(ctrl.is_initialized)

        ctrl.initialize()
        self.assertTrue(ctrl.is_initialized)

        ctrl.play()
        self.assertTrue(ctrl.is_playing())

        ctrl.pause()
        self.assertFalse(ctrl.is_playing())

        ctrl.seek_to(45.0)
        ctrl.set_volume(0.8)
        ctrl.set_looping(True)
        self.assertEqual(ctrl.position(), 0.0)
        self.assertGreater(ctrl.duration, 0)

        ctrl.dispose()
        self.assertFalse(ctrl.is_initialized)


class TestSharePlugin(unittest.TestCase):
    def test_share(self):
        self.assertTrue(share.share("Check out PyFlutter!"))
        self.assertTrue(share.share_files(["sample.txt"], text="file description"))
        self.assertTrue(share.share_uri("https://flutter.dev"))

    def test_alias(self):
        self.assertTrue(share_plus.share("Shared via alias!"))


class TestWebViewPlugin(unittest.TestCase):
    def test_webview_controller(self):
        ctrl = webview.WebViewController("https://flutter.dev")
        self.assertEqual(ctrl.current_url(), "https://flutter.dev")

        ctrl.load_url("https://python.org")
        self.assertEqual(ctrl.current_url(), "https://python.org")

        ctrl.load_html("<h1>Hello</h1>")
        self.assertTrue(ctrl.reload())

        res = ctrl.evaluate_javascript("document.title")
        self.assertIsNotNone(res)

    def test_alias(self):
        ctrl = webview_flutter.WebViewController("https://example.com")
        self.assertIsNotNone(ctrl)


class TestExtendedWidgets(unittest.TestCase):
    def test_webview_widget(self):
        wv = pf.WebView("https://flutter.dev", width=400, height=600)
        self.assertEqual(wv.widget_type, "WebView")
        self.assertEqual(wv.props["url"], "https://flutter.dev")
        self.assertEqual(float(wv.props["width"]), 400)
        self.assertEqual(float(wv.props["height"]), 600)


        # Signal connection
        called = []
        wv.navigation.connect(lambda data: called.append(data))
        self.assertTrue(hasattr(wv, "_navigation_signal"))

    def test_video_player_widget(self):
        ctrl = video_player.VideoPlayerController.file("movie.mp4")
        vp = pf.VideoPlayer(ctrl, auto_play=True)
        self.assertEqual(vp.widget_type, "VideoPlayer")
        self.assertEqual(vp.props["url"], "movie.mp4")
        self.assertTrue(vp.props["auto_play"])

        # Signal connection
        called = []
        vp.player_event.connect(lambda data: called.append(data))
        self.assertTrue(hasattr(vp, "_player_event_signal"))

    def test_camera_preview_widget(self):
        cp = pf.CameraPreview("1", width=350, height=500)
        self.assertEqual(cp.widget_type, "CameraPreview")
        self.assertEqual(cp.props["camera_id"], "1")

        # Signal connection
        called = []
        cp.shutter.connect(lambda data: called.append(data))
        self.assertTrue(hasattr(cp, "_shutter_signal"))


if __name__ == "__main__":
    unittest.main()
