"""Generates a starting point for py_framework/pyflutter/contract/widgets.json from the Python widget classes.

The contract lists, for every ``widget_type``, the props Python may send and their type
(``string | number | bool | color | icon | callback | enum``). This script reads the Python
sources with ``ast`` (keyword arguments of ``super().__init__(...)``, ``props["x"] = ...``,
``self.props["x"] = ...``) and writes a first version; a person reviews it and then maintains
``py_framework/pyflutter/contract/widgets.json`` by hand. The file is never overwritten unless ``--force`` is given.

    python tools/gen_contract.py                 # prints the generated contract
    python tools/gen_contract.py --write --force # (re)writes py_framework/pyflutter/contract/widgets.json
"""

from __future__ import annotations

import argparse
import ast
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCES = [
    ROOT / "py_framework/pyflutter/widgets/widgets.py",
    ROOT / "py_framework/pyflutter/widgets/animations.py",
    ROOT / "py_framework/pyflutter/widgets/gestures.py",
    ROOT / "py_framework/pyflutter/core/form.py",
]
OUTPUT = ROOT / "py_framework/pyflutter/contract/widgets.json"
IGNORED_KEYS = {"raw_props"}


BOOL_NAMES = {"enabled", "visible", "read_only", "selected", "disabled", "checked", "dense", "centered"}
NUMBER_NAMES = {
    "elevation", "opacity", "flex", "padding", "margin", "width", "height", "size", "spacing", "radius",
    "border_radius", "border_width", "divisions", "min", "max", "step", "scale", "duration_ms", "top",
    "bottom", "left", "right",
}
NUMBER_SUFFIXES = ("_ms", "_size", "_width", "_height", "_radius", "_spacing", "_padding", "_elevation", "_opacity")


def prop_type(name: str, annotation: str | None, value: ast.AST | None) -> str:
    """Best guess of the contract type of a prop; the reviewer fixes the rest."""
    if name.endswith("callback_id") or name == "callback_id":
        return "callback"
    if name == "color" or name.endswith("_color") or name == "background_color":
        return "color"
    if name == "icon" or name.endswith("_icon"):
        return "icon"
    if name in BOOL_NAMES:
        return "bool"
    if name in NUMBER_NAMES or name.endswith(NUMBER_SUFFIXES):
        return "number"
    ann = annotation or ""
    if "Callable" in ann:
        return "callback"
    if "bool" in ann:
        return "bool"
    if "int" in ann or "float" in ann:
        return "number"
    if isinstance(value, ast.IfExp):
        branches = [value.body, value.orelse]
        if all(isinstance(b, ast.Constant) and b.value in ("true", "false") for b in branches):
            return "bool"
    if isinstance(value, ast.Constant):
        if isinstance(value.value, bool):
            return "bool"
        if isinstance(value.value, (int, float)):
            return "number"
    return "string"


class ClassInfo:
    def __init__(self, node: ast.ClassDef):
        self.node = node
        self.prefixes: set[str] = set()
        self.style_props = False
        self.name = node.name
        self.bases = [b.id for b in node.bases if isinstance(b, ast.Name)]
        self.widget_type: str | None = None
        self.props: dict[str, str] = {}
        self.candidates: dict[str, str] = {}       # super().__init__ keywords
        self.super_kwargs: dict[str, ast.AST] = {}
        self.dynamic = False


def collect(path: Path) -> dict[str, ClassInfo]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    classes: dict[str, ClassInfo] = {}
    for node in tree.body:
        if not isinstance(node, ast.ClassDef):
            continue
        info = ClassInfo(node)
        for stmt in node.body:
            if (
                isinstance(stmt, ast.Assign)
                and any(isinstance(t, ast.Name) and t.id == "widget_type" for t in stmt.targets)
                and isinstance(stmt.value, ast.Constant)
            ):
                info.widget_type = stmt.value.value
        for fn in node.body:
            if isinstance(fn, ast.FunctionDef):
                scan_function(fn, info)
        classes[info.name] = info
    return classes


