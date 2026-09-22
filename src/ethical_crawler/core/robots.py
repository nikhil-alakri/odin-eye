"""Ethical Rule #1: Robots.txt Parser, Cache, and Validator.

Fetches, parses, and caches robots.txt directives for domains, respecting
Allow, Disallow, Crawl-delay, and discovering linked Sitemap XML files.
"""

import asyncio
import logging
import re
import time
from urllib.parse import urlparse

import httpx

from ethical_crawler.config import get_settings
from ethical_crawler.types import RobotsDirectives

logger = logging.getLogger("ethical_crawler.robots")


class RobotsEntry:
    """Parsed rule set for a specific user-agent."""

    def __init__(self, user_agent: str):
        self.user_agent = user_agent.lower()
        self.allow_patterns: list[str] = []
        self.disallow_patterns: list[str] = []
        self.crawl_delay: float | None = None

    def matches_agent(self, target_agent: str) -> bool:
        """Check if this entry applies to target user-agent."""
        target = target_agent.lower()
        return self.user_agent == "*" or self.user_agent in target


class RobotsParser:
    """Async robots.txt fetcher, parser, and in-memory cache."""

    def __init__(self, cache_ttl: int | None = None):
        settings = get_settings()
        self.cache_ttl = cache_ttl or settings.robots_cache_ttl
        self._cache: dict[str, tuple[float, RobotsDirectives, list[RobotsEntry]]] = {}
        self._lock = asyncio.Lock()

    @staticmethod
    def get_robots_url(target_url: str) -> str:
        """Derive the robots.txt URL from any URL."""
        parsed = urlparse(target_url)
        scheme = parsed.scheme or "https"
        netloc = parsed.netloc
        return f"{scheme}://{netloc}/robots.txt"

    @staticmethod
    def extract_domain(target_url: str) -> str:
        """Extract netloc/domain for caching."""
        parsed = urlparse(target_url)
        return parsed.netloc.lower()

    async def get_directives(
        self,
        target_url: str,
        client: httpx.AsyncClient | None = None,
        user_agent: str | None = None,
    ) -> RobotsDirectives:
        """Fetch or retrieve cached robots.txt directives for target domain."""
        domain = self.extract_domain(target_url)
        robots_url = self.get_robots_url(target_url)
        settings = get_settings()
        agent = user_agent or settings.user_agent

        async with self._lock:
            if domain in self._cache:
                timestamp, cached_dir, _ = self._cache[domain]
                if time.time() - timestamp < self.cache_ttl:
                    return cached_dir

        # Fetch from web
        directives, entries = await self._fetch_and_parse(robots_url, domain, agent, client)

        async with self._lock:
            self._cache[domain] = (time.time(), directives, entries)

        return directives

    async def can_fetch(
        self,
        target_url: str,
        user_agent: str | None = None,
        client: httpx.AsyncClient | None = None,
    ) -> bool:
        """Check if target_url is allowed to be crawled according to robots.txt."""
        settings = get_settings()
        if not settings.respect_robots_txt:
            return True

        domain = self.extract_domain(target_url)
        agent = user_agent or settings.user_agent

        # Ensure we have parsed rules
        async with self._lock:
            cached = self._cache.get(domain)

        if cached and (time.time() - cached[0] < self.cache_ttl):
            _, directives, entries = cached
        else:
            directives = await self.get_directives(target_url, client, agent)
            async with self._lock:
                _, _, entries = self._cache.get(domain, (0, directives, []))

        parsed_url = urlparse(target_url)
        path = parsed_url.path or "/"
        if parsed_url.query:
            path = f"{path}?{parsed_url.query}"

        # Find best matching entry for user agent
        matched_entry = self._find_best_entry(entries, agent)
        if not matched_entry:
            return True

        # Check explicit Allow rules first
        for pattern in matched_entry.allow_patterns:
            if self._path_matches(pattern, path):
                return True

        # Check Disallow rules
        for pattern in matched_entry.disallow_patterns:
            if self._path_matches(pattern, path):
                logger.info("Blocked by robots.txt: %s (pattern: %s)", target_url, pattern)
                return False

        return True

    async def get_crawl_delay(
        self,
        target_url: str,
        user_agent: str | None = None,
        client: httpx.AsyncClient | None = None,
    ) -> float | None:
        """Get declared Crawl-delay for user-agent, if any."""
        directives = await self.get_directives(target_url, client, user_agent)
        return directives.crawl_delay

    async def _fetch_and_parse(
        self,
        robots_url: str,
        domain: str,
        user_agent: str,
        client: httpx.AsyncClient | None,
    ) -> tuple[RobotsDirectives, list[RobotsEntry]]:
        """Fetch robots.txt and parse its rules."""
        raw_text = ""
        status_code = 200
        should_close = False

        if client is None:
            client = httpx.AsyncClient(
                headers={"User-Agent": user_agent}, timeout=10.0, follow_redirects=True
            )
            should_close = True

        try:
            resp = await client.get(robots_url)
            status_code = resp.status_code
            if resp.status_code == 200:
                raw_text = resp.text
            elif resp.status_code in (404, 410):
                # Scenario: 404 Not Found means no robots.txt restrictions
                logger.debug(
                    "No robots.txt found for %s (status %s), defaulting to allow",
                    domain,
                    resp.status_code,
                )
                raw_text = ""
            else:
                logger.warning(
                    "Robots.txt fetch returned status %s for %s", resp.status_code, domain
                )
        except Exception as exc:
            logger.warning("Could not fetch robots.txt for %s: %s", domain, exc)
            status_code = 500
        finally:
            if should_close:
                await client.aclose()

        entries, sitemaps = self._parse_rules(raw_text, domain)

        # Determine crawl delay for our agent
        matched_entry = self._find_best_entry(entries, user_agent)
        crawl_delay = matched_entry.crawl_delay if matched_entry else None

        directives = RobotsDirectives(
            domain=domain,
            robots_url=robots_url,
            can_fetch=True,
            crawl_delay=crawl_delay,
            sitemaps=sitemaps,
            user_agent_used=user_agent,
            status_code=status_code,
            raw_rules=raw_text[:2000],
        )

        return directives, entries

    def _parse_rules(self, text: str, base_domain: str) -> tuple[list[RobotsEntry], list[str]]:
        """Parse raw robots.txt lines into structured entries and sitemap URLs."""
        entries: list[RobotsEntry] = []
        sitemaps: list[str] = []
        current_agents: list[str] = []
        current_entry_map: dict[str, RobotsEntry] = {}

        for line in text.splitlines():
            line = line.strip()
            # Strip comments
            if "#" in line:
                line = line[: line.index("#")].strip()
            if not line or ":" not in line:
                continue

            field, _, val = line.partition(":")
            field = field.strip().lower()
            val = val.strip()

            if field == "user-agent":
                if not current_agents or (entries and entries[-1] in current_entry_map.values()):
                    current_agents = []
                agent = val.lower()
                current_agents.append(agent)
                if agent not in current_entry_map:
                    entry = RobotsEntry(agent)
                    current_entry_map[agent] = entry
                    entries.append(entry)

            elif field == "disallow":
                if val:
                    for agent in current_agents:
                        if agent in current_entry_map:
                            current_entry_map[agent].disallow_patterns.append(val)

            elif field == "allow":
                if val:
                    for agent in current_agents:
                        if agent in current_entry_map:
                            current_entry_map[agent].allow_patterns.append(val)

            elif field == "crawl-delay":
                try:
                    delay = float(val)
                    for agent in current_agents:
                        if agent in current_entry_map:
                            current_entry_map[agent].crawl_delay = delay
                except ValueError:
                    pass

            elif field == "sitemap":
                if val.startswith("http"):
                    sitemaps.append(val)
                else:
                    sitemaps.append(f"https://{base_domain}/{val.lstrip('/')}")

        return entries, sitemaps

    def _find_best_entry(self, entries: list[RobotsEntry], target_agent: str) -> RobotsEntry | None:
        """Find the most specific matching entry for a user agent, or wildcard '*'."""
        target = target_agent.lower()
        exact_match = None
        wildcard_match = None

        for entry in entries:
            if entry.user_agent == "*":
                wildcard_match = entry
            elif entry.user_agent in target:
                exact_match = entry

        return exact_match or wildcard_match

    def _path_matches(self, pattern: str, path: str) -> bool:
        """Check if an Allow/Disallow pattern matches path."""
        if not pattern:
            return False

        # Convert robots.txt pattern to regex
        # '*' matches any sequence of characters
        # '$' at end matches end of URL
        escaped = re.escape(pattern).replace(r"\*", ".*")
        if pattern.endswith("$"):
            regex = f"^{escaped}"
        else:
            regex = f"^{escaped}"

        try:
            return bool(re.match(regex, path))
        except re.error:
            return path.startswith(pattern)


# Global singleton parser
_global_robots_parser: RobotsParser | None = None


def get_robots_parser() -> RobotsParser:
    """Get or instantiate global RobotsParser."""
    global _global_robots_parser
    if _global_robots_parser is None:
        _global_robots_parser = RobotsParser()
    return _global_robots_parser
