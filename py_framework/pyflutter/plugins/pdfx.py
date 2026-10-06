"""
PyFlutter PDFX plugin (matches pub.dev package: pdfx).
Provides modern PDF rendering, pinch-to-zoom views, and document inspection.
"""

from __future__ import annotations

import itertools
from typing import Any, Optional
from pyflutter.plugins.manager import PluginError, call_plugin
from pyflutter.widgets.widgets import PdfView, PdfViewPinch


_pdf_counter = itertools.count()


class PdfDocument:
    """An opened PDF document (pdfx)."""

    def __init__(self, document_id: str, page_count: int, path: str):
        self.document_id = document_id
        self.page_count = page_count
        self.path = path

    @classmethod
    def _from_answer(cls, res: Any, path: str) -> "PdfDocument":
        if not (isinstance(res, dict) and isinstance(res.get("documentId"), str)
                and isinstance(res.get("pageCount"), int)):
            raise PluginError(f"pdfx could not open {path!r}: unexpected answer {res!r}")
        return cls(res["documentId"], res["pageCount"], path)

    @classmethod
    def open_file(cls, path: str) -> "PdfDocument":
        """Opens a PDF from the local filesystem."""
        return cls._from_answer(call_plugin("pdfx", "openPdf", {"path": str(path)}), str(path))

    @classmethod
    def open_asset(cls, asset_name: str) -> "PdfDocument":
        """Opens a PDF bundled as an application asset."""
        res = call_plugin("pdfx", "openPdf", {"url": str(asset_name), "isAsset": "true"})
        return cls._from_answer(res, str(asset_name))

    def render_page(self, page_number: int, scale: float = 2.0) -> dict[str, Any]:
        """Renders one page (1-based) to a PNG file.

        Returns ``{"pageNumber", "width", "height", "path"}``; ``path`` is the PNG location.
        """
        res = call_plugin("pdfx", "renderPage", {
            "documentId": self.document_id,
            "pageNumber": str(page_number),
            "scale": str(scale),
        })
        if not (isinstance(res, dict) and res.get("rendered") is True):
            raise PluginError(f"pdfx could not render page {page_number}: unexpected answer {res!r}")
        return dict(res)

    def close(self) -> bool:
        """Releases the document."""
        res = call_plugin("pdfx", "closePdf", {"documentId": self.document_id})
        return isinstance(res, dict) and res.get("closed") is True


class PdfController:
    """Controls page navigation for PDFX viewer."""

    def __init__(self, initial_page: int = 1, document: Optional[PdfDocument] = None):
        self.initial_page = initial_page
        self.current_page = initial_page
        self.zoom_level = 1.0
        self.document = document

    def jump_to_page(self, page_number: int) -> None:
        self.current_page = max(1, page_number)

    def next_page(self) -> None:
        self.current_page += 1

    def previous_page(self) -> None:
        if self.current_page > 1:
            self.current_page -= 1

    def set_zoom_level(self, zoom: float) -> None:
        self.zoom_level = max(0.5, min(3.0, zoom))


PdfViewerController = PdfController


__all__ = [
    "PdfDocument",
    "PdfController",
    "PdfViewerController",
    "PdfView",
    "PdfViewPinch",
]
