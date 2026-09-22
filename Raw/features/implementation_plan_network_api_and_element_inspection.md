# Implementation Plan: Network API Interception & DOM Element Inspection
**Date & Time**: 22-Sep-2026 03:48

---

## 1. Executive Summary

Modern dynamic web applications load their critical business data via asynchronous network requests (Fetch/XHR/REST/GraphQL) and render interactive DOM elements (buttons, inputs, forms, accordions, pricing tables). 

This plan details the implementation of:
1. **Network API Interception & Inspection**: Capturing client-side Fetch/XHR/REST/GraphQL calls, extracting pristine JSON payloads before DOM mutation, and tracking network errors/endpoints.
2. **DOM Element Inspection & Live Selector Checker**: An interactive element inspector that inventories buttons, forms, inputs, tables, and headings, and provides a live CSS selector tester directly inside the UI dashboard and API.

---

## 2. Key Architecture & Components

### A. Data Models (`src/ethical_crawler/types.py`)
- **`NetworkCall`**:
  - `url`: Endpoint URL
  - `method`: `GET`, `POST`, `PUT`, `DELETE`, etc.
  - `status`: HTTP status code (`200`, `401`, `404`, `500`)
  - `resource_type`: `fetch`, `xhr`, `document`
  - `content_type`: `application/json`, etc.
  - `request_data`: Post body or query parameters
  - `response_data`: Parsed JSON dict or text snippet (capped at 500 KB to avoid memory bloat)
  - `duration_ms`: Duration of network roundtrip
- **`DOMElementsInventory`**:
  - `buttons`: Detected interactive buttons & CTAs with suggested selectors
  - `inputs`: Detected form fields, search boxes, selects, and textareas
  - `tables`: Detected data tables (columns, row count)
  - `headings`: Hierarchy of `h1`, `h2`, `h3` tags
- **`CrawlResult` updates**:
  - `network_calls: list[dict[str, Any]] = Field(default_factory=list)`
  - `dom_elements: dict[str, Any] = Field(default_factory=dict)`

---

### B. Element Extraction Engine (`src/ethical_crawler/extractors/element_inspector.py`)
- `ElementInspector`:
  - `inspect_html(html: str) -> dict[str, Any]`: Analyzes raw HTML using BeautifulSoup to extract structured inventories for buttons, forms, tables, and headings with recommended resilient CSS selectors (`#id`, `.class-name`, `[name="..."]`, `button:has-text(...)`).
  - `query_selector(html: str, selector: str) -> list[dict[str, Any]]`: Queries any CSS selector against the DOM, returning count, tag, text, attributes (`href`, `value`, `src`, `data-*`, `aria-*`), and inner HTML preview.

---

### C. Engine Integrations (`src/ethical_crawler/engines/`)
- **`BrowserEngine` (`browser_engine.py`)**:
  - Attach Playwright network event listener `page.on("response", ...)`:
    - Listen for `resource_type in ("fetch", "xhr")` or `application/json` in `content-type`.
    - Asynchronously capture status code, method, request body, and response JSON / text payload safely.
    - Collect network calls across the initial navigation and any subsequently executed RPA actions.
  - Run `ElementInspector.inspect_html(raw_html)` to populate `CrawlResult.dom_elements`.
- **`HttpEngine` (`http_engine.py`)**:
  - Run `ElementInspector.inspect_html(html)` so static HTTP crawls also benefit from DOM element inspection and selector testing.

---

### D. API Endpoints (`src/ethical_crawler/api/v1/router.py`)
- `POST /api/v1/elements/check`:
  - Input: `url: str | None`, `html: str | None`, `selector: str`
  - Output: Matches found, tag name, inner text, attributes, and visibility status.
- Ensure all crawl and scrape responses properly serialize `network_calls` and `dom_elements`.

---

### E. Web UI Dashboard (`src/ethical_crawler/api/app.py`)
- In the **Page Preview Modal** (`#previewModal`), add two new tabs:
  1. **🌐 Network APIs Tab (`#viewNetworkTab`)**:
     - Metric badge showing count of intercepted API calls.
     - Search filter: filter endpoints by URL or keywords (`products`, `pricing`, `graphql`, `search`).
     - Status filter: All, 2xx (Success), 4xx/5xx (Errors).
     - Interactive cards: Method badge (`GET`/`POST`), Status code badge, Endpoint URL, Request body viewer, and Formatted JSON Response viewer with a **"Copy JSON"** button.
  2. **🔍 DOM Elements Tab (`#viewElementsTab`)**:
     - **Live CSS Selector Tester / Element Checker**:
       - Text input for any CSS selector (e.g. `button.pricing-tier`, `form input[type="email"]`, `h2`, `table`).
       - Interactive **"Check Element"** button with instant match count and attribute inspection.
       - One-click **"Copy Selector"** to clipboard for quick insertion into RPA playbooks.
     - **Categorized Elements Inventory**:
       - 🔘 Buttons & Clickable CTAs
       - 📝 Form Controls & Inputs
       - 📊 Data Tables & Structures
       - 🏷️ Headings Outline

---

## 3. Verification Plan

### Automated Tests (`tests/test_network_and_elements.py`)
- Unit test `ElementInspector.inspect_html` with synthetic HTML containing forms, buttons, tables, and headings.
- Unit test `ElementInspector.query_selector` for valid and invalid CSS selectors.
- Unit test `BrowserEngine` mock network response listener for JSON interception.
- Unit test `POST /api/v1/elements/check` API endpoint.
- Run full test suite (`pytest tests/`) ensuring 100% pass rate.

### Manual Verification
- Launch server `./crawler serve`.
- Scrape dynamic web page and open Preview Modal.
- Validate **🌐 Network APIs** tab displays live captured JSON endpoints.
- Validate **🔍 DOM Elements** tab displays categorized elements and tests selectors interactively.

