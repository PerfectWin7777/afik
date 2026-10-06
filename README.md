# PyFlutter

[![Python](https://img.shields.io/badge/python-3.10%20%7C%203.11%20%7C%203.12%20%7C%203.13-blue)](py_framework/pyproject.toml)
[![Flutter](https://img.shields.io/badge/flutter-%3E%3D3.32-02569B?logo=flutter)](https://flutter.dev)
[![Status](https://img.shields.io/badge/status-alpha-orange)]()

**PyFlutter** lets Python developers describe a user interface in Python and have it rendered by Flutter's native engine.
The Python application runs on your machine, a small Rust bridge relays messages, and a Flutter shell draws the widgets and calls native packages.

> **Status: alpha, development mode only.** The full loop (Python → Rust bridge → Flutter shell → callbacks back to Python, with hot reload) works while you develop on a connected device or desktop.
> Shipping a self-contained app that embeds Python is **not implemented yet** (see [What works today](#what-works-today)).
> The project is called *PyFlutter* in the code and the CLI; a rename (*Flarix*) is under consideration.

---

## Why PyFlutter?

- **Pythonic API**: `Component` / `StatefulComponent`, Signals, or Qt-style fluent widgets (`add_widget()`, `.clicked.connect()`).
- **Flutter's real renderer**: Material 3 widgets drawn by Flutter, not re-implemented.
- **Compact binary protocol**: Protobuf frames between Python, Rust and Dart; incremental patches instead of resending the whole tree when only properties change.
- **Packages on demand**: native Flutter packages are mapped to Python classes by hand-written shims (see [Native packages](#native-packages)); you only add the ones you use.

---

## Architecture

```mermaid
graph LR
    subgraph Python ["Python application (your machine)"]
        App["App / Component"] --> State["Signals / State"]
        State --> Render["Tree resolve + diff"]
    end

    subgraph Bridge ["Rust bridge (subprocess)"]
        Render -->|"Protobuf / JSON patch frames over stdio"| Rust["Relay"]
    end

    subgraph Flutter ["Flutter shell"]
        Rust -->|"local TCP socket"| Dart["Widget builder"]
        Dart --> Plugins["Per-package shims -> real Flutter packages"]
    end
```

Native package calls travel the same way: Python sends `{plugin, method, args}`, a hand-written Dart shim calls the real package, and the answer comes back to the waiting Python call.

---

## What works today

| Area | State |
|------|-------|
| `pyflutter run` on Android / desktop devices with hot reload (`r`) and hot restart (`R`) | Works |
| Material widgets, reactive state, forms, navigation stack, SnackBar / dialogs | Works (coverage is partial, see `PYFLUTTER_VISION.md`) |
| Incremental tree patches, reconnection resync, session token on the local socket | Works |
| Native packages with a real shim | `url_launcher`, `shared_preferences`, `path_provider`, `device_info_plus`, `file_picker`; `sqflite` uses Python's `sqlite3` |
| Native packages with a **simulated** shim (in-memory placeholder, not the real package) | `image_picker`, `camera`, `connectivity_plus`, `audioplayers`, `video_player`, `share_plus`, `webview_flutter`, `chewie`, `hive`, `flutter_local_notifications`, PDF packages |
| Security packages (`local_auth`, `permission_handler`, `flutter_secure_storage`) | Real shims exist in `dart_runtime/plugin_catalog/`; they are installed on demand (design in `AUDIT_BUGS.md`, ticket T-20) |
| Standalone app that embeds Python (APK / IPA / desktop bundle) | **Not implemented**: `pyflutter build` compiles the Flutter shell, but no Python interpreter is embedded yet |
| Web and iOS | **Not supported yet** (the shell imports `dart:io` / `dart:ffi`; iOS needs the embedded runtime) |
| Installation with `pip install` outside a repository clone | **Not available yet**: the CLI needs the `dart_runtime/` and `rust_bridge/` folders of this repository |

`AUDIT_BUGS.md` lists every known bug and missing piece with the planned fix.

---

## 🚀 Quickstart

### 1. Installation

```bash
git clone https://github.com/PerfectWin7777/pyflutter.git
cd pyflutter/py_framework
pip install -e .
```

### 2. Create Your First App (`main.py`)

```python
import pyflutter as pf

class CounterApp(pf.Component):
    def __init__(self):
        super().__init__()
        self.count = 0

    def increment(self):
        self.count += 1
        self.update()  # Triggers instant reactive UI update

    def build(self):
        return pf.Scaffold(
            app_bar=pf.AppBar(
                title=pf.Text("Counter", color=pf.Colors.WHITE),
                background_color="#1877F2",
            ),
            body=pf.Center(
                pf.Card(
                    pf.Column([
                        pf.Text("Compteur", font_size=14, color=pf.Colors.GREY),
                        pf.SizedBox(height=8),
                        pf.Text(str(self.count), font_size=48, font_weight="bold"),
                        pf.SizedBox(height=16),
                        pf.ElevatedButton("+1", on_click=self.increment),
                    ], cross_axis_alignment="center"),
                    padding=24,
                    border_radius=16,
                )
            ),
            floating_action_button=pf.FloatingActionButton(
                icon=pf.Icons.ADD,
                on_click=self.increment,
            ),
        )

if __name__ == "__main__":
    # Run interactively on a connected device or desktop (development mode):
    pf.run(CounterApp())
```

### 3. Run

```bash
# Run interactively with hot reload (needs the Rust bridge built once: see Requirements)
python main.py            # or: pyflutter run main.py

# Flutter shell build (does NOT embed Python yet)
pyflutter build apk --release
pyflutter build windows --release
```

### Requirements

- Python 3.10+
- Flutter SDK (3.32 or newer) in `PATH`, and a device, emulator or desktop target (`pyflutter devices`)
- Rust toolchain and `protoc` to build the bridge once: `cargo build --manifest-path rust_bridge/Cargo.toml`
- Android: Android SDK / NDK as required by Flutter

---

## Showcase examples

See [`examples/`](examples):

- [`examples/counter`](examples/counter): Material 3 counter with a FloatingActionButton.
- [`examples/facebook_feed`](examples/facebook_feed): social feed with dataclasses, like toggling, bottom navigation.
- [`examples/pyshop`](examples/pyshop): e-commerce showcase (Qt-style layouts, live search, reactive cart, SnackBars, `url_launcher`).

```bash
cd examples/counter
python main.py
```

---

## Native packages

PyFlutter does **not** try to expose every pub.dev package automatically. The model is:

1. A Python module per package (`pyflutter.plugins.<package>`) mirrors the package's classes and methods.
2. A hand-written Dart shim receives `{plugin, method, args}` and calls the real package API.
3. Packages are installed per project, on demand: `pyflutter add <package>` (the Flutter dependency, the shim and the native settings for that package; being finalised, see `AUDIT_BUGS.md` T-20).

For a package without a shim, the generic `pf.MethodChannel(name).invoke_method(...)` can call a native channel the package exposes, but many packages use private channels, so a shim is the reliable path.

| Package | Python module | Shim |
|---|---|---|
| `shared_preferences` | `pyflutter.plugins.shared_preferences` | Real |
| `path_provider` | `pyflutter.plugins.path_provider` | Real |
| `device_info_plus` | `pyflutter.plugins.device_info_plus` | Real |
| `url_launcher` | `pyflutter.plugins.url_launcher` | Real |
| `file_picker` | `pyflutter.plugins.file_picker` | Real |
| `sqflite` | `pyflutter.plugins.sqflite` | Python `sqlite3` |
| `local_auth`, `permission_handler`, `flutter_secure_storage` | `pyflutter.plugins.<name>` | Real, in `dart_runtime/plugin_catalog/` (install on demand) |
| `image_picker`, `camera`, `connectivity_plus`, `audioplayers`, `video_player`, `share_plus`, `webview_flutter`, `chewie`, `hive`, `flutter_local_notifications`, `syncfusion_flutter_pdfviewer`, `pdfx`, `printing`, `flutter_pdfview` | `pyflutter.plugins.<name>` | Simulated placeholder |

Without a connected Flutter runtime (unit tests, scripts), plugin calls use a local simulation so code can be tested offline. With a runtime connected, a plugin error or timeout raises `PluginError` / `PluginTimeoutError`; it is never replaced by simulated data.

---

## CLI reference

| Command | Arguments / flags | Description |
|---|---|---|
| `pyflutter run` | `[entrypoint] [-d <device>] [-p <port>] [--attach]` | Run the app interactively on a device or desktop |
| `pyflutter devices` | | List devices and emulators detected by Flutter |
| `pyflutter build` | `[target] [--debug\|--release\|--profile] [--split-per-abi]` | Build the Flutter shell (default: `apk`, debug). No embedded Python yet |
| `pyflutter create` | `<name>` | Scaffold a project |
| `pyflutter init` | | Initialise a project in the current directory |
| `pyflutter sync` | | Sync `pyflutter.yaml` permissions to the Android manifest and iOS plist |
| `pyflutter add` | `<package>` | Add a Flutter package to the runtime |
| `pyflutter remove` | `<package>` | Remove a Flutter package from the runtime |

Build targets: `apk`, `appbundle`, `windows`, `linux`, `macos`, `web`, `ipa` (`web` and `ipa` are not supported yet, see above).

---

## Tests

```bash
pip install pytest protobuf loguru pyyaml
cd py_framework
python -m pytest -q
```

The Rust relay tests (`tests/test_bridge_relay.py`) run the real bridge binary and are skipped when it is not built. The Dart runtime has no automated tests yet.

---

## Roadmap

- [x] Duplex reactive bridge (Protobuf frames, Rust relay, Flutter shell) in development mode
- [x] Material 3 widget catalog (partial coverage)
- [x] Callback lifecycle (sweep, pinned one-shot callbacks), deterministic state keys
- [x] Hot reload / hot restart, reconnection resync
- [ ] Packages on demand (`pyflutter add` with a plugin catalog)
- [ ] Embedded Python interpreter for standalone builds
- [ ] Pip distribution with a prebuilt bridge
- [ ] Hot reload of every project module, file watcher
- [ ] Documentation site

The detailed, ordered plan is in [`AUDIT_BUGS.md`](AUDIT_BUGS.md).

---

## License

MIT (the `LICENSE` file is still to be added).
