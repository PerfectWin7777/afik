import 'package:flutter/material.dart';
import '../core/color_parser.dart';
import 'plugin_registry.dart';

/// Native Flutter shim handling SnackBars, Alert Dialogs, and modal overlays
/// requested asynchronously by the Python application.
class OverlayShim implements PyFlutterPlugin {
  final GlobalKey<ScaffoldMessengerState> scaffoldMessengerKey;
  final GlobalKey<NavigatorState> navigatorKey;
  final void Function(String callbackId, Map<String, String> data)? sendEvent;

  OverlayShim({
    required this.scaffoldMessengerKey,
    required this.navigatorKey,
    this.sendEvent,
  });

  @override
  Future<dynamic> handleMethodCall(String method, Map<String, String> args) async {
    switch (method) {
      case 'show_snack_bar':
        final message = args['message'] ?? '';
        final durationMs = int.tryParse(args['duration_ms'] ?? '4000') ?? 4000;
        final actionLabel = args['action'];
        final actionId = args['action_id'];
        final bgColorHex = args['background_color'];

        final messenger = scaffoldMessengerKey.currentState;
        if (messenger != null) {
          // Hide any currently displayed snackbar before showing the new one
          messenger.hideCurrentSnackBar();
          messenger.showSnackBar(
            SnackBar(
              content: Text(message),
              duration: Duration(milliseconds: durationMs),
              backgroundColor: bgColorHex != null ? parseHexColor(bgColorHex) : null,
              behavior: SnackBarBehavior.floating,
              action: actionLabel != null && actionLabel.isNotEmpty
                  ? SnackBarAction(
                      label: actionLabel,
                      onPressed: () {
                        if (actionId != null && actionId.isNotEmpty && sendEvent != null) {
                          sendEvent!(actionId, {});
                        }
                      },
                    )
                  : null,
            ),
          );
        }
        break;

      case 'show_dialog':
        final title = args['title'] ?? '';
        final content = args['content'] ?? '';
        final confirmLabel = args['confirm_label'] ?? 'OK';
        final confirmId = args['confirm_id'];
        final cancelLabel = args['cancel_label'];
        final cancelId = args['cancel_id'];

        final context = navigatorKey.currentContext;
        if (context != null) {
          showDialog(
            context: context,
            builder: (ctx) => AlertDialog(
              title: Text(title),
              content: Text(content),
              actions: [
                if (cancelLabel != null && cancelLabel.isNotEmpty)
                  TextButton(
                    onPressed: () {
                      Navigator.of(ctx).pop();
                      if (cancelId != null && cancelId.isNotEmpty && sendEvent != null) {
                        sendEvent!(cancelId, {});
                      }
                    },
                    child: Text(cancelLabel),
                  ),
                ElevatedButton(
                  onPressed: () {
                    Navigator.of(ctx).pop();
                    if (confirmId != null && confirmId.isNotEmpty && sendEvent != null) {
                      sendEvent!(confirmId, {});
                    }
                  },
                  child: Text(confirmLabel),
                ),
              ],
            ),
          );
        }
        break;

      default:
        throw UnimplementedError('Method $method not implemented in OverlayShim');
    }
  }
}
