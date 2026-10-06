import 'dart:async';
import 'package:path_provider/path_provider.dart' as pp;
import 'package:pyflutter_dart_runtime/plugins/plugin_registry.dart';

/// Real native directory paths using Flutter's path_provider package.
class PathProviderShim implements PyFlutterPlugin {
  @override
  Future<dynamic> handleMethodCall(String method, Map<String, String> args) async {
    switch (method) {
      case 'getApplicationDocumentsDirectory':
      case 'get_app_documents_directory':
      case 'get_documents_dir':
        final dir = await pp.getApplicationDocumentsDirectory();
        return dir.path;

      case 'getTemporaryDirectory':
      case 'get_temporary_directory':
      case 'get_temp_dir':
        final dir = await pp.getTemporaryDirectory();
        return dir.path;

      case 'getApplicationSupportDirectory':
      case 'get_app_support_directory':
        final dir = await pp.getApplicationSupportDirectory();
        return dir.path;

      case 'getDownloadsDirectory':
      case 'get_downloads_directory':
        final dir = await pp.getDownloadsDirectory();
        if (dir != null) {
          return dir.path;
        }
        final fallback = await pp.getApplicationDocumentsDirectory();
        return fallback.path;

      default:
        throw UnsupportedError('Unsupported PathProvider method: $method');
    }
  }
}

/// Called by the generated `installed_plugins.dart` when this plugin is installed.
void register() {
  PluginRegistry.register('path_provider', PathProviderShim());
}
