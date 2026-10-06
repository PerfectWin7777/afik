import 'dart:async';
import 'dart:io';

import 'package:flutter/material.dart';
import 'package:pdfx/pdfx.dart';
import 'package:pyflutter_dart_runtime/ir_codec.dart';
import 'package:pyflutter_dart_runtime/plugins/plugin_registry.dart';
import 'package:pyflutter_dart_runtime/widgets/widget_registry.dart';

/// PDF documents opened from Python, keyed by document id.
class PdfxRegistry {
  static final Map<String, PdfDocument> documents = {};
  static int _next = 0;

  static String nextId() => 'doc_${_next++}';
}

/// PDF rendering (pdfx).
///
/// `openPdf` returns a document id and page count; `renderPage` renders one page to a PNG
/// file in the temporary directory and returns its path and size.
class PdfxShim implements PyFlutterPlugin {
  PdfDocument _doc(Map<String, String> args) {
    final doc = PdfxRegistry.documents[args['documentId'] ?? ''];
    if (doc == null) throw StateError('Unknown PDF document "${args['documentId']}".');
    return doc;
  }

  @override
  Future<dynamic> handleMethodCall(String method, Map<String, String> args) async {
    switch (method) {
      case 'openPdf':
        final PdfDocument doc;
        if (args['isAsset'] == 'true') {
          doc = await PdfDocument.openAsset(args['url'] ?? '');
        } else {
          doc = await PdfDocument.openFile(args['path'] ?? '');
        }
        final id = PdfxRegistry.nextId();
        PdfxRegistry.documents[id] = doc;
        return {'documentId': id, 'pageCount': doc.pagesCount};

      case 'getPageCount':
        return {'pageCount': _doc(args).pagesCount};

      case 'renderPage':
        final number = int.tryParse(args['pageNumber'] ?? '') ?? 1;
        final page = await _doc(args).getPage(number);
        try {
          final scale = double.tryParse(args['scale'] ?? '') ?? 2.0;
          final image = await page.render(
            width: page.width * scale,
            height: page.height * scale,
            format: PdfPageImageFormat.png,
          );
          if (image == null) throw StateError('pdfx could not render page $number.');
          final file = File('${Directory.systemTemp.path}/pyflutter_${args['documentId']}_p$number.png');
          await file.writeAsBytes(image.bytes);
          return {
            'pageNumber': number,
            'width': image.width,
            'height': image.height,
            'path': file.path,
            'rendered': true,
          };
        } finally {
          await page.close();
        }

      case 'closePdf':
        await PdfxRegistry.documents.remove(args['documentId'] ?? '')?.close();
        return {'closed': true};

      default:
        throw UnsupportedError('pdfx method "$method" is not supported.');
    }
  }
}

/// Widgets `PdfView(path, ...)` and `PdfViewPinch(path, ...)`. The `page` prop (1-based)
/// moves the document; page changes come back as events `{'page': '<n>'}`.
class PyPdfViewWidget extends StatefulWidget {
  final WidgetNode node;
  final void Function(String callbackId, Map<String, String> eventData) sendEvent;
  final bool pinch;

  const PyPdfViewWidget({super.key, required this.node, required this.sendEvent, required this.pinch});

  @override
  State<PyPdfViewWidget> createState() => _PyPdfViewWidgetState();
}

class _PyPdfViewWidgetState extends State<PyPdfViewWidget> {
  PdfController? _controller;
  PdfControllerPinch? _pinchController;
  int _lastPage = 1;

  @override
  void initState() {
    super.initState();
    final path = widget.node.props['path'] ?? '';
    final initial = int.tryParse(widget.node.props['page'] ?? '') ?? 1;
    _lastPage = initial;
    if (widget.pinch) {
      _pinchController = PdfControllerPinch(document: PdfDocument.openFile(path), initialPage: initial);
    } else {
      _controller = PdfController(document: PdfDocument.openFile(path), initialPage: initial);
    }
  }

  @override
  void didUpdateWidget(PyPdfViewWidget oldWidget) {
    super.didUpdateWidget(oldWidget);
    final page = int.tryParse(widget.node.props['page'] ?? '');
    if (page != null && page != _lastPage) {
      _lastPage = page;
      _controller?.jumpToPage(page);
      _pinchController?.jumpToPage(page);
    }
  }

  @override
  void dispose() {
    _controller?.dispose();
    _pinchController?.dispose();
    super.dispose();
  }

  void _onPage(int page) {
    _lastPage = page;
    final id = widget.node.callbackId;
    if (id.isNotEmpty) widget.sendEvent(id, {'page': '$page'});
  }

  @override
  Widget build(BuildContext context) {
    final props = widget.node.props;
    return SizedBox(
      width: double.tryParse(props['width'] ?? ''),
      height: double.tryParse(props['height'] ?? ''),
      child: widget.pinch
          ? PdfViewPinch(controller: _pinchController!, onPageChanged: _onPage)
          : PdfView(controller: _controller!, onPageChanged: _onPage),
    );
  }
}

void register() {
  PluginRegistry.register('pdfx', PdfxShim());
  WidgetRegistry.register('PdfView',
      (node, sendEvent) => PyPdfViewWidget(node: node, sendEvent: sendEvent, pinch: false));
  WidgetRegistry.register('PdfViewPinch',
      (node, sendEvent) => PyPdfViewWidget(node: node, sendEvent: sendEvent, pinch: true));
}
