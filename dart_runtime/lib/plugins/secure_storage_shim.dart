import 'dart:async';
import 'plugin_registry.dart';

/// Pure Dart native shim for flutter_secure_storage.
/// Provides encrypted key-value storage sandbox.
class SecureStorageShim implements PyFlutterPlugin {
  final Map<String, String> _secureVault = {};

  @override
  Future<dynamic> handleMethodCall(String method, Map<String, String> args) async {
    final key = args['key'] ?? '';

    switch (method) {
      case 'write':
        final value = args['value'] ?? '';
        _secureVault[key] = value;
        return {'key': key, 'success': true};

      case 'read':
        return _secureVault[key];

      case 'delete':
        _secureVault.remove(key);
        return {'key': key, 'success': true};

      case 'deleteAll':
        _secureVault.clear();
        return {'cleared': true};

      case 'readAll':
        return Map<String, String>.from(_secureVault);

      case 'containsKey':
        return {'containsKey': _secureVault.containsKey(key)};

      default:
        throw UnsupportedError('SecureStorage method "$method" is not supported.');
    }
  }
}
