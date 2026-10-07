import 'dart:async';

import 'package:image_picker/image_picker.dart';
import 'package:afik_dart_runtime/plugins/plugin_registry.dart';

/// Gallery / camera media picking (image_picker).
///
/// A cancelled pick answers `null`; the file itself is never faked.
class ImagePickerShim implements AfikPlugin {
  final ImagePicker _picker = ImagePicker();

  @override
  Future<dynamic> handleMethodCall(String method, Map<String, String> args) async {
    final source = args['source'] == 'camera' ? ImageSource.camera : ImageSource.gallery;

    switch (method) {
      case 'pickImage':
        final file = await _picker.pickImage(
          source: source,
          maxWidth: double.tryParse(args['maxWidth'] ?? ''),
          maxHeight: double.tryParse(args['maxHeight'] ?? ''),
          imageQuality: int.tryParse(args['imageQuality'] ?? ''),
        );
        return file == null ? null : await _describe(file);

      case 'pickVideo':
        final file = await _picker.pickVideo(source: source);
        return file == null ? null : await _describe(file);

      case 'pickMultiImage':
        final files = await _picker.pickMultiImage();
        return [for (final f in files) await _describe(f)];

      default:
        throw UnsupportedError('ImagePicker method "$method" is not supported.');
    }
  }

  Future<Map<String, dynamic>> _describe(XFile file) async => {
        'path': file.path,
        'name': file.name,
        'size': await file.length(),
      };
}

void register() {
  PluginRegistry.register('image_picker', ImagePickerShim());
}
