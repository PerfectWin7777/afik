"""
Stand-in for the Dart client, written in Python but deliberately NOT
using the `protobuf` Python library — it hand-decodes/encodes the wire
format manually, using the exact same low-level algorithm (varints,
tag = (field_number << 3) | wire_type, length-delimited fields, map
entries as repeated {key, value} submessages) that will be transcribed
into Dart next.

Why this exists: Flutter/Dart cannot run in the sandbox this was
written in (confirmed: Flutter's own Dart SDK download is blocked by
network policy here), so the real Dart code cannot be compiled or
tested before being handed off. This script validates the *algorithm*
against the real, already-working Rust bridge and Python widget tree,
so the Dart transcription has much higher confidence than untested
code would.

Connects to the Rust bridge's relay mode (`--dart-port <port>`),
receives one RenderTree frame, manually decodes and prints it, finds
the first callback_id, manually encodes a CallbackEvent, and sends it
back — exactly what the real Dart shell will do on a button tap.
"""

from __future__ import annotations

import socket
import struct
import sys

WIRE_VARINT = 0
WIRE_LEN = 2

MSG_RENDER_TREE = 0x01
MSG_CALLBACK_EVENT = 0x02


# --- Minimal manual protobuf decoder -----------------------------------

class ByteReader:
    def __init__(self, data: bytes):
        self.data = data
        self.pos = 0

    def eof(self) -> bool:
        return self.pos >= len(self.data)

    def read_byte(self) -> int:
        b = self.data[self.pos]
        self.pos += 1
        return b

    def read_varint(self) -> int:
        result = 0
        shift = 0
        while True:
            b = self.read_byte()
            result |= (b & 0x7F) << shift
            if not (b & 0x80):
                break
            shift += 7
        return result

    def read_bytes(self, n: int) -> bytes:
        chunk = self.data[self.pos:self.pos + n]
        self.pos += n
        return chunk

    def read_tag(self) -> tuple[int, int]:
        tag = self.read_varint()
        field_number = tag >> 3
        wire_type = tag & 0x07
        return field_number, wire_type

    def read_length_delimited(self) -> bytes:
        length = self.read_varint()
        return self.read_bytes(length)


def decode_widget(data: bytes) -> dict:
    """Mirrors Widget { string type=1; map<string,string> props=2;
    repeated Widget children=3; string callback_id=4; }.
    """
    reader = ByteReader(data)
    widget = {"type": "", "props": {}, "children": [], "callback_id": ""}

    while not reader.eof():
        field_number, wire_type = reader.read_tag()
        if wire_type != WIRE_LEN:
            raise ValueError(f"unexpected wire type {wire_type} for field {field_number}")
        payload = reader.read_length_delimited()

        if field_number == 1:
            widget["type"] = payload.decode("utf-8")
        elif field_number == 2:
            # map<string,string> entry: submessage with field 1=key, 2=value
            entry_reader = ByteReader(payload)
            key, value = "", ""
            while not entry_reader.eof():
                efn, ewt = entry_reader.read_tag()
                assert ewt == WIRE_LEN
                epayload = entry_reader.read_length_delimited()
                if efn == 1:
                    key = epayload.decode("utf-8")
                elif efn == 2:
                    value = epayload.decode("utf-8")
            widget["props"][key] = value
        elif field_number == 3:
            widget["children"].append(decode_widget(payload))
        elif field_number == 4:
            widget["callback_id"] = payload.decode("utf-8")

    return widget


def decode_render_tree(data: bytes) -> dict | None:
    """RenderTree { Widget root = 1; }"""
    reader = ByteReader(data)
    root = None
    while not reader.eof():
        field_number, wire_type = reader.read_tag()
        assert wire_type == WIRE_LEN
        payload = reader.read_length_delimited()
        if field_number == 1:
            root = decode_widget(payload)
    return root


# --- Minimal manual protobuf encoder ------------------------------------

def encode_varint(value: int) -> bytes:
    out = bytearray()
    while True:
        b = value & 0x7F
        value >>= 7
        if value:
            out.append(b | 0x80)
        else:
            out.append(b)
            break
    return bytes(out)


def encode_tag(field_number: int, wire_type: int) -> bytes:
    return encode_varint((field_number << 3) | wire_type)


def encode_string_field(field_number: int, value: str) -> bytes:
    encoded = value.encode("utf-8")
    return encode_tag(field_number, WIRE_LEN) + encode_varint(len(encoded)) + encoded


def encode_map_entry(field_number: int, key: str, value: str) -> bytes:
    entry = encode_string_field(1, key) + encode_string_field(2, value)
    return encode_tag(field_number, WIRE_LEN) + encode_varint(len(entry)) + entry


def encode_callback_event(callback_id: str, event_data: dict[str, str]) -> bytes:
    """CallbackEvent { string callback_id = 1; map<string,string> event_data = 2; }"""
    out = bytearray()
    out += encode_string_field(1, callback_id)
    for k, v in event_data.items():
        out += encode_map_entry(2, k, v)
    return bytes(out)


# --- Wire framing (must match rust_bridge/src/main.rs read_frame/write_frame) --

def read_frame(sock: socket.socket) -> tuple[int, bytes]:
    header = _recv_exact(sock, 5)
    msg_type, length = struct.unpack(">BI", header)
    payload = _recv_exact(sock, length)
    return msg_type, payload


def write_frame(sock: socket.socket, msg_type: int, payload: bytes) -> None:
    header = struct.pack(">BI", msg_type, len(payload))
    sock.sendall(header + payload)


def _recv_exact(sock: socket.socket, n: int) -> bytes:
    chunks = []
    remaining = n
    while remaining > 0:
        chunk = sock.recv(remaining)
        if not chunk:
            raise ConnectionError("socket closed while expecting more data")
        chunks.append(chunk)
        remaining -= len(chunk)
    return b"".join(chunks)


def find_first_callback(widget: dict) -> str | None:
    if widget["callback_id"]:
        return widget["callback_id"]
    for child in widget["children"]:
        found = find_first_callback(child)
        if found:
            return found
    return None


def print_widget(widget: dict, depth: int = 0) -> None:
    indent = "  " * depth
    print(f"{indent}{widget['type']}")
    for k, v in widget["props"].items():
        print(f"{indent}  {k} = {v}")
    if widget["callback_id"]:
        print(f"{indent}  callback_id = {widget['callback_id']}")
    for child in widget["children"]:
        print_widget(child, depth + 1)


def main():
    if len(sys.argv) != 2:
        print("Usage: python fake_dart_client.py <port>")
        sys.exit(1)

    port = int(sys.argv[1])
    sock = socket.create_connection(("127.0.0.1", port))
    print(f"[fake-dart] connected to bridge on port {port}")

    msg_type, payload = read_frame(sock)
    assert msg_type == MSG_RENDER_TREE, f"expected RenderTree, got {msg_type}"

    root = decode_render_tree(payload)
    print("[fake-dart] manually decoded tree:")
    print_widget(root)

    callback_id = find_first_callback(root)
    if callback_id is None:
        print("[fake-dart] no callback found, nothing to tap")
        sock.close()
        return

    print(f"[fake-dart] manually encoding CallbackEvent for callback_id={callback_id}")
    encoded_event = encode_callback_event(callback_id, {})
    write_frame(sock, MSG_CALLBACK_EVENT, encoded_event)
    print("[fake-dart] event sent")

    sock.close()


if __name__ == "__main__":
    main()
