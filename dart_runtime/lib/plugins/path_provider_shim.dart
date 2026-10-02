import 'dart:async';
import 'dart:io';

import 'plugin_registry.dart';

/// Provides paths to standard system directories (matching path_provider).
class PathProviderShim implements PyFlutterPlugin {
  @override
  Future<dynamic> handleMethodCall(String method, Map<String, String> args) async {
    switch (method) {
      case 'getApplicationDocumentsDirectory':
      case 'get_app_documents_directory':
      case 'get_documents_dir':
        if (Platform.isWindows) {
          final userProfile = Platform.environment['USERPROFILE'] ?? 'C:\\';
          return '$userProfile\\Documents';
        } else if (Platform.isMacOS || Platform.isLinux) {
          final home = Platform.environment['HOME'] ?? '/';
          return '$home/Documents';
        } else {
          return Directory.systemTemp.path;
        }

      case 'getTemporaryDirectory':
      case 'get_temporary_directory':
      case 'get_temp_dir':
        return Directory.systemTemp.path;

      case 'getApplicationSupportDirectory':
      case 'get_app_support_directory':
        if (Platform.isWindows) {
          final appData = Platform.environment['APPDATA'] ?? Directory.systemTemp.path;
          return '$appData\\PyFlutter';
        } else if (Platform.isMacOS) {
          final home = Platform.environment['HOME'] ?? '/';
          return '$home/Library/Application Support/PyFlutter';
        } else {
          return Directory.systemTemp.path;
        }

      case 'getDownloadsDirectory':
      case 'get_downloads_directory':
        if (Platform.isWindows) {
          final userProfile = Platform.environment['USERPROFILE'] ?? 'C:\\';
          return '$userProfile\\Downloads';
        } else if (Platform.isMacOS || Platform.isLinux) {
          final home = Platform.environment['HOME'] ?? '/';
          return '$home/Downloads';
        } else {
          return Directory.systemTemp.path;
        }

      default:
        throw UnsupportedError('Unsupported PathProvider method: $method');
    }
  }
}
