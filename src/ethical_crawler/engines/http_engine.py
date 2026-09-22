"""High-Performance Async HTTP Engine (HTTPX).

Fast, lightweight crawling engine for static web pages, APIs, and articles.
Includes Content-Type sniffing to avoid downloading large binaries.
"""

import logging
import time
from typing import Any

import httpx

from ethical_crawler.config import get_settings
from ethical_crawler.core.headers import get_default_headers
from ethical_crawler.engines.base import CrawlEngine
from ethical_crawler.extractors.element_inspector import ElementInspector
from ethical_crawler.extractors.html_cleaner import get_html_cleaner
from ethical_crawler.extractors.link_extractor import LinkExtractor
from ethical_crawler.extractors.metadata import MetadataExtractor
from ethical_crawler.types import CrawlResult, CrawlStrategy

logger = logging.getLogger("ethical_crawler.http_engine")


class HTTPEngine(CrawlEngine):
    """Async HTTP engine based on httpx."""

    def __init__(self, client: httpx.AsyncClient | None = None):
        settings = get_settings()
        self._owned_client = client is None
        headers = get_default_headers(user_agent=settings.user_agent)
        self.client = client or httpx.AsyncClient(
            headers=headers,
            timeout=settings.request_timeout,
            follow_redirects=True,
            limits=httpx.Limits(max_keepalive_connections=20, max_connections=50),
        )
        self.cleaner = get_html_cleaner()

    @property
    def strategy(self) -> CrawlStrategy:
        return CrawlStrategy.HTTP

    async def crawl(self, url: str, **kwargs: Any) -> CrawlResult:
        """Fetch URL, stream check Content-Type, extract clean markdown and links."""
        start_time = time.time()
        final_url = url
        status_code = 0
        content_type = "text/html"

        try:
            # Scenario 6: Stream request to check Content-Type before downloading large files
            async with self.client.stream("GET", url) as response:
                status_code = response.status_code
                final_url = str(response.url)
                content_type = response.headers.get("content-type", "").lower()

                # If status is not success
                if status_code >= 400:
                    return CrawlResult(
                        url=url,
                        final_url=final_url,
                        status_code=status_code,
                        content_type=content_type,
                        strategy_used=self.strategy,
                        elapsed_seconds=time.time() - start_time,
                        error=f"HTTP {status_code}",
                        confidence="LOW",
                    )

                # Skip non-HTML and binary responses
                if not any(
                    t in content_type for t in ("text/html", "application/xhtml+xml", "text/plain")
                ):
                    logger.info("Skipping non-HTML content-type %s for %s", content_type, url)
                    return CrawlResult(
                        url=url,
                        final_url=final_url,
                        status_code=status_code,
                        content_type=content_type,
                        strategy_used=self.strategy,
                        elapsed_seconds=time.time() - start_time,
                        error=f"Skipped non-HTML Content-Type: {content_type}",
                        confidence="LOW",
                    )

                # Read body content (max 10MB to avoid OOM on huge files)
                body_bytes = await response.aread()

            raw_html = body_bytes.decode(response.encoding or "utf-8", errors="replace")
            raw_size = len(raw_html)

            # Clean and convert to markdown
            markdown, title = self.cleaner.clean_and_convert(raw_html)
            cleaned_size = len(markdown)

            # Extract metadata and links
            metadata = MetadataExtractor.extract(raw_html)
            if not metadata.title and title:
                metadata.title = title

            internal_links, external_links = LinkExtractor.extract_links(raw_html, final_url)

            # Scenario 1: Check if content appears to be a JS-rendered SPA
            confidence = "HIGH"
            if self.cleaner.is_js_rendered_spa(raw_html):
                confidence = "LOW"
                logger.debug("Page %s seems to be a JS SPA requiring browser rendering", url)

            dom_elements = ElementInspector.inspect_html(raw_html)

            return CrawlResult(
                url=url,
                final_url=final_url,
                status_code=status_code,
                content_type=content_type,
                title=metadata.title or title,
                markdown=markdown,
                raw_html_size=raw_size,
                cleaned_markdown_size=cleaned_size,
                metadata=metadata,
                internal_links=internal_links,
                external_links=external_links,
                strategy_used=self.strategy,
                elapsed_seconds=time.time() - start_time,
                confidence=confidence,
                dom_elements=dom_elements,
            )

        except httpx.TimeoutException as te:
            logger.warning("Timeout crawling %s: %s", url, te)
            return CrawlResult(
                url=url,
                final_url=final_url,
                status_code=408,
                content_type=content_type,
                strategy_used=self.strategy,
                elapsed_seconds=time.time() - start_time,
                error=f"Request timeout: {te}",
                confidence="LOW",
            )
        except Exception as exc:
            logger.warning("Error crawling %s: %s", url, exc)
            return CrawlResult(
                url=url,
                final_url=final_url,
                status_code=500,
                content_type=content_type,
                strategy_used=self.strategy,
                elapsed_seconds=time.time() - start_time,
                error=str(exc),
                confidence="LOW",
            )

    async def close(self) -> None:
        if self._owned_client:
            await self.client.aclose()
