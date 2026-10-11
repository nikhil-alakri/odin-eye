# 09-Oct-2026 01:10

# Master Implementation Plan: Advanced Features Suite (1, 2, 3, 5) & Phase 1 Execution

This document defines the architectural blueprint for the 4 chosen strategic features:
1. **Feature 1: Scheduled Crawling, Content Diff & Change Alerts** *(Phase 1 — Ready for Immediate Implementation)*
2. **Feature 2: Vision & Multimodal Extraction (Screenshots, Vision LLM & PDF Parsing)** *(Phase 2)*
3. **Feature 3: Interactive Point-and-Click Element Picker** *(Phase 3)*
4. **Feature 5: Competitive Intelligence & Technology Stack Profiling** *(Phase 4)*

---

## 🏛️ Comprehensive Architecture Blueprint for All 4 Features

```
+----------------------------------------------------------------------------------------------------+
|                                    CRAWL // ETHIC PLATFORM                                         |
+----------------------------------------------------------------------------------------------------+
|  [FEAT 1] Scheduler & Diff     |  [FEAT 2] Multimodal & Vision  |  [FEAT 3] Element Picker  | [FEAT 5] Tech & Competitor |
|  - Background Async Ticker     |  - Playwright Screenshot Engine|  - Interactive DOM Canvas | - Header & Script Fingerprint
|  - Cron & Interval Parsing     |  - Image / PDF Markdown Parser |  - Element Hover Inspector| - Multi-Domain Comparison  
|  - Unified Diff & Word Diffs   |  - Visual Side-by-Side Slider  |  - Auto CSS Selector Gen  | - Feature & Pricing Matrix 
|  - Outbound Webhook Alerts     |  - Vision LLM Ingestion        |  - Instant RPA Step Insert| - PDF Dossier Integration  
+--------------------------------+--------------------------------+---------------------------+----------------------------+
|                                    Core Vector Store & Storage Layer (Preserved)                           |
+----------------------------------------------------------------------------------------------------+
```

---

## 📋 Feature Roadmap Summary

| Feature | Target Modules | Primary Purpose | User Experience Impact |
| :--- | :--- | :--- | :--- |
| **1. Scheduled Crawling & Diff Alerts** | `scheduler/`, `knowledge/diff_engine.py`, `alerts/webhook.py` | 24/7 autonomous monitoring & change detection | Dashboard tab to monitor targets, alert on changes, view green/red diffs |
| **2. Vision & Multimodal Extraction** | `engines/browser_engine.py`, `extractors/pdf_extractor.py` | Full-page screenshots, PDF parsing, Vision LLM | Visual archive, timeline slider, PDF vector search in RAG |
| **3. Point-and-Click Selector** | `extractors/element_picker.py`, UI iframe sandbox | Zero-code element selection for RPA & scraping | Hover & click elements in web preview to auto-generate selectors |
| **5. Competitive Intel & Tech Profiling**| `extractors/tech_profiler.py`, `knowledge/competitor_comparator.py`| Tech stack detection & side-by-side matrices | Identifies frameworks, CMS, analytics, & generates competitor benchmarks |

---

# 🚀 DEEP-DIVE SPECIFICATION: Feature 1 (Phase 1)
## Scheduled Crawling, Content Diff Engine & Change Alerts

### 1. Requirements & Objectives
1. **Autonomous Scheduled Runner**: Run crawl and scrape jobs automatically based on intervals (every 10m, 1h, 6h, 12h, 24h) or cron-like schedules.
2. **Persistent Schedule Storage**: Store schedules in a dedicated JSON file (`data/schedules.json`) or SQLite table without touching or disrupting the existing ChromaDB vector database.
3. **Smart Content Diff Engine**:
   - Compare the newly fetched markdown with the prior cached markdown in the vector store.
   - Detect size deltas, line-by-line additions, deletions, and percentage content similarity.
   - Generate human-readable change summaries (e.g., *"14 lines added, 3 lines removed, 98% similarity"*).
4. **Outbound Webhook Alerts**:
   - When changes exceed a configurable threshold (or upon any change), trigger an HTTP POST webhook to external services (Slack, Discord, Zapier, custom endpoint).
5. **Interactive Dashboard UI**:
   - Add a dedicated **"⏰ Schedules & Monitors"** tab or modal in the UI.
   - Enable users to create a schedule, toggle active/paused, view last run / next run timestamps, and click "Run Now".
   - An interactive **Visual Diff Modal** showing side-by-side green/red unified diff with syntax highlighting.

---

### 2. File & Component Breakdown for Feature 1

