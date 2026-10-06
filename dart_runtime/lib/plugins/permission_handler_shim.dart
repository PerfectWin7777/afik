import 'dart:async';
import 'plugin_registry.dart';

/// permission_handler is not linked into this runtime yet.
///
/// Permission state can not be queried or requested, so the shim throws instead
/// of reporting permissions as granted.
class PermissionHandlerShim implements PyFlutterPlugin {
  @override
  Future<dynamic> handleMethodCall(String method, Map<String, String> args) async {
    switch (method) {
      case 'checkPermission':
      case 'requestPermission':
      case 'openAppSettings':
        throw UnsupportedError(
            'permission_handler is not linked into the PyFlutter runtime: '
            '"$method" cannot be answered.');

      default:
        throw UnsupportedError('PermissionHandler method "$method" is not supported.');
    }
  }
}
