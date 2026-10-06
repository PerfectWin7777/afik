# Plugin catalog

One folder per Flutter package PyFlutter can drive:

- `plugin.yaml` - the pub.dev package and version constraint, the plugin names it registers, extra
  packages or required plugins, and the native settings it needs (`android:` / `ios:`).
- `shim.dart` (and optional extra files listed under `files:`) - the hand-written Dart code that
  calls the real package. It must expose a top-level `void register()` that registers the plugin
  names (`PluginRegistry.register`) and any widget types (`WidgetRegistry.register`).

Nothing here is part of the core runtime. A project lists the plugins it uses under `plugins:` in
`pyflutter.yaml`; `pyflutter add <name>` (or `pyflutter run` / `build`) copies the shims into
`lib/plugins/installed/`, writes the dependencies into `pubspec.yaml`, regenerates
`lib/plugins/installed_plugins.dart` and applies the native Android settings.

## Mapping rules

1. One Dart method = one snake_case Python method in `pyflutter/plugins/<name>.py`.
2. Return only what the platform answered. Never invent a success: a missing or malformed answer
   must read as a failure on the Python side (`isinstance(res, dict) and res.get("ok") is True`).
3. Throw (`UnsupportedError`, `ArgumentError`, the package's own exceptions) for anything that
   cannot be done; the error reaches Python as `PluginError`.
4. Keep results simple: `Map`, `List`, `String`, `num`, `bool`, `null`.
5. Arguments reach `handleMethodCall` as `String`s: a string stays as it is, `null` becomes `''`
   and any other value (number, bool, list, map) becomes its **JSON** text. A shim that needs the
   decoded values implements `StructuredPyFlutterPlugin` and reads them from `handleRawCall`.
6. Interactive calls (pickers, permission prompts, authentication) use the 120 s timeout.

## Tools

- `pyflutter plugin new <package>` creates the skeleton (entry, shim, Python module, test).
- `python tools/verify_catalog.py [plugin ...]` installs each plugin into a temporary copy of
  `dart_runtime/`, runs `flutter pub get` and `flutter analyze`, and then installs them all
  together to catch dependency conflicts between plugins.
