import 'dart:async';
import 'plugin_registry.dart';

class _PlayerSession {
  String state = 'stopped'; // 'playing', 'paused', 'stopped', 'completed'
  double volume = 1.0;
  double position = 0.0;
  double duration = 180.0; // 3 minutes default duration estimate
  String? url;
  DateTime? lastStartTime;
}

/// Pure Dart native shim for audioplayers package.
/// Tracks multi-player audio playback sessions and simulated playback timing.
class AudioPlayerShim implements PyFlutterPlugin {
  final Map<String, _PlayerSession> _sessions = {};

  _PlayerSession _getOrCreateSession(String id) {
    return _sessions.putIfAbsent(id, () => _PlayerSession());
  }

  @override
  Future<dynamic> handleMethodCall(String method, Map<String, String> args) async {
    final playerId = args['playerId'] ?? 'default';
    final session = _getOrCreateSession(playerId);

    switch (method) {
      case 'play':
        final url = args['url'];
        if (url != null) session.url = url;
        final vol = double.tryParse(args['volume'] ?? '');
        if (vol != null) session.volume = vol;
        session.state = 'playing';
        session.lastStartTime = DateTime.now();
        return {'state': session.state, 'playerId': playerId};

      case 'pause':
        if (session.state == 'playing' && session.lastStartTime != null) {
          final elapsed = DateTime.now().difference(session.lastStartTime!).inMilliseconds / 1000.0;
          session.position = (session.position + elapsed).clamp(0.0, session.duration);
        }
        session.state = 'paused';
        session.lastStartTime = null;
        return {'state': session.state, 'position': session.position};

      case 'resume':
        session.state = 'playing';
        session.lastStartTime = DateTime.now();
        return {'state': session.state};

      case 'stop':
        session.state = 'stopped';
        session.position = 0.0;
        session.lastStartTime = null;
        return {'state': session.state, 'position': 0.0};

      case 'seek':
        final pos = double.tryParse(args['position'] ?? '0.0') ?? 0.0;
        session.position = pos.clamp(0.0, session.duration);
        if (session.state == 'playing') {
          session.lastStartTime = DateTime.now();
        }
        return {'position': session.position};

      case 'setVolume':
        final vol = double.tryParse(args['volume'] ?? '1.0') ?? 1.0;
        session.volume = vol.clamp(0.0, 1.0);
        return {'volume': session.volume};

      case 'getDuration':
        return {'duration': session.duration};

      case 'getPosition':
        if (session.state == 'playing' && session.lastStartTime != null) {
          final elapsed = DateTime.now().difference(session.lastStartTime!).inMilliseconds / 1000.0;
          final current = (session.position + elapsed).clamp(0.0, session.duration);
          return {'position': current};
        }
        return {'position': session.position};

      case 'getState':
        return {'state': session.state};

      default:
        throw UnsupportedError('AudioPlayer method "$method" is not supported.');
    }
  }
}
