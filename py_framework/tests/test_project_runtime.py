"""Per-project runtime copy, managed manifest blocks and comment-preserving config edits."""

from __future__ import annotations

import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from pyflutter.cli import manifest_sync
from pyflutter.core.config import PyFlutterConfig, replace_flutter_dependencies_block, replace_plugins_block
from pyflutter.core.runtime_project import ProjectRuntime
from pyflutter.plugins import catalog

REAL_RUNTIME = Path(__file__).resolve().parents[2] / "dart_runtime"
MANIFEST = "android/app/src/main/AndroidManifest.xml"
PLIST = "ios/Runner/Info.plist"


def make_template() -> Path:
    base = Path(tempfile.mkdtemp(prefix="pf_tpl_"))
    template = base / "dart_runtime"
    shutil.copytree(
        REAL_RUNTIME, template,
        ignore=shutil.ignore_patterns("build", ".dart_tool", "installed", "*.iml"),
    )
    return template


class TestTemplateStaysNeutral(unittest.TestCase):
    """The framework template must carry no project-specific native settings."""

    def test_manifest_has_no_permissions_or_app_queries(self):
        text = (REAL_RUNTIME / MANIFEST).read_text(encoding="utf-8")
        self.assertNotIn("uses-permission", text)
        for intent in ("scheme=\"https\"", "scheme=\"tel\"", "scheme=\"mailto\"", "RecognitionService"):
            self.assertNotIn(intent, text)
        self.assertNotIn("Pyshop", text)

    def test_plist_has_no_usage_descriptions(self):
        text = (REAL_RUNTIME / PLIST).read_text(encoding="utf-8")
        self.assertNotRegex(text, r"<key>NS[A-Za-z]*UsageDescription</key>")
        self.assertNotIn("Pyshop", text)


class TestProjectRuntimeCopy(unittest.TestCase):
    def setUp(self):
        self.template = make_template()
        self.project = Path(tempfile.mkdtemp(prefix="pf_proj_"))
        self.addCleanup(shutil.rmtree, self.template.parent, ignore_errors=True)
        self.addCleanup(shutil.rmtree, self.project, ignore_errors=True)
        self.runtime = ProjectRuntime(self.project, self.template)

    def test_nothing_is_created_until_ensure(self):
        self.assertFalse(self.runtime.exists)
        self.assertFalse((self.project / ".pyflutter").exists())

    def test_copy_has_the_runtime_but_not_the_catalog_or_build_output(self):
        self.assertTrue(self.runtime.ensure())
        rt = self.runtime.runtime_dir
        self.assertTrue((rt / "lib/main.dart").exists())
        self.assertTrue((rt / "pubspec.yaml").exists())
        self.assertFalse((rt / "plugin_catalog").exists())
        self.assertFalse((rt / "build").exists())

    def test_unchanged_template_is_a_no_op(self):
        self.runtime.ensure()
        marker = self.runtime.runtime_dir / "lib" / "my_edit.txt"
        marker.write_text("kept")
        self.assertFalse(self.runtime.ensure())
        self.assertTrue(marker.exists())

    def test_template_change_refreshes_the_copy_and_keeps_project_files(self):
        self.runtime.ensure()
        rt = self.runtime.runtime_dir
        (rt / "pubspec.lock").write_text("project lock")
        (rt / "build").mkdir()
        (rt / "build" / "out.txt").write_text("artifact")
        (self.template / "lib" / "main.dart").write_text("// new framework version\n")
        self.assertTrue(self.runtime.ensure())
        self.assertEqual((rt / "lib/main.dart").read_text(), "// new framework version\n")
        self.assertEqual((rt / "pubspec.lock").read_text(), "project lock")      # resolved versions belong to the project
        self.assertTrue((rt / "build" / "out.txt").exists())                      # build output kept

    def test_file_removed_from_the_template_is_removed_from_the_copy(self):
        (self.template / "lib" / "old.dart").write_text("// old\n")
        self.runtime.ensure()
        self.assertTrue((self.runtime.runtime_dir / "lib/old.dart").exists())
        (self.template / "lib" / "old.dart").unlink()
        self.runtime.ensure()
        self.assertFalse((self.runtime.runtime_dir / "lib/old.dart").exists())

    def test_two_projects_are_independent(self):
        other_project = Path(tempfile.mkdtemp(prefix="pf_proj2_"))
        self.addCleanup(shutil.rmtree, other_project, ignore_errors=True)
        other = ProjectRuntime(other_project, self.template)
        for runtime, plugins in ((self.runtime, ["local_auth"]), (other, ["url_launcher"])):
            runtime.ensure()
            catalog.sync_plugins(runtime.runtime_dir, plugins, run_pub_get=False, template_dir=self.template)
        self.assertTrue((self.runtime.runtime_dir / "lib/plugins/installed/local_auth").exists())
        self.assertFalse((self.runtime.runtime_dir / "lib/plugins/installed/url_launcher").exists())
        self.assertTrue((other.runtime_dir / "lib/plugins/installed/url_launcher").exists())
        self.assertFalse((other.runtime_dir / "lib/plugins/installed/local_auth").exists())

    def test_project_dir_comes_from_the_config_file(self):
        (self.project / "pyflutter.yaml").write_text("name: x\n")
        config = PyFlutterConfig.find_and_load(self.project)
        runtime = ProjectRuntime.for_config(config, self.template, fallback_dir=Path("/elsewhere"))
        self.assertEqual(runtime.project_dir, self.project.resolve())

    def test_prepare_runtime_end_to_end(self):
        (self.project / "pyflutter.yaml").write_text(
            "name: demo_app\npermissions:\n  - camera\nplugins:\n  - local_auth\n  - url_launcher\n", encoding="utf-8")
        config = PyFlutterConfig.find_and_load(self.project)
        runtime = ProjectRuntime.for_config(config, self.template)
        result = catalog.prepare_runtime(runtime, config, run_pub_get=False)
        self.assertEqual(result.plugins, ["local_auth", "url_launcher"])
        manifest = (runtime.runtime_dir / MANIFEST).read_text(encoding="utf-8")
        for expected in ("android.permission.CAMERA", "android.permission.USE_BIOMETRIC",
                         "android.permission.INTERNET", 'android:scheme="https"', 'android:label="Demo App"'):
            self.assertIn(expected, manifest)
        pubspec = (runtime.runtime_dir / "pubspec.yaml").read_text(encoding="utf-8")
        self.assertIn("local_auth: ^2.3.0", pubspec)
        # a second run changes nothing
        self.assertEqual(catalog.prepare_runtime(runtime, config, run_pub_get=False).files_changed, [])


