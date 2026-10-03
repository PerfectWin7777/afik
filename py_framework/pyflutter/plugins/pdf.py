"""
PyFlutter PDF Suite:
Consolidates and re-exports the individual PDF plugins:
- syncfusion_flutter_pdfviewer
- pdfx
- printing
- flutter_pdfview
"""

from __future__ import annotations

from pyflutter.plugins.syncfusion_flutter_pdfviewer import (
    SfPdfViewer,
    PdfViewerController,
)
from pyflutter.plugins.pdfx import (
    PdfDocument,
    PdfController,
    PdfView,
    PdfViewPinch,
)
from pyflutter.plugins.printing import (
    Printing,
)
from pyflutter.plugins.flutter_pdfview import (
    PDFView,
    PDFViewController,
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
