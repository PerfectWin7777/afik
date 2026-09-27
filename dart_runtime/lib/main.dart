// PyFlutter Dart Runtime Shell
// Connects to the Rust bridge's relay mode over a local TCP socket,
// decodes incoming Protobuf RenderTree frames, and renders native Flutter widgets.

import 'dart:async';
import 'dart:convert';
import 'dart:io';
import 'dart:typed_data';

import 'package:flutter/material.dart';

import 'frame_buffer.dart';
import 'ir_codec.dart';
import 'plugins/plugin_registry.dart';
import 'plugins/url_launcher_shim.dart';
import 'widgets/widget_builder.dart';

void main() {
  // Register native plugin shims
  PluginRegistry.register('url_launcher', UrlLauncherShim());

  runApp(const PyFlutterShellApp());
}

class PyFlutterShellApp extends StatefulWidget {
  const PyFlutterShellApp({super.key});

  @override
  State<PyFlutterShellApp> createState() => _PyFlutterShellAppState();
}

class _PyFlutterShellAppState extends State<PyFlutterShellApp> {
  bool _showDebugBanner = false;

  void _onDebugBannerChanged(bool show) {
    if (_showDebugBanner != show) {
      setState(() {
        _showDebugBanner = show;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'PyFlutter',
      debugShowCheckedModeBanner: _showDebugBanner,
      home: BridgeConnectionScreen(onDebugBannerChanged: _onDebugBannerChanged),
    );
  }
}

/// Manages TCP socket communication with the Rust bridge and holds the active widget tree.
class BridgeConnectionScreen extends StatefulWidget {
  final void Function(bool show)? onDebugBannerChanged;
  const BridgeConnectionScreen({super.key, this.onDebugBannerChanged});

  @override
  State<BridgeConnectionScreen> createState() => _BridgeConnectionScreenState();
}

class _BridgeConnectionScreenState extends State<BridgeConnectionScreen> {
  static const int bridgePort = 7879;

  Socket? _socket;
  late final FrameBuffer _frameBuffer;
  WidgetNode? _tree;
  String _status = 'connecting...';

  @override
  void initState() {
    super.initState();
    _frameBuffer = FrameBuffer(_handleFrame);
    _connect();
  }

  Future<void> _connect() async {
    while (mounted && _socket == null) {
      try {
        final socket = await Socket.connect(
          '127.0.0.1',
          bridgePort,
          timeout: const Duration(seconds: 2),
        );
        if (!mounted) {
          socket.destroy();
          return;
        }
        setState(() {
          _socket = socket;
          _status = 'connected';
        });
        socket.listen(
          _frameBuffer.addChunk,
          onError: (Object e) {
            if (mounted) {
              setState(() {
                _socket = null;
                _status = 'error: $e, reconnecting...';
              });
              _connect();
            }
          },
          onDone: () {
            if (mounted) {
              setState(() {
                _socket = null;
                _status = 'bridge disconnected, reconnecting...';
              });
              _connect();
            }
          },
        );
        break;
      } catch (e) {
        if (mounted) {
          setState(() => _status = 'waiting for bridge...');
        }
        await Future.delayed(const Duration(seconds: 2));
      }
    }
  }

  void _handleFrame(int msgType, Uint8List payload) {
    if (msgType == msgRenderTree) {
      final root = decodeRenderTree(payload);
      if (root != null && root.props.containsKey('debug_banner')) {
        widget.onDebugBannerChanged?.call(root.props['debug_banner'] == 'true');
      }
      setState(() {
        _tree = root;
      });
    } else if (msgType == 0x03) {
      _handlePluginCall(payload);
    }
  }

  Future<void> _handlePluginCall(Uint8List payload) async {
    final str = utf8.decode(payload);
    final parts = str.split('\x00');
    if (parts.length >= 3) {
      final pluginName = parts[0];
      final method = parts[1];
      final argsJson = parts[2];
      try {
        final Map<String, dynamic> rawMap = jsonDecode(argsJson);
        final Map<String, String> args =
            rawMap.map((k, v) => MapEntry(k, v.toString()));
        await PluginRegistry.dispatch(pluginName, method, args);
      } catch (e) {
        debugPrint('[plugin error] $pluginName.$method: $e');
      }
    }
  }

  void _sendCallbackEvent(String callbackId, Map<String, String> eventData) {
    final socket = _socket;
    if (socket == null) return;
    final encoded = encodeCallbackEvent(callbackId, eventData);
    socket.add(encodeFrame(msgCallbackEvent, encoded));
  }

  @override
  void dispose() {
    _socket?.destroy();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final tree = _tree;
    if (tree == null) {
      return Scaffold(
        backgroundColor: const Color(0xFFF0F2F5),
        body: Center(
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              const CircularProgressIndicator(),
              const SizedBox(height: 16),
              Text('PyFlutter ($_status)'),
            ],
          ),
        ),
      );
    }

    // If the Python app returns a Scaffold, let it drive the entire screen layout
    if (tree.type == 'Scaffold') {
      return buildFromNode(tree, _sendCallbackEvent);
    }

    // Default wrapper: always protects the UI from Android bottom navigation buttons & notch
    return Scaffold(
      backgroundColor: const Color(0xFFF0F2F5),
      body: SafeArea(
        maintainBottomViewPadding: true,
        child: buildFromNode(tree, _sendCallbackEvent),
      ),
    );
  }
}
