"""Tests for Ethical Rule 4: Sitemap XML and Gzip parsing."""

import gzip

import pytest

from ethical_crawler.core.sitemap import SitemapParser
from tests.conftest import SAMPLE_SITEMAP_XML


@pytest.mark.asyncio
async def test_parse_standard_sitemap_xml(monkeypatch):
    parser = SitemapParser()

    class MockResponse:
        status_code = 200
        content = SAMPLE_SITEMAP_XML.encode("utf-8")

    class MockClient:
        async def get(self, url):
            return MockResponse()

    result = await parser.fetch_and_parse("https://example.com/sitemap.xml", client=MockClient())
    assert result.total_urls == 3
    assert result.urls[0].loc == "https://example.com/"
    assert result.urls[0].priority == 1.0
    assert result.urls[1].loc == "https://example.com/about"
    assert result.urls[2].loc == "https://example.com/contact"


@pytest.mark.asyncio
async def test_parse_gzipped_sitemap(monkeypatch):
    """Scenario 3: Parsing compressed .xml.gz sitemap."""
    parser = SitemapParser()
    compressed = gzip.compress(SAMPLE_SITEMAP_XML.encode("utf-8"))

    class MockResponse:
        status_code = 200
        content = compressed

    class MockClient:
        async def get(self, url):
            return MockResponse()

    result = await parser.fetch_and_parse("https://example.com/sitemap.xml.gz", client=MockClient())
    assert result.total_urls == 3
    assert result.urls[0].loc == "https://example.com/"
