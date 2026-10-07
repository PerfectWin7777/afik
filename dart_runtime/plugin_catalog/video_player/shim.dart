import 'dart:async';
import 'dart:io';

import 'package:flutter/material.dart';
import 'package:afik_dart_runtime/ir_codec.dart';
import 'package:afik_dart_runtime/plugins/plugin_registry.dart';
import 'package:afik_dart_runtime/widgets/widget_registry.dart';
import 'package:video_player/video_player.dart';

/// Controllers created from Python (`VideoPlayerController(...)`), shared with the widgets
/// (`VideoPlayer`, and `Chewie` from the chewie plugin) through their `controller_id`.
class VideoRegistry {
  static final Map<String, VideoPlayerController> controllers = {};

  /// Bumped whenever a controller is created, initialised or disposed so widgets rebuild.
  static final ValueNotifier<int> version = ValueNotifier<int>(0);

  static void changed() => version.value++;
}

/// Real video playback (video_player).
class VideoPlayerShim implements AfikPlugin {
  VideoPlayerController _get(Map<String, String> args) {
    final id = args['controllerId'] ?? '';
    final controller = VideoRegistry.controllers[id];
    if (controller == null) {
      throw StateError('Unknown video controller "$id". Call create first.');
    }
    return controller;
  }

  double _seconds(Duration d) => d.inMilliseconds / 1000.0;

  @override
  Future<dynamic> handleMethodCall(String method, Map<String, String> args) async {
    switch (method) {
      case 'create':
        final id = args['controllerId'] ?? '';
        final url = args['url'] ?? '';
        await VideoRegistry.controllers.remove(id)?.dispose();
        final VideoPlayerController controller;
        if (args['isAsset'] == 'true') {
          controller = VideoPlayerController.asset(url);
        } else if (url.startsWith('http://') || url.startsWith('https://')) {
          controller = VideoPlayerController.networkUrl(Uri.parse(url));
        } else {
          controller = VideoPlayerController.file(File(url));
        }
        VideoRegistry.controllers[id] = controller;
        VideoRegistry.changed();
        return {'created': true};

      case 'initialize':
        final c = _get(args);
        await c.initialize();
        VideoRegistry.changed();
        return {
          'initialized': c.value.isInitialized,
          'duration': _seconds(c.value.duration),
          'aspectRatio': c.value.aspectRatio,
        };

      case 'play':
        final c = _get(args);
        await c.play();
        return {'isPlaying': c.value.isPlaying};

      case 'pause':
        final c = _get(args);
        await c.pause();
        return {'isPlaying': c.value.isPlaying};

      case 'seekTo':
        final seconds = double.tryParse(args['position'] ?? '') ?? 0;
        await _get(args).seekTo(Duration(milliseconds: (seconds * 1000).round()));
        return {'position': seconds};

      case 'setVolume':
        final volume = double.tryParse(args['volume'] ?? '') ?? 1.0;
        await _get(args).setVolume(volume);
        return {'volume': volume};

      case 'setLooping':
        final looping = args['looping'] == 'true';
        await _get(args).setLooping(looping);
        return {'isLooping': looping};

      case 'getPosition':
        return {'position': _seconds(_get(args).value.position)};

      case 'getState':
        final c = _get(args);
        return {
          'isInitialized': c.value.isInitialized,
          'isPlaying': c.value.isPlaying,
          'position': _seconds(c.value.position),
          'duration': _seconds(c.value.duration),
          'hasError': c.value.hasError,
          'error': c.value.errorDescription,
        };

      case 'dispose':
        await VideoRegistry.controllers.remove(args['controllerId'] ?? '')?.dispose();
        VideoRegistry.changed();
        return {'disposed': true};

      default:
        throw UnsupportedError('VideoPlayer method "$method" is not supported.');
    }
  }
}

