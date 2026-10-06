import 'dart:async';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:pyflutter_dart_runtime/plugins/plugin_registry.dart';

/// Real encrypted storage: Keychain on iOS/macOS, Keystore-backed encryption on
/// Android (flutter_secure_storage).
class SecureStorageShim implements PyFlutterPlugin {
  final FlutterSecureStorage _storage = const FlutterSecureStorage();

  @override
  Future<dynamic> handleMethodCall(String method, Map<String, String> args) async {
    final key = args['key'] ?? '';

    switch (method) {
      case 'write':
        await _storage.write(key: key, value: args['value'] ?? '');
        return {'key': key, 'success': true};

      case 'read':
        return await _storage.read(key: key);

      case 'delete':
        await _storage.delete(key: key);
        return {'key': key, 'success': true};

      case 'deleteAll':
        await _storage.deleteAll();
        return {'cleared': true};

      case 'readAll':
        return await _storage.readAll();

      case 'containsKey':
        return {'containsKey': await _storage.containsKey(key: key)};

      default:
        throw UnsupportedError('SecureStorage method "$method" is not supported.');
    }
  }
}

/// Called by the generated `installed_plugins.dart` when this plugin is installed.
void register() {
  PluginRegistry.register('flutter_secure_storage', SecureStorageShim());
  PluginRegistry.register('secure_storage', SecureStorageShim());
}
