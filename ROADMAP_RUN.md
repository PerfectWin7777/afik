# PyFlutter Maturity Roadmap & Execution Plan

Date: 2026-10-02  
Status: **COMPLETED & VERIFIED** (83 unit tests passing, 0 Dart analyze warnings)

---

## Pillar 1: Tree Diffing & Optimized Hot Reload (`r` vs `R`)
- [x] Add `TreeDiff` / `Patch` representation in Python and Rust/Dart bridge (`MSG_TREE_PATCH = 0x04`)
- [x] Assign stable keys / structural node IDs (`_nid` structural path + explicit `key`)
- [x] Implement recursive node diffing algorithm in `pyflutter/core/render.py` (`diff_snapshots()`, O(N) prop diffs, child inserts/removals)
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

## Pillar 4: Plugins Architecture & 4 Core Native Plugins
- [x] Extend two-way RPC mechanism (`MSG_PLUGIN_CALL = 0x03`, `MSG_PLUGIN_RESPONSE = 0x05`, call IDs & sync/async handlers)
- [x] Implement `storage` & `shared_preferences` plugin (Key-Value persistent storage with offline fallback)
- [x] Implement `path_provider` plugin (Application Documents, Temp, Downloads directories)
- [x] Implement `device_info` plugin (OS, platform, version, processors)
- [x] Implement `file_picker` plugin (Selecting files from OS)

## Pillar 5: Rigorous Verification & Tests
- [x] Unit tests for Tree Diffing algorithm (`py_framework/tests/test_tree_diffing.py`)
- [x] Unit tests for PyQt mutators and signals (`py_framework/tests/test_pyqt_style.py`)
- [x] Unit tests for all new widgets & enhanced properties (`py_framework/tests/test_new_flutter_widgets.py`)
- [x] Unit tests for plugin RPC dispatch (`py_framework/tests/test_plugins_rpc.py`)
- [x] Verification across Dart (`dart analyze lib/` -> 0 issues) and Python (`83/83` tests passing in 0.022s)
