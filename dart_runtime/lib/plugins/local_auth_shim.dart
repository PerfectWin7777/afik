import 'dart:async';
import 'package:local_auth/local_auth.dart';
import 'plugin_registry.dart';

/// Real biometric / device-credential authentication (local_auth ^2.3).
///
/// Only the platform's own answer is ever reported: when the user cancels or the
/// check fails, `authenticated` is false and platform errors are thrown, so Python
/// can never mistake a failure for a success.
class LocalAuthShim implements PyFlutterPlugin {
  final LocalAuthentication _auth = LocalAuthentication();

  @override
  Future<dynamic> handleMethodCall(String method, Map<String, String> args) async {
    switch (method) {
      case 'canCheckBiometrics':
        return {'canCheck': await _auth.canCheckBiometrics};

      case 'isDeviceSupported':
        return {'supported': await _auth.isDeviceSupported()};

      case 'getAvailableBiometrics':
        final list = await _auth.getAvailableBiometrics();
        return list.map((b) => b.name).toList();

      case 'authenticate':
        final ok = await _auth.authenticate(
          localizedReason: args['localizedReason'] ?? '',
          options: AuthenticationOptions(
            biometricOnly: args['biometricOnly'] == 'true',
          ),
        );
        return {'authenticated': ok};

      case 'stopAuthentication':
        return {'stopped': await _auth.stopAuthentication()};

      default:
        throw UnsupportedError('LocalAuth method "$method" is not supported.');
    }
  }
}
