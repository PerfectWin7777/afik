"""Checks that every plugin of the catalog installs and analyses cleanly.

For each plugin (or the ones named on the command line) the script copies dart_runtime/ to
a temporary folder, installs the plugin there exactly like `afik add` does, runs
`flutter pub get` and `flutter analyze`, and reports analyzer errors and warnings.

    python tools/verify_catalog.py                 # all plugins, one at a time + all together
    python tools/verify_catalog.py local_auth camera
    python tools/verify_catalog.py --together      # only the combined install of every plugin

Needs the Flutter SDK in PATH. Exit code = number of failing plugins.
"""

from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "py_framework"))

from afik.plugins import catalog  # noqa: E402

RUNTIME = ROOT / "dart_runtime"
IGNORE = shutil.ignore_patterns("build", ".dart_tool", "installed", ".flutter-plugins*", "*.iml")


def verify(names: list[str]) -> tuple[bool, str]:
    work = Path(tempfile.mkdtemp(prefix="afik_verify_"))
    try:
        target = work / "dart_runtime"
        shutil.copytree(RUNTIME, target, ignore=IGNORE)
        catalog.sync_plugins(target, names, run_pub_get=False)
        for cmd in (["flutter", "pub", "get"], ["flutter", "analyze", "--no-pub"]):
            proc = subprocess.run(cmd, cwd=target, capture_output=True, text=True)
            out = proc.stdout + proc.stderr
            if cmd[1] == "pub" and proc.returncode != 0:
                return False, "flutter pub get failed:\n" + out[-2500:]
            if cmd[1] == "analyze":
                problems = [
                    l for l in out.splitlines()
                    if l.strip().startswith(("error", "warning")) and "deprecated_member_use" not in l
                ]
                if problems:
                    return False, "\n".join(problems[:40])
        return True, "ok"
    finally:
        shutil.rmtree(work, ignore_errors=True)


def main() -> int:
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    together_only = "--together" in sys.argv
    wanted = args or list(catalog.load_catalog(RUNTIME))
    failures = 0
    runs = [] if together_only else [[n] for n in wanted]
    if len(wanted) > 1:
        runs.append(wanted)
    for names in runs:
        label = names[0] if len(names) == 1 else "ALL TOGETHER"
        ok, detail = verify(names)
        print(f"{'PASS' if ok else 'FAIL'}  {label}")
        if not ok:
            failures += 1
            print("      " + detail.replace("\n", "\n      "))
    return failures


if __name__ == "__main__":
    sys.exit(main())
