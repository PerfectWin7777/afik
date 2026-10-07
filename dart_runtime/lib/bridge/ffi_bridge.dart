// Afik In-Memory FFI Bridge Connector
// Enables zero-network, direct RAM buffer communication between Dart and Python
// for autonomous standalone APK/IPA execution without a host PC or TCP socket.

import 'dart:async';
import 'dart:ffi';
import 'dart:io';

import 'package:ffi/ffi.dart';
import 'package:flutter/foundation.dart';

typedef _VersionNative = Pointer<Utf8> Function();
typedef _VersionDart = Pointer<Utf8> Function();

typedef _InitNative = Int32 Function(Pointer<Utf8> appDir, Pointer<Utf8> entrypoint);
typedef _InitDart = int Function(Pointer<Utf8> appDir, Pointer<Utf8> entrypoint);

typedef _PushNative = Int32 Function(Uint8 msgType, Pointer<Uint8> data, IntPtr len);
typedef _PushDart = int Function(int msgType, Pointer<Uint8> data, int len);

typedef _PollNative = Int32 Function(
  Pointer<Uint8> outBuf,
  IntPtr maxLen,
  Pointer<Uint8> outType,
  Pointer<IntPtr> outLen,
);
typedef _PollDart = int Function(
  Pointer<Uint8> outBuf,
  int maxLen,
  Pointer<Uint8> outType,
  Pointer<IntPtr> outLen,
);

typedef _DestroyNative = Int32 Function();
typedef _DestroyDart = int Function();

class FFIFrame {
  final int msgType;
  final Uint8List payload;

  const FFIFrame(this.msgType, this.payload);
}

/// Manages direct in-process FFI bridge communication with embedded Rust/Python runtime.
class AfikFFIBridge {
  static final AfikFFIBridge _instance = AfikFFIBridge._internal();
  factory AfikFFIBridge() => _instance;
  AfikFFIBridge._internal();

  DynamicLibrary? _dylib;
  bool _initialized = false;
  Timer? _pollTimer;
  final StreamController<FFIFrame> _frameController =
      StreamController<FFIFrame>.broadcast();

  _InitDart? _initFn;
  _PushDart? _pushFn;
  _PollDart? _pollFn;
  _DestroyDart? _destroyFn;
  _VersionDart? _versionFn;

  String get bridgeVersion =>
      _versionFn != null ? _versionFn!().toDartString() : 'unknown';


  // Reusable polling native memory buffers (allocated once, reused across polls)
  Pointer<Uint8>? _pollBuffer;
  Pointer<Uint8>? _outTypePtr;
  Pointer<IntPtr>? _outLenPtr;
  static const int _initialBufferCapacity = 2 * 1024 * 1024; // 2MB frame buffer
  static const int _maxFrameBytes = 256 * 1024 * 1024; // refuse absurd frames
  int _bufferCapacity = _initialBufferCapacity; // grows when a frame does not fit

  Stream<FFIFrame> get frameStream => _frameController.stream;

  bool get isAvailable {
    _ensureLibraryLoaded();
    return _dylib != null;
  }

  void _ensureLibraryLoaded() {
    if (_dylib != null) return;

    try {
      if (Platform.isAndroid) {
        _dylib = DynamicLibrary.open('libafik_bridge.so');
      } else if (Platform.isWindows) {
        // Look in executable directory or debug/release build folders
        final currentDir = Directory.current.path;
        final candidates = [
          'afik_bridge.dll',
          '$currentDir/rust_bridge/target/release/afik_bridge.dll',
          '$currentDir/rust_bridge/target/debug/afik_bridge.dll',
          '$currentDir/../rust_bridge/target/release/afik_bridge.dll',
          '$currentDir/../rust_bridge/target/debug/afik_bridge.dll',
        ];
        for (final path in candidates) {
          if (File(path).existsSync()) {
            _dylib = DynamicLibrary.open(path);
            break;
          }
        }
        _dylib ??= DynamicLibrary.open('afik_bridge.dll');
      } else if (Platform.isLinux) {
        _dylib = DynamicLibrary.open('libafik_bridge.so');
      } else if (Platform.isMacOS || Platform.isIOS) {
        _dylib = DynamicLibrary.process();
      }
    } catch (e) {
      debugPrint('[FFIBridge] Native library not found or failed to load: $e');
      _dylib = null;
    }

    if (_dylib != null) {
      try {
        _versionFn = _dylib!
            .lookupFunction<_VersionNative, _VersionDart>('afik_bridge_version');
        _initFn = _dylib!
            .lookupFunction<_InitNative, _InitDart>('afik_bridge_init');
        _pushFn = _dylib!
            .lookupFunction<_PushNative, _PushDart>('afik_push_to_python');
        _pollFn = _dylib!
            .lookupFunction<_PollNative, _PollDart>('afik_poll_dart_frame');
        _destroyFn = _dylib!
            .lookupFunction<_DestroyNative, _DestroyDart>('afik_bridge_destroy');
      } catch (e) {
        debugPrint('[FFIBridge] Symbol lookup failed: $e');
        _dylib = null;
      }
    }
  }

