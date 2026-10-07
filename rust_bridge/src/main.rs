// Persistent duplex bridge, framed with a 1-byte message type tag +
// 4-byte big-endian length prefix + payload:
//   type 0x01 = RenderTree     (Python -> Rust -> Dart)
//   type 0x02 = CallbackEvent  (Dart -> Rust -> Python)
//
// Two modes, selected by CLI arg:
//
//   (no args)            "simulate" mode — proven working (see
//                         README): Rust pretends to be Dart, tapping
//                         the first widget with a callback_id itself.
//                         Kept as a regression-safe fallback that needs
//                         no Dart runtime at all.
//
//   --dart-port <PORT>    "relay" mode — Rust is a pure relay between
//                         Python (stdin/stdout) and a real Dart client
//                         connected over a local TCP socket. Rust does
//                         not interpret RenderTree/CallbackEvent
//                         contents in this mode, just forwards raw
//                         frames both ways. This is the real,
//                         production-shaped path once dart_runtime/
//                         exists.

use std::env;
use std::io::{self, Read, Write};
use std::net::{TcpListener, TcpStream};
use std::sync::{Arc, Mutex};

use prost::Message;

pub mod ir {
    include!(concat!(env!("OUT_DIR"), "/afik.ir.rs"));
}

const MSG_RENDER_TREE: u8 = 0x01;
const MSG_CALLBACK_EVENT: u8 = 0x02;
#[allow(dead_code)]
const MSG_PLUGIN_CALL: u8 = 0x03;
const MSG_TREE_PATCH: u8 = 0x04;
const MSG_PLUGIN_RESPONSE: u8 = 0x05;
const MSG_HELLO: u8 = 0x06;

/// Callback id sent to Python when a Dart client (re)connects and the cached
/// tree is no longer current, asking it to resend a full tree.
const RESYNC_CALLBACK_ID: &str = "__afik_resync__";

/// Largest frame accepted from any peer (protects against forged lengths).
const MAX_FRAME_BYTES: usize = 64 * 1024 * 1024;

fn read_frame(stream: &mut impl Read) -> io::Result<(u8, Vec<u8>)> {
    let mut header = [0u8; 5]; // 1 byte type + 4 byte length
    stream.read_exact(&mut header)?;
    let msg_type = header[0];
    let len = u32::from_be_bytes([header[1], header[2], header[3], header[4]]) as usize;
    if len > MAX_FRAME_BYTES {
        return Err(io::Error::new(
            io::ErrorKind::InvalidData,
            format!("frame of {len} bytes exceeds the {MAX_FRAME_BYTES} byte limit"),
        ));
    }
    let mut payload = vec![0u8; len];
    stream.read_exact(&mut payload)?;
    Ok((msg_type, payload))
}

fn write_frame(stream: &mut impl Write, msg_type: u8, payload: &[u8]) -> io::Result<()> {
    let mut header = Vec::with_capacity(5);
    header.push(msg_type);
    header.extend_from_slice(&(payload.len() as u32).to_be_bytes());
    stream.write_all(&header)?;
    stream.write_all(payload)?;
    stream.flush()
}

/// Depth-first search for the first widget with a non-empty callback_id.
/// Only used in simulate mode (relay mode never inspects payloads).
fn find_first_callback(widget: &ir::Widget) -> Option<&str> {
    if !widget.callback_id.is_empty() {
        return Some(&widget.callback_id);
    }
    for child in &widget.children {
        if let Some(id) = find_first_callback(child) {
            return Some(id);
        }
    }
    None
}

