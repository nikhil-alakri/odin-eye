"""Unit tests for PDFExtractor."""

import io
import pytest
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

from ethical_crawler.extractors.pdf_extractor import PDFExtractor, PDFParseResult


def create_sample_pdf_bytes(title: str = "Test Research Paper", pages: int = 2) -> bytes:
    """Helper to generate in-memory PDF bytes with reportlab."""
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=letter)
    c.setTitle(title)
    c.setAuthor("Ethical Researcher")

    for i in range(1, pages + 1):
        c.drawString(100, 750, f"{title} - Page {i}")
        c.drawString(100, 700, f"This is substantive content on page {i} of the research paper.")
        c.drawString(100, 650, "Data: Item A = 100, Item B = 250.")
        c.showPage()
    c.save()
    return buf.getvalue()


def test_pdf_extract_from_bytes():
    pdf_bytes = create_sample_pdf_bytes("Machine Learning Ethics", pages=2)
    result = PDFExtractor.extract_from_bytes(pdf_bytes, url="https://example.com/ml-ethics.pdf")

    assert result.page_count == 2
    assert "Machine Learning Ethics" in result.title
    assert "Page 1" in result.markdown
    assert "Page 2" in result.markdown
    assert "substantive content" in result.markdown
    assert result.raw_size_bytes > 0


def test_pdf_extract_size_limit():
    assert PDFExtractor.MAX_PDF_SIZE_BYTES == 25 * 1024 * 1024


@pytest.mark.asyncio
async def test_pdf_extract_from_url_mock(monkeypatch):
    pdf_bytes = create_sample_pdf_bytes("AI Safety Report", pages=1)

    class MockStreamResponse:
        def __init__(self):
            self.status_code = 200
            self.headers = {"content-type": "application/pdf", "content-length": str(len(pdf_bytes))}

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc_val, exc_tb):
            pass

        async def aiter_bytes(self):
            yield pdf_bytes

    import httpx

    def mock_stream(self, method, url, **kwargs):
        return MockStreamResponse()

    monkeypatch.setattr(httpx.AsyncClient, "stream", mock_stream)

    res = await PDFExtractor.extract_from_url(
        "https://example.com/safety.pdf",
        index_in_chroma=False,
    )
    assert res.page_count == 1
    assert "AI Safety Report" in res.title
    assert res.error is None

