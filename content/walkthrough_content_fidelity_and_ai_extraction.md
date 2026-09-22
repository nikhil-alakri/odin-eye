# Walkthrough: Content Fidelity Resolution & AI-Native Extraction System

**Date & Time**: 22-Sep-2026 01:18

---

## 🎯 Executive Summary

This walkthrough documents the end-to-end resolution of two major issues identified when crawling dynamic client-rendered websites (such as `https://plexis.in/`):

1. **Page Content Fidelity Issues Resolved**:
   - **Dynamic Animated Counters**: Resolved `0+ Studios, 0+ Projects, 0+ Leads` by introducing an automated scroll-into-view loop with dynamic element stabilization so `50+ Studios, 100+ Projects, 1000+ Leads` are accurately captured.
   - **Semantic SVG Checkmarks & Comparison Tables**: Resolved blank tabular cells (`| | | | `) in pricing and feature comparison matrices by converting semantic SVG icons (`lucide-check`, `lucide-x`, `tick`) into clear Unicode indicators (`✓`, `✗`, `—`).
   - **Merged Words & Inline Element Spacing**: Fixed touching inline elements (such as `<span>Clients.</span><span>Track</span>`) that previously merged into `Clients.Track Every Step.` by enforcing whitespace between inline tags.
   - **Infinite Swiper Carousel Deduplication**: Filtered out infinite loop cloned elements (`.swiper-slide-duplicate`, `.slick-cloned`) so testimonials and quotes are not duplicated 2–3 times.
   - **Size 0 B Prevention**: Installed Playwright Chromium headless engine and added intelligent HTML metadata fallbacks so dynamic SPAs never yield 0 B markdown.

2. **AI Extraction System & Interactive Preview Integration**:
   - **1-Click On-Demand AI Extraction in Preview Modal**: Users can now click the **AI Extraction** tab in the preview modal of *any* crawled page to either view structured JSON or trigger an instant on-demand extraction with NVIDIA NIM (Llama 3.2 Vision) with schema selection (`Article`, `Product / Pricing / Services`, `FAQ`, `Custom`).
   - **Multi-Page AI Extraction in Crawler**: Added a toggle and schema selector to the **Website Crawler** tab so all crawled pages can be automatically structured with AI during the crawl.
   - **ChromaDB Vector Store Auto-Sync**: Structured AI JSON is automatically indexed and cached in ChromaDB alongside page embeddings.

---

## 🏗️ Detailed Changes Made

### 1. Browser Engine Dynamic Content Stabilization (`src/ethical_crawler/engines/browser_engine.py`)
- React and Vue Single Page Applications often use `IntersectionObserver` counters (e.g. `CountUp.js`) that remain at `0+` until scrolled into view.
- Added automated smooth-scrolling that scrolls through the entire page height to trigger all viewport-activated observers.
- Added a 1000ms stabilization delay before capturing the DOM to ensure numbers count up to their final animated values (`50+`, `100+`, `1000+`).

### 2. HTML Cleaner & Semantic SVG Preservation (`src/ethical_crawler/extractors/html_cleaner.py`)
- Indiscriminately stripping `<svg>` tags stripped checkmarks and crosses from pricing tables, creating empty cells.
- Semantic SVG mapper converts:
  - Checkmarks (`lucide-check`, `tick`, `emerald`, `success`) $\rightarrow$ `✓`
  - Crosses (`lucide-x`, `close`, `cross`, `cancel`) $\rightarrow$ `✗`
  - Minuses / dashes $\rightarrow$ `—`
- Strips duplicate cloned carousel items:
  - Removes `.swiper-slide-duplicate`, `.slick-cloned`, `[aria-hidden="true"].swiper-slide`, and `.embla__slide--clone`.
- Preserves whitespace between adjacent inline tags (`a`, `span`, `strong`, `em`, `b`, `i`) to prevent joined text like `Clients.Track`.
- Added metadata fallback so title, description, and OpenGraph tags are parsed even if page body is sparse.

### 3. On-Demand AI Extraction & Global Preview Modal (`src/ethical_crawler/api/app.py`)
- **Global Preview Modal**:
  - Re-designed with two top tabs: **Markdown** and **AI Extraction**.
  - If AI data exists: displays formatted JSON with `Copy JSON` and `Re-Extract` buttons.
  - If AI data does not exist yet: displays an interactive extraction card with:
    - Schema selector (`Article`, `Product/Pricing`, `FAQ`, `Custom`)
    - Custom prompt instruction input
    - `⚡ Extract with AI Now (NVIDIA NIM)` button with live spinner
  - On clicking extract, invokes `POST /api/v1/extract`, caches the result to ChromaDB, displays the JSON, and adds a `✨ AI` badge to the page row in the results table.
- **Website Crawler Form**:
  - Added `Extract AI Structured Data (Multi-Page)` checkbox and schema dropdown.
  - Wired parameters (`extract_ai`, `ai_schema`, `ai_prompt`) into `startCrawl()`.

### 4. Crawler Orchestration & Vector Cache (`src/ethical_crawler/crawler.py` & `router.py`)
- When `extract_ai` is enabled, the crawler automatically runs `ai_extractor.extract_structured` for every crawled page.
- Structured AI JSON is attached to `CrawlResult.ai_data` and saved to ChromaDB (`vector_store.upsert_page(result, ai_data=result.ai_data)`).
- If a page is served from cache, its cached `ai_data` is automatically restored. If AI extraction was requested but the cache lacked AI data, it extracts AI on-demand and updates ChromaDB.

---

## 🧪 Verification & Results

### 1. Test Suite Verification
All 40 unit and integration tests passed:
```
============================= 40 passed in 10.39s ==============================
```

### 2. Code Quality & Formatting
- `ruff check .` $\rightarrow$ Passed with 0 errors.
- `ruff format .` $\rightarrow$ Clean formatting applied.

### 3. Live Crawler & AI Extraction Verification
- Crawling `https://plexis.in/` using Headless Browser correctly extracts:
  - Hero statistics: `50+ Studios`, `100+ Projects`, `1000+ Leads` (no longer `0+`).
  - Pricing table: Features show clear `✓` and `✗` comparison checkmarks.
  - Testimonials: Render cleanly without duplicate clones.
  - Preview Modal: Allows 1-click on-demand AI extraction via NVIDIA NIM with instant JSON rendering.

