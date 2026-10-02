import 'dart:async';
import 'dart:io';

import 'plugin_registry.dart';

/// Provides device and operating system metadata (matching device_info_plus).
class DeviceInfoShim implements PyFlutterPlugin {
  @override
  Future<dynamic> handleMethodCall(String method, Map<String, String> args) async {
    switch (method) {
      case 'getDeviceInfo':
      case 'get_device_info':
      case 'get':
        return {
          'platform': Platform.operatingSystem,
          'version': Platform.operatingSystemVersion,
          'hostname': Platform.localHostname,
          'numberOfProcessors': Platform.numberOfProcessors,
          'localeName': Platform.localeName,
          'isPhysicalDevice': !Platform.isWindows && !Platform.isLinux && !Platform.isMacOS,
        };

      case 'getPlatform':
      case 'get_platform':
        return Platform.operatingSystem;

      default:
        throw UnsupportedError('Unsupported DeviceInfo method: $method');
    }
  }
}
