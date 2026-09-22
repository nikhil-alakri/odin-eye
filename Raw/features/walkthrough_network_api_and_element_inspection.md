# Walkthrough: Network API Interception & DOM Element Inspection
**Date & Time**: 22-Sep-2026 03:54

---

## 1. Executive Summary

We have upgraded the Ethical AI Web Crawler and Market Intelligence platform with two major features:
1. **Network API Interception**: Headless Chromium now intercepts all background `fetch` and `xhr` requests and responses containing `application/json` data, capturing raw structured payloads directly off the wire before DOM mutation or rendering.
2. **DOM Elements Inspector & Live Selector Tester**: An element analysis suite that automatically inventories interactive controls (**Buttons & CTAs**, **Forms & Inputs**, **Data Tables**, and **Headings Outline**) with resilient CSS selectors, and provides a real-time selector testing tool both via REST API and directly inside the Web UI Dashboard.

---

## 2. Key Architecture & Components Implemented

### A. Data Models (`src/ethical_crawler/types.py`)
- **`NetworkCall`**:
  - `url`: Captured endpoint URL.
  - `method`: HTTP method (`GET`, `POST`, `PUT`, `DELETE`, etc.).
  - `status`: HTTP status code (`200`, `401`, `404`, `500`).
  - `resource_type`: `fetch` or `xhr`.
  - `content_type`: Response MIME type (e.g., `application/json; charset=utf-8`).
  - `request_data`: Captured POST payload or query parameters.
  - `response_data`: Parsed JSON dict or text snippet (capped at 500 KB to avoid memory bloat).
- **`CrawlResult` updates**:
  - `network_calls`: Carries all captured network API calls.
  - `dom_elements`: Carries discovered buttons, forms, tables, headings, and counts.

### B. Element Extraction Engine (`src/ethical_crawler/extractors/element_inspector.py`)
- `ElementInspector`:
  - `inspect_html(html: str) -> dict[str, Any]`: Analyzes raw HTML using BeautifulSoup to extract structured inventories for buttons, forms, tables, and headings with recommended resilient CSS selectors (`#id`, `.class-name`, `[name="..."]`, `button:has-text(...)`).
  - `query_selector(html: str, selector: str) -> list[dict[str, Any]]`: Queries any CSS selector against the DOM, returning count, tag, text, attributes (`href`, `value`, `src`, `data-*`, `aria-*`), and inner HTML preview.

### C. Engine Integrations
- **[browser_engine.py](file:///Users/nikhilalakri/Developer/web-crawler/src/ethical_crawler/engines/browser_engine.py)**:
  - Hooks into Playwright's `page.on("response", ...)` to intercept asynchronous API traffic.
  - Filters out binary/media noise (images, fonts, stylesheets) and focuses on JSON/REST/GraphQL calls.
  - Safely buffers up to 500 KB per response and decodes JSON into structured dicts.
  - Runs `ElementInspector.inspect_html` on the rendered DOM and bundles both `network_calls` and `dom_elements` into the final `CrawlResult`.
- **[http_engine.py](file:///Users/nikhilalakri/Developer/web-crawler/src/ethical_crawler/engines/http_engine.py)**:
  - Runs `ElementInspector.inspect_html` on static responses so that non-browser crawls also provide the full DOM elements breakdown.

### D. API Endpoints (`src/ethical_crawler/api/v1/router.py`)
- **`POST /api/v1/elements/check`**:
  - Accepts `selector: str`, with either `html: str` or `url: str`.
  - Executes CSS selector queries against the DOM.
  - Returns `match_count`, list of matching element tags, classes, IDs, inner text, attributes, and errors if the selector syntax is invalid.

### E. Web UI Dashboard (`src/ethical_crawler/api/app.py`)
- In the **Page Preview Modal** (`#previewModal`), added two dedicated tabs:
  1. **🌐 Network APIs (`#viewNetworkTab`)**:
     - Metric counter badge showing total API calls captured.
     - Live search filter by endpoint URL or keyword (e.g. `pricing`, `products`, `graphql`).
     - Status filter dropdown (`All`, `2xx OK`, `4xx/5xx Errors`).
     - Expandable cards displaying Method badge, Status badge, Endpoint URL, Request POST data, and syntax-highlighted Response JSON with a **"Copy JSON"** button.
  2. **🔍 DOM Elements (`#viewElementsTab`)**:
     - **Live CSS Selector Tester**: Text input with interactive **"Check Element"** button. Evaluates arbitrary CSS selectors against the page DOM in real time, highlighting matching tags, text, attributes, and providing a one-click **"Copy Selector"** button.
     - **Categorized Elements Inventory**:
       - 🔘 **Buttons & CTAs**: Tag, text, resilient CSS selector, and copy button.
       - 📝 **Forms & Inputs**: Input type, name, placeholder, value, and selector.
       - 📊 **Tables**: Header columns, row counts, and selector.
       - 🏷️ **Headings**: H1, H2, H3 hierarchy outline.

---

## 3. Automated Test Verification

A dedicated test suite in **[tests/test_network_and_elements.py](file:///Users/nikhilalakri/Developer/web-crawler/tests/test_network_and_elements.py)** was created and verified:

```bash
$ .venv/bin/pytest tests/test_network_and_elements.py -v
tests/test_network_and_elements.py::test_element_inspector_discovery PASSED [ 16%]
tests/test_network_and_elements.py::test_element_inspector_empty_html PASSED [ 33%]
tests/test_network_and_elements.py::test_element_inspector_query_selector PASSED [ 50%]
tests/test_network_and_elements.py::test_api_element_check_endpoint PASSED [ 66%]
tests/test_network_and_elements.py::test_network_call_and_crawl_result_serialization PASSED [ 83%]
tests/test_network_and_elements.py::test_browser_engine_network_interception_logic PASSED [100%]

============================== 6 passed in 0.90s ===============================
```

Full project test suite regression test:
```bash
$ .venv/bin/pytest tests/ -v
============================= 61 passed in 28.09s ==============================
```

Code quality and formatting:
```bash
$ .venv/bin/ruff check . && .venv/bin/ruff format --check .
All checks passed!
71 files already formatted
```

---

## 4. User Impact & Value Delivered

1. **Direct Wire Data Access**: Users no longer have to parse complex or obfuscated DOM structures when an application exposes a clean JSON API endpoint under the hood.
2. **Effortless RPA Authoring**: The DOM Elements tab and Selector Tester allow users to discover and test selectors directly in the UI dashboard without needing to open external browser developer tools.
3. **API Diagnostics**: Immediately highlights failed background API calls (`401 Unauthorized`, `403 Forbidden`, `429 Too Many Requests`, `500 Server Error`) that cause dynamic pages to render blank.

