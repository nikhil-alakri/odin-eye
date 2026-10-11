# 09-Oct-2026 01:25

# Feature Specification: Scheduled Crawling, Content Diff Engine & Change Alerts (Feature 1)

## 1. Executive Summary & Problem Statement
Currently, the Ethical Web Crawler operates on an ad-hoc, manual invocation basis: users must trigger crawls or scrapes manually through the CLI or UI. To transform this into an autonomous 24/7 web monitoring platform, we need an asynchronous scheduling engine with intelligent content diffing and external alert dispatching.

This system will allow users to define monitoring jobs (e.g., monitor competitor pricing every 6 hours, check legal terms daily), detect exact content modifications against historical snapshots in ChromaDB, filter out volatile web noise, and dispatch webhook notifications (Slack, Discord, Zapier, custom endpoints).

---

## 2. Skill Alignment & Methodology (`.agents/skills`)

| Specialized Agent Skill | Applied Architecture & Operational Discipline |
| :--- | :--- |
| **`engineering-backend-architect`** | - Non-blocking async event loop ticker (`asyncio.sleep` evaluation).<br>- Idempotent job execution with persistent job lock state (`running`, `idle`).<br>- Timeout budgets and circuit breakers per monitored domain.<br>- Zero database resets: persistent job definitions stored in `data/schedules.json` without touching existing ChromaDB knowledge. |
| **`engineering-sre`** | - Webhook delivery resilience: exponential backoff with jitter on 5xx or connection drops.<br>- Alert rate limiting / deduplication window to prevent alert flooding.<br>- Health check telemetry & failure isolation (a failed scheduled job never crashes the scheduler daemon). |
| **`engineering-ai-data-remediation-engineer`** | - Noise suppression layer: cleans volatile non-content elements before diffing (dynamic session IDs, CSRF tokens, live clocks, rotating ad banners).<br>- Semantic change categorization (e.g. "Price delta", "Section added", "Structural refactor"). |
| **`testing-api-tester`** | - Comprehensive contract testing across all new endpoints (`/v1/schedules*`, `/v1/diff`).<br>- Mock webhook server integration test simulating timeout, 200 OK, 429 rate limit, and 500 error scenarios. |
| **`design-ui-designer` & `engineering-frontend-developer`** | - Unified modal HUD integration: `schedulesModal` matching theme tokens (`--ds-*`).<br>- Syntax-colored green/red visual diff viewer (`diffModal`) with line numbers and toggleable inline vs. split view. |

---

## 3. Technical Architecture & Component Specification

```
                                      [Web Dashboard / REST API]
                                                   |
                         +-------------------------+-------------------------+
                         |                                                   |
             POST /v1/schedules (Create)                             GET /v1/diff (Inspect)
                         |                                                   |
                         v                                                   v
              [ScheduleManager]                                    [ContentDiffEngine]
             (data/schedules.json)                                (difflib + Semantic)
                         |                                                   |
             Async Ticker (15s Loop)                                         |
                         |                                                   |
         +---------------+---------------+                                   |
         | Check next_run_at <= now()    |                                   |
         +---------------+---------------+                                   |
                         |                                                   |
                         v                                                   |
                [EthicalCrawler / Engine]                                    |
                         |                                                   |
             Fetch latest page content                                       |
                         |                                                   |
                         +-----------------------> Compare with <------------+
                                                   ChromaDB Vector Store
                                                   (Historical Revision)
                                                             |
                                                    Has Content Changed?
                                                   /                    \
                                                YES                      NO
                                                 |                        |
                                        [Webhook Dispatcher]         Update status:
                                       (Slack, Discord, Custom)      "no_change"
                                                 |
                                         Update status: "changed"
```

### A. Data Models (`src/ethical_crawler/scheduler/models.py`)
```python
from enum import StrEnum
from datetime import datetime
from pydantic import BaseModel, Field

class ScheduleInterval(StrEnum):
    EVERY_10_MIN = "10m"
    EVERY_30_MIN = "30m"
    HOURLY = "1h"
    EVERY_6_HOURS = "6h"
    EVERY_12_HOURS = "12h"
    DAILY = "24h"
    WEEKLY = "7d"

class ScheduleStatus(StrEnum):
    ACTIVE = "active"
    PAUSED = "paused"
    RUNNING = "running"
    ERROR = "error"

class ScheduleJob(BaseModel):
    id: str = Field(description="Unique UUID for schedule")
    name: str = Field(description="User-friendly monitor label")
    url: str = Field(description="Target URL to monitor")
    job_type: str = Field(default="scrape", description="'scrape' or 'crawl'")
    strategy: str = Field(default="auto", description="'auto', 'browser', or 'http'")
    interval: ScheduleInterval = Field(default=ScheduleInterval.DAILY)
    interval_seconds: int = Field(default=86400)
    status: ScheduleStatus = Field(default=ScheduleStatus.ACTIVE)
    created_at: datetime
    last_run_at: datetime | None = None
    next_run_at: datetime
    last_status: str | None = None  # "changed", "no_change", "failed"
    last_similarity_ratio: float | None = None
    last_diff_summary: str | None = None
    webhook_url: str | None = None
    notify_on_change_only: bool = True
    consecutive_failures: int = 0
```

