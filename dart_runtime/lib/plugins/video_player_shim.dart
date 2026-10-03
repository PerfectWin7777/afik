import 'dart:async';
import 'plugin_registry.dart';

class _VideoSession {
  bool initialized = false;
  bool isPlaying = false;
  bool isLooping = false;
  double volume = 1.0;
  double position = 0.0;
  double duration = 300.0; // 5 minutes default duration
  double aspectRatio = 16.0 / 9.0;
  String? url;
  DateTime? lastStartTime;
}

/// Pure Dart native shim for video_player package.
/// Tracks video sessions, durations, and playhead positions.
class VideoPlayerShim implements PyFlutterPlugin {
  final Map<String, _VideoSession> _sessions = {};

  _VideoSession _getOrCreateSession(String id) {
    return _sessions.putIfAbsent(id, () => _VideoSession());
  }

  @override
  Future<dynamic> handleMethodCall(String method, Map<String, String> args) async {
    final controllerId = args['controllerId'] ?? 'default';
    final session = _getOrCreateSession(controllerId);

    switch (method) {
      case 'create':
        session.url = args['url'];
        return {'controllerId': controllerId, 'created': true};

      case 'initialize':
        session.initialized = true;
        return {
          'controllerId': controllerId,
          'initialized': true,
          'duration': session.duration,
          'aspectRatio': session.aspectRatio,
        };

      case 'play':
        session.isPlaying = true;
        session.lastStartTime = DateTime.now();
        return {'controllerId': controllerId, 'isPlaying': true};

      case 'pause':
        if (session.isPlaying && session.lastStartTime != null) {
          final elapsed = DateTime.now().difference(session.lastStartTime!).inMilliseconds / 1000.0;
          session.position = (session.position + elapsed).clamp(0.0, session.duration);
        }
        session.isPlaying = false;
        session.lastStartTime = null;
        return {'controllerId': controllerId, 'isPlaying': false, 'position': session.position};

      case 'seekTo':
        final pos = double.tryParse(args['position'] ?? '0.0') ?? 0.0;
        session.position = pos.clamp(0.0, session.duration);
        if (session.isPlaying) {
          session.lastStartTime = DateTime.now();
        }
        return {'controllerId': controllerId, 'position': session.position};

      case 'setVolume':
        final vol = double.tryParse(args['volume'] ?? '1.0') ?? 1.0;
        session.volume = vol.clamp(0.0, 1.0);
        return {'controllerId': controllerId, 'volume': session.volume};

      case 'setLooping':
        session.isLooping = args['looping'] == 'true';
        return {'controllerId': controllerId, 'isLooping': session.isLooping};

      case 'getPosition':
        if (session.isPlaying && session.lastStartTime != null) {
          final elapsed = DateTime.now().difference(session.lastStartTime!).inMilliseconds / 1000.0;
          final current = (session.position + elapsed).clamp(0.0, session.duration);
          return {'controllerId': controllerId, 'position': current};
        }
        return {'controllerId': controllerId, 'position': session.position};

      case 'dispose':
        _sessions.remove(controllerId);
        return {'controllerId': controllerId, 'disposed': true};

      default:
        throw UnsupportedError('VideoPlayer method "$method" is not supported.');
    }
  }
}
