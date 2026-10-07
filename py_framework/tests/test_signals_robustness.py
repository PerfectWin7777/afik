"""Signals: safe equality, in-place mutation, and thread-safe batching."""

from __future__ import annotations

import threading
import unittest
from unittest.mock import patch

import afik as pf
from afik.core import state


class Exploding:
    """An object whose == raises, like some array libraries do on ambiguous comparisons."""

    def __eq__(self, other):
        raise ValueError("The truth value of an array is ambiguous")

    __hash__ = None  # type: ignore[assignment]


class ArrayLike:
    """Comparison returns something with .all(), like numpy."""

    def __init__(self, *items):
        self.items = items

    def __eq__(self, other):
        class _Result:
            def __init__(self, values):
                self.values = values

            def all(self):
                return all(self.values)

            def __bool__(self):
                raise ValueError("ambiguous")

        return _Result([a == b for a, b in zip(self.items, other.items)])

    __hash__ = None  # type: ignore[assignment]


class TestEquality(unittest.TestCase):
    def test_a_value_whose_comparison_raises_does_not_break_the_setter(self):
        sig = pf.Signal(Exploding(), auto_update=False)
        calls = []
        sig.add_listener(lambda: calls.append(1))
        sig.value = Exploding()           # cannot be compared: treated as a change
        self.assertEqual(calls, [1])

    def test_array_like_values_are_compared_with_all(self):
        sig = pf.Signal(ArrayLike(1, 2), auto_update=False)
        calls = []
        sig.add_listener(lambda: calls.append(1))
        sig.value = ArrayLike(1, 2)
        self.assertEqual(calls, [])       # equal arrays: no notification
        sig.value = ArrayLike(1, 3)
        self.assertEqual(calls, [1])

    def test_same_object_is_never_a_change(self):
        marker = Exploding()
        sig = pf.Signal(marker, auto_update=False)
        calls = []
        sig.add_listener(lambda: calls.append(1))
        sig.value = marker
        self.assertEqual(calls, [])

    def test_custom_equality(self):
        sig = pf.Signal(1.0, auto_update=False, equals=lambda a, b: abs(a - b) < 0.01)
        calls = []
        sig.add_listener(lambda: calls.append(1))
        sig.value = 1.001
        self.assertEqual(calls, [])
        sig.value = 2.0
        self.assertEqual(calls, [1])


class TestMutation(unittest.TestCase):
    def test_mutate_changes_in_place_and_notifies(self):
        todos = pf.Signal([], auto_update=False)
        calls = []
        todos.add_listener(lambda: calls.append(list(todos.value)))
        todos.mutate(lambda items: items.append("milk"))
        todos.mutate(lambda items: items.append("eggs"))
        self.assertEqual(calls, [["milk"], ["milk", "eggs"]])

    def test_update_that_returns_none_on_a_container_is_an_error(self):
        todos = pf.Signal([], auto_update=False)
        with self.assertRaises(TypeError):
            todos.update(lambda items: items.append("x"))
        self.assertEqual(todos.value, ["x"])      # the in-place change happened, the signal did not become None
        self.assertIsNotNone(todos.value)

    def test_update_with_a_new_value_still_works(self):
        count = pf.Signal(1, auto_update=False)
        count.update(lambda c: c + 1)
        todos = pf.Signal([1], auto_update=False)
        todos.update(lambda items: items + [2])
        self.assertEqual((count.value, todos.value), (2, [1, 2]))

    def test_update_returning_none_is_allowed_for_scalars(self):
        maybe = pf.Signal(5, auto_update=False)
        maybe.update(lambda _: None)
        self.assertIsNone(maybe.value)


class TestBatch(unittest.TestCase):
    def setUp(self):
        patcher = patch("afik.app.update")
        self.update = patcher.start()
        self.addCleanup(patcher.stop)

    def test_one_frame_and_one_notification_for_many_writes(self):
        a, b = pf.Signal(1), pf.Signal(2)
        total = pf.Computed(lambda: a.value + b.value)
        seen = []
        total.add_listener(lambda: seen.append(total.value))
        self.update.reset_mock()
        with pf.batch():
            a.value = 10
            b.value = 20
            a.value = 11
        self.assertEqual(seen, [31])
        self.assertEqual(self.update.call_count, 1)

    def test_a_batch_that_raises_still_notifies_and_propagates(self):
        sig = pf.Signal(0)
        seen = []
        sig.add_listener(lambda: seen.append(sig.value))
        self.update.reset_mock()
        with self.assertRaises(RuntimeError):
            with pf.batch():
                sig.value = 5
                raise RuntimeError("boom")
        self.assertEqual(seen, [5])
        self.assertEqual(self.update.call_count, 1)
        self.assertEqual(state._batch_depth, 0)

    def test_nested_batches_flush_once_at_the_outermost_exit(self):
        sig = pf.Signal(0)
        seen = []
        sig.add_listener(lambda: seen.append(sig.value))
        with pf.batch():
            with pf.batch():
                sig.value = 1
            self.assertEqual(seen, [])
            sig.value = 2
        self.assertEqual(seen, [2])

    def test_no_frame_when_nothing_changed(self):
        sig = pf.Signal(1)
        self.update.reset_mock()
        with pf.batch():
            sig.value = 1
        self.assertEqual(self.update.call_count, 0)

    def test_batch_as_a_function_returns_the_result(self):
        sig = pf.Signal(0)
        self.assertEqual(pf.batch(lambda: (sig.set(3), "done")[1]), "done")
        self.assertEqual(sig.value, 3)

    def test_concurrent_batches_leave_the_depth_at_zero(self):
        sig = pf.Signal(0, auto_update=False)
        errors = []

        def worker():
            try:
                for i in range(200):
                    with pf.batch():
                        sig.value = i
            except Exception as e:      # pragma: no cover - would be the bug
                errors.append(e)

        threads = [threading.Thread(target=worker) for _ in range(8)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        self.assertEqual(errors, [])
        self.assertEqual(state._batch_depth, 0)
        self.assertFalse(state._batched_listeners)


if __name__ == "__main__":
    unittest.main()
