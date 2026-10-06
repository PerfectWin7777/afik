import 'package:flutter/material.dart';
import 'package:flutter_pdfview/flutter_pdfview.dart';
import 'package:pyflutter_dart_runtime/ir_codec.dart';
import 'package:pyflutter_dart_runtime/plugins/plugin_registry.dart';
import 'package:pyflutter_dart_runtime/widgets/widget_registry.dart';

/// Native PDF view (flutter_pdfview, Android and iOS only).
///
/// Widget `PDFView(file_path, enable_swipe=, swipe_horizontal=, width=, height=, on_page_changed=)`.
/// The `page` prop (0-based) moves the document; page changes come back as events
/// `{'page': '<n>', 'total': '<count>'}`.
class PyFlutterPdfViewWidget extends StatefulWidget {
  final WidgetNode node;
  final void Function(String callbackId, Map<String, String> eventData) sendEvent;

  const PyFlutterPdfViewWidget({super.key, required this.node, required this.sendEvent});

  @override
  State<PyFlutterPdfViewWidget> createState() => _PyFlutterPdfViewWidgetState();
}

class _PyFlutterPdfViewWidgetState extends State<PyFlutterPdfViewWidget> {
  PDFViewController? _controller;
  int _lastPage = 0;

  @override
  void didUpdateWidget(PyFlutterPdfViewWidget oldWidget) {
    super.didUpdateWidget(oldWidget);
    final page = int.tryParse(widget.node.props['page'] ?? '');
    if (page != null && page != _lastPage) {
      _lastPage = page;
      _controller?.setPage(page);
    }
  }

  @override
  Widget build(BuildContext context) {
    final props = widget.node.props;
    return SizedBox(
      width: double.tryParse(props['width'] ?? ''),
      height: double.tryParse(props['height'] ?? ''),
      child: PDFView(
        filePath: props['file_path'] ?? '',
        enableSwipe: props['enable_swipe'] != 'false',
        swipeHorizontal: props['swipe_horizontal'] == 'true',
        defaultPage: int.tryParse(props['page'] ?? '') ?? 0,
        onViewCreated: (controller) => _controller = controller,
        onPageChanged: (page, total) {
          _lastPage = page ?? 0;
          final id = widget.node.callbackId;
          if (id.isNotEmpty) widget.sendEvent(id, {'page': '${page ?? 0}', 'total': '${total ?? 0}'});
        },
        onError: (error) {
          final id = widget.node.callbackId;
          if (id.isNotEmpty) widget.sendEvent(id, {'error': error.toString()});
        },
      ),
    );
  }
}

class _NoMethods implements PyFlutterPlugin {
  @override
  Future<dynamic> handleMethodCall(String method, Map<String, String> args) async {
    throw UnsupportedError('flutter_pdfview has no method "$method"; use the PDFView widget.');
  }
}

void register() {
  PluginRegistry.register('flutter_pdfview', _NoMethods());
  WidgetRegistry.register('PDFView', (node, sendEvent) => PyFlutterPdfViewWidget(node: node, sendEvent: sendEvent));
}
