"""
Runs the Facebook feed example on a connected device or desktop.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Add py_framework to path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "py_framework"))

from pyflutter import run
from main import SocialFeedApp


if __name__ == "__main__":
    run(SocialFeedApp())
