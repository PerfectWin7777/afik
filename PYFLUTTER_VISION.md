# PyFlutter — Project Vision & Architecture (v1 Draft)

> Status: pre-implementation design document. Codename `pyflutter` (final name TBD).

## 1. Motivation

Python has no mature, high-performance path to native mobile UI that stays
close to the platform's real rendering engine. Existing options either:

- reimplement a rendering engine from scratch (Kivy), which means
  reimplementing years of platform polish, accessibility, and animation
  work, or
- proxy the entire UI over a live wire protocol at every frame (Flet),
  trading long-term performance ceiling for simplicity.

PyFlutter's bet: use **Flutter's own renderer** as the target, but avoid
re-executing Python for the static shape of the UI at runtime. Static
widget trees are generated to real Dart once, at build time. Only dynamic
application logic (callbacks, state, native package calls) is executed by
an embedded Python runtime at runtime, bridged through Rust.

This is not a novel category of idea — it mirrors what Lynx (ByteDance)
does for JS→native (JS describes UI, Rust bridges, native renders) — but
applied to Python→Flutter specifically, with a Rust bridge tuned for that
pairing.

## 2. Non-goals (explicitly out of scope for v1)

- **Not** a full Python→Dart transpiler. Translating arbitrary Python
  (closures, generators, the stdlib, third-party packages) into Dart is
  not tractable for a solo/small project and is explicitly rejected.
- **Not** a runtime that re-sends the full JSON UI tree on every frame
  interaction in production. That model (Flet-like) is acceptable only
  as an internal dev-mode mechanism, not the production execution path.
- **Not** aiming for exhaustive coverage of every Flutter widget property
  in v1. Coverage is deliberately partial, with an escape hatch.
- **Not** attempting a generic, zero-effort mapping of arbitrary Flutter
  packages (camera, bluetooth, PDF, etc.) into Python. Each package
  integration requires a hand-written Dart-side dispatch shim.

## 3. Core Architecture

Three cooperating layers ship inside the final release binary:

```
┌─────────────────────────────────────────┐
│  Dart / Flutter shell                    │
│  - pre-generated static widget code      │
│  - per-package dispatch shims            │
│  - real Flutter renderer (Skia/Impeller) │
└───────────────▲───────────────┬──────────┘
                 │ results       │ calls (build/render/RPC)
┌────────────────┴───────────────▼──────────┐
│  Rust bridge                              │
│  - IR parser (Protobuf)                   │
│  - codegen: IR -> Dart (build/release)    │
│  - runtime bridge: routes calls/callbacks │
│  - dev server: hot-reload transport       │
└───────────────▲───────────────┬──────────┘
                 │ IR (Protobuf) │ callback triggers
┌────────────────┴───────────────▼──────────┐
│  Embedded Python runtime (RustPython)     │
│  - user's application code                │
│  - widget tree description (both paradigms)│
│  - callbacks / business logic             │
└────────────────────────────────────────────┘
```

### 3.1 Static UI vs. dynamic logic — the central split

Every PyFlutter app is split into two categories of code:

1. **Static widget declarations** (`Text`, `Button`, `Column`, `Row`,
   `Container`, `TextField` in v1 scope) — resolved once into the
   Intermediate Representation (IR), and compiled to real Dart at build
   time. Zero runtime cost in production.
2. **Dynamic logic** (callbacks, state mutation, computation) — always
   executed by the embedded Python runtime, regardless of which API
   paradigm was used to declare the UI.

This split is what makes the project tractable: we never translate
Python control flow to Dart. We only translate a bounded, well-defined
widget vocabulary.

### 3.2 The Intermediate Representation (IR)

The IR is the contract between Python and Rust, and therefore the most
structural design decision in the project. It is defined once, as a
**Protobuf schema**, generating consistent Python and Rust bindings from
a single source of truth (avoiding schema drift between the two
languages).

Decision: a **generic node message**, not one message type per widget:

