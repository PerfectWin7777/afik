"""
Per-project copy of the Flutter runtime.

``dart_runtime/`` in the framework repository is only a **template**. Every project works on
its own copy in ``<project>/.afik/runtime/``: the plugins it installs, the dependencies it
declares, its permissions and its build output live there, so two projects never fight over the
same files and the framework repository stays clean.

The copy is created on first use and refreshed when the template changes (a new framework
version). Refreshing overwrites the files the template owns and keeps what belongs to the project
(build output, ``pubspec.lock``); everything generated from ``afik.yaml`` is then written
again by :func:`afik.plugins.catalog.prepare_runtime`.
"""

from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path
from typing import Optional

from afik.core.logger import logger

RUNTIME_RELATIVE = Path(".afik") / "runtime"
STATE_FILE = ".afik-template.json"

# Never copied from the template, never deleted from the copy.
IGNORED_NAMES = {
    "build", ".dart_tool", ".gradle", ".idea", "Pods", ".symlinks", "ephemeral",
    "plugin_catalog", "installed", "test", ".afik", "local.properties", ".flutter-plugins",
    ".flutter-plugins-dependencies", ".packages", ".metadata", "generated_plugins.cmake",
    "generated_plugin_registrant.cc", "generated_plugin_registrant.h", "GeneratedPluginRegistrant.swift",
    "GeneratedPluginRegistrant.java", "GeneratedPluginRegistrant.m",
}
# Kept as the project has it once the copy exists (resolved versions belong to the project).
PROJECT_OWNED = {"pubspec.lock"}


def _is_ignored(rel: Path) -> bool:
    return any(part in IGNORED_NAMES or part.endswith(".iml") for part in rel.parts)


def template_files(template_dir: Path) -> list[Path]:
    """Relative paths of every template file that is copied into a project."""
    template_dir = Path(template_dir)
    files = []
    for path in sorted(template_dir.rglob("*")):
        if path.is_file():
            rel = path.relative_to(template_dir)
            if not _is_ignored(rel):
                files.append(rel)
    return files


def template_fingerprint(template_dir: Path) -> str:
    """Hash of the names and contents of the template files."""
    digest = hashlib.sha256()
    for rel in template_files(template_dir):
        digest.update(rel.as_posix().encode("utf-8"))
        digest.update(b"\0")
        digest.update((Path(template_dir) / rel).read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


class ProjectRuntime:
    """The Flutter runtime copy of one project."""

    def __init__(self, project_dir: Path, template_dir: Path):
        self.project_dir = Path(project_dir).resolve()
        self.template_dir = Path(template_dir).resolve()
        self.runtime_dir = self.project_dir / RUNTIME_RELATIVE

    @classmethod
    def for_config(cls, config, template_dir: Path, fallback_dir: Optional[Path] = None) -> "ProjectRuntime":
        """The runtime of the project that owns ``config`` (or of ``fallback_dir`` / the cwd)."""
        if getattr(config, "config_path", None):
            project_dir = Path(config.config_path).parent
        else:
            project_dir = Path(fallback_dir) if fallback_dir else Path.cwd()
        return cls(project_dir, template_dir)

    @property
    def exists(self) -> bool:
        return self.runtime_dir.is_dir()

    def ensure(self) -> bool:
        """Creates the copy, or refreshes it if the template changed. True if files were written."""
        if not self.template_dir.is_dir():
            raise FileNotFoundError(f"Flutter runtime template not found: {self.template_dir}")

        fingerprint = template_fingerprint(self.template_dir)
        state_path = self.runtime_dir / STATE_FILE
        previous: dict = {}
        if state_path.exists():
            try:
                previous = json.loads(state_path.read_text(encoding="utf-8"))
            except ValueError:
                previous = {}
        if self.exists and previous.get("fingerprint") == fingerprint:
            return False

        first_time = not self.exists
        logger.info("{} the Flutter runtime of this project ({})", "Creating" if first_time else "Refreshing", self.runtime_dir)
        files = template_files(self.template_dir)
        self.runtime_dir.mkdir(parents=True, exist_ok=True)
        for rel in files:
            target = self.runtime_dir / rel
            if rel.name in PROJECT_OWNED and target.exists():
                continue
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(self.template_dir / rel, target)

        # Files that were in the previous template but not in this one are removed.
        current = {rel.as_posix() for rel in files}
        for old in previous.get("files", []):
            if old not in current:
                stale = self.runtime_dir / old
                if stale.is_file():
                    stale.unlink()

        state_path.write_text(
            json.dumps({"fingerprint": fingerprint, "files": sorted(current)}, indent=1), encoding="utf-8"
        )
        return True
