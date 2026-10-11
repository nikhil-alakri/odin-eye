"""PDF Extractor & Ingestion Pipeline for whitepapers, documentation, and research files."""

from __future__ import annotations

import io
import logging
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

import httpx
from pydantic import BaseModel, Field

from ethical_crawler.config import get_settings
from ethical_crawler.types import CrawlResult, CrawlStrategy, PageMetadata
from ethical_crawler.vector_store import get_vector_store

logger = logging.getLogger(__name__)

try:
    import pypdf

    PYPDF_AVAILABLE = True
except ImportError:
    PYPDF_AVAILABLE = False


class PDFParseResult(BaseModel):
    """Structured result of parsing a PDF document."""
    url: str
    title: str
    page_count: int
    raw_size_bytes: int
    cleaned_markdown_size: int
    markdown: str
    author: Optional[str] = None
    creation_date: Optional[str] = None
    is_indexed_in_chroma: bool = False
    error: Optional[str] = None


class PDFExtractor:
    """Safe streaming downloader and page-by-page extractor for PDF documents."""

    MAX_PDF_SIZE_BYTES = 25 * 1024 * 1024  # 25 MB safeguard

    @classmethod
    def is_supported(cls) -> bool:
        """Check if pypdf is available."""
        return PYPDF_AVAILABLE

    @classmethod
    def extract_from_bytes(cls, pdf_bytes: bytes, url: str = "document.pdf") -> PDFParseResult:
        """Parse raw PDF bytes into structured markdown and metadata."""
        if not PYPDF_AVAILABLE:
            raise RuntimeError("pypdf is required for PDF parsing. Install with: pip install pypdf")

        reader = pypdf.PdfReader(io.BytesIO(pdf_bytes))
        num_pages = len(reader.pages)

        # Extract metadata
        meta = reader.metadata or {}
        doc_title = meta.title if hasattr(meta, "title") and meta.title else None
        if not doc_title:
            parsed = urlparse(url)
            filename = parsed.path.split("/")[-1]
            doc_title = filename if filename.endswith(".pdf") else "Untitled PDF Document"

        author = meta.author if hasattr(meta, "author") and meta.author else None
        creation_date = str(meta.creation_date) if hasattr(meta, "creation_date") and meta.creation_date else None

        # Build clean Markdown
        markdown_sections: List[str] = [
            f"# {doc_title}",
            "",
            f"> **Source:** [{url}]({url}) | **Pages:** {num_pages}",
        ]
        if author:
            markdown_sections.append(f"> **Author:** {author}")
        markdown_sections.append("")

        for page_idx, page in enumerate(reader.pages, start=1):
            text = page.extract_text() or ""
            text = text.strip()
            if text:
                markdown_sections.append(f"## Page {page_idx}")
                markdown_sections.append("")
                markdown_sections.append(text)
                markdown_sections.append("")

        full_markdown = "\n".join(markdown_sections)

        return PDFParseResult(
            url=url,
            title=doc_title,
            page_count=num_pages,
            raw_size_bytes=len(pdf_bytes),
            cleaned_markdown_size=len(full_markdown.encode("utf-8")),
            markdown=full_markdown,
            author=author,
            creation_date=creation_date,
            is_indexed_in_chroma=False,
        )

    @classmethod
    async def extract_from_url(
        cls,
        url: str,
        index_in_chroma: bool = True,
        parent_url: Optional[str] = None,
        timeout_seconds: float = 20.0,
    ) -> PDFParseResult:
        """Download PDF from URL with streaming size protection, extract text, and index into ChromaDB."""
        settings = get_settings()

        headers = {
            "User-Agent": settings.user_agent,
            "Accept": "application/pdf,*/*",
        }

        try:
            async with httpx.AsyncClient(timeout=timeout_seconds, follow_redirects=True) as client:
                # Pre-fetch check
                async with client.stream("GET", url, headers=headers) as resp:
                    if resp.status_code >= 400:
                        return PDFParseResult(
                            url=url,
                            title="Download Failed",
                            page_count=0,
                            raw_size_bytes=0,
                            cleaned_markdown_size=0,
                            markdown="",
                            error=f"HTTP {resp.status_code} while downloading PDF",
                        )

                    # Validate Content-Type or Content-Length
                    content_length = resp.headers.get("content-length")
                    if content_length and int(content_length) > cls.MAX_PDF_SIZE_BYTES:
                        return PDFParseResult(
                            url=url,
                            title="File Too Large",
                            page_count=0,
                            raw_size_bytes=int(content_length),
                            cleaned_markdown_size=0,
                            markdown="",
                            error=f"PDF size exceeds safe limit of {cls.MAX_PDF_SIZE_BYTES // (1024 * 1024)} MB",
                        )

                    # Stream download with byte counter
                    downloaded_bytes = bytearray()
                    async for chunk in resp.aiter_bytes():
                        downloaded_bytes.extend(chunk)
                        if len(downloaded_bytes) > cls.MAX_PDF_SIZE_BYTES:
                            return PDFParseResult(
                                url=url,
                                title="File Too Large",
                                page_count=0,
                                raw_size_bytes=len(downloaded_bytes),
                                cleaned_markdown_size=0,
                                markdown="",
                                error=f"Download aborted: size exceeds {cls.MAX_PDF_SIZE_BYTES // (1024 * 1024)} MB",
                            )

            # Parse bytes
            result = cls.extract_from_bytes(bytes(downloaded_bytes), url=url)

            # Optional ChromaDB indexing
            if index_in_chroma and result.markdown:
                vector_store = get_vector_store()
                crawl_res = CrawlResult(
                    url=url,
                    final_url=url,
                    status_code=200,
                    content_type="application/pdf",
                    title=result.title,
                    markdown=result.markdown,
                    raw_html_size=result.raw_size_bytes,
                    cleaned_markdown_size=result.cleaned_markdown_size,
                    metadata=PageMetadata(
                        title=result.title,
                        author=result.author,
                        description=f"PDF Document ({result.page_count} pages)",
                    ),
                    strategy_used=CrawlStrategy.HTTP,
                    confidence="HIGH",
                )
                # Attach extra PDF metadata
                ai_data = {
                    "document_type": "pdf",
                    "pdf_page_count": result.page_count,
                    "parent_url": parent_url,
                    "author": result.author,
                }
                vector_store.upsert_page(crawl_res, ai_data=ai_data)
                result.is_indexed_in_chroma = True
                logger.info("Successfully indexed PDF '%s' (%d pages) into ChromaDB", result.title, result.page_count)

            return result

        except Exception as exc:
            logger.error("Failed to parse PDF from %s: %s", url, exc)
            return PDFParseResult(
                url=url,
                title="Error Parsing PDF",
                page_count=0,
                raw_size_bytes=0,
                cleaned_markdown_size=0,
                markdown="",
                error=str(exc),
            )

