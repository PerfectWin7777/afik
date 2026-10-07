"""T-03: a State is disposed when its widget leaves the tree, but not while its page is covered."""

from __future__ import annotations

import unittest

import afik as pf
from afik.core import state as st
from afik.core.navigation import Navigator
from afik.core.render import resolve_tree


class Probe(pf.State):
    created = 0
    disposed = 0

    def init_state(self):
        Probe.created += 1

    def dispose(self):
        Probe.disposed += 1

    def build(self):
        return pf.Text("probe")


class ProbeWidget(pf.StatefulComponent):
    def create_state(self):
        return Probe()


def frame(root):
    return resolve_tree(root)


class TestStateDisposal(unittest.TestCase):
    def setUp(self):
        st.clear_state_registry()
        Navigator.reset()
        Probe.created = Probe.disposed = 0

    def tearDown(self):
        st.clear_state_registry()
        Navigator.reset()

    def test_dispose_is_called_once_when_the_widget_leaves_the_tree(self):
        frame(pf.Column([ProbeWidget(key="a")]))
        self.assertEqual((Probe.created, Probe.disposed), (1, 0))
        frame(pf.Column([pf.Text("gone")]))
        self.assertEqual(Probe.disposed, 1)
        self.assertEqual(len(st._state_registry), 0)
        frame(pf.Column([pf.Text("still gone")]))
        self.assertEqual(Probe.disposed, 1)

    def test_a_state_that_stays_is_never_disposed(self):
        for _ in range(5):
            frame(pf.Column([ProbeWidget(key="a")]))
        self.assertEqual((Probe.created, Probe.disposed), (1, 0))

    def test_removing_one_of_two_disposes_only_that_one(self):
        frame(pf.Column([ProbeWidget(key="a"), ProbeWidget(key="b")]))
        frame(pf.Column([ProbeWidget(key="b")]))
        self.assertEqual(Probe.disposed, 1)
        self.assertEqual(len(st._state_registry), 1)

    def test_a_state_comes_back_fresh_after_disposal(self):
        frame(pf.Column([ProbeWidget(key="a")]))
        frame(pf.Column([]))
        frame(pf.Column([ProbeWidget(key="a")]))
        self.assertEqual((Probe.created, Probe.disposed), (2, 1))

    def test_a_failing_build_disposes_nothing(self):
        class Broken(pf.Component):
            def build(self):
                raise RuntimeError("boom")

        frame(pf.Column([ProbeWidget(key="a")]))
        with self.assertRaises(RuntimeError):
            frame(pf.Column([Broken()]))
        self.assertEqual(Probe.disposed, 0)

    def test_an_error_in_dispose_is_logged_not_raised(self):
        class Bad(pf.State):
            def dispose(self):
                raise ValueError("cleanup failed")

            def build(self):
                return pf.Text("x")

        class BadWidget(pf.StatefulComponent):
            def create_state(self):
                return Bad()

        frame(pf.Column([BadWidget(key="b")]))
        frame(pf.Column([]))          # must not raise
        self.assertEqual(len(st._state_registry), 0)

    def test_clear_state_registry_disposes_everything_left_once(self):
        frame(pf.Column([ProbeWidget(key="a"), ProbeWidget(key="b")]))
        st.clear_state_registry()
        self.assertEqual(Probe.disposed, 2)
        st.clear_state_registry()
        self.assertEqual(Probe.disposed, 2)

    def test_a_state_subclass_without_super_init_works(self):
        class NoSuper(pf.State):
            def __init__(self):          # does not call super().__init__()
                self.x = 1

            def build(self):
                return pf.Text("x")

        class NoSuperWidget(pf.StatefulComponent):
            def create_state(self):
                return NoSuper()

        frame(pf.Column([NoSuperWidget(key="n")]))
        frame(pf.Column([]))
        self.assertEqual(len(st._state_registry), 0)


class TestStatesAndNavigation(unittest.TestCase):
    def setUp(self):
        st.clear_state_registry()
        Navigator.reset()
        Probe.created = Probe.disposed = 0

    def tearDown(self):
        st.clear_state_registry()
        Navigator.reset()

    def app(self, home):
        return pf.MaterialApp(home=home)

    def test_a_covered_page_keeps_its_state_until_it_is_popped(self):
        home = pf.Column([ProbeWidget(key="home")])
        frame(self.app(home))
        page_b = pf.Column([pf.Text("B")])
        Navigator.push(page_b)
        for _ in range(3):
            frame(self.app(pf.Column([ProbeWidget(key="home")])))     # home is covered, not rebuilt
        self.assertEqual((Probe.created, Probe.disposed), (1, 0))
        state_before = next(iter(st._state_registry.values()))

        Navigator.pop()
        frame(self.app(pf.Column([ProbeWidget(key="home")])))
        self.assertEqual((Probe.created, Probe.disposed), (1, 0))
        self.assertIs(next(iter(st._state_registry.values())), state_before)

    def test_a_popped_page_disposes_its_states(self):
        frame(self.app(pf.Column([pf.Text("home")])))
        page_b = pf.Column([ProbeWidget(key="b")])
        Navigator.push(page_b)
        frame(self.app(pf.Column([pf.Text("home")])))
        self.assertEqual((Probe.created, Probe.disposed), (1, 0))
        Navigator.pop()
        frame(self.app(pf.Column([pf.Text("home")])))
        self.assertEqual(Probe.disposed, 1)

    def test_a_page_under_two_covers_keeps_its_state(self):
        frame(self.app(pf.Column([pf.Text("home")])))
        page_b = pf.Column([ProbeWidget(key="b")])
        Navigator.push(page_b)
        frame(self.app(pf.Column([pf.Text("home")])))
        Navigator.push(pf.Column([pf.Text("C")]))
        frame(self.app(pf.Column([pf.Text("home")])))
        self.assertEqual(Probe.disposed, 0)
        Navigator.pop()
        frame(self.app(pf.Column([pf.Text("home")])))
        self.assertEqual(Probe.disposed, 0)


if __name__ == "__main__":
    unittest.main()
