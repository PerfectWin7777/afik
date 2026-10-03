import 'dart:async';
import 'plugin_registry.dart';

class _ChewieConfig {
  bool autoPlay = false;
  bool looping = false;
  bool showControls = true;
  double aspectRatio = 16.0 / 9.0;
  bool isFullScreen = false;
}

/// Pure Dart native shim for Chewie media player wrapper.
class ChewieShim implements PyFlutterPlugin {
  final Map<String, _ChewieConfig> _configs = {};

  @override
  Future<dynamic> handleMethodCall(String method, Map<String, String> args) async {
    final controllerId = args['controllerId'] ?? 'default';
    final config = _configs.putIfAbsent(controllerId, () => _ChewieConfig());

    switch (method) {
      case 'createChewieController':
        config.autoPlay = args['autoPlay'] == 'true';
        config.looping = args['looping'] == 'true';
        config.showControls = args['showControls'] != 'false';
        config.aspectRatio = double.tryParse(args['aspectRatio'] ?? '') ?? (16.0 / 9.0);
        return {'controllerId': controllerId, 'configured': true};

      case 'enterFullScreen':
        config.isFullScreen = true;
        return {'controllerId': controllerId, 'isFullScreen': true};

      case 'exitFullScreen':
        config.isFullScreen = false;
        return {'controllerId': controllerId, 'isFullScreen': false};

      case 'getConfig':
        return {
          'controllerId': controllerId,
          'autoPlay': config.autoPlay,
          'looping': config.looping,
          'showControls': config.showControls,
          'aspectRatio': config.aspectRatio,
          'isFullScreen': config.isFullScreen,
        };

      default:
        throw UnsupportedError('Chewie method "$method" is not supported.');
    }
  }
}
