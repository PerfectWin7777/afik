"""
PyFlutter Printing plugin (matches pub.dev package: printing).
Native print dialog and PDF sharing for existing PDF files.

Each function returns True only when the platform reports the user completed the action
(a cancelled print dialog returns False).
"""

from __future__ import annotations

from typing import Optional

from pyflutter.plugins.manager import INTERACTIVE_TIMEOUT, call_plugin


class Printing:
    """System printing and PDF sharing (printing)."""

    @staticmethod
    def print_pdf(path_or_name: str, document_name: Optional[str] = None) -> bool:
        """Sends a PDF file to the system print dialog."""
        res = call_plugin("printing", "printPdf", {
            "path": str(path_or_name),
            "name": str(document_name or path_or_name),
        }, timeout=INTERACTIVE_TIMEOUT)
        return isinstance(res, dict) and res.get("printed") is True

    @staticmethod
    def share_pdf(path: str, filename: Optional[str] = None) -> bool:
        """Opens the system share sheet for a PDF file."""
        res = call_plugin("printing", "sharePdf", {
            "path": str(path),
            "name": str(filename or path),
        }, timeout=INTERACTIVE_TIMEOUT)
        return isinstance(res, dict) and res.get("shared") is True

    @staticmethod
    def layout_pdf(path: str) -> bool:
        """Shows the print preview/layout dialog for a PDF file."""
        res = call_plugin("printing", "layoutPdf", {"path": str(path)}, timeout=INTERACTIVE_TIMEOUT)
        return isinstance(res, dict) and res.get("completed") is True


__all__ = [
    "Printing",
]
