# The four ethical crawling rules

Implemented in `src/ethical_crawler/core/` and enforced from `EthicalCrawler`.

## Rule 1 — robots.txt

**Code:** `core/robots.py` (`RobotsParser`)

- Derives `{scheme}://{host}/robots.txt`.
- Parses `User-agent`, `Allow`, `Disallow`, `Crawl-delay`, `Sitemap`.
- Matches the crawler’s User-Agent (and `*`).
- In-memory cache, TTL `CRAWLER_ROBOTS_CACHE_TTL` (default 3600s).
- Missing/malformed files fail open as “no extra restrictions” after fetch attempt.
- Per-request override: `CrawlRequest.respect_robots` / CLI / UI checkbox.

**API/CLI:** `GET /api/v1/robots`, `crawler robots`.

## Rule 2 — politeness delay and rate limits

**Code:** `core/rate_limiter.py` (`RateLimiter`, `DomainLimiter`)

- Default delay `CRAWLER_DEFAULT_DELAY` (2.0s) or robots `Crawl-delay` when stricter.
- Per-domain lock so two workers cannot stampede one host.
- Global `CRAWLER_MAX_CONCURRENCY` and `CRAWLER_PER_DOMAIN_CONCURRENCY` (default 1 per domain).
- HTTP 429: parse `Retry-After` (delta-seconds or HTTP-date).
- Consecutive 5xx: jittered exponential backoff (`backoff_factor`).

Request-level delay can override via `CrawlRequest.delay`.

## Rule 3 — identifiable User-Agent

**Code:** `core/headers.py`, `Settings.user_agent`

Format:

```
{BotName}/{Version} (+{DocumentationURL}; {ContactEmail})
```

Defaults from `CRAWLER_BOT_*`. Default headers also send `DNT: 1`, a normal `Accept`, and gzip-friendly encoding.

**Health:** `GET /health` returns `bot_user_agent`.

## Rule 4 — sitemaps

**Code:** `core/sitemap.py` (`SitemapParser`)

- Default `https://{host}/sitemap.xml` plus sitemaps listed in robots.txt.
- Recurses `sitemapindex`.
- `urlset` entries: `loc`, `lastmod`, `changefreq`, `priority`.
- Gzip `.xml.gz` and gzipped bodies via `defusedxml`.

**Modes:**

- Discovery helper: `crawler sitemap` / `GET /api/v1/sitemap`.
- Crawl from sitemap: `use_sitemap=True` / `--sitemap` / dashboard “Sitemap Mode” — seed queue from sitemap URLs instead of only following links.

## Extra safety (not numbered rules)

In `EthicalCrawler` / engines / `link_extractor`:

- Same-site (or `allowed_domains`) only.
- Strip tracking query params and fragments; URL dedupe.
- `max_pages` and `max_depth` caps.
- Skip non-HTML / huge binaries via Content-Type before downloading bodies (HTTP engine).
