# Implementation Plan - Robotic Process Automation (RPA) & Interactive Action Engine

**Date & Time**: 22-Sep-2026 03:28

## 1. Vision & Strategic Rationale: Why RPA for Ethical AI Crawler?

### The Shift in Market Landscape (2026–2028)
Traditional web crawlers are **passive readers**: they send a `GET` request, render the initial DOM, and extract text. However, modern SaaS, e-commerce, and enterprise applications hide their highest-value intelligence behind interactive barriers:
- **Pricing Toggles & Sliders**: Monthly vs. Annual discount toggles, user-seat sliders, feature matrix tab switches.
- **Search & Filter Forms**: Catalog navigation, currency/region selectors, quote calculators, SKU dropdowns.
- **Overlays & Dialogs**: GDPR/cookie consent prompts, newsletter popups, geo-location redirects that pollute or block page content.
- **Dynamic Accordions & Tabs**: Hidden specifications, expandable FAQs, "Read More" disclosures.
- **Pagination & Infinite Scrolling**: "Load More" buttons and paginated table queries.
- **Authenticated Dashboards**: Private portals, customer dashboards, and partner documentation behind authentication.

### How RPA Transforms the User Experience
By introducing a lightweight, ethical **Robotic Process Automation (RPA) Action Engine**:
1. **Deep Surface Coverage**: Users can crawl content that was previously unreachable by passive scrapers.
2. **Clean Noise-Free Ingestion**: Built-in automated dismissers wipe away modal popups and cookie banners before HTML is converted to Markdown.
3. **Reproducible Playbooks**: Users can save multi-step interactive workflows (e.g. *Login &rarr; Search Product &rarr; Filter Annual &rarr; Extract Data*) and execute them on schedules or with 1 click.
4. **Dual Interaction Modes**:
   - **Declarative Low-Code Builder**: Simple step list (`click`, `fill`, `wait`, `select`, `press_key`, `scroll`).
   - **AI-Guided Natural Language Directives**: Users type *"Click annual pricing and expand all tier details"*, and the AI translates it into deterministic Playwright actions.

---

## 2. Proposed Architecture & Components

```
┌────────────────────────────────────────────────────────────────────────┐
│                          User Interface (Web UI)                       │
│  - Interactive Action Sequence Builder (Drag/Add Steps)                │
│  - Natural Language RPA Prompt ("Dismiss cookie modal and click tab")  │
│  - Action Presets ("Dismiss Modals", "Toggle Annual", "Expand FAQs")   │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ Action Sequence JSON
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                        FastAPI REST Layer (/api/v1)                    │
│  - POST /api/v1/scrape  [adds rpa_steps: list[RPAStep]]                │
│  - POST /api/v1/crawl   [adds rpa_steps / auto_dismiss_banners]        │
│  - POST /api/v1/rpa/generate-actions [AI generates steps from intent]  │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                         RPA Execution Engine                           │
│  src/ethical_crawler/rpa/                                              │
│  ├── models.py       (Pydantic schemas: RPAStep, RPAActionType, etc.)  │
│  ├── executor.py     (Playwright step executor with retry/graceful)    │
│  └── presets.py      (Common recipes: Cookie banner bypass, accordions)│
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ Hooks into Page lifecycle
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                         Browser Engine (Playwright)                    │
│  1. page.goto(url)                                                     │
│  2. Run Pre-flight Hooks (Auto-dismiss common cookie/dialog banners)   │
│  3. Execute Custom RPASteps (click, fill, wait, select)                │
│  4. Settle & Snapshot HTML -> Markdown -> AI Extraction -> ChromaDB    │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Detailed Action Types Supported

| Action Type | Parameters | Example Use Case |
| :--- | :--- | :--- |
| `click` | `selector`, `optional: bool`, `wait_after_ms: int` | Click "Annual Pricing", "Accept Cookies", "Specifications" |
| `fill` | `selector`, `text`, `secret_env: str \| None` | Fill search inputs, zip codes, or login credentials safely |
| `select` | `selector`, `value` | Pick currency (USD/EUR), tier, or region dropdowns |
| `wait_for` | `selector`, `state: "visible" \| "hidden"`, `timeout_ms` | Wait for dynamic pricing tables or search results to load |
| `press_key` | `key: "Enter" \| "Tab" \| "Escape"` | Submit search queries or close modals with Escape |
| `hover` | `selector` | Reveal flyout menus, tooltips, or feature cards |
| `scroll` | `direction: "down" \| "up" \| "bottom"`, `pixels: int` | Trigger infinite loaders or specific section observers |
| `sleep` | `duration_ms: int` | Brief deliberate settle pause |

---

## 4. Phase-by-Phase Implementation Plan

### Phase 1: Core RPA Models & Action Engine (`src/ethical_crawler/rpa/`)
- [NEW] `src/ethical_crawler/rpa/models.py`:
  - Define `RPAActionType` enum (`click`, `fill`, `select`, `wait_for`, `press_key`, `hover`, `scroll`, `sleep`).
  - Define `RPAStep` Pydantic model with selector, value, timeout, optional flag (if element not found, don't crash the crawl).
  - Define `RPAResult` tracking execution log, step statuses, elapsed timing, and optional screenshots for debugging.
- [NEW] `src/ethical_crawler/rpa/executor.py`:
  - `RPAExecutor` class accepting Playwright `Page` and running ordered step sequences.
  - Safe error isolation: `optional=True` steps (e.g. cookie banners) log warnings instead of failing the crawl.
  - Built-in rate limiting and ethical delay compliance.
- [NEW] `src/ethical_crawler/rpa/presets.py`:
  - Ready-made action recipes:
    - `auto_dismiss_cookies`: Selectors for OneTrust, Cookiebot, Klaro, generic `#accept-cookies`, `[aria-label*="cookie"]`.
    - `expand_all_details`: Auto-expands `<details>` and common accordion triggers.
    - `toggle_annual_pricing`: Searches for switches with text "Annual", "Yearly", or classes `.annual-toggle`.

