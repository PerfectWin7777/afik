"""Plugin catalog: install, remove and sync Flutter plugins per project."""

from __future__ import annotations

import os
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from afik.cli import plugins_cmd
from afik.core.config import AfikConfig
from afik.plugins import catalog

REAL_RUNTIME = Path(__file__).resolve().parents[2] / "dart_runtime"
TRACKED = [
    "pubspec.yaml",
    "lib/plugins/installed_plugins.dart",
    "android/app/build.gradle.kts",
    "android/app/src/main/kotlin/com/example/afik_dart_runtime/MainActivity.kt",
    "android/app/src/main/res/values/styles.xml",
    "android/app/src/main/res/values-night/styles.xml",
]


def copy_runtime() -> Path:
    work = Path(tempfile.mkdtemp(prefix="pf_catalog_")) / "dart_runtime"
    shutil.copytree(
        REAL_RUNTIME, work,
        ignore=shutil.ignore_patterns("build", ".dart_tool", "installed", "*.iml", "ios", "macos", "linux", "windows", "web"),
    )
    return work


def snapshot(runtime: Path) -> dict[str, str]:
    return {rel: (runtime / rel).read_text(encoding="utf-8") for rel in TRACKED}


class TestCatalogEntries(unittest.TestCase):
    def test_every_entry_is_valid_and_has_its_shim(self):
        entries = catalog.load_catalog(REAL_RUNTIME)
        self.assertGreaterEqual(len(entries), 8)
        for name, entry in entries.items():
            self.assertTrue(entry.package, name)
            for rel in entry.files:
                shim = entry.directory / rel
                self.assertTrue(shim.exists(), f"{name}: missing {rel}")
            self.assertIn("void register()", (entry.directory / entry.files[0]).read_text(encoding="utf-8"), name)
            self.assertTrue(entry.registers, f"{name} registers nothing")

    def test_requirements_are_expanded_first_and_validated(self):
        cat = catalog.load_catalog(REAL_RUNTIME)
        cat["b"] = catalog.CatalogEntry("b", "b", "any", Path("."), requires=["a"])
        cat["a"] = catalog.CatalogEntry("a", "a", "any", Path("."))
        self.assertEqual([e.name for e in catalog.expand_requirements(["b"], cat)], ["a", "b"])
        with self.assertRaises(catalog.CatalogError):
            catalog.expand_requirements(["nope"], cat)
        cat["a"].requires = ["b"]
        with self.assertRaises(catalog.CatalogError):
            catalog.expand_requirements(["a"], cat)


class TestRendering(unittest.TestCase):
    def test_registrant_without_plugins_is_the_template(self):
        template = (REAL_RUNTIME / "lib/plugins/installed_plugins.dart").read_text(encoding="utf-8")
        self.assertEqual(catalog.render_registrant([]), template)

    def test_registrant_lists_imports_and_registrations(self):
        cat = catalog.load_catalog(REAL_RUNTIME)
        text = catalog.render_registrant([cat["local_auth"], cat["url_launcher"]])
        self.assertIn("import 'installed/local_auth/shim.dart' as plugin_local_auth;", text)
        self.assertIn("plugin_url_launcher.register();", text)

    def test_pubspec_block_is_replaced_and_removed(self):
        base = (REAL_RUNTIME / "pubspec.yaml").read_text(encoding="utf-8")
        with_one = catalog.render_pubspec(base, {"local_auth": "^2.3.0"})
        self.assertIn("  local_auth: ^2.3.0", with_one)
        with_two = catalog.render_pubspec(with_one, {"a_pkg": "^1.0.0", "local_auth": "^2.3.0"})
        self.assertEqual(with_two.count(catalog.PUBSPEC_BEGIN), 1)
        self.assertEqual(catalog.render_pubspec(with_two, {}).strip(), base.strip())
        # the managed block stays inside `dependencies:` (before dev_dependencies)
        self.assertLess(with_one.index("local_auth"), with_one.index("dev_dependencies:"))


