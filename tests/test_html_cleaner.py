"""Tests for HTML Cleaner, Markdown conversion, and Metadata extraction."""

from ethical_crawler.extractors.html_cleaner import HTMLCleaner
from ethical_crawler.extractors.metadata import MetadataExtractor
from tests.conftest import SAMPLE_HTML


def test_html_clean_and_convert_markdown():
    cleaner = HTMLCleaner()
    markdown, title = cleaner.clean_and_convert(SAMPLE_HTML)

    assert title == "Sample Test Article - Tech News"
    assert "Ethical Crawling in 2026" in markdown
    assert "Web scraping should always follow politeness guidelines" in markdown
    # Ads and scripts should be stripped
    assert "Buy our amazing product now!" not in markdown
    assert "script" not in markdown


def test_metadata_extraction():
    metadata = MetadataExtractor.extract(SAMPLE_HTML)
    assert metadata.title == "Sample Test Article - Tech News"
    assert metadata.description == "An in-depth article about modern ethical web crawling."
    assert metadata.author == "Jane Doe"
    assert metadata.canonical == "https://example.com/guide"
    assert metadata.og_title == "Ethical Crawling Guide"
    assert len(metadata.json_ld) == 1
    assert metadata.json_ld[0]["headline"] == "Ethical Crawling Guide"


def test_spa_detection():
    """Scenario 1: Detect JS-rendered Single Page Application placeholder."""
    cleaner = HTMLCleaner()

    spa_html = """<!DOCTYPE html>
    <html>
    <head><title>App</title><script src="/bundle.js"></script></head>
    <body>
        <div id="root"></div>
        <noscript>You need to enable JavaScript to run this app.</noscript>
    </body>
    </html>"""

    assert cleaner.is_js_rendered_spa(spa_html) is True
    assert cleaner.is_js_rendered_spa(SAMPLE_HTML) is False
