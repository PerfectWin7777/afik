import 'dart:async';
import 'dart:io';
import 'package:device_info_plus/device_info_plus.dart';
import 'package:afik_dart_runtime/plugins/plugin_registry.dart';

/// Real native device & OS metadata using Flutter's device_info_plus package.
class DeviceInfoShim implements AfikPlugin {
  final DeviceInfoPlugin _plugin = DeviceInfoPlugin();

  @override
  Future<dynamic> handleMethodCall(String method, Map<String, String> args) async {
    switch (method) {
      case 'getDeviceInfo':
      case 'get_device_info':
      case 'get':
        final BaseDeviceInfo info = await _plugin.deviceInfo;
        final Map<String, dynamic> data = Map<String, dynamic>.from(info.data);
        data['platform'] = Platform.operatingSystem;
        data['localeName'] = Platform.localeName;
        data['numberOfProcessors'] = Platform.numberOfProcessors;
        return data;

      case 'getPlatform':
      case 'get_platform':
        return Platform.operatingSystem;

      default:
        throw UnsupportedError('Unsupported DeviceInfo method: $method');
    }
  }
}

/// Called by the generated `installed_plugins.dart` when this plugin is installed.
void register() {
  PluginRegistry.register('device_info', DeviceInfoShim());
  PluginRegistry.register('device_info_plus', DeviceInfoShim());
}
