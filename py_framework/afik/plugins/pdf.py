"""
Afik PDF Suite:
Consolidates and re-exports the individual PDF plugins:
- syncfusion_flutter_pdfviewer
- pdfx
- printing
- flutter_pdfview
"""

from __future__ import annotations

from afik.plugins.flutter_pdfview import (
    PDFView,
    PDFViewController,
)
from afik.plugins.pdfx import (
    PdfController,
    PdfDocument,
    PdfView,
    PdfViewPinch,
)
from afik.plugins.printing import (
    Printing,
)
from afik.plugins.syncfusion_flutter_pdfviewer import (
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
