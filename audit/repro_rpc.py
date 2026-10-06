import sys, threading, time, struct, json, queue
import pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "py_framework"))
import pyflutter as pf
from pyflutter.core import widget_base as wb
from pyflutter.core.render import MSG_CALLBACK_EVENT, MSG_PLUGIN_RESPONSE
from pyflutter.generated import widget_pb2
from pyflutter.cli.runner import PyFlutterRunner
from pyflutter import app as appmod
from pyflutter.plugins import manager

class FakeStdin:
    """Emulates the Rust bridge + a well-behaved Dart: replies to every plugin call immediately."""
    def __init__(self, inbox, mode="ok"): self.inbox=inbox; self.mode=mode; self.t=[]
    def write(self, b):
        t, ln = struct.unpack(">BI", b[:5]); payload=b[5:5+ln]
        if t == 0x03:
            plugin, method, cid, args = payload.decode().split("\x00",3)
            if self.mode=="ok": body={"call_id":cid,"result":{"authenticated": False},"error":None}
            else:              body={"call_id":cid,"result":None,"error":"UnsupportedError: boom"}
            self.inbox.put((MSG_PLUGIN_RESPONSE, json.dumps(body).encode()))
    def flush(self): pass
class FakeProc:
    def __init__(self, inbox, mode): self.stdin=FakeStdin(inbox, mode)
class FakeSession:
    def __init__(self, mode):
        self.inbox=queue.Queue(); self.process=FakeProc(self.inbox, mode)
    def next_event(self):
        return self.inbox.get()
    def send_tree(self,*a,**k): pass

def run(mode, via_callback):
    sess=FakeSession(mode)
    r = PyFlutterRunner.__new__(PyFlutterRunner)
    r.session=sess; r.is_running=True; r.tree_lock=threading.RLock(); r._building=False; r._rebuild_requested=False; r._callback_queue=queue.Queue(); r._event_thread=None; r.app=type("A",(),{"build":lambda s: pf.Text("x")})(); r.debug_banner=None
    appmod.set_active_runner(r)
    result={}
    def handler():
        t0=time.time()
        try:
            result["val"]=manager.call_plugin("local_auth","authenticate",{}, timeout=2.0)
        except Exception as e:
            result["val"]=f"{type(e).__name__}: {e}"
        result["dt"]=time.time()-t0
    if via_callback:
        cid = wb._register_callback(handler)
        ev = widget_pb2.CallbackEvent(callback_id=cid)
        sess.inbox.put((MSG_CALLBACK_EVENT, ev))
        r.is_running=True
        threading.Thread(target=r._callback_worker, daemon=True).start()
        th=threading.Thread(target=r._event_loop, daemon=True); r._event_thread=th; th.start()
        time.sleep(1.0)
    else:
        th=threading.Thread(target=r._event_loop, daemon=True); r._event_thread=th; th.start()
        handler()
    r.is_running=False
    appmod.set_active_runner(None)
    return result

print("Dart answers authenticated=False; call made from a BUTTON CALLBACK  ->", run("ok", True))
print("Dart answers authenticated=False; call made from another thread     ->", run("ok", False))
print("Dart answers an ERROR; call from another thread                      ->", run("err", False))
