// Manual Protobuf wire-format encode/decode for exactly the 3 message
// types in ir_spec/widget.proto (Widget, RenderTree, CallbackEvent).
//
// Why hand-written instead of generated: generating real Dart protobuf
// bindings requires the `protoc-gen-dart` plugin, which itself needs a
// working Dart SDK to build/run. This code was authored in a sandbox
// where Flutter/Dart could not be installed (its SDK download is
// blocked by network policy there), so `protoc --dart_out=...` was
// never an option.
//
// Confidence note: this is a direct, line-by-line transcription of
// examples/counter/fake_dart_client.py's manual decoder/encoder, which
// WAS validated for real — it exchanged actual messages with the
// working Rust bridge (see rust_bridge/src/main.rs's relay mode) and
// correctly decoded a real tree produced by the Python widget classes,
// and its encoded CallbackEvent was correctly decoded by Rust and
// delivered to a real Python callback. This file has NOT itself been
// compiled or run (no Dart toolchain was available to do so) — that
// verification is the first thing to do on a real machine.
//
// Wire format reminder (protobuf basics used here):
//   tag = (field_number << 3) | wire_type
//   wire_type 0 = varint, wire_type 2 = length-delimited
//   varint = 7 bits per byte, MSB set means "more bytes follow"
//   map<string,string> entries are encoded as repeated submessages
//   with field 1 = key (string), field 2 = value (string)

import 'dart:convert';
import 'dart:typed_data';

const int wireVarint = 0;
const int wireLengthDelimited = 2;

const int msgRenderTree = 0x01;
const int msgCallbackEvent = 0x02;
const int msgPluginCall = 0x03;
const int msgTreePatch = 0x04;
const int msgPluginResponse = 0x05;

/// Plain data class mirroring the `Widget` protobuf message. Not named
/// `Widget` to avoid clashing with Flutter's own `Widget` class.
class WidgetNode {
  String type;
  Map<String, String> props;
  List<WidgetNode> children;
  String callbackId;

  WidgetNode({
    this.type = '',
    Map<String, String>? props,
    List<WidgetNode>? children,
    this.callbackId = '',
  })  : props = props ?? {},
        children = children ?? [];
}

/// Recursively searches for a WidgetNode matching the structural node ID (_nid).
WidgetNode? findNodeById(WidgetNode root, String nid) {
  if (root.props['_nid'] == nid) return root;
  for (final child in root.children) {
    final found = findNodeById(child, nid);
    if (found != null) return found;
  }
  return null;
}

// --- Decoding ------------------------------------------------------------

class ByteReader {
  final Uint8List data;
  int pos = 0;

  ByteReader(this.data);

  bool get isAtEnd => pos >= data.length;

  int readByte() {
    final b = data[pos];
    pos += 1;
    return b;
  }

  int readVarint() {
    int result = 0;
    int shift = 0;
    while (true) {
      final b = readByte();
      result |= (b & 0x7F) << shift;
      if ((b & 0x80) == 0) break;
      shift += 7;
    }
    return result;
  }

  Uint8List readBytes(int n) {
    final chunk = Uint8List.sublistView(data, pos, pos + n);
    pos += n;
    return chunk;
  }

  /// Returns (fieldNumber, wireType).
  (int, int) readTag() {
    final tag = readVarint();
    final fieldNumber = tag >> 3;
    final wireType = tag & 0x07;
    return (fieldNumber, wireType);
  }

  Uint8List readLengthDelimited() {
    final length = readVarint();
    return readBytes(length);
  }
}

