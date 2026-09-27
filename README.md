# PyFlutter — POC scaffold

See `PYFLUTTER_VISION.md` for full architecture/vision.

## Current state — full duplex loop proven; Rust relay + hand-authored Dart shell added (Dart itself UNVERIFIED)

- `ir_spec/widget.proto` — the IR contract (Widget, RenderTree, CallbackEvent).
- `py_framework/pyflutter/` — Python widget classes, tree building,
  Protobuf framing (`core/render.py`), and the bridge-process driver
  (`core/bridge.py`: `BridgeSession`, `run_loop`).
- `examples/counter/` —
  - `main.py` / `run_poc.py`: the counter, driven through the bridge's
    **simulate mode** (Rust taps its own first callback). **Actually
    run, 5/5 round trips, exit 0.**
  - `fake_dart_client.py`: a Python stand-in for the real Dart client,
    hand-decoding/encoding the Protobuf wire format with no `protobuf`
    library — this validates the exact algorithm later transcribed
    into `dart_runtime/lib/ir_codec.dart`.
  - `test_relay.py`: drives the bridge's **relay mode** with
    `fake_dart_client.py` standing in for Dart. **Actually run, passed**
    ("RELAY TEST PASSED", count went 0 -> 1 through the full
    Python -> Rust -> [fake Dart] -> Rust -> Python loop).
- `rust_bridge/` — now has two modes (see `main.rs` header comment):
  - **simulate mode** (no args): the original, proven behavior.
  - **relay mode** (`--dart-port <PORT>`): pure relay between Python's
    stdio and a Dart/TCP client — no widget inspection, just raw frame
    forwarding both ways. **Actually run and passed** against
    `fake_dart_client.py`.
- `dart_runtime/` — **hand-authored, not `flutter create`-generated**
  (Flutter cannot run in the authoring sandbox — see `SETUP.md`).
  Contains `pubspec.yaml` (no external packages — the wire format is
  hand-coded, not generated via `protoc-gen-dart`, which itself needs a
  Dart toolchain unavailable here) and `lib/`:
  - `ir_codec.dart` — direct transcription of the *validated*
    `fake_dart_client.py` algorithm (varint/tag/length-delimited
    decode, map<string,string> entries, matching encoder for
    CallbackEvent).
  - `frame_buffer.dart` — buffers a Dart `Socket`'s chunked byte stream
    into complete frames (ordinary async Dart, not part of the wire
    format itself).
  - `main.dart` — connects to the bridge over TCP, renders the decoded
    tree (Text, TextField, Button, Column, Row, Container), sends
    `CallbackEvent`s on taps.
  - **`SETUP.md` explains exactly what's missing (platform folders)
    and how to add them without losing this code — read it before
    running anything.**

## Honesty checkpoint: what's actually verified vs. not

| Piece | Verified how |
|---|---|
| Python widget tree + callbacks | Run directly, no Rust/Dart |
| Python -> Rust, real Protobuf | Piped bytes, Rust decoded correctly |
| Full duplex loop (simulate mode) | Run 5x, exit 0 |
| Rust relay mode | Run against `fake_dart_client.py`, passed |
| Protobuf wire algorithm for Dart | Validated in Python (`fake_dart_client.py`), *then* transcribed to Dart |
| `dart_runtime/lib/*.dart` itself | **Not compiled or run anywhere.** First real test happens on your machine. |

## A real bug hit and fixed along the way (worth knowing about)

The first duplex attempt deadlocked. Root cause: `print_widget()` in
`main.rs` used `println!` (stdout) for debug output, but **stdout is
the same stream used for the binary Protobuf protocol**. Debug text got
interleaved into the frame stream, and Python read garbage as a frame
header and hung waiting for a nonsensical payload length. **Fix and
standing rule: all human-readable output in `rust_bridge` goes through
`eprintln!` (stderr); `println!` (stdout) is reserved exclusively for
the wire protocol.**

## Environment notes (things that WILL bite you on first setup)

- **Toolchain version:** plain `apt-get install rustc cargo` gives an
  old Rust (1.75 here). Some transitive dependencies of `prost-build`
  need newer editions/features. Fixed here by pinning in `Cargo.lock`:
  ```
  cargo update -p indexmap --precise 2.2.6
  cargo update -p tempfile --precise 3.10.1
  ```
  Skip this if you have a newer toolchain via `rustup`.
- **`protoc` is required** as an external binary:
  `apt-get install protobuf-compiler`.
- **Python bindings are generated, not hand-written:** re-run whenever
  `widget.proto` changes:
  ```
  protoc --python_out=py_framework/pyflutter/generated ir_spec/widget.proto
  ```
- **stdout is protocol-only in `rust_bridge`** (see the bug above).
- **Flutter/dart_runtime: see `dart_runtime/SETUP.md`.** Nothing there
  has been compiled — treat it as a careful first draft, not working
  code, until you've run it yourself.

## How to re-run what's already proven (Python + Rust only, no Flutter needed)

```
cd rust_bridge && cargo build

# Simulate mode (Rust taps its own callback):
cd ../examples/counter
python3 run_poc.py ../../rust_bridge/target/debug/pyflutter-bridge

# Relay mode (fake Dart client stands in for real Flutter):
python3 test_relay.py ../../rust_bridge/target/debug/pyflutter-bridge
```

## Next concrete steps (in order)

1. **First real Flutter compile.** Follow `dart_runtime/SETUP.md`,
   get `flutter pub get` and `flutter run` working, fix whatever
   syntax/API mistakes turn up (there will likely be some — this was
   never compiled).
2. Once the Dart shell renders the counter and taps the button for
   real: replace `test_relay.py`'s use of `fake_dart_client.py` with
   the real Flutter app as the Dart-side client — the true end-to-end
   milestone.
3. Wrap this into a real `pyflutter` CLI (`pyflutter run`) that
   launches the bridge (in relay mode) and the Flutter app together,
   picks a free port automatically instead of hardcoding 7879, and
   implements the r/R/q keybindings (vision doc §5.1).
4. Revisit the production architecture note: this POC uses a
   subprocess + TCP socket for Rust<->Dart, which is fine for desktop
   dev but **won't work as the final production shape** — spawning
   arbitrary subprocesses isn't available on iOS, and sockets add
   unnecessary IPC overhead when Rust and Dart will eventually ship in
   the same process. The real production path is Rust as a native
   library linked into the Flutter app via `dart:ffi`, not a separate
   process. This is a known, deliberate POC simplification, not a
   design decision — flagged here so it isn't mistaken for one later.
