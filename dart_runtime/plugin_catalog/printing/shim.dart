import 'dart:async';
import 'dart:io';
import 'dart:typed_data';

import 'package:printing/printing.dart';
import 'package:afik_dart_runtime/plugins/plugin_registry.dart';

/// System print dialog and PDF sharing (printing).
///
/// `printed` / `completed` / `shared` are true only when the platform reports that the
/// user went through with it (the dialog was not cancelled).
class PrintingShim implements AfikPlugin {
  Future<Uint8List> _read(Map<String, String> args) async {
    final path = args['path'] ?? '';
    final file = File(path);
    if (!await file.exists()) throw ArgumentError('PDF file not found: $path');
    return file.readAsBytes();
  }

  @override
  Future<dynamic> handleMethodCall(String method, Map<String, String> args) async {
    switch (method) {
      case 'printPdf':
      case 'layoutPdf':
        final bytes = await _read(args);
        final done = await Printing.layoutPdf(
          onLayout: (_) async => bytes,
          name: args['name'] ?? args['path'] ?? 'document.pdf',
        );
        return method == 'printPdf'
            ? {'printed': done, 'name': args['name']}
            : {'completed': done};

      case 'sharePdf':
        final bytes = await _read(args);
        await Printing.sharePdf(
          bytes: bytes,
          filename: args['name'] ?? 'document.pdf',
        );
        return {'shared': true, 'path': args['path']};

      default:
        throw UnsupportedError('printing method "$method" is not supported.');
    }
  }
}

void register() {
  final shim = PrintingShim();
  PluginRegistry.register('printing', shim);
  PluginRegistry.register('pdf', shim);
}
