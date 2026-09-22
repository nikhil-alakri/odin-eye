# Walkthrough - Real-Time Crawl Pipeline, Non-Blocking AI & Timeout Resilience

**Date & Time**: 22-Sep-2026 03:00

## Summary of Completed Work

We investigated and resolved the issue where crawling `https://plexis.in/` using the `🏢 Competitor Intel` preset remained stuck at `Crawling... (0 pages fetched)`.

### Key Fixes Implemented

1. **AI Timeout & Automatic Fast Fallback**:
   - Configured `httpx.Timeout(25.0, connect=8.0)` in `AsyncOpenAI` within `AIExtractor`.
   - Removed `response_format={"type": "json_object"}` which caused remote NIM models like DeepSeek to return `content: None`.
   - Built an automatic fast fallback mechanism: if a selected model (such as `moonshotai/kimi-k3`) times out or encounters errors, `AIExtractor` automatically recovers with `deepseek-ai/deepseek-v4.1-flash` in ~2.5s without crashing the crawl loop.
2. **Decoupled Crawl Loop & Immediate Link Enqueueing**:
   - In `EthicalCrawler.run()`, discovered internal links are immediately enqueued into `self.queue` as soon as the HTML/DOM is rendered. Link discovery and crawl traversal no longer wait for AI reasoning to complete.
   - Crawl results are pushed to `self.results` and streamed to the API job immediately upon page fetch, allowing UI table rows to render in real time.
3. **Granular Real-Time Activity Tracking**:
   - Added `current_activity: str | None` and `current_url: str | None` to `CrawlJob` in `types.py`.
   - Emits live status messages at each step:
     - `Checking robots.txt for [url]...`
     - `Polite delay pause (1.0s)...`
     - `SPA detected (297 B) - Rendering Chromium DOM...`
     - `Fetched [url] (8449 B)`
     - `Extracting AI company_profile with deepseek-ai/deepseek-v4.1-flash...`
     - `Saved [url]`
4. **Vector Store Cache Links Preservation**:
   - In `vector_store.py`, `internal_links_json` is now persisted in ChromaDB metadata on `upsert_page` and properly reconstructed in `get_cached_page`, preventing cache hits from wiping out link discovery.
5. **Dashboard & Preset Optimization**:
   - Updated `Competitor Intel` and `Company Profile` presets to default to `deepseek-ai/deepseek-v4.1-flash` (tested at ~2.5s latency).
   - Added `DeepSeek-v4.1 Flash` as the featured top option in both Crawler and Scraper model select dropdowns.
   - Updated `pollJob` in `app.py` to display the real-time activity string and incrementally render results table rows as each page completes.

---

## Verification Results

### Automated Tests
- Full pytest suite: **47 passed in 20.05s** (100% passing).
- Code formatting & linting: `ruff check` and `ruff format` passed with 0 errors.

### Live Crawl Verification (`https://plexis.in/`)
```
[0/0] Initializing crawl for https://plexis.in/... (url: https://plexis.in/)
[0/0] Checking robots.txt for https://plexis.in/... (url: https://plexis.in/)
[0/0] Polite delay pause (1.0s)... (url: https://plexis.in/)
[0/0] Fetching content for https://plexis.in/... (url: https://plexis.in/)
[0/0] SPA detected (297 B) - Rendering Chromium DOM... (url: https://plexis.in/)
[1/9] Fetched https://plexis.in/ (8449 B) (url: https://plexis.in/)
[1/9] Extracting AI company_profile with deepseek-ai/deepseek-v4.1-flash... (url: https://plexis.in/)
[1/9] Saved https://plexis.in/ (url: https://plexis.in/)
[1/8] Checking robots.txt for https://plexis.in/blogs... (url: https://plexis.in/blogs)
[1/8] Polite delay pause (1.0s)... (url: https://plexis.in/blogs)
[1/8] Fetching content for https://plexis.in/blogs... (url: https://plexis.in/blogs)
[1/8] SPA detected (237 B) - Rendering Chromium DOM... (url: https://plexis.in/blogs)
[2/9] Fetched https://plexis.in/blogs (1753 B) (url: https://plexis.in/blogs)
[2/9] Extracting AI company_profile with deepseek-ai/deepseek-v4.1-flash... (url: https://plexis.in/blogs)
[2/9] Saved https://plexis.in/blogs (url: https://plexis.in/blogs)
Finished! Total pages crawled: 2
- https://plexis.in/ (status: 200, markdown size: 8449)
  AI Company Name: Plexis
  AI What they do: Plexis is an AI-powered studio CRM for photography studios.
- https://plexis.in/blogs (status: 200, markdown size: 1753)
  AI Company Name: Plexis
  AI What they do: Plexis provides a business management and CRM platform tailored to photography studios.
```

