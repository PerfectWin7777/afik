import 'dart:async';
import 'dart:convert';
import 'plugin_registry.dart';

/// Pure Dart native shim for sqflite SQLite database operations.
class SqfliteShim implements PyFlutterPlugin {
  final Map<String, List<Map<String, dynamic>>> _tables = {};

  @override
  Future<dynamic> handleMethodCall(String method, Map<String, String> args) async {
    final dbName = args['db'] ?? 'main.db';

    switch (method) {
      case 'openDatabase':
        return {'db': dbName, 'version': int.tryParse(args['version'] ?? '1') ?? 1, 'opened': true};

      case 'execute':
        final sql = args['sql'] ?? '';
        return {'db': dbName, 'sql': sql, 'executed': true};

      case 'insert':
        final table = args['table'] ?? 'default_table';
        final valuesJson = args['values'] ?? '{}';
        Map<String, dynamic> row = {};
        try {
          row = jsonDecode(valuesJson);
        } catch (_) {}
        final rows = _tables.putIfAbsent('$dbName.$table', () => []);
        rows.add(row);
        return {'id': rows.length, 'inserted': true};

      case 'query':
        final table = args['table'] ?? 'default_table';
        final rows = _tables['$dbName.$table'] ?? [];
        return rows;

      case 'delete':
        final table = args['table'] ?? 'default_table';
        final count = _tables['$dbName.$table']?.length ?? 0;
        _tables['$dbName.$table']?.clear();
        return {'deleted': count};

      case 'close':
        return {'db': dbName, 'closed': true};

      default:
        throw UnsupportedError('Sqflite method "$method" is not supported.');
    }
  }
}
