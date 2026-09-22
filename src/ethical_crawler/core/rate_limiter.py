"""Ethical Rule #2: Polite Rate Limiter & Concurrency Controller.

Ensures the crawler maintains politeness by enforcing per-domain delays,
respecting HTTP 429 Retry-After, exponential backoff, and concurrency caps.
"""

import asyncio
import logging
import random
import time
from contextlib import asynccontextmanager
from email.utils import parsedate_to_datetime
from urllib.parse import urlparse

from ethical_crawler.config import get_settings

logger = logging.getLogger("ethical_crawler.rate_limiter")


class DomainLimiter:
    """Tracks state and enforces delays for an individual domain."""

    def __init__(self, domain: str, default_delay: float):
        self.domain = domain
        self.default_delay = default_delay
        self.last_request_time: float = 0.0
        self.lock = asyncio.Lock()
        self.rate_limited_until: float = 0.0
        self.consecutive_errors: int = 0

    async def acquire(self, required_delay: float | None = None) -> None:
        """Wait until it is polite to make the next request to this domain."""
        async with self.lock:
            now = time.time()

            # Handle active 429 rate limit backoff
            if now < self.rate_limited_until:
                wait_time = self.rate_limited_until - now
                logger.warning(
                    "Domain %s is rate-limited (HTTP 429). Pausing for %.2f seconds.",
                    self.domain,
                    wait_time,
                )
                await asyncio.sleep(wait_time)
                now = time.time()

            # Determine delay: use robots crawl_delay if present, otherwise default_delay
            delay = required_delay if required_delay is not None else self.default_delay

            # If consecutive errors occurred, apply jittered exponential backoff
            if self.consecutive_errors > 0:
                backoff = min(30.0, delay * (1.5**self.consecutive_errors))
                jitter = random.uniform(0.1, 0.5)
                delay = backoff + jitter

            elapsed = now - self.last_request_time
            if elapsed < delay:
                to_wait = delay - elapsed
                logger.debug("Politeness delay for %s: sleeping %.2fs", self.domain, to_wait)
                await asyncio.sleep(to_wait)

            self.last_request_time = time.time()

    def record_success(self) -> None:
        """Reset consecutive error counter on successful request."""
        self.consecutive_errors = 0

    def record_error(self) -> None:
        """Increment consecutive errors for backoff calculation."""
        self.consecutive_errors += 1

    def handle_rate_limit(self, retry_after: str | None = None) -> float:
        """Process HTTP 429 response and compute pause duration."""
        self.consecutive_errors += 1
        wait_seconds = 10.0  # default 429 backoff

        if retry_after:
            retry_after = retry_after.strip()
            # Check if it is an integer/float in seconds
            try:
                wait_seconds = float(retry_after)
            except ValueError:
                # Might be an HTTP-date
                try:
                    target_dt = parsedate_to_datetime(retry_after)
                    wait_seconds = max(1.0, target_dt.timestamp() - time.time())
                except Exception:
                    wait_seconds = 15.0

        # Cap wait between 1s and 120s
        wait_seconds = max(1.0, min(120.0, wait_seconds))
        self.rate_limited_until = time.time() + wait_seconds
        logger.warning("Applied 429 backoff for %s: %.1f seconds", self.domain, wait_seconds)
        return wait_seconds


class RateLimiter:
    """Global and per-domain rate limiter."""

    def __init__(
        self,
        default_delay: float | None = None,
        max_concurrency: int | None = None,
        per_domain_concurrency: int | None = None,
    ):
        settings = get_settings()
        self.default_delay = default_delay or settings.default_delay
        self.global_semaphore = asyncio.Semaphore(max_concurrency or settings.max_concurrency)
        self.per_domain_concurrency = per_domain_concurrency or settings.per_domain_concurrency
        self.domain_semaphores: dict[str, asyncio.Semaphore] = {}
        self.domains: dict[str, DomainLimiter] = {}
        self._lock = asyncio.Lock()

    @staticmethod
    def extract_domain(url: str) -> str:
        """Extract domain netloc for rate limit grouping."""
        parsed = urlparse(url)
        return parsed.netloc.lower()

    async def _get_domain_limiter(self, domain: str) -> tuple[DomainLimiter, asyncio.Semaphore]:
        """Retrieve or create domain limiter and domain-scoped concurrency semaphore."""
        async with self._lock:
            if domain not in self.domains:
                self.domains[domain] = DomainLimiter(domain, self.default_delay)
                self.domain_semaphores[domain] = asyncio.Semaphore(self.per_domain_concurrency)
            return self.domains[domain], self.domain_semaphores[domain]

    @asynccontextmanager
    async def throttle(self, url: str, crawl_delay: float | None = None):
        """Async context manager throttling requests according to politeness rules."""
        domain = self.extract_domain(url)
        domain_limiter, domain_sem = await self._get_domain_limiter(domain)

        # 1. Acquire global concurrency slot
        async with self.global_semaphore:
            # 2. Acquire domain concurrency slot
            async with domain_sem:
                # 3. Enforce politeness delay
                await domain_limiter.acquire(required_delay=crawl_delay)
                try:
                    yield domain_limiter
                except Exception:
                    domain_limiter.record_error()
                    raise

    async def record_response(
        self, url: str, status_code: int, retry_after: str | None = None
    ) -> None:
        """Update domain rate limit statistics based on HTTP response status."""
        domain = self.extract_domain(url)
        domain_limiter, _ = await self._get_domain_limiter(domain)

        if status_code == 429:
            domain_limiter.handle_rate_limit(retry_after)
        elif 200 <= status_code < 400:
            domain_limiter.record_success()
        elif status_code >= 500:
            domain_limiter.record_error()


# Global singleton rate limiter
_global_rate_limiter: RateLimiter | None = None


def get_rate_limiter() -> RateLimiter:
    """Get or instantiate global RateLimiter."""
    global _global_rate_limiter
    if _global_rate_limiter is None:
        _global_rate_limiter = RateLimiter()
    return _global_rate_limiter
