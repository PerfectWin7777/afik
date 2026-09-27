"""
Runs the Facebook feed example on a connected device.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Add py_framework to path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "py_framework"))

from pyflutter import logger
from pyflutter.core.bridge import BridgeSession
from pyflutter.core.widget_base import invoke_callback
from main import SocialFeedApp

PORT = 7879


def main():
    bridge_binary = str(
        Path(__file__).resolve().parents[2] / "rust_bridge" / "target" / "debug" / "pyflutter-bridge.exe"
    )

    app = SocialFeedApp()
    logger.info(f"Starting PyFlutter Facebook Feed on 127.0.0.1:{PORT}")

    session = BridgeSession(bridge_binary, extra_args=["--dart-port", str(PORT)])

    logger.info("Waiting for Flutter client...")
    initial_tree = app.build()
    session.send_tree(initial_tree)
    logger.success("Facebook feed sent to phone! You can scroll and click 'J'aime'.")

    try:
        while True:
            event = session.next_event()
            if event is None:
                logger.warning("Bridge closed or disconnected.")
                break

            logger.info(f"Callback received: {event.callback_id}")
            invoke_callback(event.callback_id, dict(event.event_data))

            logger.debug("Rebuilding feed...")
            session.send_tree(app.build())
            logger.success("Updated feed sent to phone!")
    except KeyboardInterrupt:
        logger.info("Stopping...")
    finally:
        session.close()


if __name__ == "__main__":
    main()
