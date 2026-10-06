import 'dart:async';
import 'dart:io';

import 'package:audioplayers/audioplayers.dart';
import 'package:pyflutter_dart_runtime/plugins/plugin_registry.dart';

/// Audio playback (audioplayers). One AudioPlayer per `playerId`.
///
/// `url` may be an http(s) URL, a local file path, or `asset:<path>` for a bundled asset.
class AudioPlayersShim implements PyFlutterPlugin {
  final Map<String, AudioPlayer> _players = {};

  AudioPlayer _player(Map<String, String> args) {
    final id = args['playerId'] ?? 'default';
    return _players.putIfAbsent(id, () => AudioPlayer(playerId: id));
  }

  Source _source(String url) {
    if (url.startsWith('asset:')) return AssetSource(url.substring('asset:'.length));
    if (url.startsWith('http://') || url.startsWith('https://')) return UrlSource(url);
    if (File(url).existsSync()) return DeviceFileSource(url);
    throw ArgumentError('Audio source not found: $url');
  }

  @override
  Future<dynamic> handleMethodCall(String method, Map<String, String> args) async {
    final player = _player(args);

    switch (method) {
      case 'play':
        await player.play(
          _source(args['url'] ?? ''),
          volume: double.tryParse(args['volume'] ?? ''),
          position: Duration(milliseconds: ((double.tryParse(args['position'] ?? '0') ?? 0) * 1000).round()),
        );
        return {'state': player.state.name};

      case 'pause':
        await player.pause();
        return {'state': player.state.name};

      case 'resume':
        await player.resume();
        return {'state': player.state.name};

      case 'stop':
        await player.stop();
        return {'state': player.state.name};

      case 'seek':
        final seconds = double.tryParse(args['position'] ?? '') ?? 0;
        await player.seek(Duration(milliseconds: (seconds * 1000).round()));
        return {'position': seconds};

      case 'setVolume':
        final volume = double.tryParse(args['volume'] ?? '1') ?? 1.0;
        await player.setVolume(volume);
        return {'volume': volume};

      case 'getDuration':
        final d = await player.getDuration();
        return {'duration': d == null ? null : d.inMilliseconds / 1000.0};

      case 'getPosition':
        final p = await player.getCurrentPosition();
        return {'position': p == null ? null : p.inMilliseconds / 1000.0};

      case 'getState':
        return {'state': player.state.name};

      case 'dispose':
        await _players.remove(args['playerId'] ?? 'default')?.dispose();
        return {'disposed': true};

      default:
        throw UnsupportedError('AudioPlayers method "$method" is not supported.');
    }
  }
}

void register() {
  final shim = AudioPlayersShim();
  PluginRegistry.register('audioplayers', shim);
  PluginRegistry.register('audioplayer', shim);
}
