"""
PyFlutter FlutterPdfView plugin (matches pub.dev package: flutter_pdfview).
Provides platform-native PDF rendering views on Android and iOS.
"""

from __future__ import annotations

import itertools

from pyflutter.widgets.widgets import PDFView

_pdf_counter = itertools.count()


class PDFViewController:
    """Controls the native Flutter PDFView instance."""

    def __init__(self, initial_page: int = 0):
        self.current_page = initial_page

    def set_page(self, page: int) -> None:
        self.current_page = max(0, page)


# Alias
PdfViewerController = PDFViewController

__all__ = [
    "PDFView",
    "PDFViewController",
    "PdfViewerController",
]
