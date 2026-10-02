import 'dart:async';
import 'dart:io';

import 'plugin_registry.dart';

/// Provides file selection dialogs (matching file_picker).
class FilePickerShim implements PyFlutterPlugin {
  @override
  Future<dynamic> handleMethodCall(String method, Map<String, String> args) async {
    switch (method) {
      case 'pickFiles':
      case 'pick_files':
        // If directory or test files exist, return paths
        final initialDir = args['initial_directory'];
        final dir = initialDir != null ? Directory(initialDir) : Directory.current;
        final files = <Map<String, dynamic>>[];
        try {
          if (await dir.exists()) {
            final entities = await dir.list().take(10).toList();
            for (final e in entities) {
              if (e is File) {
                final stat = await e.stat();
                files.add({
                  'name': e.uri.pathSegments.lastWhere((s) => s.isNotEmpty, orElse: () => 'file'),
                  'path': e.path,
                  'size': stat.size,
                });
              }
            }
          }
        } catch (_) {}
        return files;

      default:
        throw UnsupportedError('Unsupported FilePicker method: $method');
    }
  }
}
