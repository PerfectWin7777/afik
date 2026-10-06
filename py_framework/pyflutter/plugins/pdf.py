"""
PyFlutter PDF Suite:
Consolidates and re-exports the individual PDF plugins:
- syncfusion_flutter_pdfviewer
- pdfx
- printing
- flutter_pdfview
"""

from __future__ import annotations

from pyflutter.plugins.flutter_pdfview import (
    PDFView,
    PDFViewController,
)
from pyflutter.plugins.pdfx import (
    PdfController,
    PdfDocument,
    PdfView,
    PdfViewPinch,
)
from pyflutter.plugins.printing import (
    Printing,
)
from pyflutter.plugins.syncfusion_flutter_pdfviewer import (
    PdfViewerController,
    SfPdfViewer,
)

__all__ = [
    "PdfDocument",
    "PdfController",
    "PdfViewerController",
    "Printing",
    "SfPdfViewer",
    "PdfView",
    "PdfViewPinch",
    "PDFView",
    "PDFViewController",
]
