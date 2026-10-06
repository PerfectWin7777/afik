import 'package:url_launcher/url_launcher.dart';
import 'package:pyflutter_dart_runtime/plugins/plugin_registry.dart';

/// Native dispatch shim for the Flutter url_launcher package.
class UrlLauncherShim extends PyFlutterPlugin {
  @override
  Future<dynamic> handleMethodCall(String method, Map<String, String> args) async {
    switch (method) {
      case 'open_url':
        final urlStr = args['url'] ?? '';
        final uri = Uri.parse(urlStr);
        try {
          return await launchUrl(uri, mode: LaunchMode.externalApplication);
        } catch (_) {
          return await launchUrl(uri, mode: LaunchMode.platformDefault);
        }

      case 'make_call':
        final phone = args['phone'] ?? '';
        final uri = Uri.parse('tel:$phone');
        try {
          return await launchUrl(uri);
        } catch (_) {
          return false;
        }

      case 'send_email':
        final email = args['email'] ?? '';
        final subject = args['subject'] ?? '';
        final uri = Uri.parse('mailto:$email?subject=${Uri.encodeComponent(subject)}');
        try {
          return await launchUrl(uri);
        } catch (_) {
          return false;
        }

      default:
        throw UnsupportedError('Method "$method" is not supported by url_launcher shim.');
    }
  }
}

/// Called by the generated `installed_plugins.dart` when this plugin is installed.
void register() {
  PluginRegistry.register('url_launcher', UrlLauncherShim());
}
