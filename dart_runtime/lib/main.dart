// PyFlutter Dart Runtime Shell
// Connects to the Rust bridge's relay mode over a local TCP socket,
// decodes incoming Protobuf RenderTree frames, and renders native Flutter widgets.

import 'dart:async';
import 'dart:convert';
import 'dart:io';
import 'dart:typed_data';

import 'package:flutter/material.dart';

import 'core/color_parser.dart';
import 'frame_buffer.dart';
import 'ir_codec.dart';
import 'plugins/overlay_shim.dart';
import 'plugins/plugin_registry.dart';
import 'plugins/url_launcher_shim.dart';
import 'widgets/widget_builder.dart';

void main() {
  // Register default static shims
  PluginRegistry.register('url_launcher', UrlLauncherShim());

  runApp(const PyFlutterShellApp());
}

class PyFlutterShellApp extends StatefulWidget {
  const PyFlutterShellApp({super.key});

  @override
  State<PyFlutterShellApp> createState() => _PyFlutterShellAppState();
}

class _PyFlutterShellAppState extends State<PyFlutterShellApp> {
  final GlobalKey<ScaffoldMessengerState> _scaffoldMessengerKey =
      GlobalKey<ScaffoldMessengerState>();
  final GlobalKey<NavigatorState> _navigatorKey = GlobalKey<NavigatorState>();

  String _title = 'PyFlutter';
  bool _showDebugBanner = false;
  ThemeMode _themeMode = ThemeMode.system;
  Color _seedColor = const Color(0xFF1877F2);
  bool _useMaterial3 = true;
  Color? _scaffoldBackgroundColor;

  void _onAppConfigChanged(Map<String, String> props) {
    bool changed = false;
    String newTitle = _title;
    bool newBanner = _showDebugBanner;
    ThemeMode newMode = _themeMode;
    Color newSeed = _seedColor;
    Color? newScaffoldBg = _scaffoldBackgroundColor;

    if (props.containsKey('title') && props['title']! != _title) {
      newTitle = props['title']!;
      changed = true;
    }
    if (props.containsKey('debug_banner')) {
      final b = props['debug_banner'] == 'true';
      if (b != _showDebugBanner) {
        newBanner = b;
        changed = true;
      }
    }
    if (props.containsKey('theme_mode')) {
      final modeStr = props['theme_mode'];
      ThemeMode m = ThemeMode.system;
      if (modeStr == 'light') m = ThemeMode.light;
      else if (modeStr == 'dark') m = ThemeMode.dark;
      if (m != _themeMode) {
        newMode = m;
        changed = true;
      }
    }
    final seedStr = props['seed_color'] ?? props['theme_seed_color'];
    if (seedStr != null) {
      final parsed = parseHexColor(seedStr);
      if (parsed != null && parsed != _seedColor) {
        newSeed = parsed;
        changed = true;
      }
    }
    if (props.containsKey('theme_scaffold_background_color')) {
      final parsed = parseHexColor(props['theme_scaffold_background_color']!);
      if (parsed != _scaffoldBackgroundColor) {
        newScaffoldBg = parsed;
        changed = true;
      }
    }

    if (changed) {
      WidgetsBinding.instance.addPostFrameCallback((_) {
        if (mounted) {
          setState(() {
            _title = newTitle;
            _showDebugBanner = newBanner;
            _themeMode = newMode;
            _seedColor = newSeed;
            _scaffoldBackgroundColor = newScaffoldBg;
          });
        }
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: _title,
      navigatorKey: _navigatorKey,
      scaffoldMessengerKey: _scaffoldMessengerKey,
      debugShowCheckedModeBanner: _showDebugBanner,
      themeMode: _themeMode,
      theme: ThemeData(
        useMaterial3: _useMaterial3,
        colorScheme: ColorScheme.fromSeed(
          seedColor: _seedColor,
          brightness: Brightness.light,
        ),
        scaffoldBackgroundColor: _scaffoldBackgroundColor,
      ),
      darkTheme: ThemeData(
        useMaterial3: _useMaterial3,
        colorScheme: ColorScheme.fromSeed(
          seedColor: _seedColor,
          brightness: Brightness.dark,
        ),
      ),
      home: BridgeConnectionScreen(
        key: const ValueKey('bridge_screen_root'),
        onAppConfigChanged: _onAppConfigChanged,
        scaffoldMessengerKey: _scaffoldMessengerKey,
        navigatorKey: _navigatorKey,
      ),
    );
  }
}

/// Manages TCP socket communication with the Rust bridge and holds the active widget tree.
class BridgeConnectionScreen extends StatefulWidget {
  final void Function(Map<String, String> config) onAppConfigChanged;
  final GlobalKey<ScaffoldMessengerState> scaffoldMessengerKey;
  final GlobalKey<NavigatorState> navigatorKey;

  const BridgeConnectionScreen({
    super.key,
    required this.onAppConfigChanged,
    required this.scaffoldMessengerKey,
    required this.navigatorKey,
  });

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

    // Register native Overlay plugin shim bound to active Messenger and Navigator keys
    PluginRegistry.register(
      'overlay',
      OverlayShim(
        scaffoldMessengerKey: widget.scaffoldMessengerKey,
        navigatorKey: widget.navigatorKey,
        sendEvent: _sendCallbackEvent,
      ),
    );

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
      if (root != null) {
        widget.onAppConfigChanged(root.props);
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
        backgroundColor: Theme.of(context).scaffoldBackgroundColor,
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

    WidgetNode displayNode = tree;
    // If root node is MaterialApp, render its child home slot
    if (tree.type == 'MaterialApp') {
      if (tree.children.isNotEmpty) {
        displayNode = tree.children.firstWhere(
          (c) => c.props['slot'] == 'home',
          orElse: () => tree.children.first,
        );
      }
    }

    // If the node is a Scaffold, let it drive the entire screen layout
    if (displayNode.type == 'Scaffold') {
      return buildFromNode(displayNode, _sendCallbackEvent);
    }

    // Default wrapper: always protects the UI from Android bottom navigation buttons & notch
    return Scaffold(
      backgroundColor: Theme.of(context).scaffoldBackgroundColor,
      body: SafeArea(
        maintainBottomViewPadding: true,
        child: buildFromNode(displayNode, _sendCallbackEvent),
      ),
    );
  }
}