```protobuf
message Widget {
  string type = 1;                  // "Button", "Column", "Text", ...
  map<string, string> props = 2;    // widget properties, string-encoded
  repeated Widget children = 3;     // for container widgets
  string callback_id = 4;           // opaque id resolved by Python at call time
}
```

Rationale: adding a new widget or property does not require touching the
schema or recompiling the Rust bridge — properties are added on the
Python side as map entries. This trades some compile-time type safety
for iteration speed, which is the right trade for v1. Stricter typing
can be layered in later without breaking the wire format.

An escape hatch field (`raw_props`, or reuse of `props` with a
`dart:`-prefixed key convention — TBD at implementation time) allows
passing a Flutter property PyFlutter hasn't explicitly mapped yet.

### 3.3 Wire format: Protobuf everywhere, including dev mode

**Decision: Protobuf/binary is used for IR transport in both development
and production — no JSON fallback, at any stage.** This is a deliberate
choice: starting with JSON would create a false sense of simplicity, and
the dev-mode hot-reload transport is architecturally identical to the
production update mechanism (both send an updated IR tree/patch), so
there is no technical reason to diverge the two paths.

### 3.4 Rust's three responsibilities

Rust is not a monolith; it has three distinct jobs, which may start as
one binary/crate for v1 and be split later:

1. **Codegen** — IR → real `.dart` source files, used for the static
   widget tree at release build time.
2. **Runtime bridge** — receives callback invocations from the embedded
   Python runtime, routes native package RPC calls to the Dart-side
   dispatch shims, returns results to Python.
3. **Dev server** — watches for Python code changes, regenerates the IR,
   pushes updates live to a running Dart shell for hot-reload.

### 3.4.1 POC transport vs. production transport (do not conflate)

The POC (built after this document was first drafted) uses a
subprocess-plus-local-TCP-socket transport between Rust and Dart, and a
subprocess-plus-stdio transport between Python and Rust. This was a
deliberate simplification to get an end-to-end proof working quickly
and testably (see the project's README for what was actually verified)
— **it is not the intended production transport.**

Spawning an arbitrary subprocess and piping its stdio is not available
on iOS, and even where it is available, a local socket adds IPC
overhead that defeats part of the point of using Rust for this bridge
in the first place. The intended production shape is Rust compiled as
a native library and linked directly into the Flutter app via
`dart:ffi`, with Python embedded (RustPython) inside that same native
layer — one process, no sockets, no subprocesses, matching §3.6's
"three layers in one binary" model. Porting the POC's frame-based
protocol from socket I/O to FFI calls is expected future work, not a
sign the architecture changed.

### 3.5 Native package integration (post-v1, but architecturally planned)

For features requiring OS-level access (camera, gallery, Bluetooth, PDF,
networking, etc.), PyFlutter does **not** attempt automatic mapping.
Instead:

- Python issues a generic RPC-style call: `{package, function, params}`.
- Rust transports this call verbatim to the Dart shell (no per-function
  logic needed in Rust for this step).
- A **hand-written Dart dispatch shim**, authored once per package
  function, receives the call, invokes the real Flutter/Dart package
  API, and serializes the result back.
- The result flows back through Rust to Python, mapped to an equivalent
  Python object.

This is deliberately modeled as RPC (similar in spirit to gRPC/JSON-RPC),
not code generation or reflection (`dart:mirrors` is unavailable on
Flutter mobile, which rules out fully automatic dispatch). Effort scales
per function, not per package as a whole, and is expected to start with
the ~10 most commonly needed packages (camera, gallery, video, audio,
PDF, basic networking) after the v1 core is stable.

### 3.6 Embedded runtime footprint

The production app embeds:

- An embedded Python interpreter (RustPython), trimmed to only the
  standard library modules actually imported by the user's app (freezing
  the full stdlib is avoidable and significantly reduces size).
- The Rust bridge binary (native code, no Python stdlib inside it).
- The Dart/Flutter shell, including generated static widgets and package
  dispatch shims.

