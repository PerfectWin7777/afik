"""Interpreter compatibility probe for the PyFlutter runtime.

Run it with every candidate interpreter (CPython build, RustPython, MicroPython...):

    <interpreter> audit/embedding/compat_probe.py

Each check exercises a language/stdlib feature the framework relies on (see
`stdlib_closure.py` for the module list). The script prints PASS/FAIL per check and
exits with the number of failures, so it can be used in CI for each candidate.
Keep this file free of third-party imports.
"""
import sys

results = []


def check(name):
    def deco(fn):
        try:
            fn()
            results.append((name, True, ""))
        except BaseException as e:  # noqa: BLE001 - a probe must survive anything
            results.append((name, False, f"{type(e).__name__}: {e}"))
        return fn
    return deco


@check("from __future__ import annotations + typing.Optional/Union/Generic")
def _():
    import typing
    T = typing.TypeVar("T")

    class Box(typing.Generic[T]):
        def __init__(self, v: "typing.Optional[T]"):
            self.v = v
    assert Box(3).v == 3


@check("inspect.signature on function, lambda, bound method, builtin")
def _():
    import inspect

    class A:
        def m(self, x, *, y=1): ...
    assert list(inspect.signature(A().m).parameters) == ["x", "y"]
    assert list(inspect.signature(lambda a, b=2, **kw: 0).parameters) == ["a", "b", "kw"]
    inspect.signature(len)


@check("contextvars.ContextVar get/set")
def _():
    import contextvars
    v = contextvars.ContextVar("v", default=None)
    v.set(5)
    assert v.get() == 5


@check("weakref.ref / WeakMethod / WeakSet")
def _():
    import weakref

    class O:
        def f(self): return 1
    o = O()
    assert weakref.WeakMethod(o.f)() is not None
    s = weakref.WeakSet([o])
    assert len(s) == 1
    del o
    import gc
    gc.collect()


@check("dataclasses (field, default_factory, frozen)")
def _():
    import dataclasses

    @dataclasses.dataclass
    class P:
        a: int = 0
        b: list = dataclasses.field(default_factory=list)
    assert P().b == [] and dataclasses.asdict(P(1))["a"] == 1


@check("threading: Thread, Event, RLock, Lock timeout")
def _():
    import threading
    ev, out = threading.Event(), []
    lock = threading.RLock()

    def work():
        with lock, lock:
            out.append(1)
        ev.set()
    t = threading.Thread(target=work, daemon=True)
    t.start()
    assert ev.wait(2) and out == [1]


@check("queue.Queue between threads")
def _():
    import queue
    import threading
    q = queue.Queue()
    threading.Thread(target=lambda: q.put(7), daemon=True).start()
    assert q.get(timeout=2) == 7


@check("struct / json / uuid / itertools / collections.OrderedDict")
def _():
    import collections
    import itertools
    import json
    import struct
    import uuid
    assert struct.unpack(">BI", struct.pack(">BI", 3, 9)) == (3, 9)
    assert json.loads(json.dumps({"a": [1, 2, "é"]}))["a"][2] == "é"
    assert len(uuid.uuid4().hex) == 32
    assert next(itertools.count(5)) == 5
    od = collections.OrderedDict(a=1)
    od.popitem(last=False)


@check("enum.Enum with str mixin")
def _():
    import enum

    class E(str, enum.Enum):
        A = "a"
    assert E("a") is E.A and E.A.value == "a"


@check("re (named groups, sub with function)")
def _():
    import re
    assert re.sub(r"(?P<x>\d)", lambda m: m.group("x") * 2, "a1") == "a11"


@check("copy.copy of an object with __dict__ and properties")
def _():
    import copy

    class W:
        def __init__(self): self.props = {"a": "1"}; self.children = []
        @property
        def n(self): return len(self.children)
    c = copy.copy(W())
    c.props = dict(c.props)
    assert c.n == 0


@check("sys._getframe and frame.f_globals['__name__']")
def _():
    f = sys._getframe(0)
    assert f.f_globals["__name__"] and f.f_lineno > 0


@check("importlib.util.spec_from_file_location + exec_module (hot reload)")
def _():
    import importlib.util
    import os
    import tempfile
    d = tempfile.mkdtemp()
    p = os.path.join(d, "m_probe.py")
    with open(p, "w") as fh:
        fh.write("X = 41 + 1\n")
    spec = importlib.util.spec_from_file_location("m_probe", p)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    assert mod.X == 42


@check("sqlite3 in-memory (INSERT / SELECT with row_factory)")
def _():
    import sqlite3
    c = sqlite3.connect(":memory:")
    c.row_factory = sqlite3.Row
    c.execute("CREATE TABLE t (id INTEGER PRIMARY KEY, n TEXT)")
    c.execute("INSERT INTO t (n) VALUES (?)", ("a",))
    assert dict(c.execute("SELECT * FROM t").fetchone())["n"] == "a"


@check("pathlib + tempfile + os")
def _():
    import pathlib
    import tempfile
    p = pathlib.Path(tempfile.mkdtemp()) / "x.txt"
    p.write_text("é", encoding="utf-8")
    assert p.read_text(encoding="utf-8") == "é"


@check("logging basic")
def _():
    import logging
    logging.getLogger("probe").warning("probe")


@check("exceptions: traceback formatting + chained exceptions")
def _():
    import traceback
    try:
        try:
            raise KeyError("{id}")
        except KeyError as e:
            raise RuntimeError("wrapped") from e
    except RuntimeError:
        assert "KeyError" in traceback.format_exc()


@check("f-strings with nested format specs / walrus / match statement")
def _():
    v = 3.14159
    assert f"{v:{'.2f'}}" == "3.14"
    if (n := 5) > 3:
        assert n == 5
    exec("match 3:\n    case 3:\n        r = 1\n", {})


@check("big recursion limit (tree depth 400)")
def _():
    def depth(n): return 0 if n == 0 else 1 + depth(n - 1)
    assert depth(400) == 400


@check("time.sleep / perf_counter / monotonic")
def _():
    import time
    t = time.perf_counter()
    time.sleep(0.01)
    assert time.monotonic() > 0 and time.perf_counter() > t


def main():
    width = max(len(n) for n, _, _ in results)
    failures = 0
    for name, ok, msg in results:
        print(f"{'PASS' if ok else 'FAIL'}  {name:<{width}}  {msg}")
        failures += (not ok)
    impl = getattr(sys, "implementation", None)
    print(f"\n{len(results) - failures}/{len(results)} checks passed on {getattr(impl, 'name', '?')} {sys.version.split()[0]}")
    sys.exit(failures)


main()
