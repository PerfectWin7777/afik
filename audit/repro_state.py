import sys, threading, time, struct, json, io
import pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "py_framework"))
import pyflutter as pf
from pyflutter.core.render import *
from pyflutter.core import widget_base as wb
from pyflutter.core import state as st

print("== A. cached imperative layout freezes child Components")
class Badge(pf.Component):
    n = 0
    def build(self):
        Badge.n += 1
        return pf.Text(f"build#{Badge.n}")
class Screen(pf.Component):
    def __init__(self):
        super().__init__()
        self.layout = pf.Column()
        self.layout.add_widget(Badge())
s = Screen()
r1 = resolve_tree(s); r2 = resolve_tree(s)
print("frame1:", r1.children[0].props["text"], "frame2:", r2.children[0].props["text"], "(Badge.build ran", Badge.n, "times)")

print("== B. StatefulComponent state survives frames when created in app.build()?")
class CS(pf.State):
    def init_state(self): self.n = 0
    def build(self):
        self.n += 1
        return pf.Text(str(self.n))
class C(pf.StatefulComponent):
    def create_state(self): return CS()
class App:
    def build(self):
        return pf.Column([C(), C()])
app = App()
for i in range(3):
    tree = app.build()          # like runner._build_and_tag_tree (before send_tree reset)
    r = resolve_tree(tree)
    print("frame", i, [c.props["text"] for c in r.children])
print("registry size:", len(st._state_registry))
# simulate popped screen: states are never disposed
disposed=[]
class DS(pf.State):
    def build(self): return pf.Text("x")
    def dispose(self): disposed.append(1)
class D(pf.StatefulComponent):
    def create_state(self): return DS()
resolve_tree(pf.Column([D()]))
resolve_tree(pf.Column([]))          # next frame: D is gone from the tree
print("after widget removed from tree, dispose called?", bool(disposed), "registry:", len(st._state_registry))

print("== C. build() that writes a Signal / set_state deadlocks tree_lock")
from pyflutter.cli.runner import PyFlutterRunner
from pyflutter import app as appmod
class FakeSession:
    process = object()
    def send_tree(self, tree, force_full=False, resolved=False):
        resolve_tree(tree)
runner = PyFlutterRunner.__new__(PyFlutterRunner)
runner.tree_lock = threading.RLock(); runner.session = FakeSession(); runner.debug_banner=None; runner.is_running=True
from pyflutter.core.scheduler import FrameScheduler
runner.scheduler = FrameScheduler(lambda: None); runner._force_full_next_frame = False
sig = pf.Signal(0)
class InitSetsState(pf.State):
    def init_state(self): sig.value = 1      # or self.set_state(...)
    def build(self): return pf.Text("hi")
class W(pf.StatefulComponent):
    def create_state(self): return InitSetsState()
class A2:
    def build(self): return pf.Column([W()])
runner.app = A2(); appmod.set_active_runner(runner)
t = threading.Thread(target=runner.push_update, daemon=True); t.start(); t.join(2)
print("push_update finished within 2s?", not t.is_alive(), "(False == DEADLOCK)")
appmod.set_active_runner(None)

print("== D. callbacks: event types for Slider/TextField/Checkbox")
got=[]
sl = pf.Slider(0.0, on_change=lambda v: got.append(("slider", v, type(v).__name__)))
wb.invoke_callback(sl.callback_id, {"value":"0.5"})
tf = pf.TextField("", on_change=lambda v: got.append(("tf", v, type(v).__name__)))
wb.invoke_callback(tf.callback_id, {"value":"abc"})
cb = pf.Checkbox(False, on_change=lambda v: got.append(("cb", v, type(v).__name__)))
wb.invoke_callback(cb.callback_id, {"value":"false"})
print(got)
# plain Button with handler taking an arg named differently
b = pf.Button("x", on_click=lambda e: got.append(("btn", e)))
wb.invoke_callback(b.callback_id, {})
print(got[-1])
