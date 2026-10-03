"""
PyFlutter Printing plugin (matches pub.dev package: printing).
Provides native printing dialogs, layout, and document sharing.
"""

from __future__ import annotations

from typing import Optional
from pyflutter.plugins.manager import call_plugin


class Printing:
    """Provides native printing dialogs, layout, and PDF file sharing (printing)."""

    @staticmethod
    def print_pdf(path_or_name: str, document_name: Optional[str] = None) -> bool:
        """Dispatches a PDF file to the system printer dialog."""
        res = call_plugin("printing", "printPdf", {
            "path": str(path_or_name),
            "name": str(document_name or path_or_name),
        })
        return bool(isinstance(res, dict) and res.get("printed", True))

    @staticmethod
    def share_pdf(path: str, filename: Optional[str] = None) -> bool:
        """Opens system share sheet for the PDF file."""
        res = call_plugin("printing", "sharePdf", {
            "path": str(path),
            "name": str(filename or path),
        })
        return bool(isinstance(res, dict) and res.get("shared", True))

    @staticmethod
    def layout_pdf(path: str) -> bool:
        """Prepares a PDF document for print layout preview."""
        res = call_plugin("printing", "layoutPdf", {"path": str(path)})
        return bool(isinstance(res, dict) and res.get("completed", True))


__all__ = [
    "Printing",
]
