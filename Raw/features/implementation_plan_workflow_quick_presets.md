# Implementation Plan: Workflow Quick Presets Engine & Custom Preset Memory

**Date & Time:** 22-Sep-2026 02:22  
**Feature Name:** `workflow_quick_presets`

---

## 1. Goal Description
Upgrade the crawler and scraper UI by expanding the simplistic "Quick Presets" bar into an intelligent, 1-click **Workflow Configuration Engine**:
- Transform presets from primitive number setters into full-configuration macros (configuring Pages, Depth, Delay, Engine Strategy, AI Extraction On/Off, AI Schema, AI Model, and Cache Mode simultaneously).
- Add end-to-end workflow presets tailored for real-world use cases:
  - 🏢 **Competitor & Market Intel** (`kimi-k3` + `company_profile` + Auto engine)
  - 🧠 **RAG Knowledge Base Ingest** (35 pgs + sitemap + Fast HTTP + fresh ingest)
  - 🛍️ **E-Commerce & Product Catalog** (`nemotron-3.5-lightning` + `product` schema)
  - 🌐 **Dynamic SPA / React App** (Headless Chromium + 2.5s delay)
  - 🔄 **Live Site Growth Audit** (Vector cache OFF + live revision tracking)
  - 🛡️ **Ultra-Polite Research** (4s delay + strict robots)
  - ⚡ **Quick Smoke Test** (3 pgs + Fast HTTP)
- Introduce a Quick Presets bar to the **Single Page Scraper** form:
  - 🏢 Company Profile
  - 🛍️ Product Details
  - 📰 Clean Article
  - ⚡ Instant Markdown
  - 🖥️ Dynamic JS / Chromium
- Add a **Custom Preset Manager**: Save current form settings into browser `localStorage` and recall them in 1 click.

---

## 2. Proposed Changes

### [Frontend Dashboard UI]
#### [MODIFY] [app.py](file:///Users/nikhilalakri/Developer/web-crawler/src/ethical_crawler/api/app.py)
1. **Crawl Quick Presets Bar (lines 120-137)**:
   - Replace basic buttons with categorized badges having tooltips and distinct color accents.
   - Add "+ Save Current Preset" button and container for user-saved custom presets.
2. **Scrape Quick Presets Bar (inside scraperForm)**:
   - Add matching Quick Presets toolbar directly under Scraper Mode header.
3. **JavaScript Preset Engine**:
   - Define `CRAWL_PRESETS` and `SCRAPE_PRESETS` mapping dictionaries.
   - Implement `applyCrawlPreset(presetKey)`.
   - Implement `applyScrapePreset(presetKey)`.
   - Implement `saveCustomPreset()`, `loadCustomPresets()`, and `deleteCustomPreset(id)`.
   - Show temporary visual notification badge confirming which preset was loaded and what parameters were configured.

---

## 3. Verification Plan
- Verify all presets correctly update form fields (Engine, Sitemap, Delays, AI toggle, Schema, Model, Cache).
- Verify custom preset saving and loading via `localStorage`.
- Run automated test suite: `.venv/bin/pytest tests/`
- Run formatting and linting: `.venv/bin/ruff check --fix . && .venv/bin/ruff format .`

