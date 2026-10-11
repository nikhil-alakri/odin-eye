# 08-Oct-2026 13:58

# Walkthrough: Single-URL Scrape Reflection in Vector Knowledge Store

## 1. Problem Summary
When a user executed a single page scrape via the **SCRAPE** tab (`POST /api/v1/scrape`), the scraped page was not reflecting under the **KNOWLEDGE** tab (`/api/v1/history`) or the header/tab badges.

## 2. Root Causes Identified

1. **Frontend Script Parsing Error on Page Load**:
   - An earlier inline JavaScript regex/newline string literal inside `src/ethical_crawler/api/app.py` triggered a runtime `SyntaxError` in the browser upon initial load.
   - Because of this syntax error, `loadHistory()` on initial page load never executed, leaving the Knowledge tab badge (`tabCountBadge`) and header badge (`headerStoreCount`) stuck at their default static template placeholder `0`.
   - Any attempt to switch tabs or run actions was blocked by the crashed script context.

2. **ChromaDB Internal ID Retrieval Truncation in `list_stored_pages`**:
   - In `src/ethical_crawler/vector_store.py`, `list_stored_pages(limit=...)` performed `self.collection.get(limit=limit, include=["metadatas"])` before sorting.
   - ChromaDB's `.get()` does not support ordering by metadata fields (like `crawled_at`) inside its internal SQLite query; it returns the first `limit` records by internal insertion/rowid order.
   - Because the store already contained 149 pages, calling `list_stored_pages(limit=50)` (the default limit on `/api/v1/history`) fetched only the oldest 50 records. Even if a new page was inserted as record #150, it was truncated before Python could sort by `crawled_at`, making newly scraped pages completely invisible in the list.

3. **Conditional Upsert in `/api/v1/scrape` Endpoint**:
   - In `src/ethical_crawler/api/v1/router.py`, the `/api/v1/scrape` endpoint only invoked `get_vector_store().upsert_page()` inside the `if req.extract_ai:` block.
   - When AI extraction was disabled (which is the default unchecked state in the UI), or if an AI key was not configured, `scrape_page` relied exclusively on the underlying crawler engine having saved the page. If the page was fetched from cache or if the crawler run was mocked/bypassed, no upsert was called.

4. **Cache Hit Behavior on Pre-Existing Pages**:
   - When a user scrapes a URL that already exists in ChromaDB with "Use ChromaDB cache" enabled, the crawler returned the cached result with 0 network requests. It did not refresh the timestamp or create a new entry, keeping the total count identical.

## 3. Changes Implemented

### `src/ethical_crawler/vector_store.py`
- Updated `list_stored_pages()`:
  - Retrieves all lightweight metadata records (`include=["metadatas"]`) from ChromaDB without premature SQLite limit truncation.
  - Sorts all pages by `crawled_at` descending (newest first).
  - Applies `[:limit]` after sorting, ensuring the most recently crawled or scraped pages always appear at the top.

### `src/ethical_crawler/api/v1/router.py`
- In `scrape_page`:
  - Added an explicit, safe call to `get_vector_store().upsert_page(res, ai_data=ai_data)` for every successful HTTP 200 scrape, regardless of whether AI extraction is toggled on or off.

### `tests/test_scrape_export.py`
- Added verification assertion to `test_api_scrape_endpoint` confirming that `get_vector_store().upsert_page()` is invoked during `POST /api/v1/scrape`.

## 4. Verification & Validation
- **Pytest Suite**: All 61 automated tests pass cleanly (`61 passed in 22.83s`).
- **Data Integrity**: ChromaDB collection preserved non-destructively (150 pages across 7 domains).
- **JavaScript Syntax**: Validated with `node -c` (exit code 0).

