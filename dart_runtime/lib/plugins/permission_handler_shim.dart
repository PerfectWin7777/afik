import 'dart:async';
import 'plugin_registry.dart';

/// Pure Dart native shim for permission_handler.
class PermissionHandlerShim implements PyFlutterPlugin {
  final Map<String, String> _statuses = {};

  @override
  Future<dynamic> handleMethodCall(String method, Map<String, String> args) async {
    final perm = args['permission'] ?? 'camera';

    switch (method) {
      case 'checkPermission':
        final status = _statuses[perm] ?? 'granted';
        return {'permission': perm, 'status': status};

      case 'requestPermission':
        _statuses[perm] = 'granted';
        return {'permission': perm, 'status': 'granted'};

      case 'openAppSettings':
        return {'opened': true};

      default:
        throw UnsupportedError('PermissionHandler method "$method" is not supported.');
    }
  }
}
