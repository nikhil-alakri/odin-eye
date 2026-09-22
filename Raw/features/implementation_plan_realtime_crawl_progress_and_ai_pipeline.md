# Implementation Plan - Real-Time Crawl Pipeline, Non-Blocking AI & Timeout Resilience

**Date & Time**: 22-Sep-2026 02:52

## Problem Statement & Root Cause Analysis

When crawling `https://plexis.in/` using the `🏢 Competitor Intel` preset, the user reported:
> *"I can see 0 page fetched since 1 min"* with the dashboard remaining stuck at `Crawling... (0 pages fetched)`.

Through live diagnostics and empirical benchmarking against the target site and NVIDIA NIM API, we uncovered four distinct root causes:

1. **Synchronous AI Extraction Inside Crawl Loop**:
   In `src/ethical_crawler/crawler.py` (lines 180–197), AI extraction was executed synchronously inline inside the page crawl loop before link enqueueing, before updating `job.results`, and before invoking `self.on_progress`.
2. **Missing Timeouts & NVIDIA NIM Endpoint Stalls**:
   `AsyncOpenAI` in `AIExtractor` had no client-level timeout (defaulting to httpx's 10-minute wait). NVIDIA's hosted endpoint for `moonshotai/kimi-k3` is currently timing out / queued (>60s). Furthermore, passing `response_format={"type": "json_object"}` to NIM causes some models (like DeepSeek-v4.1) to return `content: None`.
3. **Opaque Progress State in UI & Router**:
   `CrawlJob` in `types.py` only contained `pages_crawled` and `pages_discovered`. It lacked `current_activity` (e.g., *"Rendering JavaScript DOM via Chromium..."*, *"Extracting AI Company Profile..."*) and `current_url`. The frontend polling in `app.py` only rendered results when `job.status === 'completed'`, leaving the results table completely blank for minutes during multi-page crawls.
4. **ChromaDB Vector Cache Internal Links Gap**:
   In `src/ethical_crawler/vector_store.py`, `get_cached_page` reconstructed cached pages with `internal_links: []`. When `use_cache=True`, a cache hit on the seed URL resulted in 0 links discovered, halting the crawl immediately.

---

## User Review Required

> [!IMPORTANT]
> - **Preset Default Model Optimization**: For `🏢 Competitor Intel`, we recommend changing the default model from `moonshotai/kimi-k3` (which is currently timing out on NVIDIA NIM) to `deepseek-ai/deepseek-v4.1-flash` (tested at ~2.5s response with outstanding structured extraction quality) or `nvidia/nemotron-3.5-lightning-30b-a3b`, while keeping `moonshotai/kimi-k3` available in the dropdown with a 25s timeout and automatic fallback.
> - **ChromaDB Safety**: All ChromaDB changes are non-destructive and preserve existing collections and documents.

---

## Proposed Changes

### 1. Type Definitions & Granular Job State
#### [MODIFY] [types.py](file:///Users/nikhilalakri/Developer/web-crawler/src/ethical_crawler/types.py)
- Add `current_activity: str | None = None` and `current_url: str | None = None` to `CrawlJob`.
- Ensure incremental status updates are serializable and reflect real-time crawler states.

---

### 2. Robust AI Extractor with Timeouts & Model Fallback
#### [MODIFY] [ai_extractor.py](file:///Users/nikhilalakri/Developer/web-crawler/src/ethical_crawler/extractors/ai_extractor.py)
- Set strict client and call timeouts (25 seconds) using `httpx.Timeout(25.0, connect=8.0)`.
- Avoid sending `response_format={"type": "json_object"}` to models that return `content: None` when it is present (e.g. DeepSeek, Kimi). Use strict system prompt instruction + resilient regex JSON cleaning via `_clean_and_parse_json`.
- Add an automatic fallback mechanism: if the selected model (e.g., Kimi-k3) times out after 25s, attempt a fast recovery with `deepseek-ai/deepseek-v4.1-flash` or gracefully return a partial result with a descriptive note rather than freezing the crawl loop.

---

### 3. Pipeline Decoupling & Immediate Link Enqueueing
#### [MODIFY] [crawler.py](file:///Users/nikhilalakri/Developer/web-crawler/src/ethical_crawler/crawler.py)
- **Immediate Link Enqueueing**: As soon as a page is crawled by HTTP/Browser engine, immediately extract its internal links and enqueue them into `self.queue` so link discovery never waits for AI inference.
- **Granular Activity Callbacks**: Call `on_progress` with dynamic activity messages:
  - *"Checking robots.txt permissions for [url]..."*
  - *"Polite rate delay pause ([N]s)..."*
  - *"Rendering page via Chromium Headless Engine..."*
  - *"Extracting AI Company Profile with [model]..."*
- **Immediate Result Streaming**: Push `CrawlResult` immediately so the job has live results before or during AI extraction. If AI finishes shortly after, update the result in-place.

---

### 4. Background Job Worker & Streaming in API
#### [MODIFY] [router.py](file:///Users/nikhilalakri/Developer/web-crawler/src/ethical_crawler/api/v1/router.py)
- Update `_run_background_crawl`:
  - Update `job.current_activity`, `job.current_url`, `job.pages_crawled`, and incrementally append/update `job.results` in real time.
  - Allow `/api/v1/jobs/{job_id}` to return current live results so the frontend can display completed rows while later rows are still being processed.

---

### 5. Vector Store Cache Internal Links Preservation
#### [MODIFY] [vector_store.py](file:///Users/nikhilalakri/Developer/web-crawler/src/ethical_crawler/vector_store.py)
- In `upsert_page`: store `internal_links_json: json.dumps(result.internal_links[:200])` in ChromaDB metadata.
- In `get_cached_page`: reconstruct `internal_links` from `metadata.get("internal_links_json")` instead of hardcoding `[]`.

---

### 6. Frontend Real-Time Activity Display & Live Table Rendering
#### [MODIFY] [app.py](file:///Users/nikhilalakri/Developer/web-crawler/src/ethical_crawler/api/app.py)
- In `pollJob(jobId)`:
  - Display `job.current_activity` directly in the progress header (e.g., `⚡ Crawling... (1/8 pages) • Extracting AI with DeepSeek-v4.1 on https://plexis.in/`).
  - Render available results immediately using `renderResults(job.results)` on each poll, instead of waiting for `job.status === 'completed'`.
  - Update preset configuration for `competitor_intel` to default to `deepseek-ai/deepseek-v4.1-flash` (with fast 2.5s response).

---

## Verification Plan

### Automated Tests
- Run `.venv/bin/pytest tests/` to ensure all existing crawler, API, and extractor tests pass.
- Add new test in `tests/test_crawler.py` asserting that `on_progress` receives granular activity and that link enqueueing occurs prior to AI completion.
- Run `.venv/bin/ruff check .` and `.venv/bin/ruff format .`.

### Live Verification
- Test crawl of `https://plexis.in/` using the `🏢 Competitor Intel` preset.
- Verify that status updates appear immediately in real time:
  1. Status updates to `Checking robots.txt...` &rarr; `Rendering page via Chromium...` &rarr; `1 page fetched`.
  2. First page table row appears immediately.
  3. AI extraction completes within seconds using DeepSeek-v4.1-flash.
  4. Subsequent pages (`/blogs`, `/login`, etc.) are queued and crawled smoothly up to the limit.

