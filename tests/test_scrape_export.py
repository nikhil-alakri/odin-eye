"""Tests for Web Scraping and Multi-Format Exports (PDF, MD, TXT, JSON, CSV)."""

from datetime import datetime
from pathlib import Path

import pytest
from httpx import ASGITransport, AsyncClient
from typer.testing import CliRunner

from ethical_crawler.api.app import app
from ethical_crawler.api.v1.router import _JOBS_STORE
from ethical_crawler.cli import app as cli_app
from ethical_crawler.storage import StorageExporter
from ethical_crawler.types import (
    CrawlJob,
    CrawlRequest,
    CrawlResult,
    CrawlStrategy,
    JobStatus,
    PageMetadata,
)


@pytest.fixture
def sample_result() -> CrawlResult:
    return CrawlResult(
        url="https://example.com/blog/test",
        final_url="https://example.com/blog/test",
        status_code=200,
        title="Test Article Title",
        markdown="# Main Article Heading\n\nThis is the introductory paragraph with some **bold** text.\n\n## Section 1\n\nDetails about the topic and a [link](https://example.com/about).",
        raw_html="<html><body><h1>Main Article Heading</h1><p>This is the introductory paragraph.</p></body></html>",
        metadata=PageMetadata(
            title="Test Article Title",
            description="A test article for exporter validation",
            author="Crawler Tester",
        ),
        internal_links=["https://example.com/about", "https://example.com/contact"],
        external_links=["https://external.org/resource"],
        cleaned_markdown_size=180,
        strategy_used=CrawlStrategy.HTTP,
        elapsed_seconds=0.42,
        depth=0,
        crawled_at=datetime.utcnow(),
    )


def test_storage_to_pdf(sample_result: CrawlResult, tmp_path: Path):
    """Test generating valid PDF document using ReportLab."""
    pdf_path = tmp_path / "test_export.pdf"
    pdf_bytes = StorageExporter.to_pdf([sample_result], target_path_or_buf=pdf_path)

    assert pdf_path.exists()
    assert pdf_path.stat().st_size > 0
    # PDF magic bytes
    assert pdf_bytes.startswith(b"%PDF-")


def test_storage_to_markdown_single(sample_result: CrawlResult):
    """Test single-page markdown export formatting."""
    md = StorageExporter.to_markdown([sample_result])
    assert "# Test Article Title" in md
    assert "- **Source URL:** https://example.com/blog/test" in md
    assert "## Section 1" in md


def test_storage_to_markdown_multi(sample_result: CrawlResult):
    """Test multi-page consolidated markdown report."""
    md = StorageExporter.to_markdown([sample_result, sample_result], title="Multi Crawl")
    assert "# Multi Crawl" in md
    assert "**Total Pages Crawled:** 2" in md
    assert "## 1. Test Article Title" in md
    assert "## 2. Test Article Title" in md


def test_storage_to_text(sample_result: CrawlResult):
    """Test plain text export formatting."""
    txt = StorageExporter.to_text([sample_result])
    assert "TEST ARTICLE TITLE" in txt.upper()
    assert "URL:     https://example.com/blog/test" in txt
    assert "Main Article Heading" in txt


def test_storage_export_bytes(sample_result: CrawlResult):
    """Test raw bytes exporter with proper MIME types."""
    results = [sample_result]

    # PDF
    pdf_bytes, pdf_mime, pdf_name = StorageExporter.export_bytes(results, fmt="pdf")
    assert pdf_bytes.startswith(b"%PDF-")
    assert pdf_mime == "application/pdf"
    assert pdf_name.endswith(".pdf")

    # Markdown
    md_bytes, md_mime, md_name = StorageExporter.export_bytes(results, fmt="md")
    assert b"Test Article Title" in md_bytes
    assert "markdown" in md_mime
    assert md_name.endswith(".md")

    # Plain Text
    txt_bytes, txt_mime, txt_name = StorageExporter.export_bytes(results, fmt="txt")
    assert b"URL:" in txt_bytes
    assert "plain" in txt_mime
    assert txt_name.endswith(".txt")

    # CSV
    csv_bytes, csv_mime, csv_name = StorageExporter.export_bytes(results, fmt="csv")
    assert b"URL,Final URL,Status Code" in csv_bytes
    assert "csv" in csv_mime
    assert csv_name.endswith(".csv")

    # JSON
    json_bytes, json_mime, json_name = StorageExporter.export_bytes(results, fmt="json")
    assert b'"total_pages": 1' in json_bytes
    assert "json" in json_mime
    assert json_name.endswith(".json")


