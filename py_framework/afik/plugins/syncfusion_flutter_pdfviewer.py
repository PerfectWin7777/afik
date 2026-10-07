"""
Afik Syncfusion PDF Viewer plugin (matches pub.dev package: syncfusion_flutter_pdfviewer).
"""

from __future__ import annotations

import itertools

from afik.widgets.widgets import SfPdfViewer

_pdf_counter = itertools.count()


class PdfViewerController:
    """Controls page navigation and zoom for Syncfusion PDF Viewer."""

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


__all__ = [
    "SfPdfViewer",
    "PdfViewerController",
]
