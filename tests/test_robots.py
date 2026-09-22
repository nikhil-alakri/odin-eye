"""Tests for Ethical Rule 1: robots.txt parsing and permission checks."""

import pytest

from ethical_crawler.core.robots import RobotsParser
from tests.conftest import SAMPLE_ROBOTS_TXT


@pytest.mark.asyncio
async def test_robots_rule_matching():
    parser = RobotsParser()
    entries, sitemaps = parser._parse_rules(SAMPLE_ROBOTS_TXT, "example.com")

    # Check parsed sitemaps
    assert "https://example.com/sitemap.xml" in sitemaps
    assert "https://example.com/sitemap_news.xml.gz" in sitemaps

    # Wildcard user-agent rules
    wc_entry = parser._find_best_entry(entries, "RandomBot/1.0")
    assert wc_entry is not None
    assert wc_entry.crawl_delay == 3.5
    assert "/admin/" in wc_entry.disallow_patterns

    # Specific EthicalCrawlerBot rules
    bot_entry = parser._find_best_entry(entries, "EthicalCrawlerBot/1.0")
    assert bot_entry is not None
    assert bot_entry.crawl_delay == 1.0
    assert "/secret/" in bot_entry.disallow_patterns
    assert "/secret/open/" in bot_entry.allow_patterns


@pytest.mark.asyncio
async def test_robots_can_fetch_logic():
    parser = RobotsParser()
    domain = "example.com"
    entries, sitemaps = parser._parse_rules(SAMPLE_ROBOTS_TXT, domain)

    # Invalidate / inject cache
    from ethical_crawler.types import RobotsDirectives

    dirs = RobotsDirectives(
        domain=domain,
        robots_url="https://example.com/robots.txt",
        can_fetch=True,
        crawl_delay=1.0,
        sitemaps=sitemaps,
        user_agent_used="EthicalCrawlerBot",
    )
    import time

    parser._cache[domain] = (time.time(), dirs, entries)

    # Test paths for EthicalCrawlerBot
    assert await parser.can_fetch("https://example.com/", "EthicalCrawlerBot") is True
    assert await parser.can_fetch("https://example.com/blog/post-1", "EthicalCrawlerBot") is True
    assert await parser.can_fetch("https://example.com/secret/locked", "EthicalCrawlerBot") is False
    assert (
        await parser.can_fetch("https://example.com/secret/open/doc", "EthicalCrawlerBot") is True
    )

    # Test BadBot is blocked everywhere
    assert await parser.can_fetch("https://example.com/any-page", "BadBot/1.0") is False


@pytest.mark.asyncio
async def test_robots_missing_404_fallback():
    """Scenario 2: Missing robots.txt (404) defaults to allow all."""
    parser = RobotsParser()
    entries, sitemaps = parser._parse_rules("", "empty-site.com")
    assert len(entries) == 0
    assert len(sitemaps) == 0
