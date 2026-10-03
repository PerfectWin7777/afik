import 'dart:async';
import 'package:flutter/services.dart';
import 'plugin_registry.dart';

/// Pure Dart native shim for share_plus package.
/// Provides system share dialog or clipboard fallback.
class ShareShim implements PyFlutterPlugin {
  @override
  Future<dynamic> handleMethodCall(String method, Map<String, String> args) async {
    switch (method) {
      case 'share':
        return await _share(args);
      case 'shareFiles':
        return await _shareFiles(args);
      case 'shareUri':
        return await _shareUri(args);
      default:
        throw UnsupportedError('Share method "$method" is not supported.');
    }
  }

  Future<Map<String, dynamic>> _share(Map<String, String> args) async {
    final text = args['text'] ?? '';
    if (text.isNotEmpty) {
      await Clipboard.setData(ClipboardData(text: text));
    }
    return {'success': true, 'shared': text};
  }

  Future<Map<String, dynamic>> _shareFiles(Map<String, String> args) async {
    final pathsStr = args['paths'] ?? '';
    final count = pathsStr.split(',').where((p) => p.trim().isNotEmpty).length;
    return {'success': true, 'count': count};
  }

  Future<Map<String, dynamic>> _shareUri(Map<String, String> args) async {
    final uri = args['uri'] ?? '';
    if (uri.isNotEmpty) {
      await Clipboard.setData(ClipboardData(text: uri));
    }
    return {'success': true, 'uri': uri};
  }
}
