import 'dart:async';
import 'package:flutter/services.dart';

/// Base interface that any native PyFlutter plugin shim must implement.
abstract class PyFlutterPlugin {
  Future<dynamic> handleMethodCall(String method, Map<String, String> args);
}

/// Central registry for native Flutter plugins and universal MethodChannel dispatcher.
class PluginRegistry {
  static final Map<String, PyFlutterPlugin> _plugins = {};

  /// Registers a plugin under a unique name (e.g. "url_launcher").
  static void register(String name, PyFlutterPlugin plugin) {
    _plugins[name] = plugin;
  }

  /// Dispatches a method invocation from Python to either a registered shim
  /// or directly to Flutter's native MethodChannel for arbitrary pub.dev packages.
  static Future<dynamic> dispatch(
    String pluginName,
    String method,
    Map<String, dynamic> rawArgs,
  ) async {
    final plugin = _plugins[pluginName];
    if (plugin != null) {
      final Map<String, String> strArgs =
          rawArgs.map((k, v) => MapEntry(k, v?.toString() ?? ''));
      return await plugin.handleMethodCall(method, strArgs);
    }

    // Universal MethodChannel fallback (supports 100% of pub.dev plugins)
    return await _dispatchToMethodChannel(pluginName, method, rawArgs);
  }

  static Future<dynamic> _dispatchToMethodChannel(
    String pluginOrChannelName,
    String method,
    Map<String, dynamic> rawArgs,
  ) async {
    String targetChannelName = pluginOrChannelName;
    String targetMethod = method;
    dynamic targetArguments = rawArgs;

    if (pluginOrChannelName == '__method_channel__') {
      targetChannelName = rawArgs['channel']?.toString() ?? '';
      targetMethod = rawArgs['method']?.toString() ?? method;
      targetArguments = rawArgs['arguments'];
    }

    if (targetChannelName.isEmpty) {
      return {
        'platform_error': {
          'code': 'INVALID_CHANNEL',
          'message': 'MethodChannel name cannot be empty.',
          'details': null,
        }
      };
    }

    final channel = MethodChannel(targetChannelName);
    try {
      final result = await channel.invokeMethod(targetMethod, targetArguments);
      return result;
    } on PlatformException catch (e) {
      return {
        'platform_error': {
          'code': e.code,
          'message': e.message,
          'details': e.details?.toString(),
        }
      };
    } catch (e) {
      return {
        'platform_error': {
          'code': 'NATIVE_ERROR',
          'message': e.toString(),
          'details': null,
        }
      };
    }
  }
}