class TestManagedNativeBlocks(unittest.TestCase):
    def setUp(self):
        self.dir = Path(tempfile.mkdtemp(prefix="pf_native_"))
        self.addCleanup(shutil.rmtree, self.dir, ignore_errors=True)
        self.manifest = self.dir / "AndroidManifest.xml"
        shutil.copy(REAL_RUNTIME / MANIFEST, self.manifest)
        self.plist = self.dir / "Info.plist"
        shutil.copy(REAL_RUNTIME / PLIST, self.plist)
        self.original_manifest = self.manifest.read_text(encoding="utf-8")
        self.original_plist = self.plist.read_text(encoding="utf-8")

    def test_permissions_are_added_removed_and_idempotent(self):
        self.assertTrue(manifest_sync.sync_android_manifest(self.manifest, ["camera", "internet"], "Demo"))
        text = self.manifest.read_text(encoding="utf-8")
        self.assertIn("android.permission.CAMERA", text)
        self.assertFalse(manifest_sync.sync_android_manifest(self.manifest, ["camera", "internet"], "Demo"))
        manifest_sync.sync_android_manifest(self.manifest, ["internet"], "Demo")
        text = self.manifest.read_text(encoding="utf-8")
        self.assertNotIn("android.permission.CAMERA", text)
        self.assertIn("android.permission.INTERNET", text)
        manifest_sync.sync_android_manifest(self.manifest, [], None)
        self.assertNotIn("uses-permission", self.manifest.read_text(encoding="utf-8"))

    def test_removing_everything_restores_the_manifest_apart_from_the_label(self):
        manifest_sync.sync_android_manifest(self.manifest, ["camera"], None,
                                            ['<intent><action android:name="x.Y"/></intent>'])
        manifest_sync.sync_android_manifest(self.manifest, [], None)
        self.assertEqual(self.manifest.read_text(encoding="utf-8"), self.original_manifest)

    def test_permission_declared_outside_the_block_is_not_duplicated(self):
        text = self.original_manifest.replace(
            "<application", '<uses-permission android:name="android.permission.CAMERA"/>\n    <application', 1)
        self.manifest.write_text(text, encoding="utf-8")
        manifest_sync.sync_android_manifest(self.manifest, ["camera"], None)
        self.assertEqual(self.manifest.read_text(encoding="utf-8").count("android.permission.CAMERA"), 1)

    def test_label_with_special_characters_is_escaped(self):
        manifest_sync.sync_android_manifest(self.manifest, [], 'Tom & "Jerry"')
        import xml.dom.minidom
        xml.dom.minidom.parseString(self.manifest.read_text(encoding="utf-8"))

    def test_plist_block_follows_the_permissions(self):
        manifest_sync.sync_ios_plist(self.plist, ["camera", "face_id"], "Demo")
        text = self.plist.read_text(encoding="utf-8")
        self.assertIn("NSCameraUsageDescription", text)
        self.assertIn("NSFaceIDUsageDescription", text)
        manifest_sync.sync_ios_plist(self.plist, ["camera"], "Demo")
        self.assertNotIn("NSFaceIDUsageDescription", self.plist.read_text(encoding="utf-8"))
        import plistlib
        plistlib.loads(self.plist.read_bytes())                                 # still a valid plist
        manifest_sync.sync_ios_plist(self.plist, [], "pyflutter_dart_runtime")
        self.assertEqual(self.plist.read_text(encoding="utf-8"), self.original_plist)

    def test_unknown_permission_is_reported_not_written(self):
        with patch.object(manifest_sync.logger, "warning") as warn:
            manifest_sync.sync_android_manifest(self.manifest, ["camara"], None)
        warn.assert_called()
        self.assertNotIn("uses-permission", self.manifest.read_text(encoding="utf-8"))


