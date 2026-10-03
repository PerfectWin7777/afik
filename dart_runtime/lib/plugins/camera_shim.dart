import 'dart:async';
import 'dart:io';
import 'plugin_registry.dart';

/// Pure Dart native shim for camera package.
/// Supports camera enumeration, capture emulation, and controls.
class CameraShim implements PyFlutterPlugin {
  String _activeFlashMode = 'off';
  double _zoomLevel = 1.0;
  bool _isRecording = false;

  @override
  Future<dynamic> handleMethodCall(String method, Map<String, String> args) async {
    switch (method) {
      case 'availableCameras':
        return _availableCameras();
      case 'initialize':
        return _initialize(args);
      case 'takePicture':
        return await _takePicture(args);
      case 'startVideoRecording':
        return _startVideoRecording(args);
      case 'stopVideoRecording':
        return await _stopVideoRecording(args);
      case 'setFlashMode':
        return _setFlashMode(args);
      case 'setZoomLevel':
        return _setZoomLevel(args);
      case 'isRecording':
        return {'isRecording': _isRecording};
      case 'dispose':
        return {'disposed': true};
      default:
        throw UnsupportedError('Camera method "$method" is not supported.');
    }

  }

  List<Map<String, dynamic>> _availableCameras() {
    return [
      {
        'id': '0',
        'name': 'Back Camera',
        'lensFacing': 'back',
        'sensorOrientation': 90,
      },
      {
        'id': '1',
        'name': 'Front Camera (Selfie)',
        'lensFacing': 'front',
        'sensorOrientation': 270,
      },
    ];
  }

  Map<String, dynamic> _initialize(Map<String, String> args) {
    final cameraId = args['cameraId'] ?? '0';
    final resolution = args['resolution'] ?? 'high';
    return {
      'cameraId': cameraId,
      'resolution': resolution,
      'previewWidth': 1920,
      'previewHeight': 1080,
      'initialized': true,
    };
  }

  Future<Map<String, dynamic>> _takePicture(Map<String, String> args) async {
    final cameraId = args['cameraId'] ?? '0';
    final timestamp = DateTime.now().millisecondsSinceEpoch;
    final file = File('${Directory.systemTemp.path}/pyflutter_cam_${cameraId}_$timestamp.jpg');

    // Create a valid dummy image file if needed
    if (!file.existsSync()) {
      file.writeAsBytesSync([
        0xFF, 0xD8, 0xFF, 0xE0, 0x00, 0x10, 0x4A, 0x46,
        0x49, 0x46, 0x00, 0x01, 0x01, 0x00, 0x00, 0x01,
        0x00, 0x01, 0x00, 0x00, 0xFF, 0xDB, 0x00, 0x43,
        0x00, 0x08, 0x06, 0x06, 0x07, 0x06, 0x05, 0x08,
        0xFF, 0xD9,
      ]);
    }

    return {
      'path': file.path,
      'name': file.uri.pathSegments.last,
      'size': file.lengthSync(),
    };
  }

  Map<String, dynamic> _startVideoRecording(Map<String, String> args) {
    _isRecording = true;
    return {'recording': true};
  }

  Future<Map<String, dynamic>> _stopVideoRecording(Map<String, String> args) async {
    _isRecording = false;
    final timestamp = DateTime.now().millisecondsSinceEpoch;
    final file = File('${Directory.systemTemp.path}/pyflutter_vid_$timestamp.mp4');
    if (!file.existsSync()) {
      file.writeAsStringSync('dummy_video_stream');
    }
    return {
      'path': file.path,
      'name': file.uri.pathSegments.last,
      'size': file.lengthSync(),
    };
  }

  Map<String, dynamic> _setFlashMode(Map<String, String> args) {
    _activeFlashMode = args['mode'] ?? 'off';
    return {'flashMode': _activeFlashMode};
  }

  Map<String, dynamic> _setZoomLevel(Map<String, String> args) {
    _zoomLevel = double.tryParse(args['zoom'] ?? '1.0') ?? 1.0;
    return {'zoom': _zoomLevel};
  }
}
