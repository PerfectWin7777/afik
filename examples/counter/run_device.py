"""
Runs the PyFlutter counter app interactively with a real device (Flutter shell).
Waits for the Dart client (on phone or desktop), sends the initial tree,
and continuously handles tap events in a loop so the user can click +1 as many times as they want!
"""

from __future__ import annotations

import sys
from pathlib import Path

# Add py_framework to path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "py_framework"))

from pyflutter import logger
from pyflutter.core.bridge import BridgeSession
from pyflutter.core.widget_base import invoke_callback
from main import App

PORT = 7879


def main():
    bridge_binary = sys.argv[1] if len(sys.argv) > 1 else str(
        Path(__file__).resolve().parents[2] / "rust_bridge" / "target" / "debug" / "pyflutter-bridge.exe"
    )

    app = App()
    logger.info(f"Starting bridge in relay mode on 127.0.0.1:{PORT}")
    logger.debug(f"Bridge binary path: {bridge_binary}")

    session = BridgeSession(bridge_binary, extra_args=["--dart-port", str(PORT)])

    logger.info("Bridge is listening, waiting for Flutter shell...")
    logger.debug("Building initial widget tree...")
    initial_tree = app.build()
    session.send_tree(initial_tree)
    logger.success("Initial widget tree sent to bridge! Ready for user interactions on device.")

    try:
        while True:
            logger.debug("Waiting for next CallbackEvent from bridge...")
            event = session.next_event()
            if event is None:
                logger.warning("Bridge closed or disconnected.")
                break

            logger.info(f"Received CallbackEvent: callback_id={event.callback_id}, data={event.event_data}")
            invoke_callback(event.callback_id, dict(event.event_data))
            logger.success(f"Callback executed! App count is now: {app.count}")

            logger.debug("Rebuilding tree with updated state...")
            session.send_tree(app.build())
            logger.debug("Updated RenderTree sent to device.")
    except KeyboardInterrupt:
        logger.info("Received KeyboardInterrupt, stopping session...")
    finally:
        session.close()
        logger.info("Session closed.")


if __name__ == "__main__":
    main()
