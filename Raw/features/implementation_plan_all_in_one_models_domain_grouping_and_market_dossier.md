# Implementation Plan: Multi-Model NVIDIA NIM, Domain Grouping & Market Dossier Engine

**Date & Time**: 22-Sep-2026 02:07

---

## 🎯 Executive Overview

This plan defines the comprehensive implementation of three major capabilities requested by the user:

1. **Multi-Model NVIDIA NIM Integration**:
   - Support dynamic model selection across the entire crawler application (`moonshotai/kimi-k3`, `nvidia/nemotron-3.5-lightning-30b-a3b`, `z-ai/glm-5.3-flash`, `nvidia/nemotron-parse-2.0`, `meta/llama-3.2-11b-vision-instruct`).
   - Add model selector dropdowns in the Crawler Form, Scraper Form, Preview Modal, and Dossier Generator.
2. **Domain Grouping, Deletion Controls & Website Growth Tracking**:
   - Group stored pages in ChromaDB by **Domain** into modern, collapsible accordion cards with aggregate statistics (page count, total size, last updated).
   - Add safe **Selective Deletion**: Delete individual page (trash icon) and Delete entire domain.
   - Evolve the cache into **Website Evolution & Growth Tracking**: When re-crawling with cache disabled or clicking "Re-crawl", track revisions (`v2`, `v3`), compute content size growth deltas (`growth_delta_bytes`), and display update badges in the UI.
   - Add top KPI metric widgets (Tracked Domains, Embedded Pages, Knowledge Base Size, AI Profiles).
3. **Multi-Competitor Market Intelligence Dossier & Central Guidebook (Use Case A)**:
   - Introduce an executive synthesis engine using `moonshotai/kimi-k3` (or `glm-5.3-flash`).
   - Select 1 or more crawled domains (e.g. `plexis.in` and competitor sites) to automatically generate:
     - Side-by-side feature comparison table
     - Pricing tier matrix
     - Target audience overlap
     - Value proposition & market gap analysis
     - Strategic recommendations
   - 1-click export of the generated dossier to PDF and Markdown.

---

## 🛡️ Database Preservation & Safety Confirmation

> [!IMPORTANT]
> - All deletion operations (`delete_page`, `delete_domain`) are strictly user-directed through explicit UI actions (with confirmation modal) or explicit API calls.
> - No automated, wildcard, or seed-script deletions will ever occur, preserving the integrity of all user knowledge in accordance with `.agents/rules/database-preservation.md`.

---

## 🏗️ Detailed Proposed Changes

### 1. Multi-Model Architecture & Types

#### [MODIFY] [`types.py`](file:///Users/nikhilalakri/Developer/web-crawler/src/ethical_crawler/types.py)
- Add `NvidiaModelPreset` enum or constants:
  - `MOONSHOT_KIMI_K3 = "moonshotai/kimi-k3"`
  - `NEMOTRON_LIGHTNING = "nvidia/nemotron-3.5-lightning-30b-a3b"`
  - `GLM_FLASH = "z-ai/glm-5.3-flash"`
  - `NEMOTRON_PARSE = "nvidia/nemotron-parse-2.0"`
  - `LLAMA_VISION = "meta/llama-3.2-11b-vision-instruct"`
- Add `ai_model: str | None = None` to `CrawlRequest` and `ScrapeRequest`.
- Add `MarketDossierRequest` and `MarketDossierResult` schemas.

#### [MODIFY] [`config.py`](file:///Users/nikhilalakri/Developer/web-crawler/src/ethical_crawler/config.py)
- Declare supported model presets in settings.

#### [MODIFY] [`ai_extractor.py`](file:///Users/nikhilalakri/Developer/web-crawler/src/ethical_crawler/extractors/ai_extractor.py)
- Ensure dynamic `model` parameter is respected in all extraction calls.
- Optimize prompts for fast MoE models (`nemotron-3.5-lightning`) and massive context models (`kimi-k3`).

---

### 2. Domain Grouping, Deletion & Growth Tracking

#### [MODIFY] [`vector_store.py`](file:///Users/nikhilalakri/Developer/web-crawler/src/ethical_crawler/vector_store.py)
- **Revision & Growth Tracking**:
  - In `upsert_page()`: Look up existing document. If found, preserve `first_crawled_at`, increment `revision_count`, compute `growth_delta_bytes = new_size - old_size`, set `last_updated_at`, and flag `is_updated = True`.
- **Selective Deletion**:
  - `delete_page(url: str) -> bool`: Deletes document by normalized ID.
  - `delete_domain(domain: str) -> int`: Queries all IDs with `domain == domain.lower()` and deletes them in a batch.
- **Domain Aggregation**:
  - `list_domains_summary(limit: int = 200) -> list[dict]`: Groups records by domain, returning page counts, total size, newest crawl timestamp, and list of page records.

