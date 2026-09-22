# Architecture

## Surfaces

```
┌─────────────┐     ┌──────────────┐     ┌─────────────────────┐
│  ./crawler  │     │ FastAPI app  │     │ Browser dashboard   │
│  Typer CLI  │     │ api/app.py   │     │ GET /  (HTML+JS)    │
└──────┬──────┘     └──────┬───────┘     └──────────┬──────────┘
       │                   │                        │
       │                   │  /api/v1/*             │ fetch()
       └─────────┬─────────┴────────────────────────┘
                 ▼
        EthicalCrawler.run()
                 │
     ┌───────────┼───────────┐
     ▼           ▼           ▼
 RobotsParser  RateLimiter  SitemapParser
     │           │
     ▼           ▼
 HTTPEngine  BrowserEngine (+ RPA)
     │
     ▼
 HTMLCleaner / Metadata / Links / optional AIExtractor
     │
     ▼
 VectorStoreManager (Chroma, cosine, upsert)
     │
     ▼
 StorageExporter (pdf/md/txt/json/csv/sqlite)
```

## Crawl job lifecycle (HTTP)

1. `POST /api/v1/crawl` creates a `CrawlJob` in **in-memory** `_JOBS_STORE` and returns `job_id` (HTTP 202).
2. Background task runs `EthicalCrawler` with a progress callback that updates `pages_crawled`, `current_activity`, `current_url`, and `results`.
3. UI polls `GET /api/v1/jobs/{job_id}`.
4. Pages are upserted into Chroma as they succeed (same path as CLI).

Jobs **do not survive process restart**. Chroma pages **do**.

## Engine strategy

`CrawlStrategy`: `http` | `browser` | `auto` (`types.py`).

- **http** — `HTTPEngine` only.
- **browser** — Playwright; used for SPAs, RPA steps, network/XHR capture.
- **auto** — HTTP first; escalate when the cleaner thinks the page is a JS shell (empty root / placeholders), if `CRAWLER_ENABLE_BROWSER_FALLBACK` is true.

Per-page `CrawlResult.strategy_used` records what actually ran.

## Progress callbacks

`EthicalCrawler._notify_progress` inspects the callback arity so CLI (3 args), older UI (4), and live dashboard (5: result, count, total, activity, current_url) all work.

## AI path

If `extract_ai` is set (or an API key exists), `AIExtractor` runs against cleaned markdown. Default provider base URL is NVIDIA NIM (`https://integrate.api.nvidia.com/v1`). Failures can fall through `FALLBACK_MODEL_CHAIN` in `ai_extractor.py` and `dossier_generator.py`.

Schemas: `article`, `product`, `faq`, `company_profile`, `custom`.

## Knowledge path

- **Cache hit:** `get_cached_page(url, max_age_days)` can skip the network (default TTL 7 days).
- **Upsert:** same URL id is reused; `revision_count` increments; `growth_delta_bytes` tracks size change. Not a destructive replace of history metadata.
- **Search:** Chroma query + cosine distance → similarity.
- **Ask:** retrieve snippets, then LLM answers only from that context (`POST /api/v1/ask`).
- **Dossier:** pull markdown per domain from Chroma, synthesize with a long-context model (`POST /api/v1/dossier/generate`).

## Dashboard

The entire UI is one HTML document inside `DASHBOARD_HTML` in `api/app.py` (Tailwind CDN, Inter, Font Awesome). Tabs: Website Crawler, Single Page Scraper, Knowledge & History. See [dashboard-ui.md](dashboard-ui.md).