def scan_function(fn: ast.FunctionDef, info: ClassInfo) -> None:
    annotations = {
        a.arg: ast.unparse(a.annotation) if a.annotation is not None else None
        for a in fn.args.args + fn.args.kwonlyargs
    }

    def add(name: str, value: ast.AST | None) -> None:
        if name in IGNORED_KEYS or name == "callback_id":
            return
        annotation = annotations.get(value.id) if isinstance(value, ast.Name) else None
        info.props.setdefault(name, prop_type(name, annotation, value))

    def add_candidate(name: str, value: ast.AST | None) -> None:
        if name in IGNORED_KEYS or name == "callback_id":
            return
        annotation = annotations.get(value.id) if isinstance(value, ast.Name) else None
        info.candidates.setdefault(name, prop_type(name, annotation, value))

    for node in ast.walk(fn):
        if isinstance(node, ast.Call):
            func = node.func
            is_super_init = (
                isinstance(func, ast.Attribute) and func.attr == "__init__"
                and (isinstance(func.value, ast.Call) or isinstance(func.value, ast.Name))
            )
            if is_super_init:
                # Keywords are props only when the base is Widget itself; for a base that is
                # another widget class they are that class's constructor parameters.
                for kw in node.keywords:
                    if kw.arg is not None:
                        info.super_kwargs[kw.arg] = kw.value
                        add_candidate(kw.arg, kw.value)
            if isinstance(func, ast.Name) and func.id == "QtSignal" and len(node.args) >= 2:
                arg = node.args[1]
                if isinstance(arg, ast.Constant) and isinstance(arg.value, str) and arg.value != "callback_id":
                    info.props.setdefault(arg.value, "callback")
            if isinstance(func, ast.Attribute) and func.attr == "update":
                target = func.value
                if "props" in ast.unparse(target):
                    for arg in node.args:
                        if isinstance(arg, ast.Dict):
                            for k, v in zip(arg.keys, arg.values):
                                if isinstance(k, ast.Constant) and isinstance(k.value, str):
                                    add(k.value, v)
                        elif (
                            isinstance(arg, ast.Call) and isinstance(arg.func, ast.Attribute)
                            and arg.func.attr == "to_props"
                        ):
                            prefix = next(
                                (kw.value.value for kw in arg.keywords
                                 if kw.arg == "prefix" and isinstance(kw.value, ast.Constant)), None
                            )
                            if prefix:
                                info.prefixes.add(prefix)
                            else:
                                info.style_props = True      # props.update(style.to_props())
                        else:
                            info.dynamic = True
        elif isinstance(node, ast.Assign):
            for target in node.targets:
                if (
                    isinstance(target, ast.Subscript)
                    and isinstance(target.slice, ast.Constant)
                    and isinstance(target.slice.value, str)
                    and "props" in ast.unparse(target.value)
                    and ast.unparse(target.value) in ("props", "self.props", "p")
                ):
                    add(target.slice.value, node.value)


def text_style_keys() -> list[str]:
    """Keys TextStyle.to_props() can produce (read from core/style.py)."""
    tree = ast.parse((ROOT / "py_framework/pyflutter/core/style.py").read_text(encoding="utf-8"))
    for node in tree.body:
        if isinstance(node, ast.ClassDef) and node.name == "TextStyle":
            for fn in node.body:
                if isinstance(fn, ast.FunctionDef) and fn.name == "to_props":
                    return sorted({
                        t.slice.value
                        for n in ast.walk(fn) if isinstance(n, ast.Assign)
                        for t in n.targets
                        if isinstance(t, ast.Subscript) and isinstance(t.slice, ast.Constant)
                    })
    return []


TEXT_STYLE_KEYS = text_style_keys()


def build() -> dict:
    classes: dict[str, ClassInfo] = {}
    for source in SOURCES:
        classes.update(collect(source))

    def widget_bases(info: ClassInfo) -> list[ClassInfo]:
        return [classes[b] for b in info.bases if b in classes]

    def inherited(info: ClassInfo, seen=()) -> tuple[dict[str, str], bool]:
        props: dict[str, str] = {}
        dynamic = info.dynamic
        for base in widget_bases(info):
            if base.name not in seen:
                bp, bd = inherited(base, seen + (info.name,))
                props.update(bp)
                dynamic = dynamic or bd
        if not widget_bases(info):
            props.update(info.candidates)          # super().__init__(**props) goes to Widget
        props.update(info.props)
        return props, dynamic

    contract: dict[str, dict] = {}
    for info in classes.values():
        if not info.widget_type:
            continue
        props, dynamic = inherited(info)
        entry = contract.setdefault(info.widget_type, {"props": {}})
        entry["props"].update(props)
        if info.prefixes:
            entry["prefixes"] = sorted(info.prefixes)
        if info.style_props:
            for key in TEXT_STYLE_KEYS:
                entry["props"].setdefault(key, prop_type(key, None, None))
        if dynamic:
            entry["dynamic"] = True
    return {k: {**v, "props": dict(sorted(v["props"].items()))} for k, v in sorted(contract.items())}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--write", action="store_true", help="write py_framework/pyflutter/contract/widgets.json")
    parser.add_argument("--force", action="store_true", help="overwrite an existing contract")
    args = parser.parse_args()
    contract = build()
    text = json.dumps(contract, indent=1, ensure_ascii=False) + "\n"
    if not args.write:
        sys.stdout.write(text)
        return 0
    if OUTPUT.exists() and not args.force:
        print(f"{OUTPUT} exists; use --force to overwrite it", file=sys.stderr)
        return 1
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(text, encoding="utf-8")
    print(f"wrote {OUTPUT} ({len(contract)} widget types)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