#### [MODIFY] [`router.py`](file:///Users/nikhilalakri/Developer/web-crawler/src/ethical_crawler/api/v1/router.py)
- `DELETE /api/v1/history/page`: Delete individual page by URL.
- `DELETE /api/v1/history/domain`: Delete all pages under domain.
- `GET /api/v1/history/domains`: Grouped domain summaries.
- `POST /api/v1/history/recrawl`: Live re-crawl of page or domain with `use_cache=False` to detect updates and record revisions.

---

### 3. Multi-Competitor Market Dossier Engine

#### [NEW] [`dossier_generator.py`](file:///Users/nikhilalakri/Developer/web-crawler/src/ethical_crawler/knowledge/dossier_generator.py)
- Engine that:
  1. Accepts list of domain names (e.g. `["plexis.in"]` or multiple domains).
  2. Aggregates their structured company intelligence profiles, pricing, and key markdown chunks from ChromaDB.
  3. Formulates a structured prompt for `moonshotai/kimi-k3` (or `glm-5.3-flash`).
  4. Generates an **Executive Market Dossier & Central Guidebook**:
     - Industry positioning overview
     - Comparative feature matrix table
     - Pricing tier comparison table
     - Value proposition & target audience breakdown
     - Strategic gap analysis & market recommendations
  5. Returns formatted Markdown with interactive JSON data.

#### [MODIFY] [`router.py`](file:///Users/nikhilalakri/Developer/web-crawler/src/ethical_crawler/api/v1/router.py)
- `POST /api/v1/dossier/generate`: Generates executive dossier for selected domains.
- `GET /api/v1/dossier/export`: Exports dossier to PDF or Markdown.

---

### 4. Modernized Web UI Dashboard (`app.py`)

#### [MODIFY] [`app.py`](file:///Users/nikhilalakri/Developer/web-crawler/src/ethical_crawler/api/app.py)
- **Top Metric Cards**:
  - Tracked Domains (count)
  - Embedded Pages (count)
  - Knowledge Base Size (KB / MB)
  - AI Profiles Indexed
- **Model Selector Dropdown**:
  - Added to Crawler Form, Scraper Form, and Preview Modal:
    - `meta/llama-3.2-11b-vision-instruct` (Default Balanced)
    - `moonshotai/kimi-k3` (Long-Context Guidebook & Deep Synthesis)
    - `nvidia/nemotron-3.5-lightning-30b-a3b` (Ultra-Fast Planning & Extraction)
    - `z-ai/glm-5.3-flash` (Multimodal Reasoning & UI Teardown)
    - `nvidia/nemotron-parse-2.0` (Visual Document & Table Parser)
- **Domain Cards View**:
  - Hierarchical domain cards with favicon, domain name, page count badge, total size, and quick actions:
    - 🔍 `Search Domain`
    - 🔄 `Re-crawl Domain` (live growth tracking)
    - 📊 `Generate Dossier`
    - 🗑️ `Delete Domain`
  - Collapsible list of pages with:
    - Status code
    - Title & URL
    - Revision badge (e.g. `v2 (+240 B)`)
    - `✨ AI` badge
    - Actions: `Preview`, `1-Click Export` (PDF/MD/TXT/JSON), `Delete Page`.
  - View switch toggle: **"📁 Group by Domain"** (default) vs. **"📋 Flat Table"**.
- **Market Dossier Generator Panel & Modal**:
  - Domain multi-selector checkboxes
  - Model selector (`kimi-k3` recommended)
  - `⚡ Generate Market Dossier` button with progress indicator
  - Rendered dossier view with Markdown copy and PDF export buttons.
- **Delete Confirmation Modal**:
  - Safe confirmation modal displaying exactly which page or domain will be removed.

---

## 🧪 Verification Plan

### Automated Tests
- `pytest -v tests/test_vector_store.py`:
  - `test_delete_page`
  - `test_delete_domain`
  - `test_list_domains_summary`
  - `test_upsert_page_revision_and_growth_tracking`
- `pytest -v tests/test_scenarios.py`:
  - Test dossier generation mock with multi-domain context.
- `pytest -v`: Ensure all 41+ tests pass with 100% success.
- `ruff check .` and `ruff format .`: Maintain 0 lint/format issues.

### Manual Verification
- Launch `./crawler serve` and verify in the browser:
  - Model dropdown shows all 5 NVIDIA NIM models in Crawler, Scraper, and Preview Modal.
  - Domain cards neatly group `plexis.in` and `example.com`.
  - Delete `example.com/p1` $\rightarrow$ removes 1 page.
  - Delete domain `example.com` $\rightarrow$ deletes the domain card.
  - Re-crawl `plexis.in` with cache OFF $\rightarrow$ verifies revision badge updates to `v2`.
  - Select `plexis.in` $\rightarrow$ Click `⚡ Generate Market Dossier` using `kimi-k3` $\rightarrow$ verifies synthesized executive report renders and exports cleanly.

