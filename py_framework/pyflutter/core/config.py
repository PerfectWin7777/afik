"""
PyFlutter Project Configuration Management (pyflutter.yaml).
Identical concept to Flutter's pubspec.yaml: manages project metadata,
Python entrypoint, native Flutter packages, and device permissions.
"""

from __future__ import annotations

import copy
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

try:
    import yaml
except ImportError:
    yaml = None


CONFIG_FILENAMES = ["pyflutter.yaml", "pyflutter.yml"]


@dataclass
class PyFlutterConfig:
    name: str = "pyflutter_app"
    description: str = "A PyFlutter application"
    version: str = "0.1.0"
    entrypoint: str = "main.py"
    port: int = 7879
    flutter_dependencies: dict[str, str] = field(default_factory=dict)
    plugins: list[str] = field(default_factory=list)
    permissions: list[str] = field(default_factory=list)
    raw_config: dict[str, Any] = field(default_factory=dict)
    config_path: Optional[Path] = None

    @classmethod
    def find_and_load(cls, start_dir: Optional[Path] = None) -> PyFlutterConfig:
        """Searches current and parent directories for pyflutter.yaml."""
        search_dir = (start_dir or Path.cwd()).resolve()
        for directory in [search_dir, *search_dir.parents]:
            for name in CONFIG_FILENAMES:
                cfg_file = directory / name
                if cfg_file.exists():
                    return cls.from_file(cfg_file)
        # Return default config if no file found
        return cls()

    @classmethod
    def from_file(cls, path: Path) -> PyFlutterConfig:
        if yaml is None:
            return cls(config_path=path)

        try:
            with open(path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}
        except Exception as e:
            from pyflutter.core.logger import logger
            logger.warning("Could not parse {}: {}. Using default configuration.", path, e)
            data = {}
        if not isinstance(data, dict):
            from pyflutter.core.logger import logger
            logger.warning("{} must contain a mapping at its root; ignoring its content.", path)
            data = {}

        def _section(value: Any) -> dict:
            return value if isinstance(value, dict) else {}

        pyflutter_section = _section(data.get("pyflutter"))
        dependencies_section = _section(data.get("dependencies"))
        flutter_deps = dependencies_section.get("flutter") or {}

        # Flutter deps can be a dict (pkg: version) or a list of items
        deps_map: dict[str, str] = {}
        if isinstance(flutter_deps, dict):
            deps_map = {str(k): str(v) for k, v in flutter_deps.items()}
        elif isinstance(flutter_deps, list):
            for item in flutter_deps:
                if isinstance(item, dict):
                    deps_map.update({str(k): str(v) for k, v in item.items()})
                elif isinstance(item, str):
                    deps_map[item] = "any"

        permissions = data.get("permissions") or []
        if not isinstance(permissions, list):
            permissions = []

        raw_plugins = data.get("plugins") or []
        plugins = [str(p) for p in raw_plugins] if isinstance(raw_plugins, list) else []

        try:
            port = int(pyflutter_section.get("port", 7879))
        except (TypeError, ValueError):
            from pyflutter.core.logger import logger
            logger.warning("Invalid pyflutter.port in {}; using 7879.", path)
            port = 7879

        return cls(
            name=str(data.get("name") or "pyflutter_app"),
            description=data.get("description", "A PyFlutter application"),
            version=str(data.get("version", "0.1.0")),
            entrypoint=pyflutter_section.get("entrypoint", "main.py"),
            port=port,
            flutter_dependencies=deps_map,
            plugins=plugins,
            permissions=[str(p) for p in permissions],
            raw_config=data,
            config_path=path.resolve(),
        )

    def save(self, path: Optional[Path] = None) -> None:
        """Saves current configuration to pyflutter.yaml."""
        if yaml is None:
            return

        target_path = path or self.config_path or (Path.cwd() / "pyflutter.yaml")

        # Start from what is already in the file so unknown keys are not lost.
        data = copy.deepcopy(self.raw_config) if isinstance(self.raw_config, dict) else {}
        data["name"] = self.name
        data["description"] = self.description
        data["version"] = self.version
        data.setdefault("pyflutter", {})
        if not isinstance(data["pyflutter"], dict):
            data["pyflutter"] = {}
        data["pyflutter"]["entrypoint"] = self.entrypoint
        data["pyflutter"]["port"] = self.port
        deps = data.get("dependencies")
        if not isinstance(deps, dict):
            deps = {}
        deps["flutter"] = self.flutter_dependencies
        data["dependencies"] = deps
        if self.plugins:
            data["plugins"] = list(self.plugins)
        else:
            data.pop("plugins", None)
        if self.permissions:
            data["permissions"] = self.permissions
        else:
            data.pop("permissions", None)
        self.raw_config = data

        with open(target_path, "w", encoding="utf-8") as f:
            yaml.dump(data, f, sort_keys=False, default_flow_style=False)

        self.config_path = target_path.resolve()

    def add_flutter_dependency(self, package_name: str, version: str = "any") -> None:
        """Adds a native Flutter package to this project's dependencies."""
        self.flutter_dependencies[package_name] = version
        self.save()

    def add_plugin(self, name: str) -> bool:
        """Adds a catalog plugin to the project. Returns False if it was already listed."""
        if name in self.plugins:
            return False
        self.plugins.append(name)
        self.save()
        return True

    def remove_plugin(self, name: str) -> bool:
        """Removes a catalog plugin from the project. Returns False if it was not listed."""
        if name not in self.plugins:
            return False
        self.plugins.remove(name)
        self.save()
        return True

    def remove_flutter_dependency(self, package_name: str) -> None:
        """Removes a native Flutter package from this project's dependencies."""
        if package_name in self.flutter_dependencies:
            del self.flutter_dependencies[package_name]
            self.save()