/// Widget `VideoPlayer(url_or_controller, auto_play=, show_controls=, width=, height=)`.
///
/// With a Python controller the widget draws that controller; with a plain URL it owns a
/// controller of its own for the lifetime of the widget.
class PyVideoPlayerWidget extends StatefulWidget {
  final WidgetNode node;
  final void Function(String callbackId, Map<String, String> eventData) sendEvent;

  const PyVideoPlayerWidget({super.key, required this.node, required this.sendEvent});

  @override
  State<PyVideoPlayerWidget> createState() => _PyVideoPlayerWidgetState();
}

class _PyVideoPlayerWidgetState extends State<PyVideoPlayerWidget> {
  VideoPlayerController? _own;
  VideoPlayerController? _listening;
  bool _wasCompleted = false;

  String get _controllerId => widget.node.props['controller_id'] ?? '';

  @override
  void initState() {
    super.initState();
    if (_controllerId.isEmpty) {
      _startOwnController();
    }
  }

  Future<void> _startOwnController() async {
    final url = widget.node.props['url'] ?? '';
    if (url.isEmpty) return;
    final VideoPlayerController controller;
    if (url.startsWith('http://') || url.startsWith('https://')) {
      controller = VideoPlayerController.networkUrl(Uri.parse(url));
    } else {
      controller = VideoPlayerController.file(File(url));
    }
    _own = controller;
    try {
      await controller.initialize();
      if (!mounted) return;
      if (widget.node.props['auto_play'] == 'true') await controller.play();
    } catch (e) {
      _emit({'event': 'error', 'message': e.toString()});
    }
    if (mounted) setState(() {});
  }

  VideoPlayerController? get _controller =>
      _controllerId.isEmpty ? _own : VideoRegistry.controllers[_controllerId];

  void _emit(Map<String, String> data) {
    final id = widget.node.callbackId;
    if (id.isNotEmpty) widget.sendEvent(id, data);
  }

  void _onValue() {
    final c = _listening;
    if (c == null) return;
    final completed = c.value.isInitialized &&
        c.value.duration > Duration.zero &&
        c.value.position >= c.value.duration;
    if (completed && !_wasCompleted) _emit({'event': 'completed'});
    _wasCompleted = completed;
    if (c.value.hasError) _emit({'event': 'error', 'message': c.value.errorDescription ?? ''});
  }

  void _listenTo(VideoPlayerController? c) {
    if (identical(c, _listening)) return;
    _listening?.removeListener(_onValue);
    _listening = c;
    _listening?.addListener(_onValue);
  }

  @override
  void dispose() {
    _listening?.removeListener(_onValue);
    _own?.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final width = double.tryParse(widget.node.props['width'] ?? '');
    final height = double.tryParse(widget.node.props['height'] ?? '');
    final showControls = widget.node.props['show_controls'] != 'false';

    return ValueListenableBuilder<int>(
      valueListenable: VideoRegistry.version,
      builder: (context, _, __) {
        final c = _controller;
        _listenTo(c);
        Widget child;
        if (c == null || !c.value.isInitialized) {
          child = const Center(child: CircularProgressIndicator());
        } else {
          Widget video = AspectRatio(aspectRatio: c.value.aspectRatio, child: VideoPlayer(c));
          if (showControls) {
            video = Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                video,
                VideoProgressIndicator(c, allowScrubbing: true),
                ValueListenableBuilder<VideoPlayerValue>(
                  valueListenable: c,
                  builder: (context, value, _) => IconButton(
                    icon: Icon(value.isPlaying ? Icons.pause : Icons.play_arrow),
                    onPressed: () => value.isPlaying ? c.pause() : c.play(),
                  ),
                ),
              ],
            );
          }
          child = video;
        }
        return SizedBox(width: width, height: height, child: child);
      },
    );
  }
}

void register() {
  PluginRegistry.register('video_player', VideoPlayerShim());
  WidgetRegistry.register('VideoPlayer', (node, sendEvent) => PyVideoPlayerWidget(node: node, sendEvent: sendEvent));
}
