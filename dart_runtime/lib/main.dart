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
import 'plugins/audio_player_shim.dart';
import 'plugins/camera_shim.dart';
import 'plugins/connectivity_shim.dart';
import 'plugins/device_info_shim.dart';
import 'plugins/file_picker_shim.dart';
import 'plugins/image_picker_shim.dart';
import 'plugins/overlay_shim.dart';
import 'plugins/path_provider_shim.dart';
import 'plugins/plugin_registry.dart';
import 'plugins/share_shim.dart';
import 'plugins/storage_shim.dart';
import 'plugins/url_launcher_shim.dart';
import 'plugins/video_player_shim.dart';
import 'plugins/webview_shim.dart';
import 'plugins/chewie_shim.dart';
import 'plugins/hive_shim.dart';
import 'plugins/local_auth_shim.dart';
import 'plugins/local_notifications_shim.dart';
import 'plugins/permission_handler_shim.dart';
import 'plugins/secure_storage_shim.dart';
import 'plugins/sqflite_shim.dart';
import 'widgets/widget_builder.dart';

void main() {
  // Register default static shims
  PluginRegistry.register('url_launcher', UrlLauncherShim());
  PluginRegistry.register('storage', StorageShim());
  PluginRegistry.register('shared_preferences', StorageShim());
  PluginRegistry.register('path_provider', PathProviderShim());
  PluginRegistry.register('device_info', DeviceInfoShim());
  PluginRegistry.register('device_info_plus', DeviceInfoShim());
  PluginRegistry.register('file_picker', FilePickerShim());
  PluginRegistry.register('image_picker', ImagePickerShim());
  PluginRegistry.register('camera', CameraShim());
  PluginRegistry.register('connectivity', ConnectivityShim());
  PluginRegistry.register('connectivity_plus', ConnectivityShim());
  PluginRegistry.register('audioplayers', AudioPlayerShim());
  PluginRegistry.register('audioplayer', AudioPlayerShim());
  PluginRegistry.register('video_player', VideoPlayerShim());
  PluginRegistry.register('share_plus', ShareShim());
  PluginRegistry.register('share', ShareShim());
  PluginRegistry.register('webview_flutter', WebViewShim());
  PluginRegistry.register('webview', WebViewShim());
  PluginRegistry.register('chewie', ChewieShim());
  PluginRegistry.register('hive', HiveShim());
  PluginRegistry.register('sqflite', SqfliteShim());
  PluginRegistry.register('flutter_local_notifications', LocalNotificationsShim());
  PluginRegistry.register('local_notifications', LocalNotificationsShim());
  PluginRegistry.register('permission_handler', PermissionHandlerShim());
  PluginRegistry.register('flutter_secure_storage', SecureStorageShim());
  PluginRegistry.register('secure_storage', SecureStorageShim());
  PluginRegistry.register('local_auth', LocalAuthShim());



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
        for (final item in updates) {
          final u = item as Map<String, dynamic>;
          final nid = u['id'] as String?;
          if (nid == null) continue;
          final target = findNodeById(_tree!, nid);
          if (target != null) {
            if (u.containsKey('props')) {
              final p = u['props'] as Map<String, dynamic>;
              p.forEach((k, v) {
                if (v == null || v == '') {
                  target.props.remove(k);
                } else {
                  target.props[k] = v.toString();
                }
              });
              modified = true;
            }
            if (u.containsKey('callback_id')) {
              target.callbackId = u['callback_id'] as String? ?? '';
              modified = true;
            }
          }
        }
        if (modified && mounted) {
          setState(() {});
        }
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
        final Map<String, String> args =
            rawMap.map((k, v) => MapEntry(k, v.toString()));
        final res = await PluginRegistry.dispatch(pluginName, method, args);
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
        final Map<String, String> args =
            rawMap.map((k, v) => MapEntry(k, v.toString()));
        await PluginRegistry.dispatch(pluginName, method, args);
      } catch (e) {
        debugPrint('[plugin error] $pluginName.$method: $e');
      }
    }
  }

  void _sendPluginResponse(String callId, dynamic result, [String? error]) {
    final socket = _socket;
    if (socket == null) return;
    final payload = utf8.encode(jsonEncode({
      'call_id': callId,
      'result': result,
      'error': error,
    }));
    socket.add(encodeFrame(msgPluginResponse, payload));
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