  /// Initializes the FFI bridge for standalone mode and begins in-memory frame polling.
  bool init({String appDir = '', String entrypoint = 'main.py'}) {
    if (_initialized) return true;
    _ensureLibraryLoaded();
    if (_dylib == null || _initFn == null) return false;

    final appDirPtr = appDir.toNativeUtf8();
    final entrypointPtr = entrypoint.toNativeUtf8();
    final code = _initFn!(appDirPtr, entrypointPtr);
    malloc.free(appDirPtr);
    malloc.free(entrypointPtr);

    if (code != 0) return false;

    // Allocate persistent memory for frame polling
    _pollBuffer = malloc.allocate<Uint8>(_bufferCapacity);
    _outTypePtr = malloc.allocate<Uint8>(1);
    _outLenPtr = malloc.allocate<IntPtr>(1);

    _initialized = true;
    _startPolling();
    return true;
  }

  void _startPolling() {
    _pollTimer?.cancel();
    // Poll every 8ms (120 Hz polling rate for ultra-low frame latency)
    _pollTimer = Timer.periodic(const Duration(milliseconds: 8), (_) {
      _pollOnce();
    });
  }

  void _pollOnce() {
    if (!_initialized || _pollFn == null) return;
    if (_pollBuffer == null || _outTypePtr == null || _outLenPtr == null) return;

    while (true) {
      final res = _pollFn!(
        _pollBuffer!,
        _bufferCapacity,
        _outTypePtr!,
        _outLenPtr!,
      );

      if (res == 1) {
        // Frame received
        final msgType = _outTypePtr!.value;
        final length = _outLenPtr!.value;
        final Uint8List payloadCopy = Uint8List(length);
        payloadCopy.setRange(
          0,
          length,
          _pollBuffer!.asTypedList(length),
        );
        _frameController.add(FFIFrame(msgType, payloadCopy));
      } else if (res == -1) {
        // The head frame is larger than our buffer: grow it and retry, otherwise
        // that frame would block the queue forever.
        final needed = _outLenPtr!.value;
        if (needed <= _bufferCapacity || needed > _maxFrameBytes) {
          debugPrint('[FFIBridge] cannot read a frame of $needed bytes');
          break;
        }
        malloc.free(_pollBuffer!);
        _bufferCapacity = needed;
        _pollBuffer = malloc.allocate<Uint8>(_bufferCapacity);
      } else {
        // 0 = queue empty, < -1 = native error
        break;
      }
    }
  }

  /// Pushes a callback event, patch, or plugin response to embedded Python.
  bool pushToPython(int msgType, Uint8List payload) {
    if (!_initialized || _pushFn == null) return false;

    final Pointer<Uint8> dataPtr = malloc.allocate<Uint8>(payload.length);
    dataPtr.asTypedList(payload.length).setAll(0, payload);

    final res = _pushFn!(msgType, dataPtr, payload.length);
    malloc.free(dataPtr);
    return res == 0;
  }

  void dispose() {
    _pollTimer?.cancel();
    _pollTimer = null;
    _destroyFn?.call();

    if (_pollBuffer != null) {
      malloc.free(_pollBuffer!);
      _pollBuffer = null;
    }
    if (_outTypePtr != null) {
      malloc.free(_outTypePtr!);
      _outTypePtr = null;
    }
    if (_outLenPtr != null) {
      malloc.free(_outLenPtr!);
      _outLenPtr = null;
    }
    _initialized = false;
  }
}