### Phase 2: Integration with `BrowserEngine` & API Schemas
- [MODIFY] `src/ethical_crawler/engines/browser_engine.py`:
  - Add `rpa_steps: list[RPAStep] | None = None` and `auto_dismiss_modals: bool = True` to `crawl()` parameters.
  - Integrate `RPAExecutor` execution right after page navigation and before markdown serialization.
- [MODIFY] `src/ethical_crawler/types.py`:
  - Add `rpa_steps` and `rpa_execution_log` to `CrawlRequest` and `CrawlResult`.
- [MODIFY] `src/ethical_crawler/api/v1/router.py`:
  - Expose RPA parameters in `/api/v1/scrape` and `/api/v1/crawl`.
  - Add `/api/v1/rpa/presets` to retrieve standard automation recipes.
  - Add `/api/v1/rpa/generate` endpoint using fast NIM model (`deepseek-ai/deepseek-v4.1-flash`) to convert natural language descriptions into valid `RPAStep` arrays.

### Phase 3: Web Dashboard UI Integration
- [MODIFY] `src/ethical_crawler/api/app.py`:
  - **RPA Playbook Section**: An expandable accordion inside the Scraper and Crawler panels labeled **"🤖 Robotic Process Automation (RPA Playbook)"**.
  - **Quick Action Recipes**:
    - Toggle: `[✓] Auto-Dismiss Cookie & Newsletter Banners`
    - Toggle: `[ ] Expand Collapsed Accordions / FAQs`
    - Toggle: `[ ] Toggle Annual Pricing`
  - **Interactive Step Builder**:
    - Add Step button: Action Type dropdown, Selector input, Value input, Optional checkbox.
  - **Natural Language RPA Copilot**:
    - Input: *"Dismiss popups, then click the 'Technical Specs' tab"* &rarr; clicks "Generate Steps" &rarr; populates the step list automatically.
  - **Live Execution Feedback**:
    - Shows step-by-step RPA execution status during crawl/scrape with individual step elapsed times.

---

## 5. User Review Required & Design Decisions

> [!IMPORTANT]
> **Ethical & Safety Guardrails**:
> 1. **No CAPTCHA Breaking**: Consistent with our ethical crawler principles, the RPA engine will **not** attempt to solve or circumvent CAPTCHAs/Cloudflare challenges; it will respect site friction and report high-friction status code 403/429.
> 2. **Credential Safety**: Sensitive inputs (passwords/API keys) will be supported via environment variable references (`secret_env: "PORTAL_PASSWORD"`) rather than raw plaintext values stored in the browser.
> 3. **Graceful Fallbacks**: All pre-flight banner dismissal steps will have `optional=True` and short timeouts (1.5s max) so they never slow down sites that don't have popups.

---

## 6. Verification Plan

### Automated Tests
- Unit test suite in `tests/test_rpa_executor.py`:
  - Test executing `click`, `fill`, `select`, `wait_for` on mock HTML pages in Playwright.
  - Test `optional=True` step handling when selectors are missing.
  - Test auto-dismiss cookie recipes.
- API test in `tests/test_api_rpa.py`:
  - Test `/api/v1/scrape` with `rpa_steps`.
  - Test `/api/v1/rpa/generate` with DeepSeek V4.1 Flash.

### Manual Verification
- Test on a real dynamic site with cookie prompts (e.g. GitHub explore, Wikipedia, or modern SaaS landing page).
- Verify before/after markdown output to prove hidden content was uncovered and modals dismissed.