fn print_widget(node: &ir::Widget, depth: usize) {
    let indent = "  ".repeat(depth);
    eprintln!("{indent}{}", node.r#type);
    for (k, v) in &node.props {
        eprintln!("{indent}  {k} = {v}");
    }
    if !node.callback_id.is_empty() {
        eprintln!("{indent}  callback_id = {}", node.callback_id);
    }
    for child in &node.children {
        print_widget(child, depth + 1);
    }
}

fn simulate_mode() {
    let mut stdin = io::stdin();
    let mut stdout = io::stdout();

    loop {
        let (msg_type, payload) = match read_frame(&mut stdin) {
            Ok(v) => v,
            Err(e) => {
                eprintln!("[bridge] stdin closed or read error, exiting: {e}");
                break;
            }
        };

        match msg_type {
            t if t == MSG_RENDER_TREE => {
                let tree = match ir::RenderTree::decode(&*payload) {
                    Ok(t) => t,
                    Err(e) => {
                        eprintln!("[bridge] failed to decode RenderTree: {e}");
                        continue;
                    }
                };

                let Some(root) = &tree.root else {
                    eprintln!("[bridge] received empty tree, nothing to render");
                    continue;
                };

                eprintln!("[bridge] received tree:");
                print_widget(root, 0);

                if let Some(callback_id) = find_first_callback(root) {
                    eprintln!("[bridge] simulating tap on callback_id={callback_id}");
                    let event = ir::CallbackEvent {
                        callback_id: callback_id.to_string(),
                        event_data: Default::default(),
                    };
                    let encoded = event.encode_to_vec();
                    if let Err(e) = write_frame(&mut stdout, MSG_CALLBACK_EVENT, &encoded) {
                        eprintln!("[bridge] failed to send CallbackEvent: {e}");
                        break;
                    }
                } else {
                    eprintln!("[bridge] no callback found in tree, nothing to simulate");
                }
            }
            other => {
                eprintln!("[bridge] unknown message type {other}, ignoring");
            }
        }
    }
}

fn lock<T>(m: &Mutex<T>) -> std::sync::MutexGuard<'_, T> {
    // A panic in another thread must not take the whole relay down.
    m.lock().unwrap_or_else(|e| e.into_inner())
}

