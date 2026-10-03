import 'dart:async';
import 'plugin_registry.dart';

/// Pure Dart native shim for Hive NoSQL key-value store.
class HiveShim implements PyFlutterPlugin {
  final Map<String, Map<String, dynamic>> _boxes = {};

  Map<String, dynamic> _getBox(String name) {
    return _boxes.putIfAbsent(name, () => {});
  }

  @override
  Future<dynamic> handleMethodCall(String method, Map<String, String> args) async {
    final boxName = args['boxName'] ?? 'default_box';

    switch (method) {
      case 'openBox':
        _getBox(boxName);
        return {'boxName': boxName, 'opened': true};

      case 'put':
        final key = args['key'] ?? '';
        final value = args['value'];
        _getBox(boxName)[key] = value;
        return {'boxName': boxName, 'key': key, 'success': true};

      case 'get':
        final key = args['key'] ?? '';
        final val = _getBox(boxName)[key];
        return {'boxName': boxName, 'key': key, 'value': val ?? args['defaultValue']};

      case 'delete':
        final key = args['key'] ?? '';
        _getBox(boxName).remove(key);
        return {'boxName': boxName, 'key': key, 'success': true};

      case 'clear':
        _getBox(boxName).clear();
        return {'boxName': boxName, 'cleared': true};

      case 'getAll':
        return Map<String, dynamic>.from(_getBox(boxName));

      case 'close':
        _boxes.remove(boxName);
        return {'boxName': boxName, 'closed': true};

      default:
        throw UnsupportedError('Hive method "$method" is not supported.');
    }
  }
}
