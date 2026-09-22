# Implementation Plan: Domain Grouping, Selective Deletion & Website Growth Tracking

**Date & Time**: 22-Sep-2026 01:48

---

## 🎯 Background & Purpose

The user raised three critical UX and architectural questions:
1. **Why Cache vs. Tracking Updates/Growth**:
   - Current: `⚡ Use ChromaDB Vector Cache (Skip network if crawled)` blindly skips network requests if a page was already scraped.
   - User Insight: *"if they update their website or content or pages, we should also update our data as per that not complete replace update so that we know how they are growing and updating their self."*
   - Solution: Evolve the cache from a simple bypass to an **Intelligent Evolution & Change Tracker**:
     - Clarify the cache toggle in the UI: Cache allows fast, polite, zero-network queries when testing. Unchecking it runs a **Live Refresh & Change Detection Crawl**.
     - In the vector store: Record page revisions (`revision_count`, `first_crawled_at`, `previous_size`, `last_updated_at`, and `growth_delta_bytes`).
     - Display a **"Updated / Revisions"** badge in the UI showing how much a page has grown or changed since first crawl.
2. **Selective Deletion**:
   - The user noticed no option to delete pages (e.g. junk test pages like `example.com` with `0 B`).
   - Solution: Provide safe, explicit deletion controls:
     - Delete individual pages (`DELETE /api/v1/history/page?url=...`).
     - Delete entire domains (`DELETE /api/v1/history/domain?domain=...`).
     - Adhere strictly to the Database Preservation Rule (deletion is exclusively triggered by explicit user request in the UI, never automated or indiscriminate).
3. **Domain Grouping & Modernized UI Dashboard**:
   - Current: Flat, unorganized table with 20+ mixed pages from multiple domains.
   - Solution:
     - Group pages hierarchically by **Domain** (e.g. `plexis.in` with 18 pages, `example.com` with 2 pages).
     - Modern Domain Cards: Domain favicon/globe icon, total pages, total size, last updated, quick actions (Search Domain, Recrawl Domain, Delete Domain).
     - Collapsible sub-table of pages under each domain.
     - View switch toggle: **"Group by Domain"** vs. **"Flat List"**.
     - Top KPI Metrics: Total Domains Tracked, Total Pages Stored, Total Knowledge Size, AI Profiles Indexed.

---

## 🏗️ Proposed Changes

### 1. Vector Store Enhancements (`src/ethical_crawler/vector_store.py`)
- **Revision & Growth Tracking**:
  - In `upsert_page()`: Check if document ID already exists.
  - If existing: read old metadata, compute `growth_delta_bytes = new_size - old_size`, increment `revision_count`, preserve `first_crawled_at`, and record `last_updated_at`.
- **Selective Deletion**:
  - `delete_page(url: str) -> bool`: Deletes a single document ID from ChromaDB.
  - `delete_domain(domain: str) -> int`: Queries and removes all documents matching domain metadata, returns count.
- **Domain Aggregation**:
  - `list_domains_summary(limit: int = 200) -> list[dict]`: Groups all stored pages by domain with aggregated stats (page count, total size, newest timestamp, pages list).

### 2. REST API Endpoints (`src/ethical_crawler/api/v1/router.py`)
- `DELETE /api/v1/history/page`: Delete a single stored page by URL.
- `DELETE /api/v1/history/domain`: Delete all stored pages for a specific domain.
- `GET /api/v1/history/domains`: Return grouped domain summaries with stats and page lists.
- `POST /api/v1/history/recrawl`: Trigger a background recrawl of a stored page or domain without cache to detect updates and record revisions.

### 3. Web UI Dashboard Modernization (`src/ethical_crawler/api/app.py`)
- **Metric Bar**:
  - 4 quick KPI widgets: **Domains Tracked**, **Pages Stored**, **Total KB Stored**, **AI Profiles**.
- **Domain Grouped View (Default)**:
  - Interactive accordion cards for each domain.
  - Domain header shows domain name, page count badge, total size, and quick actions:
    - 🔍 `Search in Domain`
    - 🔄 `Re-crawl Domain` (live fetch to track updates)
    - 🗑️ `Delete Domain` (with confirmation modal)
  - Expandable body listing pages with revision badges (`v2 (+140 B)`), size, timestamp, Preview, Export, and Delete buttons.
- **View Toggle**:
  - Switch between **"📁 Group by Domain"** and **"📋 Flat Table"**.
- **Cache & Growth Guide Accordion**:
  - Clear explanation of how caching works, why it exists, and how to uncheck it for live growth tracking.

---

## 🧪 Verification Plan

### Automated Tests
- Run `pytest -v tests/test_vector_store.py` to verify:
  - `test_delete_page`
  - `test_delete_domain`
  - `test_list_domains_summary`
  - `test_page_growth_revision_tracking`
- Run `pytest -v` across all 40+ tests to maintain 100% pass rate.
- Run `ruff check .` and `ruff format .`.

### Manual UI Verification
- Start `./crawler serve` and verify in the browser:
  - Group by domain view renders `plexis.in` and `example.com` in separate clean cards.
  - Delete single page deletes `example.com/p1` cleanly.
  - Delete domain deletes `example.com` and removes it from the list.
  - Re-crawling a page updates revision count and growth delta.

