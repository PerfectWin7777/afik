import 'dart:async';

import 'package:connectivity_plus/connectivity_plus.dart';
import 'package:pyflutter_dart_runtime/plugins/plugin_registry.dart';

/// Real network state (connectivity_plus).
///
/// `checkConnectivity` answers with every active connection type reported by the platform
/// (`results`) and the first one as `status` ("none" when the device is offline).
class ConnectivityShim implements PyFlutterPlugin {
  final Connectivity _connectivity = Connectivity();

  @override
  Future<dynamic> handleMethodCall(String method, Map<String, String> args) async {
    switch (method) {
      case 'checkConnectivity':
        final results = await _connectivity.checkConnectivity();
        final names = results.map((r) => r.name).toList();
        return {
          'status': names.isEmpty ? 'none' : names.first,
          'results': names,
        };

      default:
        throw UnsupportedError('Connectivity method "$method" is not supported.');
    }
  }
}

void register() {
  final shim = ConnectivityShim();
  PluginRegistry.register('connectivity', shim);
  PluginRegistry.register('connectivity_plus', shim);
}
