import sys, threading, time
import pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "py_framework"))
import pyflutter as pf
from pyflutter.core.render import *
from pyflutter.core import widget_base as wb

print("== 1. Navigator.can_pop / current_page exist?")
from pyflutter.core.navigation import Navigator
print("can_pop", hasattr(Navigator, "can_pop"), "current_page", hasattr(Navigator, "current_page"))
try:
    m = pf.MaterialApp(home=pf.Text("x")); print(m.children)
except Exception as e: print("MaterialApp.children ERR", type(e).__name__, e)

print("== 2. TextFormField validator receives?")
fk = pf.FormKey()
f = pf.TextFormField("", name="email", validator=pf.Validators.required(), form_key=fk)
print("value attr type:", type(f.value))
print("validate() with empty ->", fk.validate(), "(expected False)")
print("get_values:", fk.get_values())

print("== 3. keyed reorder diff")
def mk(keys):
    return pf.Column([pf.Text(k.upper(), key=k) for k in keys])
a = mk(["a","b"]); b = mk(["b","a"])
for w in (a,b):
    r = resolve_tree(w); assign_node_ids(r)
sa = widget_to_snapshot(resolve_tree(a)); 
a2 = mk(["a","b"]); assign_node_ids(a2); sa = widget_to_snapshot(a2)
b2 = mk(["b","a"]); assign_node_ids(b2); sb = widget_to_snapshot(b2)
print(diff_snapshots(sa, sb))

print("== 4. empty-string prop vs removed")
t1 = pf.TextField("hello"); t1.props["_nid"]="root"; t2 = pf.TextField(""); t2.props["_nid"]="root"
print(diff_snapshots(widget_to_snapshot(t1), widget_to_snapshot(t2)))

print("== 5. Watch listener leak")
sig = pf.Signal(0, auto_update=False)
for i in range(50):
    resolve_tree(pf.Watch(lambda: pf.Text(str(sig.value))))
print("listeners on signal after 50 frames:", len(sig._listeners))

print("== 6. overlay callback swept at next send")
from pyflutter.plugins.overlay import show_snack_bar
from pyflutter.core.widget_base import _callback_registry
called=[]
show_snack_bar("hi", action="undo", on_action=lambda: called.append(1))
ids=[k for k in _callback_registry if k.startswith("cb_snackbar")]
print("registered:", ids)
root = pf.Text("x"); concrete = resolve_tree(root)
wb.sweep_stale_callbacks(wb.collect_active_callback_ids(concrete))
print("after one frame sweep still registered:", [k for k in _callback_registry if k.startswith("cb_snackbar")])

print("== 7. loguru braces in error message")
from pyflutter.core.logger import logger
try:
    logger.error("Error inside callback x: {'a': 1}", exc_info=True)
    print("no crash")
except Exception as e: print("CRASH", type(e).__name__, e)
def bad(): raise KeyError("{id}")
wb._callback_registry["z"]=bad
try:
    wb.invoke_callback("z", {}); print("invoke_callback survived")
except Exception as e: print("invoke_callback CRASH", type(e).__name__, e)
logger.error("Error in TextEditingController listener: %s", "boom")

print("== 8. config crashes")
import tempfile, pathlib
from pyflutter.core.config import PyFlutterConfig
for txt in ["dependencies:\npermissions:\n", "- a\n- b\n", "pyflutter:\n  port: abc\n", "name: [unclosed\n"]:
    p = pathlib.Path(tempfile.mkdtemp())/"pyflutter.yaml"; p.write_text(txt)
    try:
        c = PyFlutterConfig.from_file(p); print(repr(txt[:20]), "->", c.name, c.permissions)
    except Exception as e: print(repr(txt[:20]), "CRASH", type(e).__name__, e)

print("== 9. CLI build --release")
import pyflutter.cli.main as m
captured={}
import pyflutter.cli.builder as bld
class FB:
    def __init__(self, **kw): captured.update(kw)
    def build(self): return True
bld.PyFlutterBuilder = FB
try: m.main(["build","apk","--release"])
except SystemExit: pass
print(captured)
try: m.main(["remove","foo"])
except BaseException as e: print("remove:", type(e).__name__, e)
