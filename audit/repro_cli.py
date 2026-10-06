import sys, tempfile, pathlib, re, importlib
import pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "py_framework"))
import pyflutter as pf
from pyflutter.cli.creator import create_project
from pyflutter.cli.runner import load_app_from_file
from pyflutter.core.render import resolve_tree, assign_node_ids, widget_to_snapshot
d = pathlib.Path(tempfile.mkdtemp())/"my_app"
create_project(d, "my_app")
mod, app = load_app_from_file(d/"main.py")
print("scaffold loaded:", type(app).__name__)
t = resolve_tree(app.build()); assign_node_ids(t); print("scaffold tree ok:", t.widget_type)

for ex in ["counter","facebook_feed","pyshop"]:
    p = pathlib.Path(str(pathlib.Path(__file__).resolve().parents[1] / "examples"))/ex/"main.py"
    try:
        m, a = load_app_from_file(p)
        t = resolve_tree(a.build() if hasattr(a,"build") else a); assign_node_ids(t)
        print(ex, "OK ->", type(a).__name__, t.widget_type)
    except Exception as e:
        print(ex, "FAIL", type(e).__name__, e)

print("== manifest sync with '&' in name")
from pyflutter.cli.manifest_sync import sync_android_manifest, sync_ios_plist
mf = pathlib.Path(tempfile.mkdtemp())/"AndroidManifest.xml"
mf.write_text('<manifest xmlns:android="x">\n<application android:label="a" android:name="b"/>\n</manifest>')
sync_android_manifest(mf, ["internet","camara"], "Tom & Jerry")
print(mf.read_text())
import xml.dom.minidom
try: xml.dom.minidom.parseString(mf.read_text()); print("valid xml")
except Exception as e: print("INVALID XML:", e)

print("== entrypoint discovery picks alphabetically-first zero-arg MainWindow")
src = '''
import pyflutter as pf
class AboutPage(pf.MainWindow):
    def build(self): return pf.Text("about")
class HomePage(pf.MainWindow):
    def build(self): return pf.Text("home")
if __name__ == "__main__":
    pf.run(HomePage())
'''
f = pathlib.Path(tempfile.mkdtemp())/"app_x.py"; f.write_text(src)
m,a = load_app_from_file(f); print("bare discovery ->", type(a).__name__)
m,a = load_app_from_file(f, prefer_class="HomePage"); print("hot-reload with prefer_class=HomePage ->", type(a).__name__)

print("== module-name shadowing: entrypoint called json.py / random.py")
f2 = pathlib.Path(tempfile.mkdtemp())/"random.py"; f2.write_text("import pyflutter as pf\nclass App:\n    def build(self): return pf.Text('x')\n")
import random as stdrandom
load_app_from_file(f2)
import sys as _s
print("sys.modules['random'] replaced by user file:", getattr(_s.modules['random'],'__file__','') == str(f2))