Estimated combined footprint for Python + Rust, well optimized (LTO +
stripped binaries, selective stdlib freezing): roughly **10–20 MB**,
comparable to typical cross-platform app overhead. This is treated as an
accepted cost in exchange for not needing a full Python→Dart transpiler.

## 4. API Design

### 4.1 Two supported paradigms

Both resolve to the same IR before reaching Rust — neither is a
second-class citizen internally.

- **Declarative** (Flutter-style): composition via constructors.
  ```python
  page = Column([
      Text("Hello"),
      Button("Click me", on_click=handle_click),
  ])
  ```
- **Imperative** (Qt-style): explicit widget construction and mutation.
  ```python
  column = Column()
  column.add_widget(Text("Hello"))
  button = Button("Click me")
  button.on_click(handle_click)
  column.add_widget(button)
  ```

### 4.2 Naming conventions

- Classes: `CamelCase` (`Button`, `TextField`, `Column`) — consistent
  with both Qt heritage and Python's own PEP 8 convention for classes.
- Methods and parameters: `snake_case` (`on_click=`, `set_text()`,
  `text_align=`) — deliberately **not** full camelCase, to avoid
  friction with standard Python linters (pylint/ruff/flake8) and to
  avoid an initial "this isn't pythonic" reaction from the Python
  community, which works against the project's goal of community
  adoption.

### 4.3 Widget property coverage

v1 covers the most commonly used properties per widget (text, color,
size, primary callback), not the full surface Flutter exposes. An escape
hatch (raw/unmapped property passthrough) unblocks edge cases without
requiring exhaustive coverage before shipping. Coverage expands
incrementally, driven by real usage rather than a theoretical checklist.

## 5. Developer Experience

### 5.1 CLI, not raw `python file.py`

The framework ships a dedicated CLI, `pyflutter`, mirroring the
`flutter` CLI's ergonomics rather than relying on bare script execution
(which cannot own a persistent dev server, device detection, or a
keyboard-driven reload loop).

```
pyflutter run
```

This command:

1. Detects connected devices/emulators (mirroring `flutter devices`).
2. Starts the Rust dev server / bridge.
3. Builds/launches the minimal Dart shell on the target device.
4. Executes the user's Python entry point to produce the initial IR and
   sends it over.
5. Stays attached to the terminal, listening for the same keybindings
   Flutter developers already know:
   - `r` — hot reload (push updated IR)
   - `R` — full restart
   - `q` — quit

### 5.2 Enforced project entry point

To keep the CLI simple and the experience predictable for developers
coming from Flutter, PyFlutter enforces a conventional entry point:
a `main.py` or `app.py` file exposing a recognized `App` class or
`main()` function. This mirrors Flutter's own convention around
`lib/main.dart`.

## 6. Proof of Concept Scope

The POC exists to validate the full chain end-to-end before investing in
breadth. It deliberately excludes anything not required for that
validation.

**In scope:**
- Widgets: `Text`, `TextField`, `Button`, `Column`, `Row`, `Container`.
- Full IR round-trip: Python → Protobuf IR → Rust → Dart shell renders.
- Basic callback execution: a button click triggers a Python function
  that mutates state and updates displayed text.
- `pyflutter run` with working hot reload (`r`) via the same Protobuf
  transport used in production — no JSON shortcut.

**Explicitly out of scope for the POC:**
- Native package RPC system (camera, PDF, etc.).
- Exhaustive per-widget property coverage.
- Diff-optimized hot-reload protocol — sending the full tree on every
  change is acceptable until the base pipeline is proven.
- Release packaging pipeline (`pyflutter build`) — to be scoped once the
  POC pipeline works end-to-end in dev mode.

## 6.5 Relationship to Provider / Riverpod (Flutter state management)

`provider` and `riverpod` are Dart-side state management packages,
solving the problem of propagating a state change through the native
Flutter widget tree without manually threading it through every layer
(`provider` builds on `InheritedWidget`; `riverpod` removes the
`BuildContext` dependency `provider` has).