WidgetNode decodeWidget(Uint8List data) {
  final reader = ByteReader(data);
  final widget = WidgetNode();

  while (!reader.isAtEnd) {
    final (fieldNumber, wireType) = reader.readTag();
    if (wireType != wireLengthDelimited) {
      throw FormatException(
          'unexpected wire type $wireType for field $fieldNumber');
    }
    final payload = reader.readLengthDelimited();

    switch (fieldNumber) {
      case 1:
        widget.type = utf8.decode(payload);
        break;
      case 2:
        // map<string,string> entry: submessage, field 1=key, 2=value
        final entryReader = ByteReader(payload);
        String key = '';
        String value = '';
        while (!entryReader.isAtEnd) {
          final (efn, ewt) = entryReader.readTag();
          if (ewt != wireLengthDelimited) {
            throw FormatException('unexpected map entry wire type $ewt');
          }
          final epayload = entryReader.readLengthDelimited();
          if (efn == 1) {
            key = utf8.decode(epayload);
          } else if (efn == 2) {
            value = utf8.decode(epayload);
          }
        }
        widget.props[key] = value;
        break;
      case 3:
        widget.children.add(decodeWidget(payload));
        break;
      case 4:
        widget.callbackId = utf8.decode(payload);
        break;
      default:
        // Unknown field: ignore (forward compatibility with future
        // schema additions — matches the "raw_props escape hatch"
        // spirit from the vision doc).
        break;
    }
  }

  return widget;
}

/// RenderTree { Widget root = 1; }
WidgetNode? decodeRenderTree(Uint8List data) {
  final reader = ByteReader(data);
  WidgetNode? root;
  while (!reader.isAtEnd) {
    final (fieldNumber, wireType) = reader.readTag();
    if (wireType != wireLengthDelimited) {
      throw FormatException('unexpected wire type $wireType in RenderTree');
    }
    final payload = reader.readLengthDelimited();
    if (fieldNumber == 1) {
      root = decodeWidget(payload);
    }
  }
  return root;
}

// --- Encoding --------------------------------------------------------------

Uint8List encodeVarint(int value) {
  final out = <int>[];
  int v = value;
  while (true) {
    final b = v & 0x7F;
    v >>= 7;
    if (v != 0) {
      out.add(b | 0x80);
    } else {
      out.add(b);
      break;
    }
  }
  return Uint8List.fromList(out);
}

Uint8List encodeTag(int fieldNumber, int wireType) {
  return encodeVarint((fieldNumber << 3) | wireType);
}

Uint8List _concat(List<Uint8List> parts) {
  final totalLen = parts.fold<int>(0, (sum, p) => sum + p.length);
  final out = Uint8List(totalLen);
  var offset = 0;
  for (final p in parts) {
    out.setRange(offset, offset + p.length, p);
    offset += p.length;
  }
  return out;
}

Uint8List encodeStringField(int fieldNumber, String value) {
  final encoded = Uint8List.fromList(utf8.encode(value));
  return _concat([
    encodeTag(fieldNumber, wireLengthDelimited),
    encodeVarint(encoded.length),
    encoded,
  ]);
}

Uint8List encodeMapEntry(int fieldNumber, String key, String value) {
  final entry = _concat([
    encodeStringField(1, key),
    encodeStringField(2, value),
  ]);
  return _concat([
    encodeTag(fieldNumber, wireLengthDelimited),
    encodeVarint(entry.length),
    entry,
  ]);
}

/// CallbackEvent { string callback_id = 1; map<string,string> event_data = 2; }
Uint8List encodeCallbackEvent(String callbackId, Map<String, String> eventData) {
  final parts = <Uint8List>[encodeStringField(1, callbackId)];
  eventData.forEach((k, v) {
    parts.add(encodeMapEntry(2, k, v));
  });
  return _concat(parts);
}

// --- Wire framing (must match rust_bridge/src/main.rs read_frame/write_frame) --

/// Wraps a payload with the [1-byte type][4-byte big-endian length]
/// header the Rust bridge expects/produces.
Uint8List encodeFrame(int msgType, Uint8List payload) {
  final header = Uint8List(5);
  header[0] = msgType;
  header.buffer.asByteData().setUint32(1, payload.length, Endian.big);
  return _concat([header, payload]);
}
