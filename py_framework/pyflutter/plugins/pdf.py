"""
PyFlutter PDF Suite plugins:
- syncfusion_flutter_pdfviewer (enterprise viewer & pagination controller)
- pdfx (modern pdfium viewer & document rendering)
- printing (PDF generation, layout, print dialog, system share)
- flutter_pdfview (native platform PDF viewer)
"""

from __future__ import annotations

import itertools
from typing import Any, Optional
from pyflutter.plugins.manager import call_plugin


_pdf_counter = itertools.count()


class PdfViewerController:
    """Controls page navigation and zoom for PDF viewers (Syncfusion / PDFX)."""

    def __init__(self, initial_page: int = 1):
        self.current_page = initial_page
        self.zoom_level = 1.0

    def jump_to_page(self, page_number: int) -> None:
        """Jumps directly to the specified page number."""
        self.current_page = max(1, page_number)

    def next_page(self) -> None:
        """Navigates to the next page."""
        self.current_page += 1

    def previous_page(self) -> None:
        """Navigates to the previous page."""
        if self.current_page > 1:
            self.current_page -= 1

    def set_zoom_level(self, zoom: float) -> None:
        """Sets the viewport zoom level."""
        self.zoom_level = max(0.5, min(3.0, zoom))


class PdfDocument:
    """Represents an opened PDF document file for rendering and introspection."""

    def __init__(self, document_id: str, page_count: int, path: str):
        self.document_id = document_id
        self.page_count = page_count
        self.path = path

    @classmethod
    def open_file(cls, path: str) -> PdfDocument:
        """Opens a PDF file from a local filesystem path."""
        res = call_plugin("pdf", "openPdf", {"path": str(path)})
        doc_id = res.get("documentId", f"doc_{next(_pdf_counter)}") if isinstance(res, dict) else "doc_1"
        page_count = int(res.get("pageCount", 10)) if isinstance(res, dict) else 10
        return cls(doc_id, page_count, str(path))

    @classmethod
    def open_asset(cls, asset_name: str) -> PdfDocument:
        """Opens a PDF file from application assets."""
        res = call_plugin("pdf", "openPdf", {"url": str(asset_name), "isAsset": "true"})
        doc_id = res.get("documentId", f"doc_{next(_pdf_counter)}") if isinstance(res, dict) else "doc_1"
        page_count = int(res.get("pageCount", 10)) if isinstance(res, dict) else 10
        return cls(doc_id, page_count, str(asset_name))

    def render_page(self, page_number: int) -> dict[str, Any]:
        """Renders a single PDF page into raster dimensions."""
        res = call_plugin("pdf", "renderPage", {
            "documentId": self.document_id,
            "pageNumber": str(page_number),
        })
        return dict(res) if isinstance(res, dict) else {"pageNumber": page_number, "width": 595, "height": 842}


class Printing:
    """Provides native printing dialogs, layout, and PDF file sharing."""

    @staticmethod
    def print_pdf(path_or_name: str, document_name: Optional[str] = None) -> bool:
        """Dispatches a PDF file to the system printer dialog."""
        res = call_plugin("pdf", "printPdf", {
            "path": str(path_or_name),
            "name": str(document_name or path_or_name),
        })
        return bool(isinstance(res, dict) and res.get("printed", True))

    @staticmethod
    def share_pdf(path: str, filename: Optional[str] = None) -> bool:
        """Opens system share sheet for the PDF file."""
        res = call_plugin("pdf", "sharePdf", {
            "path": str(path),
            "name": str(filename or path),
        })
        return bool(isinstance(res, dict) and res.get("shared", True))

    @staticmethod
    def layout_pdf(path: str) -> bool:
        """Prepares a PDF document for print layout preview."""
        res = call_plugin("pdf", "layoutPdf", {"path": str(path)})
        return bool(isinstance(res, dict) and res.get("completed", True))
