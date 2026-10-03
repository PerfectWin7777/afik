import 'dart:async';
import 'plugin_registry.dart';

/// Pure Dart native shim for local_auth biometric authentication.
class LocalAuthShim implements PyFlutterPlugin {
  @override
  Future<dynamic> handleMethodCall(String method, Map<String, String> args) async {
    switch (method) {
      case 'canCheckBiometrics':
        return {'canCheck': true};

      case 'isDeviceSupported':
        return {'supported': true};

      case 'getAvailableBiometrics':
        return ['fingerprint', 'face', 'weak', 'strong'];

      case 'authenticate':
        return {'authenticated': true};

      case 'stopAuthentication':
        return {'stopped': true};

      default:
        throw UnsupportedError('LocalAuth method "$method" is not supported.');
    }
  }
}
