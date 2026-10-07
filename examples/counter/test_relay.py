"""
Tests the Rust bridge's relay mode end to end, using fake_dart_client.py
as a stand-in for the real Dart shell (which can't be run in this
sandbox — see fake_dart_client.py's docstring).

Flow: real Python App -> BridgeSession (relay mode) -> TCP socket ->
fake_dart_client (manual protobuf decode/encode) -> back through the
socket -> BridgeSession -> real Python callback invoked.

Usage:
    python test_relay.py /path/to/afik-bridge
"""

import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "py_framework"))

from afik.core.bridge import BridgeSession  # noqa: E402
from main import App  # noqa: E402

PORT = 7879


def main():
    if len(sys.argv) != 2:
        print("Usage: python test_relay.py /path/to/afik-bridge")
        sys.exit(1)

    bridge_binary = sys.argv[1]
    app = App()

    session = BridgeSession(bridge_binary, extra_args=["--dart-port", str(PORT)])

    # Give the bridge a moment to bind and start listening before the
    # fake Dart client tries to connect.
    time.sleep(0.3)

    fake_dart_script = str(Path(__file__).resolve().parent / "fake_dart_client.py")
    dart_client = subprocess.Popen(
        [sys.executable, "-u", fake_dart_script, str(PORT)],
        stdout=None,  # let its prints show up directly
        stderr=None,
    )

    try:
        session.send_tree(app.build())

        event = session.next_event()
        if event is None:
            print("[python] bridge closed with no event received — FAILED")
            sys.exit(1)

        print(f"[python] received callback event: callback_id={event.callback_id}")
        from afik.core.widget_base import invoke_callback
        invoke_callback(event.callback_id, dict(event.event_data))

        print(f"[python] final count: {app.count}")
        if app.count == 1:
            print("[python] RELAY TEST PASSED")
        else:
            print(f"[python] RELAY TEST FAILED — expected count=1, got {app.count}")
            sys.exit(1)
    finally:
        dart_client.wait(timeout=2)
        session.close()


if __name__ == "__main__":
    main()
