"""
PyFlutter PDFX plugin (matches pub.dev package: pdfx).
Provides modern PDF rendering, pinch-to-zoom views, and document inspection.
"""

from __future__ import annotations

import itertools
from typing import Any, Optional
from pyflutter.plugins.manager import call_plugin
from pyflutter.widgets.widgets import PdfView, PdfViewPinch


_pdf_counter = itertools.count()


class PdfDocument:
    """Represents an opened PDF document file for rendering and introspection (pdfx)."""

    def __init__(self, document_id: str, page_count: int, path: str):
        self.document_id = document_id
        self.page_count = page_count
        self.path = path

    @classmethod
    def open_file(cls, path: str) -> PdfDocument:
        """Opens a PDF file from a local filesystem path."""
        res = call_plugin("pdfx", "openPdf", {"path": str(path)})
        doc_id = res.get("documentId", f"doc_{next(_pdf_counter)}") if isinstance(res, dict) else "doc_1"
        page_count = int(res.get("pageCount", 10)) if isinstance(res, dict) else 10
        return cls(doc_id, page_count, str(path))

    @classmethod
    def open_asset(cls, asset_name: str) -> PdfDocument:
        """Opens a PDF file from application assets."""
        res = call_plugin("pdfx", "openPdf", {"url": str(asset_name), "isAsset": "true"})
        doc_id = res.get("documentId", f"doc_{next(_pdf_counter)}") if isinstance(res, dict) else "doc_1"
        page_count = int(res.get("pageCount", 10)) if isinstance(res, dict) else 10
        return cls(doc_id, page_count, str(asset_name))

    def render_page(self, page_number: int) -> dict[str, Any]:
        """Renders a single PDF page into raster dimensions."""
        res = call_plugin("pdfx", "renderPage", {
            "documentId": self.document_id,
            "pageNumber": str(page_number),
        })
        return dict(res) if isinstance(res, dict) else {"pageNumber": page_number, "width": 595, "height": 842}


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
