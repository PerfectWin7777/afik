"""Checks py_framework/afik/contract/widgets.json against the Python widgets and the Dart builder.

    python tools/check_contract.py            # report, exit code 1 on a real inconsistency
    python tools/check_contract.py --verbose  # also list the advisory findings

Checks
  python  every prop a Python widget class can send is in the contract, and every contract
          type with props has a Python class (hard errors).
  dart    every contract prop is read by the Dart code that builds that widget (hard error
          unless the prop is marked ``"dart": false`` in the contract, which records a known gap),
          and a prop marked ``"dart": false`` that Dart reads after all is reported so the mark
          is removed.
  advisory  Dart reads a prop the contract does not know (often internal or inherited).

The Dart side is read with regular expressions: the ``case 'Type':`` blocks of
``buildFromNode`` plus the ``Py*Widget`` classes and ``_build*`` helpers they delegate to, and
the ``WidgetRegistry.register('Type', ...)`` shims of ``plugin_catalog/``. Reads outside those
places are not seen, so a finding here is a lead to confirm, not proof.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import gen_contract  # noqa: E402

CONTRACT = ROOT / "py_framework/afik/contract/widgets.json"
BUILDER = ROOT / "dart_runtime/lib/widgets/widget_builder.dart"
DART_DIR = ROOT / "dart_runtime/lib"
CATALOG = ROOT / "dart_runtime/plugin_catalog"

COMMON = {"key", "slot", "_nid", "visible", "enabled", "tooltip", "debug_banner"}   # read for every widget by the framework

READ = re.compile(r"""props\[\s*['"]([A-Za-z0-9_]+)['"]\s*\]|containsKey\(\s*['"]([A-Za-z0-9_]+)['"]\s*\)""")
CASE = re.compile(r"^    case '([A-Za-z0-9_]+)':", re.M)
DELEGATE = re.compile(r"\b(Py[A-Za-z0-9_]+Widget|_build[A-Za-z0-9_]+)\(")
# Types with no `case` of their own: the code that reads their props belongs to the parent.
CONSUMED_BY = {
    "TextSpan": ["_buildTextSpan"],
    "DropdownMenuItem": ["PyDropdownButtonWidget", "PyDropdownMenuWidget"],
    "PopupMenuItem": ["PopupMenuButton"],
    "BottomNavigationBarItem": ["BottomNavigationBar"],
}
# Props read outside the builder (theme handling in main.dart).
EXTRA_FILES = {"MaterialApp": "main.dart", "AppBar": "app_bar_builder.dart"}
REGISTER = re.compile(r"WidgetRegistry\.register\(\s*'([A-Za-z0-9_]+)'")


def reads(text: str) -> set[str]:
    return {a or b for a, b in READ.findall(text)}


def block_of(source: str, header: re.Pattern | str) -> str:
    """Source of the class or function whose declaration matches ``header`` (brace matched)."""
    match = re.search(header, source, re.M)
    if not match:
        return ""
    start = source.find("{", match.end())
    if start < 0:
        return ""
    depth = 0
    for i in range(start, len(source)):
        if source[i] == "{":
            depth += 1
        elif source[i] == "}":
            depth -= 1
            if depth == 0:
                return source[match.start():i + 1]
    return source[match.start():]


def dart_reads(contract_types: list[str]) -> dict[str, set[str]]:
    """Props read by the Dart code that builds each widget type."""
    result: dict[str, set[str]] = {}
    sources = "\n".join(p.read_text(encoding="utf-8") for p in sorted(DART_DIR.rglob("*.dart")))
    builder = BUILDER.read_text(encoding="utf-8")

    cases = list(CASE.finditer(builder))
    default = builder.find("    default:", cases[-1].end()) if cases else -1
    labels: list[str] = []
    for i, match in enumerate(cases):
        labels.append(match.group(1))
        end = cases[i + 1].start() if i + 1 < len(cases) else (default if default > 0 else len(builder))
        body = builder[match.end():end]
        if not body.strip():
            continue                      # `case 'A': case 'B':` share the body that follows
        found = reads(body)
        for name in DELEGATE.findall(body):
            is_widget_class = name.startswith("Py")
            if is_widget_class:
                found |= reads(block_of(sources, rf"^class {name}\b"))
                found |= reads(block_of(sources, rf"^class _{name}State\b"))
            else:
                found |= reads(block_of(sources, rf"^\S[^\n]*\b{name}\s*\("))
        for label in labels:
            result.setdefault(label, set()).update(found)
        labels = []

    # Post-switch wrappers guarded by `node.type == 'X' && node.props.containsKey('p')`.
    for wtype, prop in re.findall(r"node\.type == '(\w+)'\s*&&\s*node\.props\.containsKey\('(\w+)'\)", builder):
        result.setdefault(wtype, set()).add(prop)

    # Types consumed by their parent (AppBar, TextSpan, menu items...) or read in another file.
    for wtype in contract_types:
        found = set(result.get(wtype, set()))
        for name in CONSUMED_BY.get(wtype, []):
            if name.startswith("Py"):
                found |= reads(block_of(sources, rf"^class {name}\b"))
                found |= reads(block_of(sources, rf"^class _{name}State\b"))
            elif name.startswith("_build"):
                found |= reads(block_of(sources, rf"^\S[^\n]*\b{name}\s*\("))
            else:
                found |= result.get(name, set())
        extra = EXTRA_FILES.get(wtype)
        if extra:
            for path in DART_DIR.rglob(extra):
                found |= reads(path.read_text(encoding="utf-8"))
        if found:
            result[wtype] = found

    for shim in sorted(CATALOG.glob("*/shim.dart")):
        text = shim.read_text(encoding="utf-8")
        types = REGISTER.findall(text)
        for t in types:
            result.setdefault(t, set()).update(reads(text))
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()

    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    generated = gen_contract.build()
    errors: list[str] = []
    notes: list[str] = []

    # --- Python side -----------------------------------------------------------------------
    for wtype, entry in generated.items():
        known = contract.get(wtype)
        if known is None:
            errors.append(f"python: widget type {wtype} is missing from the contract")
            continue
        for prop in entry["props"]:
            if prop not in known["props"]:
                errors.append(f"python: {wtype}.{prop} can be sent but is not in the contract")
    for wtype, entry in contract.items():
        if wtype not in generated and entry["props"]:
            errors.append(f"python: contract type {wtype} has no Python class")

    # --- Dart side -------------------------------------------------------------------------
    dart = dart_reads(list(contract))
    for wtype, entry in contract.items():
        read = dart.get(wtype)
        if read is None:
            if entry["props"]:
                errors.append(f"dart: no builder found for widget type {wtype}")
            continue
        prefixes = tuple(entry.get("prefixes", []))
        for prop, spec in entry["props"].items():
            declared = spec if isinstance(spec, dict) else {"type": spec}
            if prop in read or prop in COMMON or declared["type"] == "callback":
                if declared.get("dart") is False and prop in read:
                    errors.append(f"dart: {wtype}.{prop} is marked \"dart\": false but Dart reads it; remove the mark")
                continue
            if declared.get("dart") is False:
                notes.append(f"known gap: {wtype}.{prop} is sent but Dart ignores it")
                continue
            errors.append(f"dart: {wtype}.{prop} is sent by Python but Dart never reads it")
        for prop in sorted(read - set(entry["props"]) - COMMON):
            if prefixes and prop.startswith(prefixes):
                continue
            notes.append(f"advisory: Dart reads {wtype}.{prop}, which the contract does not list")

    for line in errors:
        print("ERROR", line)
    if args.verbose or not errors:
        for line in notes:
            print("note ", line)
    print(f"\n{len(contract)} widget types, {len(errors)} error(s), {len(notes)} note(s)")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
