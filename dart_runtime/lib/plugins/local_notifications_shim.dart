import 'dart:async';
import 'package:flutter/material.dart';
import 'plugin_registry.dart';

/// Pure Dart native shim for flutter_local_notifications.
class LocalNotificationsShim implements PyFlutterPlugin {
  final List<Map<String, dynamic>> _active = [];

  @override
  Future<dynamic> handleMethodCall(String method, Map<String, String> args) async {
    switch (method) {
      case 'initialize':
        return {'initialized': true};

      case 'show':
        final id = int.tryParse(args['id'] ?? '0') ?? 0;
        final title = args['title'] ?? '';
        final body = args['body'] ?? '';
        final payload = args['payload'];

        final notif = {
          'id': id,
          'title': title,
          'body': body,
          'payload': payload,
          'timestamp': DateTime.now().toIso8601String(),
        };
        _active.removeWhere((item) => item['id'] == id);
        _active.add(notif);
        debugPrint('[notification] ($id) $title: $body');
        return {'id': id, 'shown': true};

      case 'cancel':
        final id = int.tryParse(args['id'] ?? '0') ?? 0;
        _active.removeWhere((item) => item['id'] == id);
        return {'id': id, 'cancelled': true};

      case 'cancelAll':
        final count = _active.length;
        _active.clear();
        return {'cancelledCount': count};

      case 'getActiveNotifications':
        return List<Map<String, dynamic>>.from(_active);

      default:
        throw UnsupportedError('LocalNotifications method "$method" is not supported.');
    }
  }
}
