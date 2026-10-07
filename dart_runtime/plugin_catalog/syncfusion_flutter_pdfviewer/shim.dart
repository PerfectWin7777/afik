import 'dart:io';

import 'package:flutter/material.dart';
import 'package:afik_dart_runtime/ir_codec.dart';
import 'package:afik_dart_runtime/plugins/plugin_registry.dart';
import 'package:afik_dart_runtime/widgets/widget_registry.dart';
import 'package:syncfusion_flutter_pdfviewer/pdfviewer.dart';

/// PDF viewer (syncfusion_flutter_pdfviewer). Syncfusion packages require a Syncfusion
/// (community or commercial) licence for your app.
///
/// Widget `SfPdfViewer(src, controller=, can_show_pagination=, width=, height=, on_page_changed=)`.
/// `src` is an http(s) URL, a local file path, or `asset:<name>`. The Python controller's
/// page and zoom travel as the `page` / `zoom` props; page changes come back as events
/// `{'page': '<n>'}`.
class PySfPdfViewerWidget extends StatefulWidget {
  final WidgetNode node;
  final void Function(String callbackId, Map<String, String> eventData) sendEvent;

  const PySfPdfViewerWidget({super.key, required this.node, required this.sendEvent});

  @override
  State<PySfPdfViewerWidget> createState() => _PySfPdfViewerWidgetState();
}

class _PySfPdfViewerWidgetState extends State<PySfPdfViewerWidget> {
  final PdfViewerController _controller = PdfViewerController();
  int _lastPage = 0;
  double _lastZoom = 0;

  @override
  void didUpdateWidget(PySfPdfViewerWidget oldWidget) {
    super.didUpdateWidget(oldWidget);
    final page = int.tryParse(widget.node.props['page'] ?? '');
    if (page != null && page != _lastPage) {
      _lastPage = page;
      _controller.jumpToPage(page);
    }
    final zoom = double.tryParse(widget.node.props['zoom'] ?? '');
    if (zoom != null && zoom != _lastZoom) {
      _lastZoom = zoom;
      _controller.zoomLevel = zoom;
    }
  }

  @override
  Widget build(BuildContext context) {
    final src = widget.node.props['src'] ?? '';
    final paginationDialog = widget.node.props['can_show_pagination'] != 'false';
    void onPage(PdfPageChangedDetails d) {
      _lastPage = d.newPageNumber;
      final id = widget.node.callbackId;
      if (id.isNotEmpty) widget.sendEvent(id, {'page': '${d.newPageNumber}'});
    }

    final Widget viewer;
    if (src.startsWith('http://') || src.startsWith('https://')) {
      viewer = SfPdfViewer.network(src,
          controller: _controller, canShowPaginationDialog: paginationDialog, onPageChanged: onPage);
    } else if (src.startsWith('asset:')) {
      viewer = SfPdfViewer.asset(src.substring('asset:'.length),
          controller: _controller, canShowPaginationDialog: paginationDialog, onPageChanged: onPage);
    } else {
      viewer = SfPdfViewer.file(File(src),
          controller: _controller, canShowPaginationDialog: paginationDialog, onPageChanged: onPage);
    }
    return SizedBox(
      width: double.tryParse(widget.node.props['width'] ?? ''),
      height: double.tryParse(widget.node.props['height'] ?? ''),
      child: viewer,
    );
  }
}

/// This plugin only provides the widget; there are no method calls to answer.
class _NoMethods implements AfikPlugin {
  @override
  Future<dynamic> handleMethodCall(String method, Map<String, String> args) async {
    throw UnsupportedError('syncfusion_flutter_pdfviewer has no method "$method"; use the SfPdfViewer widget.');
  }
}

void register() {
  final shim = _NoMethods();
  PluginRegistry.register('syncfusion_flutter_pdfviewer', shim);
  PluginRegistry.register('syncfusion_pdfviewer', shim);
  WidgetRegistry.register('SfPdfViewer', (node, sendEvent) => PySfPdfViewerWidget(node: node, sendEvent: sendEvent));
}
