"""`pyflutter add / remove / plugin` commands built on the plugin catalog and the project runtime."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from pyflutter.core.config import PyFlutterConfig
from pyflutter.core.logger import logger
from pyflutter.core.runtime_project import ProjectRuntime
from pyflutter.plugins import catalog


def _template_dir() -> Path:
    from pyflutter.cli.runner import find_workspace_root

    return find_workspace_root() / "dart_runtime"


def _project() -> tuple[PyFlutterConfig, ProjectRuntime]:
    """The configuration and the runtime copy of the project in the current directory."""
    config = PyFlutterConfig.find_and_load(Path.cwd())
    return config, ProjectRuntime.for_config(config, _template_dir(), Path.cwd())


def add(name: str) -> bool:
    """Installs ``name``. Catalog plugins are wired automatically; other packages get the Flutter
    dependency and a hint to write a shim."""
    config, runtime = _project()
    entries = catalog.load_catalog(runtime.template_dir)
    if name in entries:
        try:
            catalog.expand_requirements([name], entries)
            config.add_plugin(name)
            result = catalog.prepare_runtime(runtime, config)
        except (catalog.CatalogError, OSError) as e:
            print(f"Error: {e}")
            return False
        print(f"Installed plugin '{name}'. Plugins in this project: {', '.join(result.plugins)}")
        for note in [entries[n].notes for n in result.plugins if entries[n].notes]:
            print(f"  note: {note}")
        return True

    print(f"'{name}' has no shim in the plugin catalog.")
    if not install_package(name, config, runtime):
        return False
    print(
        "The Flutter package was added to this project, but Python cannot call it yet. Create the mapping with:\n"
        f"  pyflutter plugin new {name}\n"
        "then fill the generated shim by following the package documentation."
    )
    return True


def install_package(name: str, config: Optional[PyFlutterConfig] = None, runtime: Optional[ProjectRuntime] = None) -> bool:
    """Adds a Flutter package that has no catalog entry to the project's ``dependencies.flutter``.

    The constraint written to pyflutter.yaml is the version `flutter pub get` actually resolved.
    """
    if config is None or runtime is None:
        config, runtime = _project()
    previous = dict(config.flutter_dependencies)
    config.set_flutter_dependencies({**previous, name: "any"})
    try:
        catalog.prepare_runtime(runtime, config)
    except (catalog.CatalogError, OSError) as e:
        config.set_flutter_dependencies(previous)
        print(f"Error: could not add '{name}': {e}")
        return False
    version = catalog.resolved_version(runtime.runtime_dir, name)
    if version:
        config.set_flutter_dependencies({**config.flutter_dependencies, name: f"^{version}"})
        catalog.prepare_runtime(runtime, config, run_pub_get=False)
    logger.info("Added Flutter package {} {}", name, config.flutter_dependencies[name])
    return True


def remove(name: str) -> bool:
    config, runtime = _project()
    entries = catalog.load_catalog(runtime.template_dir)
    if name in entries:
        if not config.remove_plugin(name):
            print(f"Plugin '{name}' is not installed in this project.")
            return False
        try:
            result = catalog.prepare_runtime(runtime, config)
        except (catalog.CatalogError, OSError) as e:
            print(f"Error: {e}")
            return False
        print(f"Removed plugin '{name}'. Plugins left: {', '.join(result.plugins) or '(none)'}")
        return True
    if name not in config.flutter_dependencies:
        print(f"'{name}' is not a plugin or a Flutter package of this project.")
        return False
    config.set_flutter_dependencies({k: v for k, v in config.flutter_dependencies.items() if k != name})
    try:
        catalog.prepare_runtime(runtime, config)
    except (catalog.CatalogError, OSError) as e:
        print(f"Error: {e}")
        return False
    print(f"Removed Flutter package '{name}'.")
    return True


def list_plugins() -> None:
    config, runtime = _project()
    entries = catalog.load_catalog(runtime.template_dir)
    print(f"{'plugin':28s} {'package':32s} installed")
    for name, e in entries.items():
        mark = "yes" if name in config.plugins else ""
        print(f"{name:28s} {e.package + ' ' + e.constraint:32s} {mark}")
    extras = [n for n in config.flutter_dependencies if n not in {e.package for e in entries.values()}]
    if extras:
        print("\nFlutter packages without a shim: " + ", ".join(extras))


def new(name: str) -> bool:
    py_framework = Path(__file__).resolve().parents[2]
    try:
        created = catalog.scaffold_plugin(name, _template_dir(), py_framework)
    except catalog.CatalogError as e:
        print(f"Error: {e}")
        return False
    print("Created:")
    for p in created:
        print(f"  {p}")
    print("Next: read the package documentation, map its methods in shim.dart and the Python module, "
          "then `pyflutter add " + name + "`.")
    return True