fn relay_mode(port: u16, token: Option<String>) {
    eprintln!("[bridge] relay mode: listening on 127.0.0.1:{port} ...");
    let listener = match TcpListener::bind(("127.0.0.1", port)) {
        Ok(l) => l,
        Err(e) => {
            eprintln!("[bridge] failed to bind 127.0.0.1:{port}: {e}");
            std::process::exit(2);
        }
    };

    let current_dart_write: Arc<Mutex<Option<(u64, TcpStream)>>> = Arc::new(Mutex::new(None));
    // Last full tree received from Python. `tree_is_current` becomes false as soon
    // as a patch is relayed: the cache then no longer matches what Dart displays.
    let last_tree: Arc<Mutex<Option<Vec<u8>>>> = Arc::new(Mutex::new(None));
    let tree_is_current = Arc::new(Mutex::new(true));
    let stdout = Arc::new(Mutex::new(io::stdout()));

    // Thread 1: Python (stdin) -> Rust -> Dart (socket)
    {
        let dart_writer = Arc::clone(&current_dart_write);
        let last_tree = Arc::clone(&last_tree);
        let tree_is_current = Arc::clone(&tree_is_current);
        std::thread::spawn(move || {
            let mut stdin = io::stdin();
            loop {
                let (msg_type, payload) = match read_frame(&mut stdin) {
                    Ok(v) => v,
                    Err(e) => {
                        eprintln!("[bridge] stdin closed ({e}). Parent Python process exited. Shutting down.");
                        std::process::exit(0);
                    }
                };
                if msg_type == MSG_RENDER_TREE {
                    if let Ok(tree) = ir::RenderTree::decode(&*payload) {
                        if let Some(root) = &tree.root {
                            eprintln!("[bridge] received tree from Python (type: {})", root.r#type);
                        }
                    }
                    *lock(&last_tree) = Some(payload.clone());
                    *lock(&tree_is_current) = true;
                } else if msg_type == MSG_TREE_PATCH {
                    *lock(&tree_is_current) = false;
                }

                let mut guard = lock(&dart_writer);
                if let Some((id, ref mut stream)) = *guard {
                    if let Err(e) = write_frame(stream, msg_type, &payload) {
                        eprintln!("[bridge] failed to forward frame to Dart (client {id} dropped): {e}");
                        *guard = None;
                    }
                } else if msg_type == MSG_RENDER_TREE {
                    eprintln!("[bridge] tree cached; waiting for Dart client to connect...");
                }
            }
        });
    }

    let mut next_conn_id: u64 = 0;
    for stream_res in listener.incoming() {
        let dart_stream = match stream_res {
            Ok(s) => s,
            Err(e) => {
                eprintln!("[bridge] error accepting Dart connection: {e}");
                continue;
            }
        };
        next_conn_id += 1;
        let conn_id = next_conn_id;
        let addr = dart_stream.peer_addr().map(|a| a.to_string()).unwrap_or_default();
        eprintln!("[bridge] Dart client {conn_id} connected from {addr}");

        let current_dart_write = Arc::clone(&current_dart_write);
        let last_tree = Arc::clone(&last_tree);
        let tree_is_current = Arc::clone(&tree_is_current);
        let stdout = Arc::clone(&stdout);
        let token = token.clone();

        // One thread per client so a stale socket can never block the next one.
        std::thread::spawn(move || {
            let mut read_socket = dart_stream;

            // Optional shared-secret handshake: the first frame must be HELLO(token).
            if let Some(expected) = token.as_ref() {
                let _ = read_socket.set_read_timeout(Some(std::time::Duration::from_secs(5)));
                match read_frame(&mut read_socket) {
                    Ok((MSG_HELLO, payload)) if payload == expected.as_bytes() => {}
                    _ => {
                        eprintln!("[bridge] client {conn_id} rejected: missing or invalid session token");
                        let _ = read_socket.shutdown(std::net::Shutdown::Both);
                        return;
                    }
                }
                let _ = read_socket.set_read_timeout(None);
            }

            let write_socket = match read_socket.try_clone() {
                Ok(s) => s,
                Err(e) => {
                    eprintln!("[bridge] failed to clone Dart stream: {e}");
                    return;
                }
            };

            // The newest client replaces (and closes) any previous one.
            {
                let mut guard = lock(&current_dart_write);
                if let Some((old_id, old)) = guard.take() {
                    eprintln!("[bridge] closing previous Dart client {old_id}");
                    let _ = old.shutdown(std::net::Shutdown::Both);
                }
                let mut write_socket = write_socket;
                let cached = lock(&last_tree).clone();
                let current = *lock(&tree_is_current);
                match (cached, current) {
                    (Some(tree), true) => {
                        if write_frame(&mut write_socket, MSG_RENDER_TREE, &tree).is_ok() {
                            eprintln!("[bridge] sent cached tree to Dart client {conn_id}");
                        }
                    }
                    _ => {
                        // Cache missing or outdated by patches: ask Python for a full tree.
                        let event = ir::CallbackEvent {
                            callback_id: RESYNC_CALLBACK_ID.to_string(),
                            event_data: Default::default(),
                        };
                        let mut out = lock(&stdout);
                        if let Err(e) = write_frame(&mut *out, MSG_CALLBACK_EVENT, &event.encode_to_vec()) {
                            eprintln!("[bridge] failed to request resync: {e}");
                        }
                    }
                }
                *guard = Some((conn_id, write_socket));
            }

            loop {
                let (event_type, event_payload) = match read_frame(&mut read_socket) {
                    Ok(v) => v,
                    Err(e) => {
                        eprintln!("[bridge] Dart client {conn_id} disconnected: {e}");
                        break;
                    }
                };
                if event_type != MSG_CALLBACK_EVENT && event_type != MSG_PLUGIN_RESPONSE {
                    eprintln!("[bridge] unexpected msg type {event_type} from Dart, ignoring");
                    continue;
                }
                let mut out = lock(&stdout);
                if let Err(e) = write_frame(&mut *out, event_type, &event_payload) {
                    eprintln!("[bridge] failed to forward event to Python (stdout closed): {e}");
                    std::process::exit(0);
                }
            }

            // Only clear the writer if it still belongs to this connection.
            let mut guard = lock(&current_dart_write);
            if matches!(*guard, Some((id, _)) if id == conn_id) {
                *guard = None;
            }
            eprintln!("[bridge] waiting for next Dart connection...");
        });
    }
}

fn main() {
    let args: Vec<String> = env::args().collect();
    if let Some(pos) = args.iter().position(|a| a == "--dart-port") {
        let port: u16 = match args.get(pos + 1).and_then(|v| v.parse().ok()) {
            Some(p) => p,
            None => {
                eprintln!("[bridge] --dart-port requires a valid port number");
                std::process::exit(2);
            }
        };
        let token = args
            .iter()
            .position(|a| a == "--token")
            .and_then(|pos| args.get(pos + 1))
            .cloned();
        relay_mode(port, token);
    } else {
        simulate_mode();
    }
}
