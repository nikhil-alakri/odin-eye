"""Base interface for web crawling engines."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from ethical_crawler.types import CrawlResult, CrawlStrategy


class CrawlEngine(ABC):
    """Abstract base class for all crawler engines."""

    @property
    @abstractmethod
    def strategy(self) -> CrawlStrategy:
        """The strategy type represented by this engine."""
        pass

    @abstractmethod
    async def crawl(self, url: str, **kwargs: Any) -> CrawlResult:
        """Crawl a single URL and return the processed result."""
        pass

    @abstractmethod
    async def close(self) -> None:
        """Clean up resources, sessions, or browser instances."""
        pass

    async def __aenter__(self) -> CrawlEngine:
        """Enter async context."""
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Exit async context and close resources."""
        await self.close()
