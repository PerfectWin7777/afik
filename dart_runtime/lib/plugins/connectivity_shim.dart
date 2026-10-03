import 'dart:async';
import 'dart:io';
import 'plugin_registry.dart';

/// Pure Dart native shim for connectivity_plus.
/// Inspects network interfaces to report WiFi, Mobile, Ethernet, or None.
class ConnectivityShim implements PyFlutterPlugin {
  @override
  Future<dynamic> handleMethodCall(String method, Map<String, String> args) async {
    switch (method) {
      case 'checkConnectivity':
        return await _checkConnectivity();
      default:
        throw UnsupportedError('Connectivity method "$method" is not supported.');
    }
  }

  Future<Map<String, dynamic>> _checkConnectivity() async {
    try {
      final interfaces = await NetworkInterface.list();
      if (interfaces.isEmpty) {
        return {'status': 'none'};
      }

      for (final iface in interfaces) {
        final name = iface.name.toLowerCase();
        if (name.contains('wlan') || name.contains('wifi') || name.contains('wireless')) {
          return {'status': 'wifi'};
        } else if (name.contains('cellular') || name.contains('mobile') || name.contains('rmnet')) {
          return {'status': 'mobile'};
        } else if (name.contains('eth') || name.contains('en') || name.contains('ethernet')) {
          return {'status': 'ethernet'};
        }
      }

      // Default when an active interface is found
      return {'status': 'wifi'};
    } catch (_) {
      return {'status': 'none'};
    }
  }
}
