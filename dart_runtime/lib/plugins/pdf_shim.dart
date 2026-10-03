import 'dart:async';
import 'plugin_registry.dart';

/// Pure Dart native shim for PDF packages (syncfusion_flutter_pdfviewer, pdfx, printing).
class PdfShim implements PyFlutterPlugin {
  int _docCounter = 0;
  final Map<String, int> _documents = {};

  @override
  Future<dynamic> handleMethodCall(String method, Map<String, String> args) async {
    switch (method) {
      case 'openPdf':
        _docCounter++;
        final docId = 'doc_$_docCounter';
        final pageCount = int.tryParse(args['pageCount'] ?? '8') ?? 8;
        _documents[docId] = pageCount;
        return {
          'documentId': docId,
          'pageCount': pageCount,
          'path': args['path'] ?? args['url'] ?? 'document.pdf',
        };

      case 'getPageCount':
        final docId = args['documentId'] ?? '';
        return {'pageCount': _documents[docId] ?? 8};

      case 'renderPage':
        final page = int.tryParse(args['pageNumber'] ?? '1') ?? 1;
        return {
          'pageNumber': page,
          'width': 595.0,
          'height': 842.0, // Standard A4 points
          'rendered': true,
        };

      case 'printPdf':
        return {'printed': true, 'name': args['name'] ?? 'document.pdf'};

      case 'sharePdf':
        return {'shared': true, 'path': args['path'] ?? ''};

      case 'layoutPdf':
        return {'completed': true};

      default:
        throw UnsupportedError('PDF method "$method" is not supported.');
    }
  }
}
