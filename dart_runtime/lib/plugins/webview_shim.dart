import 'dart:async';
import 'plugin_registry.dart';

class _WebSession {
  String url = 'about:blank';
  String? html;
  final List<String> history = [];
  int historyIndex = 0;
}

/// Pure Dart native shim for webview_flutter.
/// Manages navigation history, URLs, and JavaScript evaluation state.
class WebViewShim implements PyFlutterPlugin {
  final Map<String, _WebSession> _sessions = {};

  _WebSession _getOrCreateSession(String id) {
    return _sessions.putIfAbsent(id, () => _WebSession());
  }

  @override
  Future<dynamic> handleMethodCall(String method, Map<String, String> args) async {
    final viewId = args['viewId'] ?? 'default';
    final session = _getOrCreateSession(viewId);

    switch (method) {
      case 'loadUrl':
        final url = args['url'] ?? 'about:blank';
        session.url = url;
        session.html = null;
        session.history.add(url);
        session.historyIndex = session.history.length - 1;
        return {'viewId': viewId, 'url': url};

      case 'loadHtml':
        final html = args['html'] ?? '';
        session.html = html;
        session.url = 'data:text/html;charset=utf-8,...';
        return {'viewId': viewId, 'success': true};

      case 'reload':
        return {'viewId': viewId, 'reloaded': true};

      case 'goBack':
        if (session.historyIndex > 0) {
          session.historyIndex--;
          session.url = session.history[session.historyIndex];
          return {'viewId': viewId, 'url': session.url, 'success': true};
        }
        return {'viewId': viewId, 'success': false};

      case 'goForward':
        if (session.historyIndex < session.history.length - 1) {
          session.historyIndex++;
          session.url = session.history[session.historyIndex];
          return {'viewId': viewId, 'url': session.url, 'success': true};
        }
        return {'viewId': viewId, 'success': false};

      case 'canGoBack':
        return {'canGoBack': session.historyIndex > 0};

      case 'canGoForward':
        return {'canGoForward': session.historyIndex < session.history.length - 1};

      case 'evaluateJavascript':
        final script = args['script'] ?? '';
        return {'viewId': viewId, 'result': 'eval($script)'};

      case 'currentUrl':
        return {'viewId': viewId, 'url': session.url};

      default:
        throw UnsupportedError('WebView method "$method" is not supported.');
    }
  }
}
