"""
Unit tests for Afik PDF Suite:
- syncfusion_flutter_pdfviewer (SfPdfViewer, PdfViewerController)
- pdfx (PdfDocument, PdfView, PdfViewPinch)
- printing (Printing layout, print, share)
- flutter_pdfview (PDFView widget)
"""

import unittest

import afik as pf
from afik.plugins import (
    flutter_pdfview,
    pdf,
    pdfx,
    printing,
    syncfusion_pdfviewer,
)


class TestPdfControllerAndDocument(unittest.TestCase):
    def test_pdf_viewer_controller(self):
        ctrl = pdf.PdfViewerController(initial_page=1)
        self.assertEqual(ctrl.current_page, 1)

        ctrl.next_page()
        self.assertEqual(ctrl.current_page, 2)

        ctrl.previous_page()
        self.assertEqual(ctrl.current_page, 1)

        ctrl.jump_to_page(7)
        self.assertEqual(ctrl.current_page, 7)

        ctrl.set_zoom_level(2.0)
        self.assertEqual(ctrl.zoom_level, 2.0)

    def test_pdf_document_open_and_render(self):
        doc = pdf.PdfDocument.open_file("my_document.pdf")
        self.assertIsInstance(doc, pdf.PdfDocument)
        self.assertEqual(doc.path, "my_document.pdf")
        self.assertGreater(doc.page_count, 0)

        page_meta = doc.render_page(1)
        self.assertIsInstance(page_meta, dict)
        self.assertEqual(page_meta.get("pageNumber"), 1)
        self.assertEqual(page_meta.get("width"), 595)

    def test_printing_methods(self):
        self.assertTrue(pdf.Printing.print_pdf("invoice.pdf"))
        self.assertTrue(pdf.Printing.share_pdf("invoice.pdf"))
        self.assertTrue(pdf.Printing.layout_pdf("invoice.pdf"))

    def test_plugin_aliases(self):
        ctrl = syncfusion_pdfviewer.PdfViewerController()
        self.assertIsNotNone(ctrl)

        doc = pdfx.PdfDocument.open_asset("assets/guide.pdf")
        self.assertEqual(doc.path, "assets/guide.pdf")

        self.assertTrue(printing.Printing.print_pdf("test.pdf"))

        vctrl = flutter_pdfview.PdfViewerController()
        self.assertIsNotNone(vctrl)


class TestPdfWidgets(unittest.TestCase):
    def test_syncfusion_pdf_viewer_widget(self):
        viewer = pf.SfPdfViewer.network("https://example.com/catalog.pdf", width=500, height=700)
        self.assertEqual(viewer.widget_type, "SfPdfViewer")
        self.assertEqual(viewer.props["src"], "https://example.com/catalog.pdf")
        self.assertEqual(float(viewer.props["width"]), 500)
        self.assertEqual(float(viewer.props["height"]), 700)

        # File and Asset constructors
        f_viewer = pf.SfPdfViewer.file("local.pdf")
        self.assertEqual(f_viewer.props["src"], "local.pdf")

        a_viewer = pf.SfPdfViewer.asset("guide.pdf")
        self.assertEqual(a_viewer.props["src"], "guide.pdf")

        # Signal connection
        called = []
        viewer.page_changed.connect(lambda data: called.append(data))
        self.assertTrue(hasattr(viewer, "_page_changed_signal"))

    def test_pdfx_widgets(self):
        pview = pf.PdfView("document.pdf", width=400, height=600)
        self.assertEqual(pview.widget_type, "PdfView")
        self.assertEqual(pview.props["path"], "document.pdf")

        pinch_view = pf.PdfViewPinch("contract.pdf")
        self.assertEqual(pinch_view.widget_type, "PdfViewPinch")
        self.assertEqual(pinch_view.props["path"], "contract.pdf")

        called = []
        pview.page_changed.connect(lambda data: called.append(data))
        self.assertTrue(hasattr(pview, "_page_changed_signal"))

    def test_flutter_pdfview_widget(self):
        pdfview = pf.PDFView("sample.pdf", enable_swipe=True, swipe_horizontal=True)
        self.assertEqual(pdfview.widget_type, "PDFView")
        self.assertEqual(pdfview.props["file_path"], "sample.pdf")
        self.assertTrue(pdfview.props["enable_swipe"])
        self.assertTrue(pdfview.props["swipe_horizontal"])

        called = []
        pdfview.page_changed.connect(lambda data: called.append(data))
        self.assertTrue(hasattr(pdfview, "_page_changed_signal"))


if __name__ == "__main__":
    unittest.main()
