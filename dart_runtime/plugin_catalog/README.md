# Plugin catalog

One folder per Flutter package that PyFlutter knows how to drive:

- `plugin.yaml` — package name and version constraint, shim class, names it registers, native requirements.
- `shim.dart` — the hand-written dispatch shim that calls the real package API.

Nothing in this folder is compiled into the runtime by default. `pyflutter add <package>`
is meant to add the dependency to the project's own runtime copy, copy the shim and register it
(design in `AUDIT_BUGS.md`, ticket T-20). Until that command exists, these files are only the
reference implementation of each shim.
