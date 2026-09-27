"""
Runs the full POC loop for the counter example:

  Python builds tree -> Rust bridge -> Rust simulates a tap on the
  button (standing in for Dart, which doesn't exist yet) -> Python
  receives the callback event -> runs App.increment() -> re-sends the
  updated tree -> repeat.

Usage:
    python run_poc.py /path/to/pyflutter-bridge
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "py_framework"))

from pyflutter.core.bridge import run_loop  # noqa: E402
from main import App  # noqa: E402


def main():
    if len(sys.argv) != 2:
        print("Usage: python run_poc.py /path/to/pyflutter-bridge")
        sys.exit(1)

    bridge_binary = sys.argv[1]
    app = App()

    run_loop(bridge_binary, build_tree=app.build, max_iterations=5)

    print(f"[python] final count: {app.count}")


if __name__ == "__main__":
    main()
