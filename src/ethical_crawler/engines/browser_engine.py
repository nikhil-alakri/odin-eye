"""Headless Browser Engine (Playwright).

Provides full JavaScript execution, DOM hydration, scroll-to-load, and screenshot
capabilities for dynamic SPAs and modern web apps.
"""

import asyncio
import logging
import time
from typing import Any

from ethical_crawler.config import get_settings
from ethical_crawler.engines.base import CrawlEngine
from ethical_crawler.extractors.element_inspector import ElementInspector
from ethical_crawler.extractors.html_cleaner import get_html_cleaner
from ethical_crawler.extractors.link_extractor import LinkExtractor
from ethical_crawler.extractors.metadata import MetadataExtractor
from ethical_crawler.rpa.executor import RPAExecutor
from ethical_crawler.rpa.models import RPAStep
from ethical_crawler.rpa.presets import COOKIE_BANNER_DISMISSAL_STEPS
from ethical_crawler.types import CrawlResult, CrawlStrategy

logger = logging.getLogger("ethical_crawler.browser_engine")

try:
    from playwright.async_api import async_playwright

    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False


class BrowserEngine(CrawlEngine):
    """Playwright-powered headless browser engine."""

    def __init__(self, headless: bool | None = None):
        settings = get_settings()
        self.headless = headless if headless is not None else settings.headless_browser
        self.cleaner = get_html_cleaner()
        self._playwright = None
        self._browser = None
        self._lock = asyncio.Lock()

    @property
    def strategy(self) -> CrawlStrategy:
        return CrawlStrategy.BROWSER

    @staticmethod
    def is_supported() -> bool:
        """Check if Playwright is installed."""
        return PLAYWRIGHT_AVAILABLE

    async def _get_browser(self) -> Any:
        """Lazy-initialize Playwright browser instance."""
        if not PLAYWRIGHT_AVAILABLE:
            raise RuntimeError(
                "Playwright is not installed. Install with: pip install 'ethical-crawler[browser]' "
                "&& playwright install chromium"
            )

        async with self._lock:
            if self._browser is None:
                self._playwright = await async_playwright().start()
                self._browser = await self._playwright.chromium.launch(
                    headless=self.headless,
                    args=["--no-sandbox", "--disable-dev-shm-usage"],
                )
            return self._browser

    async def crawl(
        self,
        url: str,
        rpa_steps: list[RPAStep | dict[str, Any]] | None = None,
        auto_dismiss_modals: bool = True,
        **kwargs: Any,
    ) -> CrawlResult:
        """Render page in headless browser, execute RPA interactive steps, and extract data."""
        start_time = time.time()
        settings = get_settings()

        if not PLAYWRIGHT_AVAILABLE:
            return CrawlResult(
                url=url,
                final_url=url,
                status_code=501,
                strategy_used=self.strategy,
                elapsed_seconds=time.time() - start_time,
                error="Playwright not installed. Run 'make install-browser' to enable JS rendering.",
                confidence="LOW",
            )

        context = None
        page = None
        try:
            browser = await self._get_browser()
            context = await browser.new_context(
                user_agent=settings.user_agent,
                viewport={"width": 1280, "height": 800},
            )
            page = await context.new_page()

            # Intercept network API calls (fetch, xhr, json)
            captured_api_calls: list[dict[str, Any]] = []
            pending_response_tasks: list[asyncio.Task] = []

            async def _on_response(resp: Any) -> None:
                try:
                    req = resp.request
                    res_type = req.resource_type
                    content_type = resp.headers.get("content-type", "").lower()
                    url_str = resp.url

                    is_api = (
                        res_type in ("fetch", "xhr")
                        or "application/json" in content_type
                        or "application/graphql" in content_type
                        or url_str.split("?")[0].endswith(".json")
                    )
                    if not is_api:
                        return

                    if any(
                        c in content_type
                        for c in ("image/", "font/", "audio/", "video/", "octet-stream")
                    ):
                        return

                    parsed_body: Any = None
                    try:
                        body_bytes = await resp.body()
                        if len(body_bytes) <= 500_000:
                            import json

                            raw_text = body_bytes.decode("utf-8", errors="replace")
                            try:
                                parsed_body = json.loads(raw_text)
                            except Exception:
                                parsed_body = raw_text[:2000]
                    except Exception:
                        pass

                    post_data = None
                    try:
                        post_data = req.post_data
                        if post_data and len(post_data) > 2000:
                            post_data = post_data[:2000] + "... [truncated]"
                    except Exception:
                        pass

                    captured_api_calls.append(
                        {
                            "url": url_str,
                            "method": req.method,
                            "status": resp.status,
                            "resource_type": res_type,
                            "content_type": content_type,
                            "request_data": post_data,
                            "response_data": parsed_body,
                        }
                    )
                except Exception:
                    pass

            def handle_resp_event(resp: Any) -> None:
                t = asyncio.create_task(_on_response(resp))
                pending_response_tasks.append(t)

            page.on("response", handle_resp_event)

            # Navigate to URL
            response = await page.goto(
                url,
                wait_until="domcontentloaded",
                timeout=int(settings.request_timeout * 1000),
            )

            status_code = response.status if response else 200
            final_url = page.url

            # Wait briefly for JavaScript frameworks (React, Vue) to mount
            await page.wait_for_timeout(800)

            # Execute RPA actions (pre-flight modal dismissals and user-defined playbooks)
            rpa_logs: list[str] = []
            executor = RPAExecutor(page)

            if auto_dismiss_modals:
                cookie_res = await executor.execute_playbook(COOKIE_BANNER_DISMISSAL_STEPS)
                rpa_logs.extend(cookie_res.logs)

            if rpa_steps:
                parsed_steps = [
                    step if isinstance(step, RPAStep) else RPAStep(**step) for step in rpa_steps
                ]
                logger.info("Executing %d custom RPA steps on %s...", len(parsed_steps), url)
                custom_res = await executor.execute_playbook(parsed_steps)
                rpa_logs.extend(custom_res.logs)

            # Auto-scroll smoothly through page to trigger lazy-loaded sections, IntersectionObservers, and animated counters
            try:
                await page.evaluate(
                    """async () => {
                        await new Promise((resolve) => {
                            let totalHeight = 0;
                            let distance = 400;
                            let timer = setInterval(() => {
                                let scrollHeight = document.body.scrollHeight;
                                window.scrollBy(0, distance);
                                totalHeight += distance;
                                if (totalHeight >= scrollHeight || totalHeight > 15000) {
                                    clearInterval(timer);
                                    window.scrollTo(0, 0);
                                    resolve();
                                }
                            }, 50);
                        });
                    }"""
                )
            except Exception:
                await page.evaluate("window.scrollBy(0, window.innerHeight)")

            # Wait for animated numbers and dynamic hydration to settle
            await page.wait_for_timeout(1000)

            # Extract fully rendered HTML
            raw_html = await page.content()
            raw_size = len(raw_html)

            # Settle pending network response capture tasks
            if pending_response_tasks:
                await asyncio.gather(*pending_response_tasks, return_exceptions=True)

            # Inspect DOM interactive elements and key content
            dom_elements = ElementInspector.inspect_html(raw_html)

            # Clean and convert to markdown
            markdown, title = self.cleaner.clean_and_convert(raw_html)
            cleaned_size = len(markdown)

            # Extract metadata and links
            metadata = MetadataExtractor.extract(raw_html)
            if not metadata.title and title:
                metadata.title = title

            internal_links, external_links = LinkExtractor.extract_links(raw_html, final_url)

            return CrawlResult(
                url=url,
                final_url=final_url,
                status_code=status_code,
                content_type="text/html",
                title=metadata.title or title,
                markdown=markdown,
                raw_html_size=raw_size,
                cleaned_markdown_size=cleaned_size,
                metadata=metadata,
                internal_links=internal_links,
                external_links=external_links,
                strategy_used=self.strategy,
                elapsed_seconds=time.time() - start_time,
                confidence="HIGH",
                rpa_logs=rpa_logs,
                network_calls=captured_api_calls,
                dom_elements=dom_elements,
            )

        except Exception as exc:
            logger.error("Browser crawl error on %s: %s", url, exc)
            return CrawlResult(
                url=url,
                final_url=url,
                status_code=500,
                strategy_used=self.strategy,
                elapsed_seconds=time.time() - start_time,
                error=f"Browser crawl error: {exc}",
                confidence="LOW",
            )
        finally:
            if page:
                try:
                    await page.close()
                except Exception:
                    pass
            if context:
                try:
                    await context.close()
                except Exception:
                    pass

    async def close(self) -> None:
        """Close browser and stop Playwright."""
        async with self._lock:
            if self._browser:
                try:
                    await self._browser.close()
                except Exception:
                    pass
                self._browser = None
            if self._playwright:
                try:
                    await self._playwright.stop()
                except Exception:
                    pass
                self._playwright = None