class TestPluginsBlockEdit(unittest.TestCase):
    TEXT = "# my project\nname: demo  # inline\n\npermissions:\n  - internet\n\n# plugins I use\nplugins:\n  - a\n  - b\n\nother: 1\n"

    def test_replaces_the_block_in_place_and_keeps_comments(self):
        out = replace_plugins_block(self.TEXT, ["a", "c"])
        self.assertIn("# my project", out)
        self.assertIn("name: demo  # inline", out)
        self.assertIn("# plugins I use\nplugins:\n  - a\n  - c\n\nother: 1", out)
        self.assertNotIn("  - b", out)

    def test_adds_the_block_when_missing(self):
        out = replace_plugins_block("name: demo\n", ["a"])
        self.assertEqual(out, "name: demo\n\nplugins:\n  - a\n")

    def test_removes_the_block_when_empty(self):
        out = replace_plugins_block(self.TEXT, [])
        self.assertNotIn("plugins:", out)
        self.assertIn("other: 1", out)
        self.assertEqual(replace_plugins_block("name: demo\n", []), "name: demo\n")

    def test_flow_style_entry_is_replaced(self):
        out = replace_plugins_block("plugins: [a, b]\nname: x\n", ["a"])
        self.assertEqual(out, "plugins:\n  - a\nname: x\n")


if __name__ == "__main__":
    unittest.main()


class TestFlutterDependenciesBlockEdit(unittest.TestCase):
    edit = staticmethod(replace_flutter_dependencies_block)

    TEXT = "# my app\nname: demo\n\ndependencies:\n  # packages\n  flutter:\n    intl: ^0.20.0\n    other: any\n\npermissions:\n  - internet\n"

    def test_replaces_only_the_flutter_entries(self):
        out = self.edit(self.TEXT, {"intl": "^0.20.3"})
        self.assertIn("# my app", out)
        self.assertIn("  # packages\n  flutter:\n    intl: ^0.20.3\n\npermissions:", out)
        self.assertNotIn("other: any", out)

    def test_creates_the_block(self):
        self.assertEqual(self.edit("name: x\n", {"a": "any"}), "name: x\n\ndependencies:\n  flutter:\n    a: any\n")

    def test_removing_the_last_package_drops_the_empty_section(self):
        out = self.edit("name: x\ndependencies:\n  flutter:\n    a: any\nplugins:\n  - p\n", {})
        self.assertEqual(out, "name: x\nplugins:\n  - p\n")

    def test_keeps_other_dependency_sections(self):
        out = self.edit("dependencies:\n  python:\n    - requests\n  flutter:\n    a: any\n", {})
        self.assertIn("python:", out)
        self.assertNotIn("flutter:", out)

    def test_ranges_are_quoted(self):
        out = self.edit("name: x\n", {"a": ">=1.0.0 <2.0.0"})
        self.assertIn("a: '>=1.0.0 <2.0.0'", out)
        import yaml
        self.assertEqual(yaml.safe_load(out)["dependencies"]["flutter"]["a"], ">=1.0.0 <2.0.0")

    def test_config_keeps_comments_when_a_package_is_added(self):
        d = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, d, ignore_errors=True)
        (d / "pyflutter.yaml").write_text("# top\nname: x\npermissions:\n  - internet\n", encoding="utf-8")
        config = PyFlutterConfig.find_and_load(d)
        config.add_flutter_dependency("intl", "^0.20.3")
        text = (d / "pyflutter.yaml").read_text(encoding="utf-8")
        self.assertIn("# top", text)
        self.assertNotIn("description:", text)          # no defaults injected into an existing file
        config.remove_flutter_dependency("intl")
        self.assertEqual((d / "pyflutter.yaml").read_text(encoding="utf-8"), "# top\nname: x\npermissions:\n  - internet\n")
