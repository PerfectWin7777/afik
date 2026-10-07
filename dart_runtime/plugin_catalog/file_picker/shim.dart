import 'dart:async';
import 'dart:convert';
import 'package:file_picker/file_picker.dart';
import 'package:afik_dart_runtime/plugins/plugin_registry.dart';

/// Real native file selection dialogs using Flutter's file_picker package.
class FilePickerShim implements AfikPlugin {
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

        final List<PlatformFile> picked;
        if (allowMultiple) {
          picked = await FilePicker.pickFiles(
            initialDirectory: initialDir,
            type: fileType,
            allowedExtensions: allowedExtensions,
          );
        } else {
          final file = await FilePicker.pickFile(
            initialDirectory: initialDir,
            type: fileType,
            allowedExtensions: allowedExtensions,
          );
          picked = file == null ? <PlatformFile>[] : [file];
        }

        return [
          for (final file in picked)
            {
              'name': file.name,
              'path': file.path ?? '',
              'size': await file.length() ?? 0,
            },
        ];

      case 'getDirectoryPath':
      case 'get_directory_path':
        final initialDir = args['initial_directory'];
        final path = await FilePicker.getDirectoryPath(
          initialDirectory: initialDir,
        );
        return path;

      case 'saveFile':
      case 'save_file':
        // `data` is the file content, base64 encoded by the Python side.
        final uri = await FilePicker.saveFile(
          fileName: args['file_name'] ?? 'untitled',
          bytes: base64Decode(args['data'] ?? ''),
          initialDirectory: args['initial_directory'],
        );
        return uri?.toString();

      default:
        throw UnsupportedError('Unsupported FilePicker method: $method');
    }
  }
}

/// Called by the generated `installed_plugins.dart` when this plugin is installed.
void register() {
  PluginRegistry.register('file_picker', FilePickerShim());
}
