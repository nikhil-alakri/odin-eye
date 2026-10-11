# 09-Oct-2026 01:35

# Walkthrough: Scheduled Crawling, Content Diff Engine & Change Alerts (Feature 1)

## 🎯 What Was Built

We have successfully engineered and verified **Feature 1: Scheduled Crawling, Content Diff & Change Alerts**, turning the Ethical AI Web Crawler into an autonomous 24/7 web monitoring system.

---

## 🏛️ Changes Summary

### 1. Scheduler Engine & Persistence Layer
* **`src/ethical_crawler/scheduler/models.py`**:
  * Pydantic schemas: `ScheduleInterval` (`10m`, `30m`, `1h`, `6h`, `12h`, `24h`, `7d`), `ScheduleStatus` (`active`, `paused`, `running`, `error`).
  * `ScheduleJob`: Tracks job configuration, execution history (`last_run_at`, `next_run_at`), diff metrics (`last_similarity_ratio`, `last_diff_summary`, `last_raw_diff`), webhook URL, and failure counts.
* **`src/ethical_crawler/scheduler/manager.py`**:
  * Thread-safe and async `ScheduleManager` storing job configurations in `data/schedules.json` without modifying ChromaDB knowledge.
  * Background async ticker loop (`_ticker_loop`) evaluating due monitors every 15 seconds.
  * Autonomous execution engine (`execute_job`): triggers HTTP or Playwright crawl, fetches historical baseline from ChromaDB, computes content diff, updates vector store revision, and dispatches webhook alerts.
* **`src/ethical_crawler/scheduler/__init__.py`**:
  * Clean public exports for `ScheduleManager`, `get_schedule_manager`, and models.

### 2. Smart Content Diff Engine
* **`src/ethical_crawler/knowledge/diff_engine.py`**:
  * `ContentDiffEngine`:
    * Noise suppression layer neutralizing dynamic volatile tokens (timestamps, session IDs, CSRF tokens) to eliminate false-positive alerts.
    * Line-by-line `difflib.unified_diff` and `SequenceMatcher` similarity ratio calculation.
    * Generates human-readable change summaries (e.g., *"Modified: +14 lines, -2 lines (96.4% similarity)"*).
    * Pre-renders color-coded HTML diff blocks (`diff-add` in emerald, `diff-del` in rose, `diff-chunk` in purple) with line formatting for instant UI rendering.

### 3. Outbound Webhook Alerting
* **`src/ethical_crawler/alerts/webhook.py`**:
  * `dispatch_webhook_alert`: Delivers asynchronous webhook notifications via `httpx.AsyncClient` with exponential backoff retries.
  * Auto-formats adaptive payloads for Slack incoming webhooks (`blocks` + `mrkdwn`), Discord webhooks (`embeds` with color and fields), and standard JSON receivers.
* **`src/ethical_crawler/alerts/__init__.py`**:
  * Exports `dispatch_webhook_alert`.

### 4. REST API Endpoints (`src/ethical_crawler/api/v1/router.py`)
* `GET /v1/schedules`: List all configured monitors.
* `POST /v1/schedules`: Create a new monitor with interval, strategy, and webhook URL.
* `GET /v1/schedules/{id}`: Retrieve monitor details, last diff, and history.
* `PATCH /v1/schedules/{id}`: Update monitor parameters (name, interval, webhook).
* `POST /v1/schedules/{id}/toggle`: Toggle active / paused state.
* `DELETE /v1/schedules/{id}`: Remove monitor.
* `POST /v1/schedules/{id}/run`: Immediate out-of-schedule manual execution ("Run Now").
* `POST /v1/diff`: Compare two texts or compare a URL against historical cache.

### 5. Lifespan Integration (`src/ethical_crawler/api/app.py`)
* Added `@asynccontextmanager` `lifespan(app: FastAPI)` starting the background scheduler ticker on application startup and stopping it cleanly on shutdown.
* Added async context manager protocol (`__aenter__` and `__aexit__`) to `CrawlEngine` base class in `src/ethical_crawler/engines/base.py`.

### 6. Interactive Dashboard UI (`src/ethical_crawler/api/app.py`)
* **Header Navbar Badge**: Added `⏰ MONITORS` button with live active monitor counter (`#headerSchedulesCount`).
* **`schedulesModal` Dialog**:
  * Quick-add monitor bar (Target URL, Name, Interval dropdown, Strategy, Webhook URL).
  * Filterable monitor status table with status badges (`Active`, `Paused`, `Running`, `⚡ Changed`, `Error`).
  * Instant action buttons per row: `Run Now`, `Diff Inspector`, `Pause / Resume`, and `Delete`.
* **`diffModal` Dialog**:
  * High-contrast visual diff viewer comparing the latest crawl vs. historical baseline.
  * Metric summary bar with additions badge (`+X`), deletions badge (`-X`), and similarity percentage (`X% Match`).
  * Dark syntax-colored unified diff viewer container.

---

## 🧪 Verification & Test Results

### 1. Test Suite Execution
* **Total Tests**: **77 passed** in 23.05s across 15 test files:
  * `tests/test_diff_engine.py`: 4 tests (identical match, additions/deletions, noise suppression, None handling).
  * `tests/test_scheduler.py`: 4 tests (create/list, toggle/update, delete, mock execution).
  * `tests/test_schedules_api.py`: 2 tests (full CRUD REST API integration, diff API).
  * All 67 pre-existing test suites passed with 0 regressions.

### 2. Database Preservation
* Verified with `get_vector_store().collection.count()`: **151 documents across 7 domains fully preserved** without data loss or table truncation.

### 3. JavaScript Syntax
* Validated with `node -c`: 100% valid JavaScript syntax.