def test_storage_save_file_extensions(sample_result: CrawlResult, tmp_path: Path):
    """Verify save_file automatically detects formats by file extension."""
    results = [sample_result]

    for ext in (".pdf", ".md", ".txt", ".json", ".csv"):
        fpath = tmp_path / f"output{ext}"
        saved = StorageExporter.save_file(results, fpath)
        assert Path(saved).exists()
        assert Path(saved).stat().st_size > 0


@pytest.mark.asyncio
async def test_api_scrape_endpoint(monkeypatch, sample_result: CrawlResult):
    """Test POST /api/v1/scrape endpoint."""

    async def mock_crawler_run(self):
        return [sample_result]

    from ethical_crawler.crawler import EthicalCrawler

    monkeypatch.setattr(EthicalCrawler, "run", mock_crawler_run)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            "/api/v1/scrape",
            json={
                "url": "https://example.com/blog/test",
                "strategy": "http",
                "extract_ai": False,
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert data["result"]["title"] == "Test Article Title"
        assert "Main Article Heading" in data["result"]["markdown"]


@pytest.mark.asyncio
async def test_api_jobs_export_endpoint(sample_result: CrawlResult):
    """Test GET /api/v1/jobs/{job_id}/export for PDF, MD, TXT, JSON, CSV."""
    job_id = "test-export-job"
    job = CrawlJob(
        job_id=job_id,
        request=CrawlRequest(url="https://example.com"),
        status=JobStatus.COMPLETED,
        results=[sample_result],
        pages_crawled=1,
    )
    _JOBS_STORE[job_id] = job

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        for fmt in ["pdf", "md", "txt", "json", "csv"]:
            resp = await client.get(f"/api/v1/jobs/{job_id}/export?format={fmt}")
            assert resp.status_code == 200
            assert "Content-Disposition" in resp.headers
            assert f".{fmt}" in resp.headers["Content-Disposition"]
            assert len(resp.content) > 0


@pytest.mark.asyncio
async def test_api_scrape_and_export_endpoint(monkeypatch, sample_result: CrawlResult):
    """Test POST /api/v1/scrape/export streaming download."""

    async def mock_crawler_run(self):
        return [sample_result]

    from ethical_crawler.crawler import EthicalCrawler

    monkeypatch.setattr(EthicalCrawler, "run", mock_crawler_run)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            "/api/v1/scrape/export?url=https://example.com/blog/test&format=pdf"
        )
        assert resp.status_code == 200
        assert resp.headers["Content-Type"] == "application/pdf"
        assert resp.content.startswith(b"%PDF-")


def test_cli_scrape_command(monkeypatch, sample_result: CrawlResult, tmp_path: Path):
    """Test CLI scrape command with --format and --output."""

    async def mock_crawler_run(self):
        return [sample_result]

    from ethical_crawler.crawler import EthicalCrawler

    monkeypatch.setattr(EthicalCrawler, "run", mock_crawler_run)

    runner = CliRunner()
    out_file = str(tmp_path / "cli_test.pdf")

    result = runner.invoke(
        cli_app,
        ["scrape", "https://example.com/blog/test", "--output", out_file, "--format", "pdf"],
    )
    assert result.exit_code == 0
    assert "Results successfully exported to:" in result.stdout
    assert Path(out_file).exists()
    assert Path(out_file).read_bytes().startswith(b"%PDF-")
