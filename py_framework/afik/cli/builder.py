"""
Afik CLI Standalone Builder.
Builds autonomous production packages (APK, AppBundle, Windows, Linux, macOS, Web)
by embedding the Python app assets and native FFI bridge library (.so / .dll).
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path
from typing import Optional

from afik.core.config import AfikConfig
from afik.core.logger import logger
from afik.core.runtime_project import ProjectRuntime


def find_workspace_root() -> Path:
    """Finds the root directory containing dart_runtime and rust_bridge."""
    current = Path.cwd().resolve()
    for parent in [current, *current.parents]:
        if (parent / "dart_runtime").exists() and (parent / "rust_bridge").exists():
            return parent
    return Path(__file__).resolve().parents[3]


class AfikBuilder:
    """Orchestrates building autonomous standalone packages."""

    def __init__(
        self,
        target: str = "apk",
        entrypoint: str = "main.py",
        release: bool = False,
        split_per_abi: bool = False,
        profile: bool = False,
    ):
        raw_target = target.lower()
        if raw_target == "bundle":
            self.target = "appbundle"
        elif raw_target == "ios":
            self.target = "ipa"
        else:
            self.target = raw_target

        self.entrypoint = Path(entrypoint).resolve()
        self.release = release
        self.profile = profile and not release
        self.split_per_abi = split_per_abi
        self.workspace_root = find_workspace_root()
        self.rust_bridge = self.workspace_root / "rust_bridge"
        # Set in build(): the project's own copy of the Flutter runtime (never the framework template).
        self.runtime: Optional[ProjectRuntime] = None
        self.dart_runtime = self.workspace_root / "dart_runtime"

    def build(self) -> bool:
        """Executes the complete end-to-end autonomous standalone build pipeline."""
        logger.info(f"🚀 Starting Afik Standalone Build ({self.target.upper()})...")
        mode_str = "Release" if self.release else "Profile" if self.profile else "Debug"
        logger.info(f"   Target: {self.target} | Mode: {mode_str} | Entrypoint: {self.entrypoint.name}")

        # 1. Validate environment
        if not self.entrypoint.exists():
            logger.error(f"Entrypoint file '{self.entrypoint}' not found.")
            return False

        flutter_bin = shutil.which("flutter") or shutil.which("flutter.bat")
        if not flutter_bin:
            logger.error("Flutter SDK not found in PATH.")
            return False

        # 2. Sync metadata from afik.yaml
        config = AfikConfig.find_and_load(self.entrypoint.parent)
        if config.config_path is None:
            config = AfikConfig.find_and_load(Path.cwd())
        self.runtime = ProjectRuntime.for_config(config, self.workspace_root / "dart_runtime", self.entrypoint.parent)
        self.dart_runtime = self.runtime.runtime_dir
        logger.info("📦 Synchronizing platform manifests & permissions...")
        from afik.plugins.catalog import CatalogError, prepare_runtime
        try:
            prepare_runtime(self.runtime, config)
        except CatalogError as e:
            logger.error("{}", e)
            return False

        # 3. Package Python application code into assets
        assets_app_dir = self.dart_runtime / "assets" / "app"
        assets_app_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"📁 Bundling Python app assets into {assets_app_dir}...")
        
        # Copy entrypoint
        shutil.copy2(self.entrypoint, assets_app_dir / "main.py")

        # Copy any local python source files or config
        source_dir = self.entrypoint.parent
        for py_file in source_dir.glob("*.py"):
            if py_file.name != self.entrypoint.name:
                shutil.copy2(py_file, assets_app_dir / py_file.name)

        # Copy afik.yaml if present
        if (source_dir / "afik.yaml").exists():
            shutil.copy2(source_dir / "afik.yaml", assets_app_dir / "afik.yaml")
        elif (Path.cwd() / "afik.yaml").exists():
            shutil.copy2(Path.cwd() / "afik.yaml", assets_app_dir / "afik.yaml")

        # Copy requirements.txt if present
        if (source_dir / "requirements.txt").exists():
            shutil.copy2(source_dir / "requirements.txt", assets_app_dir / "requirements.txt")

        # 4. Build native Rust FFI library if cargo is available
        logger.info("⚙️ Compiling native Rust FFI bridge library...")
        cargo_bin = shutil.which("cargo") or shutil.which("cargo.exe")
        if cargo_bin:
            build_cmd = [cargo_bin, "build"]
            if self.release:
                build_cmd.append("--release")
            try:
                subprocess.run(build_cmd, cwd=str(self.rust_bridge), check=True)
                logger.success("Native Rust FFI bridge compiled successfully.")
            except Exception as e:
                logger.error(f"Could not compile the Rust bridge with cargo: {e}")
                return False
        else:
            logger.error("cargo not found in PATH: the native Rust bridge cannot be built.")
            return False

        # 5. Build Flutter package with Standalone flag enabled
        logger.info(f"🔨 Building standalone Flutter {self.target.upper()} ({mode_str})...")
        flutter_cmd = [
            flutter_bin,
            "build",
            self.target,
            "--dart-define=AFIK_STANDALONE=true",
        ]
        if self.release:
            flutter_cmd.append("--release")
        elif self.profile:
            flutter_cmd.append("--profile")
        else:
            flutter_cmd.append("--debug")

        if self.split_per_abi and self.target == "apk":
            flutter_cmd.append("--split-per-abi")

        logger.info(f"   Executing: {' '.join(flutter_cmd)}")
        try:
            res = subprocess.run(
                flutter_cmd,
                cwd=str(self.dart_runtime),
                check=True,
            )
            if res.returncode == 0:
                logger.success(f"🎉 Afik Standalone {self.target.upper()} build completed successfully!")
                output_dirs = {
                    "apk": self.dart_runtime / "build" / "app" / "outputs" / "flutter-apk",
                    "appbundle": self.dart_runtime / "build" / "app" / "outputs" / "bundle",
                    "windows": self.dart_runtime / "build" / "windows",
                    "linux": self.dart_runtime / "build" / "linux",
                    "macos": self.dart_runtime / "build" / "macos",
                    "web": self.dart_runtime / "build" / "web",
                    "ipa": self.dart_runtime / "build" / "ios" / "ipa",
                }
                output_dir = output_dirs.get(self.target, self.dart_runtime / "build")
                logger.info(f"📦 Output artifacts located at:\n   {output_dir}")
                logger.warning(
                    "No Python interpreter is embedded in this build yet (see AFIK_VISION.md §3.6): "
                    "the packaged app can render but will not run your Python code on a device."
                )
                return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Flutter build failed with exit code {e.returncode}")
        except Exception as e:
            logger.error(f"Build execution error: {e}")

        return False
