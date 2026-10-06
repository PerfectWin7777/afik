import 'dart:async';
import 'dart:convert';

import 'package:pyflutter_dart_runtime/plugins/plugin_registry.dart';
import 'package:share_plus/share_plus.dart';

/// Native share sheet (share_plus).
///
/// `success` is true only when the platform reports that the user picked a target
/// (`status == "success"`). When the platform cannot tell (`unavailable`) the status is
/// returned and `success` stays false, so Python never assumes a share happened.
class ShareShim implements PyFlutterPlugin {
  @override
  Future<dynamic> handleMethodCall(String method, Map<String, String> args) async {
    switch (method) {
      case 'share':
        return _report(await SharePlus.instance.share(ShareParams(
          text: args['text'],
          subject: _nonEmpty(args['subject']),
          title: _nonEmpty(args['title']),
        )));

      case 'shareFiles':
        // `paths` is a JSON list of file paths.
        final paths = (jsonDecode(args['paths'] ?? '[]') as List).map((p) => p.toString()).toList();
        if (paths.isEmpty) {
          throw ArgumentError('shareFiles needs at least one path.');
        }
        return _report(await SharePlus.instance.share(ShareParams(
          files: paths.map((p) => XFile(p)).toList(),
          text: _nonEmpty(args['text']),
          subject: _nonEmpty(args['subject']),
        )));

      case 'shareUri':
        final uri = Uri.tryParse(args['uri'] ?? '');
        if (uri == null) {
          throw ArgumentError('Invalid URI "${args['uri']}".');
        }
        return _report(await SharePlus.instance.share(ShareParams(uri: uri)));

      default:
        throw UnsupportedError('Share method "$method" is not supported.');
    }
  }

  String? _nonEmpty(String? v) => (v == null || v.isEmpty) ? null : v;

  Map<String, dynamic> _report(ShareResult result) => {
        'success': result.status == ShareResultStatus.success,
        'status': result.status.name,
      };
}

void register() {
  final shim = ShareShim();
  PluginRegistry.register('share_plus', shim);
  PluginRegistry.register('share', shim);
}
