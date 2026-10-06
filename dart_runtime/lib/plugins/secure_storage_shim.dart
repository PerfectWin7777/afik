import 'dart:async';
import 'plugin_registry.dart';

/// flutter_secure_storage is not linked into this runtime yet.
///
/// Secrets must never be kept in plain memory while pretending to be stored in
/// the Keychain / KeyStore, so every call is refused.
class SecureStorageShim implements PyFlutterPlugin {
  @override
  Future<dynamic> handleMethodCall(String method, Map<String, String> args) async {
    throw UnsupportedError(
        'flutter_secure_storage is not linked into the PyFlutter runtime: '
        '"$method" refused (no secret is stored).');
  }
}
