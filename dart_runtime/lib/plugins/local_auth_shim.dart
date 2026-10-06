import 'dart:async';
import 'plugin_registry.dart';

/// local_auth is not linked into this runtime yet.
///
/// Every method answers "not available" / throws, so an application can never
/// believe a user was authenticated when no biometric check happened.
class LocalAuthShim implements PyFlutterPlugin {
  @override
  Future<dynamic> handleMethodCall(String method, Map<String, String> args) async {
    switch (method) {
      case 'canCheckBiometrics':
        return {'canCheck': false};

      case 'isDeviceSupported':
        return {'supported': false};

      case 'getAvailableBiometrics':
        return <String>[];

      case 'stopAuthentication':
        return {'stopped': true};

      case 'authenticate':
        throw UnsupportedError(
            'local_auth is not linked into the PyFlutter runtime: authentication refused.');

      default:
        throw UnsupportedError('LocalAuth method "$method" is not supported.');
    }
  }
}
