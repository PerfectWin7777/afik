import 'dart:async';

import 'package:chewie/chewie.dart';
import 'package:flutter/material.dart';
import 'package:afik_dart_runtime/ir_codec.dart';
import 'package:afik_dart_runtime/plugins/plugin_registry.dart';
import 'package:afik_dart_runtime/widgets/widget_registry.dart';

import '../video_player/shim.dart';

/// Chewie controllers, keyed by the id of the video controller they wrap.
class ChewieRegistry {
  static final Map<String, ChewieController> controllers = {};
}

/// Chewie playback UI (chewie) on top of the video_player plugin.
class ChewieShim implements AfikPlugin {
  ChewieController _get(Map<String, String> args) {
    final id = args['controllerId'] ?? '';
    final controller = ChewieRegistry.controllers[id];
    if (controller == null) {
      throw StateError('Unknown chewie controller "$id". Call createChewieController first.');
    }
    return controller;
  }

  @override
  Future<dynamic> handleMethodCall(String method, Map<String, String> args) async {
    switch (method) {
      case 'createChewieController':
        final id = args['controllerId'] ?? '';
        final video = VideoRegistry.controllers[id];
        if (video == null) {
          throw StateError('Unknown video controller "$id". Create a VideoPlayerController first.');
        }
        ChewieRegistry.controllers.remove(id)?.dispose();
        ChewieRegistry.controllers[id] = ChewieController(
          videoPlayerController: video,
          autoPlay: args['autoPlay'] == 'true',
          looping: args['looping'] == 'true',
          showControls: args['showControls'] != 'false',
          aspectRatio: double.tryParse(args['aspectRatio'] ?? ''),
        );
        VideoRegistry.changed();
        return {'configured': true};

      case 'enterFullScreen':
        _get(args).enterFullScreen();
        return {'isFullScreen': true};

      case 'exitFullScreen':
        _get(args).exitFullScreen();
        return {'isFullScreen': false};

      case 'dispose':
        ChewieRegistry.controllers.remove(args['controllerId'] ?? '')?.dispose();
        return {'disposed': true};

      default:
        throw UnsupportedError('Chewie method "$method" is not supported.');
    }
  }
}

/// Widget `Chewie(controller, ...)`.
class PyChewieWidget extends StatelessWidget {
  final WidgetNode node;

  const PyChewieWidget({super.key, required this.node});

  @override
  Widget build(BuildContext context) {
    final width = double.tryParse(node.props['width'] ?? '');
    final height = double.tryParse(node.props['height'] ?? '');
    final id = node.props['controller_id'] ?? '';

    return ValueListenableBuilder<int>(
      valueListenable: VideoRegistry.version,
      builder: (context, _, __) {
        final controller = ChewieRegistry.controllers[id];
        return SizedBox(
          width: width,
          height: height,
          child: controller == null
              ? const Center(child: CircularProgressIndicator())
              : Chewie(controller: controller),
        );
      },
    );
  }
}

void register() {
  PluginRegistry.register('chewie', ChewieShim());
  WidgetRegistry.register('Chewie', (node, sendEvent) => PyChewieWidget(node: node));
}