**PyFlutter does not need to integrate either package**, because state
does not live in the Dart widget tree in this architecture — it lives in
Python. The Dart shell in PyFlutter is comparatively "dumb": it renders
whatever IR it is given and does not need its own state-propagation
mechanism, because updates arrive pre-resolved from the Rust bridge.

This does **not** mean state management is a non-issue — it means the
problem shifts entirely to the Python side, and PyFlutter needs its own
answer for "how does a developer signal that state changed and the UI
should update." See section 6.6.

## 6.6 State update model (open design question, informed by prior art)

How should a PyFlutter developer trigger a UI update after mutating
state? Four existing models were reviewed for comparison:

- **PyQt / Qt (signals & slots):** a component emits a signal when its
  data changes; any interested widget connects a slot (a function) to
  that signal. Widgets do not need to be manually told to redraw —
  changing a widget's content triggers its own redraw automatically.
  The developer's job is limited to wiring signals to slots once; no
  manual "update the whole page" call is needed for normal cases.
- **Flet:** explicit, imperative. The developer mutates a control's
  property directly, then calls `page.update()` (or
  `control.update()`) to flush the change to the frontend. Simple to
  reason about, but the developer must remember to call `update()`.
- **React / Vue:** state is declared via a reactive primitive
  (`useState` in React, `ref`/`reactive` in Vue). Mutating that
  specific primitive automatically schedules a re-render of whatever
  depends on it — the framework tracks the dependency, the developer
  never calls an explicit "redraw" function.
- **Angular:** similar reactive intent, traditionally driven by
  "zone.js" change detection (automatically re-checking bindings after
  async events) historically, with newer Angular versions moving
  toward explicit fine-grained reactive signals closer to the
  React/Vue model.

**Two candidate directions for PyFlutter:**

1. **Explicit, Flet-style:** developer mutates a plain Python attribute,
   then calls something like `widget.update()` or `page.update()` to
   push a new IR. Simplest to implement first — no dependency tracking
   required — but places the burden of remembering to call it on the
   developer, and is easy to forget on non-trivial callbacks.
2. **Reactive, React/Vue-style:** UI-bound state is wrapped in a small
   reactive primitive (e.g. a `State` or `Signal` object); mutating it
   automatically marks the dependent part of the tree dirty and
   triggers an IR patch without an explicit call. More ergonomic long
   term, but requires building a dependency-tracking layer — real
   additional engineering scope, not something to attempt in the POC.

**Recommendation for v1 sequencing:** start with the explicit
Flet-style `update()` model for the POC and early v1 (fastest to
implement, easiest to debug, and closest in spirit to the "no magic"
principle already applied elsewhere in this document). A reactive layer
can be introduced later as an additive, opt-in ergonomic improvement
without breaking the explicit model — similgreatly to how Qt itself
lets you skip signals/slots and just call `.update()` directly on a
widget when you don't need automatic propagation. This should not be
treated as a permanently closed decision; it is deferred, not settled.

## 7. Open Questions (deferred, not blocking the POC)

- Exact final `.proto` field-level schema.
- State/reactivity model: see section 6.6 — explicit `update()` calls
  chosen as the starting point, reactive model deferred as a later
  addition.
- Error handling: behavior when embedded Python raises an unhandled
  exception mid-callback on an end user's device.
- `pyflutter build` packaging pipeline: how Python + Rust + Dart get
  assembled into a single APK/IPA.
- Final project name (currently codenamed `pyflutter`).

## 8. Adoption Strategy Notes

Flet is the closest existing competitor and has a multi-year head start,
an active community, and documentation. PyFlutter's differentiation
thesis is performance-oriented: pre-compiled static widgets plus a
narrower runtime bridge, versus Flet's fully live JSON/WebSocket model
for every frame. This thesis must be demonstrated, not just claimed —
the README and any public writing should lead with an honest technical
comparison, not a "replaces Flet" claim, and should be accompanied by a
working POC and transparent write-ups of real trade-offs encountered
during development.
