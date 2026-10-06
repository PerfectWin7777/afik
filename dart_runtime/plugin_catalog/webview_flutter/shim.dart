import 'dart:async';

import 'package:flutter/material.dart';
import 'package:pyflutter_dart_runtime/ir_codec.dart';
import 'package:pyflutter_dart_runtime/plugins/plugin_registry.dart';
import 'package:pyflutter_dart_runtime/widgets/widget_registry.dart';
import 'package:webview_flutter/webview_flutter.dart';

/// Web view controllers keyed by the `view_id` used from Python.
class WebViewRegistry {
  static final Map<String, WebViewController> controllers = {};
  static final ValueNotifier<int> version = ValueNotifier<int>(0);

  static WebViewController obtain(String id) {
    return controllers.putIfAbsent(id, () {
      final controller = WebViewController()..setJavaScriptMode(JavaScriptMode.unrestricted);
      version.value++;
      return controller;
    });
  }
}

/// Embedded browser (webview_flutter).
class WebViewShim implements PyFlutterPlugin {
  WebViewController _controller(Map<String, String> args) =>
      WebViewRegistry.obtain(args['viewId'] ?? 'default');

  @override
  Future<dynamic> handleMethodCall(String method, Map<String, String> args) async {
    final controller = _controller(args);
    switch (method) {
      case 'loadUrl':
        final uri = Uri.tryParse(args['url'] ?? '');
        if (uri == null) throw ArgumentError('Invalid URL "${args['url']}".');
        await controller.loadRequest(uri);
        return {'url': uri.toString()};

      case 'loadHtml':
        await controller.loadHtmlString(args['html'] ?? '');
        return {'success': true};

      case 'reload':
        await controller.reload();
        return {'reloaded': true};

      case 'goBack':
        final can = await controller.canGoBack();
        if (can) await controller.goBack();
        return {'success': can};

      case 'goForward':
        final can = await controller.canGoForward();
        if (can) await controller.goForward();
        return {'success': can};

      case 'canGoBack':
        return {'canGoBack': await controller.canGoBack()};

      case 'canGoForward':
        return {'canGoForward': await controller.canGoForward()};

      case 'evaluateJavascript':
        final result = await controller.runJavaScriptReturningResult(args['script'] ?? '');
        return result.toString();

      case 'currentUrl':
        return {'url': await controller.currentUrl()};

      default:
        throw UnsupportedError('WebView method "$method" is not supported.');
    }
  }
}

/// Widget `WebView(url, controller=, width=, height=, show_address_bar=, on_navigation=)`.
class PyWebViewWidget extends StatefulWidget {
  final WidgetNode node;
  final void Function(String callbackId, Map<String, String> eventData) sendEvent;

  const PyWebViewWidget({super.key, required this.node, required this.sendEvent});

  @override
  State<PyWebViewWidget> createState() => _PyWebViewWidgetState();
}

class _PyWebViewWidgetState extends State<PyWebViewWidget> {
  late final WebViewController _controller;
  String _loadedUrl = '';
  String _shownUrl = '';

  @override
  void initState() {
    super.initState();
    final viewId = widget.node.props['view_id'] ?? '';
    _controller = viewId.isEmpty
        ? (WebViewController()..setJavaScriptMode(JavaScriptMode.unrestricted))
        : WebViewRegistry.obtain(viewId);
    _controller.setNavigationDelegate(NavigationDelegate(
      onUrlChange: (change) {
        if (mounted) setState(() => _shownUrl = change.url ?? _shownUrl);
      },
      onPageFinished: (url) => _emit({'event': 'page_finished', 'url': url}),
      onWebResourceError: (error) => _emit({'event': 'error', 'message': error.description}),
    ));
    _loadUrlProp();
  }

  @override
  void didUpdateWidget(PyWebViewWidget oldWidget) {
    super.didUpdateWidget(oldWidget);
    _loadUrlProp();
  }

  void _emit(Map<String, String> data) {
    final id = widget.node.callbackId;
    if (id.isNotEmpty) widget.sendEvent(id, data);
  }

  /// Loads the `url` prop when it changed (a controller driven from Python loads its own URLs).
  void _loadUrlProp() {
    final url = widget.node.props['url'] ?? '';
    final uri = Uri.tryParse(url);
    if (url.isEmpty || url == 'about:blank' || url == _loadedUrl || uri == null) return;
    _loadedUrl = url;
    _shownUrl = url;
    _controller.loadRequest(uri);
  }

  @override
  Widget build(BuildContext context) {
    final width = double.tryParse(widget.node.props['width'] ?? '');
    final height = double.tryParse(widget.node.props['height'] ?? '');
    final showAddressBar = widget.node.props['show_address_bar'] != 'false';

    return SizedBox(
      width: width,
      height: height,
      child: Column(
        children: [
          if (showAddressBar)
            Row(
              children: [
                IconButton(icon: const Icon(Icons.arrow_back, size: 18), onPressed: () async {
                  if (await _controller.canGoBack()) await _controller.goBack();
                }),
                IconButton(icon: const Icon(Icons.arrow_forward, size: 18), onPressed: () async {
                  if (await _controller.canGoForward()) await _controller.goForward();
                }),
                IconButton(icon: const Icon(Icons.refresh, size: 18), onPressed: _controller.reload),
                Expanded(child: Text(_shownUrl, maxLines: 1, overflow: TextOverflow.ellipsis)),
              ],
            ),
          Expanded(child: WebViewWidget(controller: _controller)),
        ],
      ),
    );
  }
}

void register() {
  final shim = WebViewShim();
  PluginRegistry.register('webview_flutter', shim);
  PluginRegistry.register('webview', shim);
  WidgetRegistry.register('WebView', (node, sendEvent) => PyWebViewWidget(node: node, sendEvent: sendEvent));
}
