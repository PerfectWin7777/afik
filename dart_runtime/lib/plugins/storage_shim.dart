import 'dart:async';
import 'dart:convert';
import 'dart:io';

import 'plugin_registry.dart';

/// Implements persistent Key-Value storage (matching shared_preferences).
/// Stores key-value entries in a local JSON file in application storage.
class StorageShim implements PyFlutterPlugin {
  static final Map<String, dynamic> _memoryCache = {};
  static bool _loaded = false;
  static File? _storageFile;

  static Future<void> _ensureLoaded() async {
    if (_loaded) return;
    try {
      final baseDir = Directory.systemTemp;
      _storageFile = File('${baseDir.path}/.pyflutter_storage.json');
      if (await _storageFile!.exists()) {
        final content = await _storageFile!.readAsString();
        if (content.isNotEmpty) {
          final decoded = jsonDecode(content) as Map<String, dynamic>;
          _memoryCache.addAll(decoded);
        }
      }
    } catch (_) {}
    _loaded = true;
  }

  static Future<void> _save() async {
    try {
      if (_storageFile != null) {
        await _storageFile!.writeAsString(jsonEncode(_memoryCache));
      }
    } catch (_) {}
  }

  @override
  Future<dynamic> handleMethodCall(String method, Map<String, String> args) async {
    await _ensureLoaded();
    final key = args['key'] ?? '';

    switch (method) {
      case 'setString':
      case 'set_string':
        final val = args['value'] ?? '';
        _memoryCache[key] = val;
        await _save();
        return true;

      case 'getString':
      case 'get_string':
        return _memoryCache[key]?.toString();

      case 'setInt':
      case 'set_int':
        final val = int.tryParse(args['value'] ?? '') ?? 0;
        _memoryCache[key] = val;
        await _save();
        return true;

      case 'getInt':
      case 'get_int':
        final v = _memoryCache[key];
        return v is int ? v : int.tryParse(v?.toString() ?? '');

      case 'setBool':
      case 'set_bool':
        final val = args['value'] == 'true';
        _memoryCache[key] = val;
        await _save();
        return true;

      case 'getBool':
      case 'get_bool':
        final v = _memoryCache[key];
        return v is bool ? v : (v?.toString().toLowerCase() == 'true');

      case 'setDouble':
      case 'set_double':
        final val = double.tryParse(args['value'] ?? '') ?? 0.0;
        _memoryCache[key] = val;
        await _save();
        return true;

      case 'getDouble':
      case 'get_double':
        final v = _memoryCache[key];
        return v is num ? v.toDouble() : double.tryParse(v?.toString() ?? '');

      case 'remove':
        _memoryCache.remove(key);
        await _save();
        return true;

      case 'clear':
        _memoryCache.clear();
        await _save();
        return true;

      case 'getAll':
      case 'get_all':
        return Map<String, dynamic>.from(_memoryCache);

      default:
        throw UnsupportedError('Unsupported Storage method: $method');
    }
  }
}
