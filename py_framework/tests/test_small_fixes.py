"""Small correctness fixes: CLI fall-through, project template, SnackBar duration, start-up errors."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

import yaml

import pyflutter as pf
from pyflutter.cli import creator, main as cli
from pyflutter.cli.runner import PyFlutterRunner
from pyflutter.core.bridge import BridgeSession
from pyflutter.plugins import overlay


class TestRunDoesNotFallThroughIntoBuild(unittest.TestCase):
    def test_run_command_never_instantiates_the_builder(self):
        entry = Path(tempfile.mkdtemp()) / "main.py"
        entry.write_text("x = 1\n")
        runner = MagicMock()
        with patch.object(cli, "PyFlutterRunner", return_value=runner), \
             patch("pyflutter.cli.builder.PyFlutterBuilder") as builder:
            cli.main(["run", str(entry)])
        runner.start.assert_called_once()
        builder.assert_not_called()


class TestProjectTemplate(unittest.TestCase):
    def test_description_with_quotes_and_colons_stays_valid_yaml(self):
        project = Path(tempfile.mkdtemp()) / "demo"
        creator.create_project(project, "demo", description='He said "hi": it\'s #1')
        data = yaml.safe_load((project / "pyflutter.yaml").read_text(encoding="utf-8"))
        self.assertEqual(data["description"], 'He said "hi": it\'s #1')
        self.assertEqual(data["plugins"], ["url_launcher"])

    def test_readme_lists_only_shortcuts_that_exist(self):
        project = Path(tempfile.mkdtemp()) / "demo"
        creator.create_project(project, "demo")
        text = (project / "README.md").read_text(encoding="utf-8")
        for key in ("`r`", "`R`", "`q`"):
            self.assertIn(key, text)
        self.assertNotIn("`d` :", text)
        handled = PyFlutterRunner._handle_key.__code__.co_consts
        self.assertNotIn("d", handled)


class TestSnackBarDuration(unittest.TestCase):
    def _ms(self, **kwargs):
        with patch.object(overlay, "invoke_plugin_method") as call:
            overlay.show_snack_bar("hi", **kwargs)
        return call.call_args.args[2]["duration_ms"]

    def test_defaults_to_four_seconds(self):
        self.assertEqual(self._ms(), 4000)

    def test_numbers_are_seconds(self):
        self.assertEqual(self._ms(duration=3), 3000)
        self.assertEqual(self._ms(duration=2.5), 2500)
        self.assertEqual(self._ms(duration=pf.Duration(seconds=6)), 6000)

    def test_milliseconds_have_their_own_parameter(self):
        self.assertEqual(self._ms(duration_ms=1500), 1500)

    def test_a_number_that_looks_like_milliseconds_is_rejected_not_guessed(self):
        with self.assertRaises(ValueError):
            self._ms(duration=3000)
        with self.assertRaises(ValueError):
            self._ms(duration=2, duration_ms=2000)

    def test_component_helper_forwards_both(self):
        class Screen(pf.Component):
            def build(self):
                return pf.Text("x")

        with patch.object(overlay, "invoke_plugin_method") as call:
            Screen().show_snack_bar("hi", duration_ms=900)
        self.assertEqual(call.call_args.args[2]["duration_ms"], 900)


class TestRunnerStartup(unittest.TestCase):
    def test_constructing_a_runner_does_not_need_the_bridge(self):
        with patch("pyflutter.cli.runner.find_bridge_binary", side_effect=FileNotFoundError("missing")), \
             patch("pyflutter.cli.runner.atexit.register"):
            PyFlutterRunner(entrypoint=Path(__file__))     # must not raise

    def test_missing_bridge_is_a_clear_message_and_exit_code_1(self):
        with patch("pyflutter.cli.runner.find_bridge_binary", side_effect=FileNotFoundError("bridge not built")), \
             patch("pyflutter.cli.runner.atexit.register"), \
             patch("pyflutter.cli.runner.logger") as log:
            runner = PyFlutterRunner(entrypoint=Path(__file__))
            with self.assertRaises(SystemExit) as raised:
                runner.start()
        self.assertEqual(raised.exception.code, 1)
        messages = " ".join(str(c.args) for c in log.error.call_args_list)
        self.assertIn("cargo build", messages)

    def test_debug_banner_lands_on_the_widget_that_is_sent_even_if_build_returns_a_component(self):
        class Inner(pf.Component):
            def build(self):
                return pf.Column([pf.Text("hi")])

        class App:
            debug_banner = True

            def build(self):
                return Inner()

        with patch("pyflutter.cli.runner.find_bridge_binary", return_value=Path("b")), \
             patch("pyflutter.cli.runner.atexit.register"):
            runner = PyFlutterRunner(entrypoint=Path(__file__))
        runner.app = App()
        tree = runner._build_and_tag_tree()
        self.assertEqual(tree.widget_type, "Column")
        self.assertEqual(tree.props["debug_banner"], "true")


class TestSendTreeAcceptsAResolvedTree(unittest.TestCase):
    def _session(self):
        session = BridgeSession.__new__(BridgeSession)
        session.process = MagicMock()
        session.process.poll.return_value = None
        session._last_snapshot = None
        return session

    def test_resolved_tree_is_not_built_twice(self):
        builds = []

        class Counter(pf.Component):
            def build(self):
                builds.append(1)
                return pf.Text("x")

        from pyflutter.core.render import resolve_tree
        session = self._session()
        tree = resolve_tree(pf.Column([Counter()]))
        self.assertEqual(len(builds), 1)
        session.send_tree(tree, resolved=True)
        self.assertEqual(len(builds), 1)                      # no second build
        session.process.stdin.write.assert_called()

    def test_unresolved_tree_still_works(self):
        session = self._session()
        session.send_tree(pf.Column([pf.Text("a")]))
        session.process.stdin.write.assert_called()


if __name__ == "__main__":
    unittest.main()
