"""`pyflutter add / remove / plugin` commands built on the plugin catalog."""

from __future__ import annotations

from pathlib import Path

from pyflutter.core.config import PyFlutterConfig
from pyflutter.plugins import catalog


def _runtime_dir() -> Path:
    from pyflutter.cli.runner import find_workspace_root

    return find_workspace_root() / "dart_runtime"


def add(name: str) -> bool:
    """Installs ``name``. Catalog plugins are wired automatically; other packages only get the
    Flutter dependency and a hint to write a shim."""
    runtime_dir = _runtime_dir()
    entries = catalog.load_catalog(runtime_dir)
    config = PyFlutterConfig.find_and_load(Path.cwd())
    if name in entries:
        try:
            catalog.expand_requirements([name], entries)
            config.add_plugin(name)
            result = catalog.prepare_runtime(runtime_dir.parent, config)
        except catalog.CatalogError as e:
            print(f"Error: {e}")
            return False
        print(f"Installed plugin '{name}'. Plugins in this project: {', '.join(result.plugins)}")
        for note in [entries[n].notes for n in result.plugins if entries[n].notes]:
            print(f"  note: {note}")
        return True

    from pyflutter.plugins.manager import add_flutter_package

    print(f"'{name}' has no shim in the plugin catalog.")
    ok = add_flutter_package(name)
    if ok:
        print(
            f"The Flutter package was added, but Python cannot call it yet. Create the mapping with:\n"
            f"  pyflutter plugin new {name}\n"
            f"then fill the generated shim by following the package documentation."
        )
    return ok


def remove(name: str) -> bool:
    runtime_dir = _runtime_dir()
    config = PyFlutterConfig.find_and_load(Path.cwd())
    entries = catalog.load_catalog(runtime_dir)
    if name in entries:
        if not config.remove_plugin(name):
            print(f"Plugin '{name}' is not installed in this project.")
            return False
        try:
            result = catalog.prepare_runtime(runtime_dir.parent, config)
        except catalog.CatalogError as e:
            print(f"Error: {e}")
            return False
        print(f"Removed plugin '{name}'. Plugins left: {', '.join(result.plugins) or '(none)'}")
        return True
    from pyflutter.plugins.manager import remove_flutter_package

    return remove_flutter_package(name)


def list_plugins() -> None:
    runtime_dir = _runtime_dir()
    entries = catalog.load_catalog(runtime_dir)
    config = PyFlutterConfig.find_and_load(Path.cwd())
    print(f"{'plugin':28s} {'package':28s} installed")
    for name, e in entries.items():
        mark = "yes" if name in config.plugins else ""
        print(f"{name:28s} {e.package + ' ' + e.constraint:28s} {mark}")


def new(name: str) -> bool:
    runtime_dir = _runtime_dir()
    py_framework = Path(__file__).resolve().parents[2]
    try:
        created = catalog.scaffold_plugin(name, runtime_dir, py_framework)
    except catalog.CatalogError as e:
        print(f"Error: {e}")
        return False
    print("Created:")
    for p in created:
        print(f"  {p}")
    print("Next: read the package documentation, map its methods in shim.dart and the Python module, "
          "then `pyflutter add " + name + "`.")
    return True
