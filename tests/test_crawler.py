"""Tests for EthicalCrawler orchestrator."""

import pytest

from ethical_crawler.crawler import EthicalCrawler
from ethical_crawler.types import CrawlRequest, CrawlResult, CrawlStrategy


@pytest.mark.asyncio
async def test_crawler_respects_limits(monkeypatch):
    """Test that crawler obeys max_pages limit."""
    req = CrawlRequest(
        url="https://example.com",
        max_pages=2,
        max_depth=1,
        respect_robots=False,
    )

    crawler = EthicalCrawler(req)

    # Mock _crawl_page
    async def mock_crawl_page(url: str) -> CrawlResult:
        return CrawlResult(
            url=url,
            final_url=url,
            status_code=200,
            title=f"Page {url}",
            markdown=f"# Content for {url}",
            internal_links=[
                "https://example.com/p1",
                "https://example.com/p2",
                "https://example.com/p3",
            ],
            strategy_used=CrawlStrategy.HTTP,
        )

    monkeypatch.setattr(crawler, "_crawl_page", mock_crawl_page)

    results = await crawler.run()
    assert len(results) == 2
    assert crawler.results[0].url == "https://example.com/"


@pytest.mark.asyncio
async def test_crawler_progress_callback_granular_activity(monkeypatch):
    """Test that crawler reports real-time granular activity and current_url."""
    activity_log = []

    def on_progress(result, current, total, activity="", current_url=None):
        activity_log.append(
            {
                "current": current,
                "total": total,
                "activity": activity,
                "url": current_url,
            }
        )

    req = CrawlRequest(
        url="https://example.com",
        max_pages=1,
        max_depth=0,
        respect_robots=False,
    )

    crawler = EthicalCrawler(req, on_progress=on_progress)

    async def mock_crawl_page(url: str) -> CrawlResult:
        return CrawlResult(
            url=url,
            final_url=url,
            status_code=200,
            title="Home",
            markdown="# Welcome",
            internal_links=[],
            strategy_used=CrawlStrategy.HTTP,
        )

    monkeypatch.setattr(crawler, "_crawl_page", mock_crawl_page)

    results = await crawler.run()
    assert len(results) == 1
    assert len(activity_log) >= 2
    # Ensure activity messages were reported
    activities = [entry["activity"] for entry in activity_log]
    assert any("Initializing" in a or "Fetching" in a for a in activities)
    assert any("Fetched" in a or "Completed" in a for a in activities)


@pytest.mark.asyncio
async def test_crawler_immediate_link_discovery(monkeypatch):
    """Test that internal links are enqueued immediately upon page fetch."""
    crawled_urls = []

    async def mock_crawl_page(url: str) -> CrawlResult:
        crawled_urls.append(url)
        return CrawlResult(
            url=url,
            final_url=url,
            status_code=200,
            title=f"Page {url}",
            markdown=f"# Content {url}",
            internal_links=["https://example.com/subpage"],
            strategy_used=CrawlStrategy.HTTP,
        )

    req = CrawlRequest(
        url="https://example.com",
        max_pages=2,
        max_depth=1,
        respect_robots=False,
    )

    crawler = EthicalCrawler(req)
    monkeypatch.setattr(crawler, "_crawl_page", mock_crawl_page)

    results = await crawler.run()
    assert len(results) == 2
    assert "https://example.com/subpage" in crawled_urls
