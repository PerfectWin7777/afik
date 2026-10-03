//! PyFlutter Native FFI Bridge Library.
//! Exposes a high-performance C ABI interface for in-memory bidirectional
//! communication between Flutter (via `dart:ffi`) and Python in standalone APK/app releases.

use std::collections::VecDeque;
use std::os::raw::{c_char, c_int};
use std::sync::{Arc, Mutex, Once};

pub mod ir {
    include!(concat!(env!("OUT_DIR"), "/pyflutter.ir.rs"));
}

pub const MSG_RENDER_TREE: u8 = 0x01;
pub const MSG_CALLBACK_EVENT: u8 = 0x02;
pub const MSG_PLUGIN_CALL: u8 = 0x03;
pub const MSG_TREE_PATCH: u8 = 0x04;
pub const MSG_PLUGIN_RESPONSE: u8 = 0x05;

#[derive(Clone, Debug)]
pub struct FrameMessage {
    pub msg_type: u8,
    pub payload: Vec<u8>,
}

// Thread-safe queues for in-memory Dart <-> Python messaging
static INIT: Once = Once::new();
static mut TO_DART_QUEUE: Option<Arc<Mutex<VecDeque<FrameMessage>>>> = None;
static mut TO_PYTHON_QUEUE: Option<Arc<Mutex<VecDeque<FrameMessage>>>> = None;

fn ensure_initialized() {
    INIT.call_once(|| unsafe {
        TO_DART_QUEUE = Some(Arc::new(Mutex::new(VecDeque::new())));
        TO_PYTHON_QUEUE = Some(Arc::new(Mutex::new(VecDeque::new())));
    });
}

/// Returns the native bridge version string.
#[no_mangle]
pub extern "C" fn pyflutter_bridge_version() -> *const c_char {
    static VERSION: &str = "0.1.0\0";
    VERSION.as_ptr() as *const c_char
}

/// Initializes the in-process standalone bridge runtime.
#[no_mangle]
pub extern "C" fn pyflutter_bridge_init(
    _app_dir: *const c_char,
    _entrypoint: *const c_char,
) -> c_int {
    ensure_initialized();
    0 // Success
}

/// Pushes a message frame into the queue destined for Dart.
/// Called from embedded Python/Rust runtime.
#[no_mangle]
pub extern "C" fn pyflutter_push_to_dart(
    msg_type: u8,
    data: *const u8,
    len: usize,
) -> c_int {
    ensure_initialized();
    if data.is_null() && len > 0 {
        return -1;
    }

    let payload = if len > 0 {
        unsafe { std::slice::from_raw_parts(data, len).to_vec() }
    } else {
        Vec::new()
    };

    unsafe {
        if let Some(ref queue_arc) = TO_DART_QUEUE {
            if let Ok(mut queue) = queue_arc.lock() {
                queue.push_back(FrameMessage { msg_type, payload });
                return 0;
            }
        }
    }
    -2
}

/// Pushes a message frame from Dart into the queue destined for Python.
/// Called from `dart:ffi`.
#[no_mangle]
pub extern "C" fn pyflutter_push_to_python(
    msg_type: u8,
    data: *const u8,
    len: usize,
) -> c_int {
    ensure_initialized();
    if data.is_null() && len > 0 {
        return -1;
    }

    let payload = if len > 0 {
        unsafe { std::slice::from_raw_parts(data, len).to_vec() }
    } else {
        Vec::new()
    };

    unsafe {
        if let Some(ref queue_arc) = TO_PYTHON_QUEUE {
            if let Ok(mut queue) = queue_arc.lock() {
                queue.push_back(FrameMessage { msg_type, payload });
                return 0;
            }
        }
    }
    -2
}

/// Polls the next pending frame destined for Dart.
/// Writes up to `max_len` bytes into `out_buf`, sets `*out_type` and `*out_len`.
/// Returns:
///   1 if a frame was read
///   0 if the queue is empty
///  -1 if the buffer was too small
///  -2 on lock or memory error
#[no_mangle]
pub extern "C" fn pyflutter_poll_dart_frame(
    out_buf: *mut u8,
    max_len: usize,
    out_type: *mut u8,
    out_len: *mut usize,
) -> c_int {
    ensure_initialized();
    if out_buf.is_null() || out_type.is_null() || out_len.is_null() {
        return -2;
    }

    unsafe {
        if let Some(ref queue_arc) = TO_DART_QUEUE {
            if let Ok(mut queue) = queue_arc.lock() {
                if let Some(frame) = queue.front() {
                    if frame.payload.len() > max_len {
                        *out_len = frame.payload.len();
                        return -1; // Buffer too small
                    }
                    let frame = queue.pop_front().unwrap();
                    *out_type = frame.msg_type;
                    *out_len = frame.payload.len();
                    std::ptr::copy_nonoverlapping(
                        frame.payload.as_ptr(),
                        out_buf,
                        frame.payload.len(),
                    );
                    return 1; // Read successfully
                } else {
                    return 0; // Empty queue
                }
            }
        }
    }
    -2
}

/// Polls the next pending frame destined for Python.
#[no_mangle]
pub extern "C" fn pyflutter_poll_python_frame(
    out_buf: *mut u8,
    max_len: usize,
    out_type: *mut u8,
    out_len: *mut usize,
) -> c_int {
    ensure_initialized();
    if out_buf.is_null() || out_type.is_null() || out_len.is_null() {
        return -2;
    }

    unsafe {
        if let Some(ref queue_arc) = TO_PYTHON_QUEUE {
            if let Ok(mut queue) = queue_arc.lock() {
                if let Some(frame) = queue.front() {
                    if frame.payload.len() > max_len {
                        *out_len = frame.payload.len();
                        return -1;
                    }
                    let frame = queue.pop_front().unwrap();
                    *out_type = frame.msg_type;
                    *out_len = frame.payload.len();
                    std::ptr::copy_nonoverlapping(
                        frame.payload.as_ptr(),
                        out_buf,
                        frame.payload.len(),
                    );
                    return 1;
                } else {
                    return 0;
                }
            }
        }
    }
    -2
}

/// Cleans up and clears all in-memory queues.
#[no_mangle]
pub extern "C" fn pyflutter_bridge_destroy() -> c_int {
    unsafe {
        if let Some(ref queue_arc) = TO_DART_QUEUE {
            if let Ok(mut queue) = queue_arc.lock() {
                queue.clear();
            }
        }
        if let Some(ref queue_arc) = TO_PYTHON_QUEUE {
            if let Ok(mut queue) = queue_arc.lock() {
                queue.clear();
            }
        }
    }
    0
}
