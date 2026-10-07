"""
Runs the POC loop for the counter example.
Usage:
    python run_poc.py [/path/to/afik-bridge]
"""

from __future__ import annotations

import sys
from pathlib import Path

# Add py_framework to path
repo_root = Path(__file__).resolve().parents[2]
framework_path = repo_root / "py_framework"
if str(framework_path) not in sys.path:
    sys.path.insert(0, str(framework_path))

from afik import run
from main import App


def main():
    if len(sys.argv) > 1 and not sys.argv[1].startswith("-"):
        from afik.core.bridge import run_loop
        bridge_binary = sys.argv[1]
        app = App()
        run_loop(bridge_binary, build_tree=app.build, max_iterations=5)
        print(f"[python] final count: {app.count}")
    else:
        run(App())


if __name__ == "__main__":
    main()