#### A. [NEW] `src/ethical_crawler/scheduler/models.py`
- Pydantic models:
  - `ScheduleInterval`: Enum (`"10m"`, `"30m"`, `"1h"`, `"6h"`, `"12h"`, `"24h"`, `"7d"`)
  - `ScheduleJob`:
    - `id: str` (UUID)
    - `url: str`
    - `job_type: str` (`"scrape"` or `"crawl"`)
    - `strategy: CrawlStrategy` (`"auto"`, `"browser"`, `"http"`)
    - `interval: ScheduleInterval`
    - `interval_seconds: int`
    - `is_active: bool = True`
    - `created_at: datetime`
    - `last_run_at: datetime | None`
    - `next_run_at: datetime`
    - `last_status: str | None` (`"success"`, `"failed"`, `"no_change"`, `"changed"`)
    - `webhook_url: str | None`
    - `notify_on_change_only: bool = True`
    - `last_diff_summary: str | None`
  - `ScheduleCreateRequest` & `ScheduleUpdateRequest`

#### B. [NEW] `src/ethical_crawler/scheduler/manager.py`
- Class `ScheduleManager`:
  - Persistent file storage in `data/schedules.json`.
  - Methods: `create_schedule()`, `list_schedules()`, `get_schedule()`, `update_schedule()`, `delete_schedule()`, `toggle_schedule()`.
  - Background async runner (`start_scheduler()`, `stop_scheduler()`):
    - Background task running `asyncio.sleep(15)` ticks.
    - Evaluates `datetime.now(timezone.utc) >= job.next_run_at`.
    - Triggers execution, computes diff against previous crawl in ChromaDB, dispatches webhooks, and updates `last_run_at` and `next_run_at`.

#### C. [NEW] `src/ethical_crawler/knowledge/diff_engine.py`
- Class `ContentDiffEngine`:
  - `compute_diff(old_text: str, new_text: str) -> ContentDiffResult`:
    - Uses Python `difflib.unified_diff` and `difflib.SequenceMatcher`.
    - Returns:
      - `similarity_ratio: float` (0.0 to 1.0)
      - `has_changed: bool`
      - `added_lines_count: int`
      - `removed_lines_count: int`
      - `raw_diff: str` (unified diff text)
      - `html_diff: str` (syntax-colored HTML lines ready for UI rendering)
      - `summary: str` (e.g., *"Modified: +18 lines, -4 lines (96.4% similar)"*)

#### D. [NEW] `src/ethical_crawler/alerts/webhook.py`
- Function `async def dispatch_webhook_alert(webhook_url: str, payload: dict) -> bool`:
  - Transmits standardized payload via `httpx.AsyncClient`:
    - `event: "page_changed" | "scheduled_crawl_completed"`
    - `url: str`
    - `timestamp: str`
    - `diff_summary: str`
    - `added_count: int`
    - `removed_count: int`
    - `title: str`

#### E. [MODIFY] `src/ethical_crawler/api/v1/router.py`
- Add API endpoints:
  - `GET /v1/schedules`: List all active and paused schedules.
  - `POST /v1/schedules`: Create a new scheduled monitor.
  - `GET /v1/schedules/{schedule_id}`: Retrieve single schedule details.
  - `PATCH /v1/schedules/{schedule_id}`: Toggle active state or update interval/webhook.
  - `DELETE /v1/schedules/{schedule_id}`: Delete a schedule.
  - `POST /v1/schedules/{schedule_id}/run`: Immediate manual trigger ("Run Now").
  - `GET /v1/diff`: Compare two cached revisions of a page or current page vs historical.

#### F. [MODIFY] `src/ethical_crawler/api/app.py`
- **FastAPI Lifespan**: Start scheduler background worker on app startup, cancel gracefully on shutdown.
- **UI Header / Navigation**:
  - Add **"⏰ Monitors & Schedules"** button in navigation or header with active monitor counter.
- **Schedules Modal / Tab (`schedulesModal`)**:
  - List of monitored targets with status pills (*Active*, *Paused*, *Changed*), last run time, next run countdown, and "Run Now" button.
  - "New Monitor" form: Target URL, engine strategy, interval dropdown, optional webhook URL.
- **Visual Diff Viewer Modal (`diffModal`)**:
  - Green/Red high-contrast diff viewer comparing previous snapshot with latest content.

---

## 🧪 Verification Plan for Feature 1

### Automated Tests
1. `tests/test_diff_engine.py`:
   - Test exact match (similarity = 1.0, has_changed = False).
   - Test additions and deletions detection.
   - Test unified diff output formatting.
2. `tests/test_scheduler.py`:
   - Test schedule creation, persistence to JSON, and retrieval.
   - Test interval calculation (`next_run_at` math for 10m, 1h, 24h).
   - Test toggle pause/resume and deletion.
   - Test execution trigger and diff comparison against ChromaDB.
3. `tests/test_schedules_api.py`:
   - Verify `GET /v1/schedules`, `POST /v1/schedules`, `POST /v1/schedules/{id}/run`, `DELETE`.
4. Full Regression Suite:
   - Ensure all 67 existing tests continue passing.

### Database Preservation Verification
- Verify ChromaDB collection `crawled_knowledge` remains intact with 150 documents.
- Verify non-destructive revisions increment smoothly during scheduled recrawls.

