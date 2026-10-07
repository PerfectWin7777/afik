# Afik Maturity Roadmap & Execution Plan

Date: 2026-10-03  
Status: **COMPLETED & VERIFIED** (117 unit tests passing in 0.233s, 0 Dart analyze warnings)

---

## Pillar 1: Tree Diffing & Optimized Hot Reload (`r` vs `R`)
- [x] Add `TreeDiff` / `Patch` representation in Python and Rust/Dart bridge (`MSG_TREE_PATCH = 0x04`)
- [x] Assign stable keys / structural node IDs (`_nid` structural path + explicit `key`)
- [x] Implement recursive node diffing algorithm in `afik/core/render.py` (`diff_snapshots()`, O(N) prop diffs, child inserts/removals)
- [x] Separate `r` (Hot Reload: preserve Python app state / signals, re-execute `build()`, send micro-patch) from `R` (Hot Restart: clear state, rebuild root tree)
- [x] Update `dart_runtime` to support applying granular patches directly to `WidgetNode`s in-place without re-evaluating the entire tree (`findNodeById`, `_handleTreePatch`)

## Pillar 2: PyQt / PySide OOP Programming Maturity
- [x] Direct widget mutators with automatic reactivity (`label.setText(...)`, `button.setEnabled(...)`, `widget.setVisible(...)`, `input.set_value(...)`, `switch.setChecked(...)`)
- [x] Rich typed signals (`textChanged`, `valueChanged`, `toggled`, `on_changed`) passing values directly to connected slots
- [x] `QMainWindow` style enhancements (`setCentralWidget`, `setMenuBar`, `setStatusBar`, `addToolBar`)
- [x] Automatic dirty tracking (`_notify_dirty()`) for modified widgets so UI updates automatically without manual boilerplates

## Pillar 3: Flutter Mirroring & Missing Widgets
- [x] Add `GridView`, `GridView.count`, `GridView.extent`
- [x] Add `Radio`, `RadioListTile`
- [x] Add `Tooltip`
- [x] Add `RichText` & `TextSpan`
- [x] Add `CircleAvatar`
- [x] Add `LinearProgressIndicator`
- [x] Add `PopupMenuButton` & `PopupMenuItem`
- [x] Add `RefreshIndicator`
- [x] Add declarative `AlertDialog` / `SimpleDialog`
- [x] Enrich existing widgets:
  - `Container`: `margin`, `box_shadow`, `gradient` (Linear/Radial), individual side borders
  - `TextField`: `keyboard_type`, `obscure_text`, `prefix_icon`, `suffix_icon`, `max_length`, `read_only`
  - `ListView`: `physics`, `shrink_wrap`, `padding`, `reverse`
  - `Image`: network vs asset vs memory base64 support, `fit`, `width`, `height`

## Pillar 4: Core Plugins Infrastructure
- [x] Extend two-way RPC mechanism (`MSG_PLUGIN_CALL = 0x03`, `MSG_PLUGIN_RESPONSE = 0x05`, call IDs & sync/async handlers)
- [x] Implement `storage` & `shared_preferences` plugin (Key-Value persistent storage with offline fallback)
- [x] Implement `path_provider` plugin (Application Documents, Temp, Downloads directories)
- [x] Implement `device_info` plugin (OS, platform, version, processors)
- [x] Implement `file_picker` plugin (Selecting files from OS)

## Pillar 5: Wave 1 Media & Connectivity Packages
- [x] `image_picker`: Camera & gallery photo/video selection with `XFile` (`pick_image`, `pick_video`, `pick_multi_image`)
- [x] `camera`: Camera discovery (`available_cameras`), `CameraController` lifecycle, zoom/flash/recording control, and `CameraPreview` viewfinder widget
- [x] `connectivity_plus`: Network status detection (`check_connectivity`, `is_connected`, `ConnectivityResult`)
- [x] `audioplayers`: Multi-player audio engine (`AudioPlayer`, `play`, `pause`, `stop`, `seek`, `set_volume`, `get_duration`, `get_position`)
- [x] `video_player`: Streaming & local video (`VideoPlayerController`, network/file/asset loaders) and `VideoPlayer` viewport widget with playback scrubber controls
- [x] `share_plus`: System share sheets for text, URLs, and multi-file attachments (`share`, `share_files`, `share_uri`)
- [x] `webview_flutter`: Embedded web browser (`WebViewController`, `load_url`, `load_html`, `reload`, `go_back`, JS evaluation) and `WebView` browser widget

## Pillar 6: Wave 2 Databases, Security & System Packages
- [x] `chewie`: Enhanced video player controls with full-screen support, Material styling, and `Chewie` widget
- [x] `hive`: Ultra-fast lightweight key-value NoSQL database (`open_box`, `Box`, `put`, `get`, `delete`, dict-like syntax)
- [x] `sqflite`: Relational SQLite engine (`open_database`, `Database`, `execute`, `insert`, `query`, `update`, `delete`, `raw_query`)
- [x] `flutter_local_notifications`: Local system notifications (`FlutterLocalNotificationsPlugin`, `show`, `cancel`, `cancel_all`, `get_active_notifications`)
- [x] `permission_handler`: Granular permission checks and requests (`Permission`, `PermissionStatus`, `check_permission`, `request_permission`, `open_app_settings`)
- [x] `flutter_secure_storage`: Encrypted storage vault (`FlutterSecureStorage`, `write`, `read`, `delete`, `read_all`)
- [x] `local_auth`: Biometric authentication (`LocalAuthentication`, `can_check_biometrics`, `is_device_supported`, `get_available_biometrics`, `authenticate`)

## Pillar 7: PDF Ecosystem Suite & Document Viewers
- [x] `syncfusion_flutter_pdfviewer`: Enterprise PDF viewer (`SfPdfViewer.network`, `SfPdfViewer.file`, `SfPdfViewer.asset`) with top pagination/zoom toolbar and `PdfViewerController`
- [x] `pdfx`: Modern pdfium rendering engine with `PdfView`, `PdfViewPinch`, and `PdfDocument` (`open_file`, `open_asset`, `render_page`)
- [x] `printing` / `pdf`: Native printing dialog, layout generator, and system PDF file sharing (`Printing.print_pdf`, `Printing.share_pdf`, `Printing.layout_pdf`)
- [x] `flutter_pdfview`: Native mobile platform viewer (`PDFView` widget with swipe navigation and page events)

## Pillar 8: Rigorous Verification & Tests
- [x] Unit tests for Tree Diffing algorithm (`py_framework/tests/test_tree_diffing.py`)
- [x] Unit tests for PyQt mutators and signals (`py_framework/tests/test_pyqt_style.py`)
- [x] Unit tests for Flutter mirrored widgets & enhanced properties (`py_framework/tests/test_new_flutter_widgets.py`)
- [x] Unit tests for plugin RPC dispatch & first 4 plugins (`py_framework/tests/test_plugins_rpc.py`)
- [x] Unit tests for Wave 1 packages & media widgets (`py_framework/tests/test_extended_plugins_and_widgets.py`)
- [x] Unit tests for Wave 2 packages & Chewie widget (`py_framework/tests/test_second_wave_plugins.py`)
- [x] Unit tests for PDF Suite plugins & widgets (`py_framework/tests/test_pdf_suite.py`)
- [x] Verification across Dart (`dart analyze lib/` -> 0 issues) and Python (`117/117` tests passing in 0.233s)
