import 'dart:async';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:afik_dart_runtime/plugins/plugin_registry.dart';

/// Real native Key-Value storage using Flutter's shared_preferences package.
class StorageShim implements AfikPlugin {
  Future<SharedPreferences> get _prefs => SharedPreferences.getInstance();

  @override
  Future<dynamic> handleMethodCall(String method, Map<String, String> args) async {
    final prefs = await _prefs;
    final key = args['key'] ?? '';

    switch (method) {
      case 'setString':
      case 'set_string':
        final val = args['value'] ?? '';
        return await prefs.setString(key, val);

      case 'getString':
      case 'get_string':
        return prefs.getString(key);

      case 'setInt':
      case 'set_int':
        final val = int.tryParse(args['value'] ?? '') ?? 0;
        return await prefs.setInt(key, val);

      case 'getInt':
      case 'get_int':
        return prefs.getInt(key);

      case 'setBool':
      case 'set_bool':
        final val = args['value'] == 'true';
        return await prefs.setBool(key, val);

      case 'getBool':
      case 'get_bool':
        return prefs.getBool(key);

      case 'setDouble':
      case 'set_double':
        final val = double.tryParse(args['value'] ?? '') ?? 0.0;
        return await prefs.setDouble(key, val);

      case 'getDouble':
      case 'get_double':
        return prefs.getDouble(key);

      case 'remove':
        return await prefs.remove(key);

      case 'clear':
        return await prefs.clear();

      case 'getAll':
      case 'get_all':
        final Map<String, dynamic> result = {};
        for (final k in prefs.getKeys()) {
          result[k] = prefs.get(k);
        }
        return result;

      default:
        throw UnsupportedError('Unsupported Storage method: $method');
    }
  }
}

/// Called by the generated `installed_plugins.dart` when this plugin is installed.
void register() {
  PluginRegistry.register('storage', StorageShim());
  PluginRegistry.register('shared_preferences', StorageShim());
}
