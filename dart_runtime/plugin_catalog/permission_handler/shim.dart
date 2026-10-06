import 'dart:async';
import 'package:permission_handler/permission_handler.dart';
import 'package:pyflutter_dart_runtime/plugins/plugin_registry.dart';

/// Real runtime permission checks and requests (permission_handler).
///
/// Every permission used by the app must also be declared natively: Android
/// permissions through `pyflutter.yaml` (synced into AndroidManifest.xml), iOS
/// usage descriptions in Info.plist plus the matching permission_handler build
/// settings (see the package README).
class PermissionHandlerShim implements PyFlutterPlugin {
  static final Map<String, Permission> _permissions = {
    'camera': Permission.camera,
    'microphone': Permission.microphone,
    'storage': Permission.storage,
    'photos': Permission.photos,
    'location': Permission.location,
    'locationAlways': Permission.locationAlways,
    'locationWhenInUse': Permission.locationWhenInUse,
    'notification': Permission.notification,
    'bluetooth': Permission.bluetooth,
    'contacts': Permission.contacts,
  };

  @override
  Future<dynamic> handleMethodCall(String method, Map<String, String> args) async {
    switch (method) {
      case 'checkPermission':
      case 'requestPermission':
        final name = args['permission'] ?? '';
        final permission = _permissions[name];
        if (permission == null) {
          throw ArgumentError('Unknown permission "$name".');
        }
        final status = method == 'checkPermission'
            ? await permission.status
            : await permission.request();
        return {'permission': name, 'status': _statusName(status)};

      case 'openAppSettings':
        return {'opened': await openAppSettings()};

      default:
        throw UnsupportedError('PermissionHandler method "$method" is not supported.');
    }
  }

  String _statusName(PermissionStatus status) {
    if (status.isGranted) return 'granted';
    if (status.isPermanentlyDenied) return 'permanentlyDenied';
    if (status.isRestricted) return 'restricted';
    if (status.isLimited) return 'limited';
    return 'denied';
  }
}

/// Called by the generated `installed_plugins.dart` when this plugin is installed.
void register() {
  PluginRegistry.register('permission_handler', PermissionHandlerShim());
}
