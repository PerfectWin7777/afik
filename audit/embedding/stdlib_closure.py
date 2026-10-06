"""Measures which standard-library modules the framework really loads, and their size.

Usage (from the repository root):
    python audit/embedding/stdlib_closure.py            # imports pyflutter as it is today
    python audit/embedding/stdlib_closure.py --no-loguru  # simulates a logger-free runtime

Output: the list of stdlib modules loaded (beyond interpreter start-up), the size of their
.py sources and of the compiled -OO bytecode zipped with deflate. This is the number to
compare with the size budget in AUDIT_BUGS.md (part C).
"""
import importlib.util
import io
import marshal
import pathlib
import subprocess
import sys
import sysconfig
import zipfile

ROOT = pathlib.Path(__file__).resolve().parents[2]
CHILD = r"""
import sys, json
sys.path.insert(0, %(root)r)
if %(no_loguru)r:
    import types
    fake = types.ModuleType("loguru"); fake.logger = type("L", (), {"__getattr__": lambda s, n: (lambda *a, **k: None)})()
    sys.modules["loguru"] = fake
before = set(sys.modules)
import pyflutter
import pyflutter.core.render, pyflutter.core.state, pyflutter.core.widget_base, pyflutter.plugins.manager
after = set(sys.modules)
print(json.dumps(sorted(after - before)))
"""


def main() -> None:
    no_loguru = "--no-loguru" in sys.argv
    code = CHILD % {"root": str(ROOT / "py_framework"), "no_loguru": no_loguru}
    out = subprocess.run([sys.executable, "-I", "-c", code], capture_output=True, text=True, check=True).stdout
    import json
    loaded = json.loads(out.strip().splitlines()[-1])
    stdlib = set(sys.stdlib_module_names)
    stdlib_dir = pathlib.Path(sysconfig.get_paths()["stdlib"])
    rows, py_total = [], 0
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
        for name in loaded:
            top = name.split(".")[0]
            if top not in stdlib:
                continue
            spec = importlib.util.find_spec(name)
            origin = getattr(spec, "origin", None)
            if not origin or not origin.endswith(".py"):
                rows.append((name, 0, "builtin/extension"))
                continue
            src = pathlib.Path(origin)
            py_total += src.stat().st_size
            code_obj = compile(src.read_text(encoding="utf-8"), name, "exec", optimize=2, dont_inherit=True)
            zf.writestr(name.replace(".", "/") + ".pyc", marshal.dumps(code_obj))
            rows.append((name, src.stat().st_size, "pure python"))
    print(f"{'module':40s} {'source bytes':>12s}  kind")
    for name, size, kind in sorted(rows, key=lambda r: -r[1]):
        print(f"{name:40s} {size:12d}  {kind}")
    print()
    print(f"stdlib modules loaded : {len(rows)}")
    print(f"pure-python sources   : {py_total / 1024:.0f} KiB")
    print(f"-OO bytecode, zipped  : {len(buf.getvalue()) / 1024:.0f} KiB   <-- stdlib payload to ship")
    third = sorted({n.split('.')[0] for n in loaded if n.split('.')[0] not in stdlib and n.split('.')[0] != 'pyflutter'})
    print(f"third-party modules   : {third}")


if __name__ == "__main__":
    main()
