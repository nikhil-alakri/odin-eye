# Configuration

Settings class: `ethical_crawler.config.Settings`  
Load: `.env` file + environment, prefix **`CRAWLER_`**, extra keys ignored.

Copy `.env.example` → `.env`. Never commit `.env`.

## Variables

| Variable | Default | Meaning |
|----------|---------|---------|
| `CRAWLER_BOT_NAME` | EthicalCrawlerBot | UA name |
| `CRAWLER_BOT_VERSION` | 1.0.0 | UA version (`GET /health` uses this) |
| `CRAWLER_BOT_URL` | example GitHub URL | UA documentation URL |
| `CRAWLER_BOT_EMAIL` | crawler-contact@example.com | UA contact |
| `CRAWLER_DEFAULT_DELAY` | 2.0 | Seconds between hits to one domain |
| `CRAWLER_MAX_CONCURRENCY` | 5 | Global in-flight fetches |
| `CRAWLER_PER_DOMAIN_CONCURRENCY` | 1 | Per-host in-flight (settings field; not always in `.env.example`) |
| `CRAWLER_MAX_DEPTH` | 3 | Default max depth |
| `CRAWLER_MAX_PAGES` | 50 | Default max pages |
| `CRAWLER_REQUEST_TIMEOUT` | 15.0 | HTTP timeout seconds |
| `CRAWLER_MAX_RETRIES` | 3 | Transient retry count |
| `CRAWLER_BACKOFF_FACTOR` | 1.5 | Error backoff multiplier |
| `CRAWLER_RESPECT_ROBOTS_TXT` | true | Global robots enforcement |
| `CRAWLER_ROBOTS_CACHE_TTL` | 3600 | robots.txt memory cache |
| `CRAWLER_AUTO_DISCOVER_SITEMAP` | true | Sitemap discovery default |
| `CRAWLER_ENABLE_BROWSER_FALLBACK` | true | auto strategy may use Playwright |
| `CRAWLER_HEADLESS_BROWSER` | true | Headless Chromium |
| `CRAWLER_AI_BASE_URL` | NVIDIA NIM v1 | OpenAI-compatible base |
| `CRAWLER_AI_API_KEY` | empty | Required for extract/ask/dossier/RPA generate |
| `CRAWLER_AI_MODEL` | meta/llama-3.2-11b-vision-instruct | Default chat model |
| `CRAWLER_API_HOST` | 0.0.0.0 | Documented server host |
| `CRAWLER_API_PORT` | 8000 | Documented server port |
| `CRAWLER_CHROMA_DIR` | data/chroma | Persist path |
| `CRAWLER_ENABLE_CACHE` | true | Lookup cache before fetch |
| `CRAWLER_CACHE_TTL_DAYS` | 7 | Freshness window |
| `CRAWLER_CHROMA_COLLECTION` | crawled_knowledge | Collection name |

RPA `secret_env` on a step can pull a password from **another** env var name at execution time — keep those out of git as well.

## Optional extras

```bash
pip install -e ".[browser]"   # playwright
playwright install chromium
pip install -e ".[dev]"       # pytest, ruff
```

Python: **≥ 3.11** (classified 3.11/3.12). Ruff target `py312`.
