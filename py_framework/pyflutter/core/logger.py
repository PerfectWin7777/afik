"""
Logger configuration for PyFlutter.
Uses Loguru if installed, otherwise falls back gracefully to standard library logging.
"""

from __future__ import annotations

import sys

try:
    from loguru import logger

    logger.remove()
    logger.add(
        sys.stderr,
        format="<green>{time:HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level="DEBUG",
        colorize=True,
    )
except ImportError:
    import logging

    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s | %(levelname)-8s | %(name)s - %(message)s",
    )
    logger = logging.getLogger("pyflutter")
    # Provide .success() compatibility
    if not hasattr(logger, "success"):
        logger.success = logger.info  # type: ignore

__all__ = ["logger"]
