import 'dart:async';

/// Base interface that any native PyFlutter plugin shim must implement.
abstract class PyFlutterPlugin {
  Future<dynamic> handleMethodCall(String method, Map<String, String> args);
}

/// Central registry for native Flutter plugins in the PyFlutter shell.
class PluginRegistry {
  static final Map<String, PyFlutterPlugin> _plugins = {};

  /// Registers a plugin under a unique name (e.g. "url_launcher").
  static void register(String name, PyFlutterPlugin plugin) {
    _plugins[name] = plugin;
  }

  /// Dispatches a method invocation from Python to the appropriate plugin.
  static Future<dynamic> dispatch(
    String pluginName,
    String method,
    Map<String, String> args,
  ) async {
    final plugin = _plugins[pluginName];
    if (plugin == null) {
      throw UnsupportedError('Plugin "$pluginName" is not registered in the Dart shell.');
    }
    return await plugin.handleMethodCall(method, args);
  }
}
