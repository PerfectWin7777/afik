"""
Logger configuration for Afik.
Uses Loguru if installed, otherwise falls back gracefully to standard library logging.

The level defaults to INFO and can be changed with the AFIK_LOG_LEVEL
environment variable (e.g. AFIK_LOG_LEVEL=DEBUG). Only Loguru's default
handler is replaced: handlers installed by the host application are kept.
"""

from __future__ import annotations

import os
import sys

_LEVEL = os.environ.get("AFIK_LOG_LEVEL", "INFO").upper()

try:
    from loguru import logger

    try:
        logger.remove(0)  # Loguru's default stderr handler only
    except ValueError:
        pass
    logger.add(
        sys.stderr,
        format="<green>{time:HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level=_LEVEL,
        colorize=True,
    )
except ImportError:
    import logging

    class _StdLogger:
        """Loguru-compatible subset on top of the standard library."""

        def __init__(self, inner: logging.Logger, exception: bool = False):
            self._inner = inner
            self._exception = exception

        def opt(self, *, exception: bool = False, **_: object) -> "_StdLogger":
            return _StdLogger(self._inner, exception)

        def _log(self, level: int, message: str, *args: object, **kwargs: object) -> None:
            if args or kwargs:
                try:
                    message = message.format(*args, **kwargs)
                except Exception:
                    pass
            self._inner.log(level, message, exc_info=self._exception)

        def debug(self, m, *a, **k): self._log(logging.DEBUG, m, *a, **k)
        def info(self, m, *a, **k): self._log(logging.INFO, m, *a, **k)
        def success(self, m, *a, **k): self._log(logging.INFO, m, *a, **k)
        def warning(self, m, *a, **k): self._log(logging.WARNING, m, *a, **k)
        def error(self, m, *a, **k): self._log(logging.ERROR, m, *a, **k)
        def exception(self, m, *a, **k): self._log(logging.ERROR, m, *a, **{**k})

    logging.basicConfig(
        level=getattr(logging, _LEVEL, logging.INFO),
        format="%(asctime)s | %(levelname)-8s | %(name)s - %(message)s",
    )
    logger = _StdLogger(logging.getLogger("afik"))  # type: ignore[assignment]

__all__ = ["logger"]
