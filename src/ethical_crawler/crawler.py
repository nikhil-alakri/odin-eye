"""Main Crawler Orchestrator.

Manages link queues, applies the 4 ethical crawling rules, handles auto-escalation
from HTTP to Browser, deduplicates URLs, and aggregates crawl results.
"""

import logging
from collections import deque
from collections.abc import Callable
from urllib.parse import urlparse

from ethical_crawler.config import get_settings
from ethical_crawler.core.rate_limiter import get_rate_limiter
from ethical_crawler.core.robots import get_robots_parser
from ethical_crawler.core.sitemap import get_sitemap_parser
from ethical_crawler.engines.browser_engine import BrowserEngine
from ethical_crawler.engines.http_engine import HTTPEngine
from ethical_crawler.extractors.ai_extractor import AIExtractor
from ethical_crawler.extractors.link_extractor import LinkExtractor
from ethical_crawler.types import (
    CrawlRequest,
    CrawlResult,
    CrawlStrategy,
)
from ethical_crawler.vector_store import get_vector_store

logger = logging.getLogger("ethical_crawler.crawler")


class EthicalCrawler:
    """Async crawler enforcing ethical standards and multi-engine execution."""

    def __init__(
        self,
        request: CrawlRequest,
        on_progress: Callable[[CrawlResult, int, int], None] | None = None,
    ):
        self.request = request
        self.settings = get_settings()
        self.on_progress = on_progress

        self.robots_parser = get_robots_parser()
        self.rate_limiter = get_rate_limiter()
        self.sitemap_parser = get_sitemap_parser()

        # Engines
        self.http_engine = HTTPEngine()
        self.browser_engine = BrowserEngine(headless=self.settings.headless_browser)

        # AI Extractor
        self.ai_extractor = (
            AIExtractor(model=self.request.ai_model)
            if (self.request.extract_ai or self.settings.ai_api_key)
            else None
        )

        # State
        self.visited_urls: set[str] = set()
        self.queue: deque[tuple[str, int]] = deque()
        self.results: list[CrawlResult] = []
        self.errors: list[str] = []

        # Domains allowed
        base_domain = urlparse(request.url).netloc.lower()
        self.allowed_domains = {base_domain}
        if request.allowed_domains:
            self.allowed_domains.update(d.lower() for d in request.allowed_domains)

    def _notify_progress(
        self,
        result: CrawlResult | None = None,
        activity: str = "",
        current_url: str | None = None,
    ) -> None:
        """Helper to invoke on_progress callback safely with granular activity."""
        if not self.on_progress:
            return
        current_count = len(self.results)
        total_discovered = len(self.queue) + len(self.results)
        try:
            import inspect

            sig = inspect.signature(self.on_progress)
            param_count = len(sig.parameters)
            if param_count >= 5:
                self.on_progress(result, current_count, total_discovered, activity, current_url)
            elif param_count >= 4:
                self.on_progress(result, current_count, total_discovered, activity)
            elif result is not None:
                self.on_progress(result, current_count, total_discovered)
        except Exception as cb_err:
            logger.debug("Progress callback error: %s", cb_err)

    async def run(self) -> list[CrawlResult]:
        """Execute the crawl according to the request parameters."""
        logger.info(
            "Starting crawl for %s (max_pages=%s, max_depth=%s)",
            self.request.url,
            self.request.max_pages,
            self.request.max_depth,
        )
        self._notify_progress(
            activity=f"Initializing crawl for {self.request.url}...",
            current_url=self.request.url,
        )

        # Rule 4: Check if Sitemap mode requested or should discover sitemap
        if self.request.use_sitemap:
            sitemap_target = (
                self.request.url
                if self.request.url.endswith(".xml") or self.request.url.endswith(".xml.gz")
                else self.sitemap_parser.get_default_sitemap_url(self.request.url)
            )
            logger.info("Extracting URLs from sitemap: %s", sitemap_target)
            self._notify_progress(
                activity=f"Discovering sitemap: {sitemap_target}...",
                current_url=sitemap_target,
            )
            sitemap_res = await self.sitemap_parser.fetch_and_parse(sitemap_target)
            if sitemap_res.urls:
                for sm_url in sitemap_res.urls[: self.request.max_pages]:
                    normalized = LinkExtractor.normalize_url(sm_url.loc)
                    if normalized not in self.visited_urls:
                        self.queue.append((normalized, 0))
            else:
                logger.info("No URLs found in sitemap, falling back to seed URL.")
                self.queue.append((LinkExtractor.normalize_url(self.request.url), 0))
        else:
            # Seed URL
            self.queue.append((LinkExtractor.normalize_url(self.request.url), 0))

        # BFS Crawl loop
        while self.queue and len(self.results) < self.request.max_pages:
            current_url, current_depth = self.queue.popleft()

            if current_url in self.visited_urls:
                continue

            # Check domain allowance
            current_domain = urlparse(current_url).netloc.lower()
            if not any(
                current_domain == d or current_domain.endswith(f".{d}")
                for d in self.allowed_domains
            ):
                continue

            self.visited_urls.add(current_url)

            # Check local vector store cache if enabled ("Don't crawl again")
            vector_store = get_vector_store()
            cached_item = None
            if self.request.use_cache and self.settings.enable_cache:
                cached_item = vector_store.get_cached_page(
                    current_url, max_age_days=self.request.cache_ttl_days
                )

            if cached_item:
                result, cached_ai_data = cached_item
                result.ai_data = cached_ai_data
                logger.info("Cache hit for %s (0 network requests)", current_url)

                # Enqueue internal links immediately
                if not self.request.use_sitemap and current_depth < self.request.max_depth:
                    for link in result.internal_links:
                        if link not in self.visited_urls:
                            self.queue.append((link, current_depth + 1))

                self.results.append(result)
                self._notify_progress(
                    result=result,
                    activity=f"⚡ Vector Cache hit for {current_url}",
                    current_url=current_url,
                )

                # If user requested AI extraction and cached result doesn't have it yet
                if (
                    self.request.extract_ai
                    and not result.ai_data
                    and self.ai_extractor
                    and self.ai_extractor.is_available()
                ):
                    self._notify_progress(
                        result=result,
                        activity=f"Extracting AI {self.request.ai_schema} with {self.ai_extractor.model}...",
                        current_url=current_url,
                    )
                    try:
                        ai_res = await self.ai_extractor.extract_structured(
                            markdown=result.markdown,
                            url=result.url,
                            schema_type=self.request.ai_schema or "article",
                            custom_prompt=self.request.ai_prompt,
                        )
                        result.ai_data = ai_res.data
                        result.ai_model_used = ai_res.model_used
                        vector_store.upsert_page(result, ai_data=result.ai_data)
                        activity_msg = (
                            f"Extracted with fallback {ai_res.model_used} for {current_url}"
                            if ai_res.model_used != self.ai_extractor.model
                            else f"Saved AI data for {current_url}"
                        )
                        self._notify_progress(
                            result=result,
                            activity=activity_msg,
                            current_url=current_url,
                        )
                    except Exception as ai_err:
                        logger.warning(
                            "AI extraction failed for cached %s: %s", current_url, ai_err
                        )
            else:
                # Rule 1: Check robots.txt permissions
                if self.request.respect_robots:
                    self._notify_progress(
                        activity=f"Checking robots.txt for {current_url}...",
                        current_url=current_url,
                    )
                    can_crawl = await self.robots_parser.can_fetch(
                        current_url, self.settings.user_agent
                    )
                    if not can_crawl:
                        logger.warning("Skipping %s (Disallowed by robots.txt)", current_url)
                        self.errors.append(f"Disallowed by robots.txt: {current_url}")
                        continue

                # Determine crawl delay (Rule 2)
                crawl_delay = self.request.delay
                if crawl_delay is None and self.request.respect_robots:
                    crawl_delay = await self.robots_parser.get_crawl_delay(
                        current_url, self.settings.user_agent
                    )

                # Rule 2: Polite Rate Limiting & Concurrency Throttling
                try:
                    if crawl_delay and crawl_delay > 0:
                        self._notify_progress(
                            activity=f"Polite delay pause ({crawl_delay:.1f}s)...",
                            current_url=current_url,
                        )
                    async with self.rate_limiter.throttle(current_url, crawl_delay):
                        self._notify_progress(
                            activity=f"Fetching content for {current_url}...",
                            current_url=current_url,
                        )
                        result = await self._crawl_page(current_url)

                    # Record response in rate limiter for 429 detection
                    await self.rate_limiter.record_response(current_url, result.status_code)

                except Exception as exc:
                    logger.error("Failed to crawl %s: %s", current_url, exc)
                    self.errors.append(f"Error on {current_url}: {exc}")
                    continue

                # Enqueue discovered internal links immediately so crawler is never stalled
                if not self.request.use_sitemap and current_depth < self.request.max_depth:
                    for link in result.internal_links:
                        if link not in self.visited_urls:
                            self.queue.append((link, current_depth + 1))

                # Immediately append result and notify UI so page appears without waiting for AI
                self.results.append(result)
                self._notify_progress(
                    result=result,
                    activity=f"Fetched {current_url} ({result.cleaned_markdown_size} B)",
                    current_url=current_url,
                )

                # Run AI extraction if requested and page was fetched successfully
                if (
                    result.status_code == 200
                    and self.request.extract_ai
                    and self.ai_extractor
                    and self.ai_extractor.is_available()
                ):
                    self._notify_progress(
                        result=result,
                        activity=f"Extracting AI {self.request.ai_schema} with {self.ai_extractor.model}...",
                        current_url=current_url,
                    )
                    try:
                        ai_res = await self.ai_extractor.extract_structured(
                            markdown=result.markdown,
                            url=result.url,
                            schema_type=self.request.ai_schema or "article",
                            custom_prompt=self.request.ai_prompt,
                        )
                        result.ai_data = ai_res.data
                        result.ai_model_used = ai_res.model_used
                    except Exception as ai_err:
                        logger.warning("AI extraction failed for %s: %s", current_url, ai_err)

                # Auto-save to ChromaDB vector store if fetched successfully
                if result.status_code == 200:
                    try:
                        vector_store.upsert_page(result, ai_data=result.ai_data)
                    except Exception as store_err:
                        logger.debug("Failed to store vector embedding: %s", store_err)

                activity_msg = (
                    f"Extracted with fallback {result.ai_model_used} for {current_url}"
                    if (
                        result.ai_model_used
                        and self.ai_extractor
                        and result.ai_model_used != self.ai_extractor.model
                    )
                    else f"Saved {current_url}"
                )
                self._notify_progress(
                    result=result,
                    activity=activity_msg,
                    current_url=current_url,
                )

        await self.close()
        logger.info("Crawl finished. Crawled %s pages.", len(self.results))
        return self.results

    async def _crawl_page(self, url: str) -> CrawlResult:
        """Crawl a single page with strategy selection and auto-escalation."""
        strategy = self.request.strategy

        has_rpa = bool(self.request.rpa_steps)
        if strategy == CrawlStrategy.BROWSER or has_rpa:
            act_msg = (
                f"Executing RPA on {url} with Chromium Headless..."
                if has_rpa
                else f"Rendering {url} with Chromium Headless..."
            )
            self._notify_progress(
                activity=act_msg,
                current_url=url,
            )
            return await self.browser_engine.crawl(
                url,
                rpa_steps=self.request.rpa_steps,
                auto_dismiss_modals=self.request.auto_dismiss_modals,
                capture_screenshot=self.request.capture_screenshot,
            )

        # Default HTTP strategy
        http_result = await self.http_engine.crawl(url)

        # Scenario 1: Auto-escalation if page is JS SPA or low content and browser fallback is enabled
        if strategy == CrawlStrategy.AUTO and self.settings.enable_browser_fallback:
            should_escalate = (
                http_result.confidence == "LOW" or http_result.cleaned_markdown_size < 150
            )
            if should_escalate and BrowserEngine.is_supported():
                self._notify_progress(
                    activity=f"SPA detected ({http_result.cleaned_markdown_size} B) - Rendering Chromium DOM...",
                    current_url=url,
                )
                logger.info(
                    "Auto-escalating %s to Browser Engine (SPA or sparse content detected)", url
                )
                browser_result = await self.browser_engine.crawl(
                    url,
                    rpa_steps=self.request.rpa_steps,
                    auto_dismiss_modals=self.request.auto_dismiss_modals,
                    capture_screenshot=self.request.capture_screenshot,
                )
                # If browser succeeded with better content, use it
                if (
                    browser_result.status_code == 200
                    and browser_result.cleaned_markdown_size > http_result.cleaned_markdown_size
                ):
                    return browser_result

        return http_result

    async def close(self) -> None:
        """Clean up engines and HTTP clients."""
        await self.http_engine.close()
        await self.browser_engine.close()
