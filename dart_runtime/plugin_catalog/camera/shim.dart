import 'dart:async';
import 'dart:io';

import 'package:camera/camera.dart';
import 'package:flutter/material.dart';
import 'package:afik_dart_runtime/ir_codec.dart';
import 'package:afik_dart_runtime/plugins/plugin_registry.dart';
import 'package:afik_dart_runtime/widgets/widget_registry.dart';

/// Camera controllers keyed by the camera id used from Python (the index in
/// `availableCameras()`), shared with the `CameraPreview` widget.
class CameraRegistry {
  static List<CameraDescription> cameras = [];
  static final Map<String, CameraController> controllers = {};
  static final ValueNotifier<int> version = ValueNotifier<int>(0);

  static void changed() => version.value++;
}

/// Camera capture (camera).
class CameraShim implements AfikPlugin {
  CameraController _get(Map<String, String> args) {
    final id = args['cameraId'] ?? '';
    final controller = CameraRegistry.controllers[id];
    if (controller == null || !controller.value.isInitialized) {
      throw StateError('Camera "$id" is not initialised. Call initialize first.');
    }
    return controller;
  }

  Future<Map<String, dynamic>> _describe(XFile file) async => {
        'path': file.path,
        'name': file.name,
        'size': await File(file.path).length(),
      };

  ResolutionPreset _preset(String? name) {
    switch (name) {
      case 'low':
        return ResolutionPreset.low;
      case 'medium':
        return ResolutionPreset.medium;
      case 'veryHigh':
      case 'very_high':
        return ResolutionPreset.veryHigh;
      case 'ultraHigh':
      case 'ultra_high':
        return ResolutionPreset.ultraHigh;
      case 'max':
        return ResolutionPreset.max;
      default:
        return ResolutionPreset.high;
    }
  }

  FlashMode _flash(String? name) {
    switch (name) {
      case 'auto':
        return FlashMode.auto;
      case 'always':
        return FlashMode.always;
      case 'torch':
        return FlashMode.torch;
      default:
        return FlashMode.off;
    }
  }

  @override
  Future<dynamic> handleMethodCall(String method, Map<String, String> args) async {
    switch (method) {
      case 'availableCameras':
        CameraRegistry.cameras = await availableCameras();
        return [
          for (var i = 0; i < CameraRegistry.cameras.length; i++)
            {
              'id': '$i',
              'name': CameraRegistry.cameras[i].name,
              'lensFacing': CameraRegistry.cameras[i].lensDirection.name,
              'sensorOrientation': CameraRegistry.cameras[i].sensorOrientation,
            },
        ];

      case 'initialize':
        final id = args['cameraId'] ?? '0';
        if (CameraRegistry.cameras.isEmpty) {
          CameraRegistry.cameras = await availableCameras();
        }
        final index = int.tryParse(id);
        if (index == null || index < 0 || index >= CameraRegistry.cameras.length) {
          throw ArgumentError('No camera with id "$id".');
        }
        await CameraRegistry.controllers.remove(id)?.dispose();
        final controller = CameraController(
          CameraRegistry.cameras[index],
          _preset(args['resolution']),
        );
        CameraRegistry.controllers[id] = controller;
        await controller.initialize();
        CameraRegistry.changed();
        return {'cameraId': id, 'initialized': controller.value.isInitialized};

      case 'takePicture':
        return _describe(await _get(args).takePicture());

      case 'startVideoRecording':
        await _get(args).startVideoRecording();
        return {'recording': true};

      case 'stopVideoRecording':
        return _describe(await _get(args).stopVideoRecording());

      case 'isRecording':
        final c = CameraRegistry.controllers[args['cameraId'] ?? ''];
        return {'isRecording': c?.value.isRecordingVideo ?? false};

      case 'setFlashMode':
        final mode = _flash(args['mode']);
        await _get(args).setFlashMode(mode);
        return {'flashMode': mode.name};

      case 'setZoomLevel':
        final c = _get(args);
        final zoom = double.tryParse(args['zoom'] ?? '') ?? 1.0;
        final clamped = zoom.clamp(await c.getMinZoomLevel(), await c.getMaxZoomLevel()).toDouble();
        await c.setZoomLevel(clamped);
        return {'zoom': clamped};

      case 'dispose':
        await CameraRegistry.controllers.remove(args['cameraId'] ?? '')?.dispose();
        CameraRegistry.changed();
        return {'disposed': true};

      default:
        throw UnsupportedError('Camera method "$method" is not supported.');
    }
  }
}

/// Widget `CameraPreview(controller_or_camera_id, width=, height=)`.
class PyCameraPreviewWidget extends StatelessWidget {
  final WidgetNode node;

  const PyCameraPreviewWidget({super.key, required this.node});

  @override
  Widget build(BuildContext context) {
    final width = double.tryParse(node.props['width'] ?? '');
    final height = double.tryParse(node.props['height'] ?? '');
    final id = node.props['camera_id'] ?? '0';

    return ValueListenableBuilder<int>(
      valueListenable: CameraRegistry.version,
      builder: (context, _, __) {
        final controller = CameraRegistry.controllers[id];
        final ready = controller != null && controller.value.isInitialized;
        return SizedBox(
          width: width,
          height: height,
          child: ready ? CameraPreview(controller) : const Center(child: CircularProgressIndicator()),
        );
      },
    );
  }
}

void register() {
  PluginRegistry.register('camera', CameraShim());
  WidgetRegistry.register('CameraPreview', (node, sendEvent) => PyCameraPreviewWidget(node: node));
}
