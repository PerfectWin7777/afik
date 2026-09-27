import 'package:url_launcher/url_launcher.dart';
import 'plugin_registry.dart';

/// Native dispatch shim for the Flutter url_launcher package.
class UrlLauncherShim extends PyFlutterPlugin {
  @override
  Future<dynamic> handleMethodCall(String method, Map<String, String> args) async {
    switch (method) {
      case 'open_url':
        final urlStr = args['url'] ?? '';
        final uri = Uri.parse(urlStr);
        if (await canLaunchUrl(uri)) {
          return await launchUrl(uri, mode: LaunchMode.externalApplication);
        }
        return false;

      case 'make_call':
        final phone = args['phone'] ?? '';
        final uri = Uri.parse('tel:$phone');
        return await launchUrl(uri);

      case 'send_email':
        final email = args['email'] ?? '';
        final subject = args['subject'] ?? '';
        final uri = Uri.parse('mailto:$email?subject=${Uri.encodeComponent(subject)}');
        return await launchUrl(uri);

      default:
        throw UnsupportedError('Method "$method" is not supported by url_launcher shim.');
    }
  }
}
