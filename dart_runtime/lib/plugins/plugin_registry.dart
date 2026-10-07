import 'dart:async';
import 'dart:convert';
import 'package:flutter/services.dart';

/// Base interface that any native Afik plugin shim must implement.
abstract class AfikPlugin {
  Future<dynamic> handleMethodCall(String method, Map<String, String> args);
}

/// Optional interface for plugins that need structured arguments.
///
/// [AfikPlugin.handleMethodCall] receives every argument as a `String`: strings are passed
/// as they are, `null` becomes `''`, and any other value (number, bool, list, map) becomes its
/// **JSON** text (`true`, `1.5`, `[1,2]`, `{"a":1}`), never Dart's `toString()` syntax.
/// A plugin that wants the decoded values (a list, a nested map, a number) implements this
/// interface too and reads them from [handleRawCall]; the registry then calls it instead.
abstract class StructuredAfikPlugin implements AfikPlugin {
  Future<dynamic> handleRawCall(String method, Map<String, dynamic> args);
}

/// The text form of an argument given to [AfikPlugin.handleMethodCall].
String pluginArgumentText(dynamic value) {
  if (value == null) return '';
  if (value is String) return value;
  return jsonEncode(value);
}

/// Central registry for native Flutter plugins and universal MethodChannel dispatcher.
class PluginRegistry {
  static final Map<String, AfikPlugin> _plugins = {};

  /// Registers a plugin under a unique name (e.g. "url_launcher").
  static void register(String name, AfikPlugin plugin) {
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
      if (plugin is StructuredAfikPlugin) {
        return await plugin.handleRawCall(method, rawArgs);
      }
      final Map<String, String> strArgs =
          rawArgs.map((k, v) => MapEntry(k, pluginArgumentText(v)));
      return await plugin.handleMethodCall(method, strArgs);
    }

    // Only the explicit generic channel call may reach an arbitrary MethodChannel.
    // Any other name is a Afik plugin that is not installed in this runtime.
    if (pluginName != '__method_channel__') {
      throw UnsupportedError(
          'Plugin "$pluginName" is not installed in this runtime. '
          'Install it with: afik add $pluginName');
    }
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

