# Walkthrough: RPA Playbook Automation Engine for Dynamic Web Intelligence
**Date & Time**: 22-Sep-2026 03:38

---

## 1. Executive Summary

We have engineered an interactive **Robotic Process Automation (RPA) Engine** directly embedded inside the Ethical AI Web Crawler and Market Intelligence platform.

Modern web pages hide critical content behind:
1. **Cookie consent banners & GDPR walls** (which blur, shade, or freeze DOM access).
2. **Pricing interval toggles** (Annual vs. Monthly billing switches that change DOM price tags).
3. **Accordions & FAQ toggles** (lazy-loaded HTML sections collapsed by default).
4. **Interactive filters, search inputs, tabs, and pagination buttons**.

With this native RPA engine, users can now execute pre-flight or custom Playwright interactions inside headless Chromium *before* DOM extraction, AI analysis, or market intelligence dossier synthesis occurs.

---

## 2. Key Architecture & Components Implemented

### A. Core RPA Package (`src/ethical_crawler/rpa/`)
1. **[models.py](file:///Users/nikhilalakri/Developer/web-crawler/src/ethical_crawler/rpa/models.py)**:
   - `RPAActionType`: Enumeration supporting `click`, `fill`, `select`, `wait_for`, `press_key`, `hover`, `scroll`, and `sleep`.
   - `RPAStep`: Pydantic step definition with CSS/XPath `selector`, `value`, `timeout_ms`, `wait_after_ms`, `optional` flag (fail-safe execution), `description`, and `secret_env` (for secure credential/token injection).
   - `RPAResult`: Step-by-step execution journal detailing step index, action, selector, duration, outcome (`success`, `failed_optional`, `error`), and detailed status messages.
2. **[presets.py](file:///Users/nikhilalakri/Developer/web-crawler/src/ethical_crawler/rpa/presets.py)**:
   - `auto_dismiss_cookies`: Multi-selector cookie banner and GDPR popup dismisser.
   - `expand_accordions`: Expands details/summary and FAQ accordion items.
   - `toggle_annual_pricing`: Automates toggling between Monthly and Annual pricing switches.
3. **[executor.py](file:///Users/nikhilalakri/Developer/web-crawler/src/ethical_crawler/rpa/executor.py)**:
   - `RPAExecutor`: Playwright async executor that maps steps to page actions (`page.click()`, `page.fill()`, `page.select_option()`, `page.wait_for_selector()`, `page.keyboard.press()`, `page.hover()`, `page.evaluate(...)` for scrolling, and `asyncio.sleep`).
   - Resilient error handling: If `optional=True`, non-critical selector timeouts log a warning and let the crawl continue seamlessly without breaking the pipeline.
   - Env secret resolution: Injects environment variables dynamically via `secret_env` without hardcoding sensitive strings in API payloads or playbooks.

### B. Engine Escalation & Crawl Pipeline Integration
1. **[browser_engine.py](file:///Users/nikhilalakri/Developer/web-crawler/src/ethical_crawler/engines/browser_engine.py)**:
   - Integrated `RPAExecutor` into `BrowserEngine.crawl()`.
   - Pre-flight cookie dismissal triggers when `auto_dismiss_modals=True`.
   - Custom `rpa_steps` run after navigation and network idle, immediately before capturing final DOM HTML and title.
2. **[crawler.py](file:///Users/nikhilalakri/Developer/web-crawler/src/ethical_crawler/crawler.py)**:
   - Auto-escalation: If `rpa_steps` are provided in `CrawlRequest`, the crawler automatically selects `browser_engine` (since HTTP engines cannot execute interactive JavaScript/browser actions).
3. **[types.py](file:///Users/nikhilalakri/Developer/web-crawler/src/ethical_crawler/types.py)**:
   - Added `rpa_steps: list[dict[str, Any]]` and `auto_dismiss_modals: bool` to `CrawlRequest`.
   - Added `rpa_logs: list[dict[str, Any]]` to `CrawlResult`.

### C. API Endpoints (`src/ethical_crawler/api/v1/router.py`)
1. `GET /api/v1/rpa/presets`: Returns available pre-built recipe templates with names, descriptions, and step sequences.
2. `POST /api/v1/rpa/generate`: Natural Language RPA Copilot. Users provide high-level intent (e.g., *"Dismiss GDPR banner, select Enterprise tab, and scroll to footer"*), and NVIDIA NIM LLM synthesizes structured, valid `RPAStep` JSON.
3. `POST /api/v1/scrape` & `POST /api/v1/crawl`: Both accept `rpa_steps` and `auto_dismiss_modals` parameters.

### D. Web UI Dashboard (`src/ethical_crawler/api/app.py`)
1. **RPA Playbook Collapsible Cards**:
   - Integrated into both the **Crawl form** and **Scrape form**.
   - One-click Preset badges:
     - 🍪 *Auto-Dismiss Cookies*
     - 📂 *Expand Accordions*
     - 💳 *Toggle Annual Pricing*
2. **Natural Language AI Playbook Copilot**:
   - Input prompt with ✨ *Generate Steps* button that queries `/api/v1/rpa/generate` and renders parsed steps in the queue.
3. **Visual Step Builder Modal**:
   - `Add Step` button opens an interactive modal with Action dropdown (Click, Fill, Select, Wait, Press Key, Hover, Scroll, Sleep), Selector input, Value input, Delay slider, and Optional checkbox.
4. **Page Preview Modal - RPA Execution Logs**:
   - Added a dedicated 🤖 *RPA Logs* tab in `#previewModal`.
   - Visual execution status badges (`SUCCESS`, `SKIPPED (OPTIONAL)`, `FAILED`), action names, target selectors, and timing stats.

---

## 3. Automated Test Verification

A dedicated test suite was built in **[tests/test_rpa.py](file:///Users/nikhilalakri/Developer/web-crawler/tests/test_rpa.py)** and validated across the entire 55-test project suite:

```bash
$ .venv/bin/pytest tests/test_rpa.py -v
tests/test_rpa.py::test_rpa_models PASSED                                [ 12%]
tests/test_rpa.py::test_rpa_presets PASSED                               [ 25%]
tests/test_rpa.py::test_rpa_executor_success PASSED                      [ 37%]
tests/test_rpa.py::test_rpa_executor_optional_failure PASSED             [ 50%]
tests/test_rpa.py::test_rpa_executor_mandatory_failure PASSED            [ 62%]
tests/test_rpa.py::test_rpa_executor_secret_env PASSED                   [ 75%]
tests/test_rpa.py::test_api_rpa_presets_endpoint PASSED                  [ 87%]
tests/test_rpa.py::test_api_rpa_generate_endpoint PASSED                 [100%]

============================== 8 passed in 0.76s ===============================
```

Full project suite regression test:
```bash
$ .venv/bin/pytest tests/ -v
============================= 55 passed in 28.36s ==============================
```

Code formatting & lint verification:
```bash
$ .venv/bin/ruff check .
All checks passed!

$ .venv/bin/ruff format --check .
67 files already formatted
```

---

## 4. User Impact & Value Delivered

1. **Unlocks Gated Dynamic Content**: The crawler is no longer restricted to static DOM trees or pre-rendered SPAs; it can actively dismiss modals, open drawers, trigger tabs, and simulate real user flows.
2. **No Coding Required**: Non-technical users can use natural language prompts to generate automation steps or pick battle-tested presets with a single click.
3. **Observability & Debuggability**: The Page Preview modal gives instant insight into which RPA steps ran, how long they took, and whether any optional step was skipped.
4. **Safety & Zero Disruption**: All optional steps gracefully fall through if a selector is absent, ensuring crawls never stall or crash unexpectedly.

