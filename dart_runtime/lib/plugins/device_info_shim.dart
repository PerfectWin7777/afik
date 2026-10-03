import 'dart:async';
import 'dart:io';
import 'package:device_info_plus/device_info_plus.dart';
import 'plugin_registry.dart';

/// Real native device & OS metadata using Flutter's device_info_plus package.
class DeviceInfoShim implements PyFlutterPlugin {
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
