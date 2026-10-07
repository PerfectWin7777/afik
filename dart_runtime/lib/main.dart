// Afik Dart Runtime Shell
// Connects to the Rust bridge's relay mode over a local TCP socket,
// decodes incoming Protobuf RenderTree frames, and renders native Flutter widgets.

import 'dart:async';
import 'dart:convert';
import 'dart:io';
import 'dart:typed_data';

import 'package:flutter/material.dart';

import 'bridge/ffi_bridge.dart';
import 'core/color_parser.dart';
import 'frame_buffer.dart';
import 'ir_codec.dart';
import 'plugins/overlay_shim.dart';
import 'plugins/installed_plugins.dart';
import 'plugins/plugin_registry.dart';
import 'widgets/widget_builder.dart';


/// Callback id that asks Python for the full tree (see the Rust bridge and the runner).
const String resyncCallbackId = '__afik_resync__';

void main() {
  // Plugins installed with `afik add` (generated file, empty by default)
  registerInstalledPlugins();




  runApp(const AfikShellApp());
}

class AfikShellApp extends StatefulWidget {
  const AfikShellApp({super.key});

  @override
  State<AfikShellApp> createState() => _AfikShellAppState();
}

class _AfikShellAppState extends State<AfikShellApp> {
  final GlobalKey<ScaffoldMessengerState> _scaffoldMessengerKey =
      GlobalKey<ScaffoldMessengerState>();
  final GlobalKey<NavigatorState> _navigatorKey = GlobalKey<NavigatorState>();

  String _title = 'Afik';
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
  // Set by `afik run` through --dart-define=AFIK_PORT=<port>.
  static const int bridgePort =
      int.fromEnvironment('AFIK_PORT', defaultValue: 7879);
  // Shared secret handed over by `afik run`; empty when attaching manually.
  static const String bridgeToken =
      String.fromEnvironment('AFIK_TOKEN', defaultValue: '');

  Socket? _socket;
  late final FrameBuffer _frameBuffer;
  WidgetNode? _tree;
  String _status = 'connecting...';
  bool _isFFIMode = false;
  StreamSubscription<FFIFrame>? _ffiSub;

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

    _initBridge();
  }

  void _initBridge() {
    final ffi = AfikFFIBridge();
    const bool isExplicitStandalone =
        bool.fromEnvironment('AFIK_STANDALONE', defaultValue: false);

    // The in-process FFI transport is only used by standalone builds. Probing
    // for the native library in development would hijack the TCP relay as soon
    // as `cargo build` has produced afik_bridge.{so,dll}.
    if (isExplicitStandalone) {
      final success = ffi.init();
      if (success) {
        setState(() {
          _isFFIMode = true;
          _status = 'embedded (standalone)';
        });
        _ffiSub = ffi.frameStream.listen((frame) {
          _handleFrame(frame.msgType, frame.payload);
        });
        return;
      }
    }

    // Development fallback: connect to local TCP socket relay
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
        if (bridgeToken.isNotEmpty) {
          socket.add(encodeFrame(
              msgHello, Uint8List.fromList(utf8.encode(bridgeToken))));
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
    } else if (msgType == msgTreePatch) {
      _handleTreePatch(payload);
    } else if (msgType == msgPluginCall) {
      _handlePluginCall(payload);
    }
  }

  void _handleTreePatch(Uint8List payload) {
    try {
      final jsonStr = utf8.decode(payload);
      final data = jsonDecode(jsonStr) as Map<String, dynamic>;
      final updates = data['updates'] as List<dynamic>?;
      if (updates != null && _tree != null) {
        bool modified = false;
        bool unknownNode = false;
        for (final item in updates) {
          final u = item as Map<String, dynamic>;
          final nid = u['id'] as String?;
          if (nid == null) continue;
          final target = findNodeById(_tree!, nid);
          if (target == null) {
            unknownNode = true;
            continue;
          }
          if (u.containsKey('props')) {
            final p = u['props'] as Map<String, dynamic>;
            // An empty string is a real value; removals are listed in "remove".
            p.forEach((k, v) {
              if (v == null) {
                target.props.remove(k);
              } else {
                target.props[k] = v.toString();
              }
            });
            modified = true;
          }
          if (u.containsKey('remove')) {
            for (final k in (u['remove'] as List<dynamic>)) {
              target.props.remove(k.toString());
            }
            modified = true;
          }
          if (u.containsKey('callback_id')) {
            target.callbackId = u['callback_id'] as String? ?? '';
            modified = true;
          }
        }
        if (modified && mounted) {
          setState(() {});
        }
        if (unknownNode) {
          // The patch addressed a node this tree does not have: ask Python for the full tree.
          debugPrint('[patch] unknown node id, requesting a full tree');
          _sendCallbackEvent(resyncCallbackId, const {});
        }
      } else if (updates != null) {
        // A patch with no tree to apply it to: ask for the full tree.
        _sendCallbackEvent(resyncCallbackId, const {});
      }
    } catch (e) {
      debugPrint('[patch error] Failed to apply tree patch: $e');
    }
  }

  Future<void> _handlePluginCall(Uint8List payload) async {
    final str = utf8.decode(payload);
    final parts = str.split('\x00');
    if (parts.length >= 4) {
      final pluginName = parts[0];
      final method = parts[1];
      final callId = parts[2];
      final argsJson = parts[3];
      try {
        final Map<String, dynamic> rawMap = jsonDecode(argsJson);
        final res = await PluginRegistry.dispatch(pluginName, method, rawMap);
        _sendPluginResponse(callId, res);
      } catch (e) {
        debugPrint('[plugin error] $pluginName.$method: $e');
        _sendPluginResponse(callId, null, e.toString());
      }
    } else if (parts.length >= 3) {
      final pluginName = parts[0];
      final method = parts[1];
      final argsJson = parts[2];
      try {
        final Map<String, dynamic> rawMap = jsonDecode(argsJson);
        await PluginRegistry.dispatch(pluginName, method, rawMap);
      } catch (e) {
        debugPrint('[plugin error] $pluginName.$method: $e');
      }
    }
  }

  void _sendPluginResponse(String callId, dynamic result, [String? error]) {
    List<int> body;
    try {
      body = utf8.encode(jsonEncode({
        'call_id': callId,
        'result': result,
        'error': error,
      }));
    } catch (e) {
      // A non JSON-serializable result must still produce an answer, otherwise
      // Python would wait until its timeout.
      body = utf8.encode(jsonEncode({
        'call_id': callId,
        'result': null,
        'error': 'Result is not serializable: $e',
      }));
    }
    final payload = Uint8List.fromList(body);
    if (_isFFIMode) {
      AfikFFIBridge().pushToPython(msgPluginResponse, payload);
    } else {
      final socket = _socket;
      if (socket != null) {
        socket.add(encodeFrame(msgPluginResponse, payload));
      }
    }
  }

  void _sendCallbackEvent(String callbackId, Map<String, String> eventData) {
    final encoded = encodeCallbackEvent(callbackId, eventData);
    if (_isFFIMode) {
      AfikFFIBridge().pushToPython(msgCallbackEvent, encoded);
    } else {
      final socket = _socket;
      if (socket != null) {
        socket.add(encodeFrame(msgCallbackEvent, encoded));
      }
    }
  }

  @override
  void dispose() {
    _ffiSub?.cancel();
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
              Text('Afik ($_status)'),
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
