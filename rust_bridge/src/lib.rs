//! Afik Native FFI Bridge Library.
//! Exposes a high-performance C ABI interface for in-memory bidirectional
//! communication between Flutter (via `dart:ffi`) and Python in standalone APK/app releases.

use std::collections::VecDeque;
use std::os::raw::{c_char, c_int};
use std::sync::{Mutex, MutexGuard, OnceLock};

pub mod ir {
    include!(concat!(env!("OUT_DIR"), "/afik.ir.rs"));
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
type Queue = Mutex<VecDeque<FrameMessage>>;

static TO_DART_QUEUE: OnceLock<Queue> = OnceLock::new();
static TO_PYTHON_QUEUE: OnceLock<Queue> = OnceLock::new();

/// Upper bound of queued frames per direction: the producer is refused instead of
/// growing memory without limit when the consumer stalls.
const MAX_QUEUED_FRAMES: usize = 4096;

fn to_dart() -> &'static Queue {
    TO_DART_QUEUE.get_or_init(|| Mutex::new(VecDeque::new()))
}

fn to_python() -> &'static Queue {
    TO_PYTHON_QUEUE.get_or_init(|| Mutex::new(VecDeque::new()))
}

fn lock(queue: &'static Queue) -> MutexGuard<'static, VecDeque<FrameMessage>> {
    queue.lock().unwrap_or_else(|e| e.into_inner())
}

fn ensure_initialized() {
    to_dart();
    to_python();
}

fn push(queue: &'static Queue, msg_type: u8, data: *const u8, len: usize) -> c_int {
    if data.is_null() && len > 0 {
        return -1;
    }
    let payload = if len > 0 {
        unsafe { std::slice::from_raw_parts(data, len).to_vec() }
    } else {
        Vec::new()
    };
    let mut q = lock(queue);
    if q.len() >= MAX_QUEUED_FRAMES {
        return -3; // queue full
    }
    q.push_back(FrameMessage { msg_type, payload });
    0
}

fn poll(
    queue: &'static Queue,
    out_buf: *mut u8,
    max_len: usize,
    out_type: *mut u8,
    out_len: *mut usize,
) -> c_int {
    if out_buf.is_null() || out_type.is_null() || out_len.is_null() {
        return -2;
    }
    let mut q = lock(queue);
    let Some(frame) = q.front() else {
        return 0; // empty queue
    };
    unsafe {
        if frame.payload.len() > max_len {
            // Report the needed size; the frame stays queued so the caller can retry
            // with a bigger buffer.
            *out_len = frame.payload.len();
            return -1;
        }
        let frame = q.pop_front().expect("front() was Some");
        *out_type = frame.msg_type;
        *out_len = frame.payload.len();
        std::ptr::copy_nonoverlapping(frame.payload.as_ptr(), out_buf, frame.payload.len());
    }
    1
}

/// Returns the native bridge version string.
#[no_mangle]
pub extern "C" fn afik_bridge_version() -> *const c_char {
    static VERSION: &str = "0.1.0\0";
    VERSION.as_ptr() as *const c_char
}

/// Initializes the in-process standalone bridge runtime.
#[no_mangle]
pub extern "C" fn afik_bridge_init(
    _app_dir: *const c_char,
    _entrypoint: *const c_char,
) -> c_int {
    ensure_initialized();
    0 // Success
}

/// Pushes a message frame into the queue destined for Dart.
/// Called from embedded Python/Rust runtime.
#[no_mangle]
pub extern "C" fn afik_push_to_dart(msg_type: u8, data: *const u8, len: usize) -> c_int {
    push(to_dart(), msg_type, data, len)
}

/// Pushes a message frame from Dart into the queue destined for Python.
/// Called from `dart:ffi`.
#[no_mangle]
pub extern "C" fn afik_push_to_python(msg_type: u8, data: *const u8, len: usize) -> c_int {
    push(to_python(), msg_type, data, len)
}

/// Polls the next pending frame destined for Dart.
/// Writes up to `max_len` bytes into `out_buf`, sets `*out_type` and `*out_len`.
/// Returns:
///   1 if a frame was read
///   0 if the queue is empty
///  -1 if the buffer was too small
///  -2 on lock or memory error
#[no_mangle]
pub extern "C" fn afik_poll_dart_frame(
    out_buf: *mut u8,
    max_len: usize,
    out_type: *mut u8,
    out_len: *mut usize,
) -> c_int {
    poll(to_dart(), out_buf, max_len, out_type, out_len)
}

/// Polls the next pending frame destined for Python.
#[no_mangle]
pub extern "C" fn afik_poll_python_frame(
    out_buf: *mut u8,
    max_len: usize,
    out_type: *mut u8,
    out_len: *mut usize,
) -> c_int {
    poll(to_python(), out_buf, max_len, out_type, out_len)
}

/// Cleans up and clears all in-memory queues.
#[no_mangle]
pub extern "C" fn afik_bridge_destroy() -> c_int {
    lock(to_dart()).clear();
    lock(to_python()).clear();
    0
}