class TestSync(unittest.TestCase):
    def setUp(self):
        self.runtime = copy_runtime()
        self.addCleanup(shutil.rmtree, self.runtime.parent, ignore_errors=True)
        self.original = snapshot(self.runtime)

    def sync(self, names):
        return catalog.sync_plugins(self.runtime, names, run_pub_get=False)

    def test_install_writes_everything_and_is_idempotent(self):
        first = self.sync(["local_auth", "flutter_secure_storage"])
        self.assertTrue(first.pubspec_changed)
        self.assertTrue((self.runtime / "lib/plugins/installed/local_auth/shim.dart").exists())
        registrant = (self.runtime / "lib/plugins/installed_plugins.dart").read_text(encoding="utf-8")
        self.assertIn("plugin_flutter_secure_storage.register();", registrant)
        second = self.sync(["local_auth", "flutter_secure_storage"])
        self.assertEqual(second.files_changed, [])

    def test_native_android_settings_follow_the_plugins(self):
        self.sync(["local_auth", "flutter_secure_storage"])
        state = snapshot(self.runtime)
        self.assertIn("FlutterFragmentActivity", state[TRACKED[3]])
        self.assertIn("Theme.AppCompat.DayNight.NoActionBar", state[TRACKED[4]])
        self.assertIn("Theme.AppCompat.DayNight.NoActionBar", state[TRACKED[5]])
        self.assertIn("minSdk = maxOf(flutter.minSdkVersion, 23)", state[TRACKED[2]])

    def test_removing_every_plugin_restores_the_original_files(self):
        self.sync(["local_auth", "flutter_secure_storage", "url_launcher"])
        self.sync([])
        self.assertEqual(snapshot(self.runtime), self.original)
        self.assertFalse((self.runtime / "lib/plugins/installed/local_auth").exists())

    def test_removing_one_plugin_keeps_the_others(self):
        self.sync(["local_auth", "url_launcher"])
        self.sync(["url_launcher"])
        self.assertFalse((self.runtime / "lib/plugins/installed/local_auth").exists())
        self.assertTrue((self.runtime / "lib/plugins/installed/url_launcher/shim.dart").exists())
        self.assertNotIn("FlutterFragmentActivity", snapshot(self.runtime)[TRACKED[3]])

    def test_desugaring_is_added_and_removed(self):
        fake = self.runtime / "plugin_catalog" / "needs_desugar"
        fake.mkdir()
        (fake / "plugin.yaml").write_text(
            "name: needs_desugar\npackage: needs_desugar\nconstraint: ^1.0.0\nandroid: {desugaring: true}\n")
        (fake / "shim.dart").write_text("void register() {}\n")
        self.sync(["needs_desugar"])
        gradle = (self.runtime / TRACKED[2]).read_text(encoding="utf-8")
        self.assertIn("isCoreLibraryDesugaringEnabled = true", gradle)
        self.assertIn("coreLibraryDesugaring", gradle)
        self.sync([])
        self.assertEqual((self.runtime / TRACKED[2]).read_text(encoding="utf-8"), self.original[TRACKED[2]])