### B. Content Diff Engine (`src/ethical_crawler/knowledge/diff_engine.py`)
- **Cleaning Pass**: Normalizes markdown, strips trailing whitespace, removes timestamp patterns (`\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}`).
- **Sequence Matching**: Computes `difflib.SequenceMatcher(None, old_clean, new_clean).ratio()`.
- **Unified Diff Generation**: Generates standard unified diff lines with `+` (green addition) and `-` (red deletion).
- **Semantic Summary**: Produces executive summary: `"+24 lines, -6 lines (97.2% similarity) - Content Modified"`.

### C. Webhook Dispatcher (`src/ethical_crawler/alerts/webhook.py`)
- Asynchronous POST using `httpx.AsyncClient(timeout=10.0)`.
- Standard JSON envelope:
  ```json
  {
    "event": "content_changed",
    "monitor_id": "sched_12345",
    "monitor_name": "Competitor Pricing Monitor",
    "url": "https://example.com/pricing",
    "timestamp": "2026-10-09T01:25:00Z",
    "similarity_ratio": 0.942,
    "diff_summary": "+12 lines, -2 lines (94.2% similarity)",
    "additions_count": 12,
    "deletions_count": 2,
    "view_diff_url": "http://localhost:8000/?view_diff=sched_12345"
  }
  ```

### D. REST API Endpoints (`src/ethical_crawler/api/v1/router.py`)
- `GET /v1/schedules`: List all configured monitors.
- `POST /v1/schedules`: Create a new monitor.
- `GET /v1/schedules/{id}`: Get monitor details, run history, and last diff.
- `PATCH /v1/schedules/{id}`: Update interval, webhook, or toggle active/paused.
- `DELETE /v1/schedules/{id}`: Delete monitor configuration.
- `POST /v1/schedules/{id}/run`: Trigger immediate execution out-of-schedule.
- `GET /v1/diff`: Compare two specific text blocks or historical page revisions.

### E. Dashboard UI Integration
- **Header Button**: `⏰ MONITORS` badge displaying count of active monitors (e.g. `3 Active`).
- **`schedulesModal`**:
  - Filterable table of monitors (Target URL, Interval, Next Run countdown, Status pill, Actions).
  - Quick actions: "Run Now" (instant refresh), "Pause / Resume", "View Diff", "Delete".
  - "Add New Monitor" drawer: Target URL, interval selector, strategy, optional webhook URL.
- **`diffModal`**:
  - Split / Unified Green-Red diff viewer with additions highlighted in soft emerald and deletions highlighted in soft rose.

---

## 4. Scenarios & Edge Cases

| Scenario | Challenge | Architectural Resolution |
| :--- | :--- | :--- |
| **1. Dynamic Timestamp/Cookie Noise** | Page changes every minute due to a live copyright year or server time in footer. | `ContentDiffEngine` applies regex sanitization to ignore timestamp banners and dynamic session tokens before sequence matching. |
| **2. Target Server HTTP 429 / Down** | Target returns 429 or 503 during a scheduled run. | Honors Ethical Rule 2: skips run, applies exponential backoff, increments `consecutive_failures`, alerts webhook if failures >= 3. |
| **3. Webhook Receiver Unreachable** | External webhook returns 500 or times out. | SRE retry strategy: 3 retries with jittered backoff; logs failure without blocking next scheduled crawl. |
| **4. Server Restart / Crash** | App restarts while jobs are scheduled. | State persists in `data/schedules.json`. On app startup, `ScheduleManager` recalculates missed runs (`next_run_at < now()`) and runs them gracefully. |
| **5. Zero Historical Snapshot** | First time running a schedule on a new URL. | Creates baseline snapshot in ChromaDB, marks status as `"baseline_created"`, no change alert dispatched. |

---

## 5. Acceptance Criteria & Test Verification Matrix

- [ ] `tests/test_diff_engine.py`: 100% pass on exact matches, text additions, deletions, and markdown cleaning.
- [ ] `tests/test_scheduler.py`: 100% pass on interval calculation, persistence to `data/schedules.json`, pause/resume, and run-now execution.
- [ ] `tests/test_schedules_api.py`: 100% pass on all CRUD endpoints.
- [ ] ChromaDB preservation: Zero data wiped, historical records and revisions increment cleanly.
- [ ] Full regression suite: All existing 67 tests remain passing.

