import 'dart:async';
import 'package:file_picker/file_picker.dart';
import 'plugin_registry.dart';

/// Real native file selection dialogs using Flutter's file_picker package.
class FilePickerShim implements PyFlutterPlugin {
  @override
  Future<dynamic> handleMethodCall(String method, Map<String, String> args) async {
    switch (method) {
      case 'pickFiles':
      case 'pick_files':
        final allowMultiple = args['allow_multiple'] == 'true';
        final initialDir = args['initial_directory'];
        final allowedExtStr = args['allowed_extensions'];
        List<String>? allowedExtensions;
        FileType fileType = FileType.any;

        if (allowedExtStr != null && allowedExtStr.trim().isNotEmpty) {
          allowedExtensions = allowedExtStr
              .split(',')
              .map((e) => e.trim().replaceAll('.', ''))
              .where((e) => e.isNotEmpty)
              .toList();
          if (allowedExtensions.isNotEmpty) {
            fileType = FileType.custom;
          }
        }

        final result = await FilePicker.pickFiles(
          allowMultiple: allowMultiple,
          initialDirectory: initialDir,
          type: fileType,
          allowedExtensions: allowedExtensions,
        );

        if (result == null || result.files.isEmpty) {
          return <Map<String, dynamic>>[];
        }

        return result.files.map((file) {
          return {
            'name': file.name,
            'path': file.path ?? '',
            'size': file.size,
          };
        }).toList();

      case 'getDirectoryPath':
      case 'get_directory_path':
        final initialDir = args['initial_directory'];
        final path = await FilePicker.getDirectoryPath(
          initialDirectory: initialDir,
        );
        return path;

      case 'saveFile':
      case 'save_file':
        final fileName = args['file_name'] ?? 'untitled';
        final initialDir = args['initial_directory'];
        final path = await FilePicker.saveFile(
          fileName: fileName,
          initialDirectory: initialDir,
        );
        return path;

      default:
        throw UnsupportedError('Unsupported FilePicker method: $method');
    }
  }
}