class TestProjectCommands(unittest.TestCase):
    """`afik add / remove` work on the runtime copy of the project in the current directory."""

    def setUp(self):
        self.template = copy_runtime()          # stands for the framework's dart_runtime/
        shutil.copytree(REAL_RUNTIME / "plugin_catalog", self.template / "plugin_catalog", dirs_exist_ok=True)
        self.project = Path(tempfile.mkdtemp(prefix="pf_project_"))
        (self.project / "afik.yaml").write_text(
            "name: demo\n# keep me\ncustom_key: 42\npermissions:\n  - internet\n", encoding="utf-8")
        self.addCleanup(shutil.rmtree, self.template.parent, ignore_errors=True)
        self.addCleanup(shutil.rmtree, self.project, ignore_errors=True)
        self.cwd = os.getcwd()
        os.chdir(self.project)
        self.addCleanup(os.chdir, self.cwd)
        real_sync = catalog.sync_plugins

        def no_pub_get(rt, names, **kw):
            kw["run_pub_get"] = False
            return real_sync(rt, names, **kw)

        for patcher in (
            patch.object(plugins_cmd, "_template_dir", return_value=self.template),
            patch.object(catalog, "sync_plugins", side_effect=no_pub_get),
        ):
            patcher.start()
            self.addCleanup(patcher.stop)

    def test_add_then_remove_updates_afik_yaml_and_the_project_runtime(self):
        self.assertTrue(plugins_cmd.add("local_auth"))
        config = AfikConfig.find_and_load(self.project)
        self.assertEqual(config.plugins, ["local_auth"])
        self.assertEqual(config.raw_config.get("custom_key"), 42)
        text = (self.project / "afik.yaml").read_text(encoding="utf-8")
        self.assertIn("# keep me", text)                                  # comments survive
        runtime = self.project / ".afik" / "runtime"
        self.assertIn("USE_BIOMETRIC", (runtime / "android/app/src/main/AndroidManifest.xml").read_text(encoding="utf-8"))
        self.assertTrue((runtime / "lib/plugins/installed/local_auth/shim.dart").exists())
        self.assertTrue(plugins_cmd.remove("local_auth"))
        self.assertEqual(AfikConfig.find_and_load(self.project).plugins, [])
        self.assertFalse((runtime / "lib/plugins/installed/local_auth").exists())
        self.assertNotIn("USE_BIOMETRIC", (runtime / "android/app/src/main/AndroidManifest.xml").read_text(encoding="utf-8"))

    def test_the_framework_template_is_never_modified(self):
        before = snapshot(self.template)
        plugins_cmd.add("local_auth")
        plugins_cmd.add("flutter_secure_storage")
        plugins_cmd.remove("local_auth")
        self.assertEqual(snapshot(self.template), before)
        self.assertFalse((self.template / "lib/plugins/installed/local_auth").exists())

    def test_unknown_package_is_added_as_a_dependency_with_the_resolved_version(self):
        def fake_pub_get(cmd, cwd=None, **kw):
            Path(cwd, "pubspec.lock").write_text(
                "packages:\n  some_unmapped_package:\n    dependency: direct main\n    version: \"2.4.1\"\n", encoding="utf-8")
            return type("R", (), {"returncode": 0, "stdout": "", "stderr": ""})()

        # exercise the real code path: pubspec change -> flutter pub get (faked) -> lock read back
        with patch.object(catalog, "sync_plugins", side_effect=lambda rt, names, **kw: _sync_with_fake_pub_get(rt, names, fake_pub_get, **kw)):
            self.assertTrue(plugins_cmd.add("some_unmapped_package"))
        config = AfikConfig.find_and_load(self.project)
        self.assertEqual(config.flutter_dependencies["some_unmapped_package"], "^2.4.1")
        pubspec = (self.project / ".afik/runtime/pubspec.yaml").read_text(encoding="utf-8")
        self.assertIn("some_unmapped_package: ^2.4.1", pubspec)
        self.assertTrue(plugins_cmd.remove("some_unmapped_package"))
        self.assertNotIn("some_unmapped_package", (self.project / ".afik/runtime/pubspec.yaml").read_text(encoding="utf-8"))
        self.assertEqual(AfikConfig.find_and_load(self.project).flutter_dependencies, {})

    def test_scaffold_creates_the_mapping_skeleton(self):
        framework = Path(tempfile.mkdtemp(prefix="pf_fw_"))
        (framework / "afik" / "plugins").mkdir(parents=True)
        (framework / "tests").mkdir()
        self.addCleanup(shutil.rmtree, framework, ignore_errors=True)
        created = catalog.scaffold_plugin("my_package", self.template, framework)
        names = sorted(p.name for p in created)
        self.assertEqual(names, ["my_package.py", "plugin.yaml", "shim.dart", "test_plugin_my_package.py"])
        entry = catalog.load_entry(self.template / "plugin_catalog" / "my_package")
        self.assertEqual(entry.package, "my_package")
        with self.assertRaises(catalog.CatalogError):
            catalog.scaffold_plugin("my_package", self.template, framework)
        with self.assertRaises(catalog.CatalogError):
            catalog.scaffold_plugin("Bad-Name", self.template, framework)


def _sync_with_fake_pub_get(runtime, names, fake_pub_get, **kw):
    """Runs the real sync_plugins with `flutter pub get` replaced by ``fake_pub_get``."""
    real = _REAL_SYNC
    with patch.object(catalog.shutil, "which", return_value="flutter"), \
         patch.object(catalog.subprocess, "run", side_effect=fake_pub_get):
        kw["run_pub_get"] = True
        return real(runtime, names, **kw)


_REAL_SYNC = catalog.sync_plugins


if __name__ == "__main__":
    unittest.main()
