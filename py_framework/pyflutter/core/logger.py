"""
Logger configuration for PyFlutter using Loguru.
Configured with verbose / debug output and rich formatting.
"""

from __future__ import annotations

import sys
from loguru import logger

# Remove default logger handler
logger.remove()

# Configure verbose, detailed logging to stderr with color
logger.add(
    sys.stderr,
    format="<green>{time:HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
    level="DEBUG",
    colorize=True,
)

__all__ = ["logger"]
