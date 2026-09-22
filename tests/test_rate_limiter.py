"""Tests for Ethical Rule 2: Rate limiting, politeness delays, and 429 backoff."""

import time

import pytest

from ethical_crawler.core.rate_limiter import DomainLimiter, RateLimiter


@pytest.mark.asyncio
async def test_domain_limiter_delay():
    limiter = DomainLimiter("test.com", default_delay=0.1)

    await limiter.acquire()
    t1 = time.time()

    # Second acquire must wait ~0.1s
    await limiter.acquire()
    t2 = time.time()

    assert (t2 - t1) >= 0.08  # Tolerates minor clock jitter


@pytest.mark.asyncio
async def test_rate_limiter_throttle_context():
    rate_limiter = RateLimiter(default_delay=0.05, max_concurrency=2)

    async with rate_limiter.throttle("https://example.com/page1"):
        pass

    async with rate_limiter.throttle("https://example.com/page2"):
        pass


@pytest.mark.asyncio
async def test_429_retry_after_handling():
    """Scenario 4: Handling HTTP 429 Retry-After header."""
    limiter = DomainLimiter("busy-server.org", default_delay=0.1)

    # Simulate integer seconds
    wait_time = limiter.handle_rate_limit("5")
    assert wait_time == 5.0
    assert limiter.rate_limited_until > time.time() + 4.0

    # Reset
    limiter.rate_limited_until = 0.0
    limiter.record_success()
    assert limiter.consecutive_errors == 0
