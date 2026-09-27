// A TCP `Socket` in Dart delivers bytes as a Stream<Uint8List> in
// arbitrary chunks — one chunk might contain half a frame, several
// frames, or a frame split across two chunks. This buffers incoming
// bytes and emits complete, framed messages ([type, payload]) only
// once enough bytes have actually arrived.
//
// This has no Python equivalent to validate against (fake_dart_client.py
// used Python's blocking socket.recv, which doesn't have this problem)
// — it is standard Dart stream-buffering logic, not part of the wire
// format itself, so the risk profile here is different from
// ir_codec.dart: this is ordinary async Dart, not a hand-rolled binary
// protocol. Still unverified by an actual compiler/run in this sandbox.

import 'dart:typed_data';

typedef FrameHandler = void Function(int msgType, Uint8List payload);

class FrameBuffer {
  final List<int> _buffer = [];
  final FrameHandler onFrame;

  FrameBuffer(this.onFrame);

  void addChunk(Uint8List chunk) {
    _buffer.addAll(chunk);
    _drain();
  }

  void _drain() {
    while (true) {
      if (_buffer.length < 5) return; // not even a full header yet

      final msgType = _buffer[0];
      final length = ByteData.sublistView(
        Uint8List.fromList(_buffer.sublist(1, 5)),
      ).getUint32(0, Endian.big);

      if (_buffer.length < 5 + length) return; // payload not fully arrived

      final payload = Uint8List.fromList(_buffer.sublist(5, 5 + length));
      _buffer.removeRange(0, 5 + length);
      onFrame(msgType, payload);
      // loop again: the buffer may contain another complete frame
    }
  }
}
