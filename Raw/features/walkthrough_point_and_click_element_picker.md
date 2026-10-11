# Walkthrough: Interactive Point-and-Click Visual Element Picker
**Date & Time**: 09-Oct-2026 02:05

---

## 1. Overview & Objectives
The **Interactive Point-and-Click Visual Element Picker** provides a seamless, visual workflow for extracting data and targeting interactive RPA steps without requiring manual browser DevTools inspection. Users can load any target webpage in a sandboxed, security-hardened visual sandbox iframe, hover over elements to see live bounding highlights and generated CSS selectors, click an element to inspect it, and automatically inject or copy the selector into Scraper custom prompts or RPA execution steps.

---

## 2. Key Components Implemented

### A. Element Picker Engine (`src/ethical_crawler/extractors/element_picker.py`)
- **Visual Sandbox HTML Preparation**:
  - Automatically neutralizes frame breakout scripts (`window.top.location`, `parent.location`, `frameElement`).
  - Injects `<base href="...">` to ensure stylesheets, fonts, and relative images resolve accurately without breaking layout.
  - Injects a high-performance visual overlay script (`__ethic_element_picker_script__`).
- **Selector Synthesis Heuristics**:
  - `getBestSelector(el)` prioritizes clean IDs (filtering out auto-generated numbers), unique `data-testid` / `data-cy` / `data-qa` / `name` / `aria-label` attributes, semantic ARIA roles, clean class list permutations (filtering transient Tailwind pseudo-states like `hover:`, `focus:`), and hierarchical parent chaining.
  - Server-side fallback heuristic `generate_selector_from_bs4()` for BeautifulSoup Tag nodes.
- **Inter-Frame Communication**:
  - Captures element clicks with `e.preventDefault()` and `e.stopPropagation()` to prevent unwanted navigation.
  - Dispatches `postMessage({ type: 'ELEMENT_PICKED', selector, tagName, innerText, matchCount })` to the parent window.

### B. Sandbox REST API (`src/ethical_crawler/api/v1/router.py`)
- `GET /v1/elements/sandbox`:
  - Fetches the target URL with ethical headers and timeouts.
  - Passes the HTML through `ElementPicker.sanitize_and_prepare_html()`.
  - Serves `HTMLResponse` with `X-Frame-Options: SAMEORIGIN` and `sandbox="allow-scripts allow-same-origin"` isolation.

### C. Visual Dashboard Integration (`src/ethical_crawler/api/app.py`)
- **Scraper Tab Integration**: Added `🎯 Pick Element` button next to the Target Page URL input.
- **RPA Step Modal Integration**: Added `Visual Picker` quick-action button directly into the interactive RPA step creator dialog.
- **Full-Screen Modal Dialog (`#elementPickerModal`)**:
  - Real-time toolbar displaying the picked selector, tag badge, uniqueness counter (`1 unique match`), "Copy" button, and "Use Selector" action.
  - Loading spinner state while fetching and instrumenting DOM assets.
  - Integrated into `MODAL_IDS`, `syncBodyScrollLock()`, and `closeTopModal()`.
  - Event listener for `ELEMENT_PICKED` updating UI seamlessly.

---

## 3. Verification & Automated Tests
- **Test File**: `tests/test_element_picker.py`
  - `test_element_picker_sanitize`: Validates frame breakout neutralization, `<base href>` injection, and picker script injection.
  - `test_element_picker_heuristic`: Validates clean ID and class selector generation.
  - `test_element_sandbox_api`: Verifies HTTP 200 `text/html` response with headers and payload instrumentation.
- **Regression Suite**: All 88 tests in the full test suite passed cleanly (`88 passed in 23.58s`).
- **Database Preservation**: ChromaDB collection `crawled_knowledge` with 145 items preserved with 0 loss.

