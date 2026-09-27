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
    include!(concat!(env!("OUT_DIR"), "/pyflutter.ir.rs"));
}

const MSG_RENDER_TREE: u8 = 0x01;
const MSG_CALLBACK_EVENT: u8 = 0x02;

fn read_frame(stream: &mut impl Read) -> io::Result<(u8, Vec<u8>)> {
    let mut header = [0u8; 5]; // 1 byte type + 4 byte length
    stream.read_exact(&mut header)?;
    let msg_type = header[0];
    let len = u32::from_be_bytes([header[1], header[2], header[3], header[4]]) as usize;
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

fn relay_mode(port: u16) {
    eprintln!("[bridge] relay mode: listening on 127.0.0.1:{port} ...");
    let listener = TcpListener::bind(("127.0.0.1", port))
        .unwrap_or_else(|e| panic!("failed to bind 127.0.0.1:{port}: {e}"));

    let current_dart_write: Arc<Mutex<Option<TcpStream>>> = Arc::new(Mutex::new(None));
    let last_tree: Arc<Mutex<Option<Vec<u8>>>> = Arc::new(Mutex::new(None));

    let dart_writer_for_py = Arc::clone(&current_dart_write);
    let last_tree_for_py = Arc::clone(&last_tree);

    // Thread 1: Python (stdin) -> Rust -> Dart (socket) [RenderTree push]
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

                // Save last tree so any future reconnecting Dart client gets it immediately
                {
                    let mut guard = last_tree_for_py.lock().unwrap();
                    *guard = Some(payload.clone());
                }
            } else if msg_type == 0x03 {
                eprintln!("[bridge] forwarding plugin call to Dart");
            }

            // Forward to active Dart client if connected
            let mut guard = dart_writer_for_py.lock().unwrap();
            if let Some(ref mut stream) = *guard {
                if let Err(e) = write_frame(stream, msg_type, &payload) {
                    eprintln!("[bridge] failed to forward frame to Dart (client dropped): {e}");
                    *guard = None; // Reset so next accept reconnects cleanly
                }
            } else if msg_type == MSG_RENDER_TREE {
                eprintln!("[bridge] tree cached; waiting for Dart client to connect...");
            }
        }
    });

    // Main thread / Thread 2: Accept Dart clients in a loop and forward CallbackEvents to Python stdout
    let mut stdout = io::stdout();
    for stream_res in listener.incoming() {
        let dart_stream = match stream_res {
            Ok(s) => s,
            Err(e) => {
                eprintln!("[bridge] error accepting Dart connection: {e}");
                continue;
            }
        };

        let addr = dart_stream.peer_addr().map(|a| a.to_string()).unwrap_or_default();
        eprintln!("[bridge] Dart client connected from {addr}");

        let dart_write_clone = match dart_stream.try_clone() {
            Ok(s) => s,
            Err(e) => {
                eprintln!("[bridge] failed to clone Dart stream: {e}");
                continue;
            }
        };

        // If we already have a cached tree, immediately send it to the new Dart client!
        {
            let mut guard = current_dart_write.lock().unwrap();
            let mut write_socket = dart_write_clone;
            if let Some(ref cached) = *last_tree.lock().unwrap() {
                if let Err(e) = write_frame(&mut write_socket, MSG_RENDER_TREE, cached) {
                    eprintln!("[bridge] failed to send initial cached tree to Dart: {e}");
                } else {
                    eprintln!("[bridge] sent initial cached tree to newly connected Dart client");
                }
            }
            *guard = Some(write_socket);
        }

        // Read callbacks from this Dart client until it disconnects
        let mut read_socket = dart_stream;
        loop {
            let (event_type, event_payload) = match read_frame(&mut read_socket) {
                Ok(v) => v,
                Err(e) => {
                    eprintln!("[bridge] Dart client {addr} disconnected: {e}");
                    break;
                }
            };
            if event_type != MSG_CALLBACK_EVENT {
                eprintln!("[bridge] unexpected msg type {event_type} from Dart, ignoring");
                continue;
            }

            eprintln!("[bridge] relaying callback event to Python");
            if let Err(e) = write_frame(&mut stdout, MSG_CALLBACK_EVENT, &event_payload) {
                eprintln!("[bridge] failed to forward event to Python (stdout closed): {e}");
                return;
            }
        }

        // Dart disconnected, clear active writer
        {
            let mut guard = current_dart_write.lock().unwrap();
            *guard = None;
        }
        eprintln!("[bridge] waiting for next Dart connection...");
    }
}

fn main() {
    let args: Vec<String> = env::args().collect();
    if let Some(pos) = args.iter().position(|a| a == "--dart-port") {
        let port: u16 = args
            .get(pos + 1)
            .expect("--dart-port requires a value")
            .parse()
            .expect("--dart-port value must be a valid port number");
        relay_mode(port);
    } else {
        simulate_mode();
    }
}
