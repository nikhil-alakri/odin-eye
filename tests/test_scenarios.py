"""Comprehensive edge-case and scenario testing suite."""

import json
import tempfile
from pathlib import Path

import pytest

from ethical_crawler.extractors.ai_extractor import AIExtractor
from ethical_crawler.extractors.link_extractor import LinkExtractor
from ethical_crawler.storage import StorageExporter
from ethical_crawler.types import CrawlResult, CrawlStrategy, PageMetadata
from tests.conftest import SAMPLE_HTML


def test_scenario_spider_trap_normalization():
    """Scenario 5: URL normalization strips tracking params and fragments to avoid spider traps."""
    trap_url = "https://Example.COM:443/products/shoes/?utm_source=fb&utm_medium=cpc&sessionid=12345#reviews"
    normalized = LinkExtractor.normalize_url(trap_url)
    assert normalized == "https://example.com/products/shoes"

    # Trailing slash consistency
    assert LinkExtractor.normalize_url("https://example.com/blog/") == "https://example.com/blog"
    assert LinkExtractor.normalize_url("https://example.com/") == "https://example.com/"


def test_scenario_binary_file_filtering():
    """Scenario 6: Filter out PDF, ZIP, and other binary file links."""
    internal, external = LinkExtractor.extract_links(SAMPLE_HTML, "https://example.com/guide")

    # /downloads/manual.pdf should be excluded from crawlable links
    assert not any(link.endswith(".pdf") for link in internal)
    # mailto: should be excluded
    assert not any("mailto:" in link for link in internal)
    # Valid internal links kept
    assert "https://example.com/docs/robots" in internal
    # External links categorized
    assert "https://other-domain.org/external" in external


def test_scenario_storage_exports():
    """Scenario 7: Export to JSON, JSONL, CSV, Markdown, and SQLite."""
    result = CrawlResult(
        url="https://example.com/test",
        final_url="https://example.com/test",
        status_code=200,
        title="Test Page",
        markdown="# Test Content",
        cleaned_markdown_size=14,
        strategy_used=CrawlStrategy.HTTP,
        elapsed_seconds=0.25,
        metadata=PageMetadata(title="Test Page", description="Test Description"),
    )

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)

        # JSON
        json_file = tmp_path / "out.json"
        StorageExporter.save_file([result], json_file)
        assert json_file.exists()
        loaded = json.loads(json_file.read_text())
        assert loaded["total_pages"] == 1
        assert loaded["data"][0]["title"] == "Test Page"

        # CSV
        csv_file = tmp_path / "out.csv"
        StorageExporter.save_file([result], csv_file)
        assert csv_file.exists()
        assert "Test Page" in csv_file.read_text()

        # Markdown
        md_file = tmp_path / "out.md"
        StorageExporter.save_file([result], md_file)
        assert md_file.exists()
        assert "# Test Page" in md_file.read_text()

        # Plain Text
        txt_file = tmp_path / "out.txt"
        StorageExporter.save_file([result], txt_file)
        assert txt_file.exists()
        assert "TEST PAGE" in txt_file.read_text().upper()

        # PDF
        pdf_file = tmp_path / "out.pdf"
        StorageExporter.save_file([result], pdf_file)
        assert pdf_file.exists()
        assert pdf_file.read_bytes().startswith(b"%PDF-")

        # SQLite
        db_file = tmp_path / "out.sqlite"
        StorageExporter.save_file([result], db_file)
        assert db_file.exists()


def test_scenario_ai_json_repair():
    """Scenario 8: AI extractor handles markdown-wrapped and slightly malformed JSON."""
    extractor = AIExtractor(api_key="mock-key")

    raw_response = """
    Here is the extracted data:
    ```json
    {
        "title": "Clean Title",
        "author": "Alice",
        "date": "2026-03-01",
        "summary": "Short summary",
        "key_points": ["Point 1", "Point 2"],
        "tags": ["ai", "tech"]
    }
    ```
    Hope this helps!
    """

    parsed = extractor._clean_and_parse_json(raw_response)
    assert parsed["title"] == "Clean Title"
    assert parsed["author"] == "Alice"
    assert len(parsed["key_points"]) == 2


@pytest.mark.asyncio
async def test_nemotron_parser_mock(monkeypatch):
    """Test NemotronParser payload construction and response handling."""
    from ethical_crawler.extractors.nemotron_parser import NemotronParser

    parser = NemotronParser(api_key="mock-key")
    assert parser.is_available() is True

    class MockResponse:
        def raise_for_status(self):
            pass

        def json(self):
            return {
                "choices": [{"message": {"content": "# Parsed Document\n\nSample text."}}],
                "usage": {"total_tokens": 50},
            }

    class MockClient:
        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc_val, exc_tb):
            pass

        async def post(self, url, json, headers):
            assert json["model"] == "nvidia/nemotron-parse-2.0"
            assert "messages" in json
            return MockResponse()

    import httpx

    monkeypatch.setattr(httpx, "AsyncClient", lambda **kwargs: MockClient())

    res = await parser.parse_image(b"mock_image_bytes", task="markdown_bbox")
    assert res["model"] == "nvidia/nemotron-parse-2.0"
    assert "# Parsed Document" in res["raw_output"]


def test_company_profile_schema_validation():
    """Verify CompanyProfileSchema validates rich business intelligence output."""
    from ethical_crawler.types import CompanyProfileSchema

    data = {
        "company_name": "Plexis",
        "headline_or_tagline": "AI Studio Operating System",
        "what_they_do": "Studio CRM to onboard clients, manage bookings, and deliver albums.",
        "target_audience": ["Photography Studios", "Event Cinematographers"],
        "main_product": "Plexis Studio CRM",
        "products_and_features": [
            {
                "name": "Leads & Clients",
                "description": "Instant quotes and lead tracking",
                "price": "$29/mo",
                "features": ["WhatsApp Auto-reply", "Quoting"],
            }
        ],
        "why_in_market": "Solves manual data entry and fragmented communication",
        "strategic_purpose": "Best suited for multi-person photography studios looking to automate",
        "key_differentiators": ["24/7 WhatsApp AI automation", "Face search across 10k photos"],
    }

    profile = CompanyProfileSchema.model_validate(data)
    assert profile.company_name == "Plexis"
    assert len(profile.products_and_features) == 1
    assert profile.products_and_features[0].features == ["WhatsApp Auto-reply", "Quoting"]
