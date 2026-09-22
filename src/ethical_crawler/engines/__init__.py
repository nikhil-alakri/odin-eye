"""Crawling engines package: Base, HTTP, and Browser."""

from ethical_crawler.engines.base import CrawlEngine
from ethical_crawler.engines.browser_engine import BrowserEngine
from ethical_crawler.engines.http_engine import HTTPEngine

__all__ = ["CrawlEngine", "HTTPEngine", "BrowserEngine"]
