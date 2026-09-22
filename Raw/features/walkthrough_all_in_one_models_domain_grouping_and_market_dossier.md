# Walkthrough: Multi-Model Intelligence, Domain Grouping & Change Tracking, and Market Intelligence Dossier

**Date & Time:** 22-Sep-2026 02:18  
**Feature Name:** `all_in_one_models_domain_grouping_and_market_dossier`  
**Status:** Completed & Validated (47/47 Tests Passing)

---

## 1. Executive Summary

This release delivers the complete end-to-end upgrade requested across the crawler architecture:
1. **Dynamic Multi-Model Intelligence Engine:** Native support for NVIDIA NIM's newest frontier models (`moonshotai/kimi-k3`, `nvidia/nemotron-3.5-lightning-30b-a3b`, `z-ai/glm-5.3-flash`, `nvidia/nemotron-parse-2.0`, and `meta/llama-3.2-11b-vision-instruct`) with schema selection (`company_profile`, `article`, `product`, `faq`, `event`) and custom prompt pass-through across Crawl, Scrape, and Preview modals.
2. **Domain Grouping, Selective Deletion & Temporal Change Tracking:**
   - Vector store archives are now intelligently grouped into collapsible Domain Accordions with domain-level KPIs (total pages, total size, AI profiles extracted).
   - Solved the vector cache dilemma: Instead of simply skipping or replacing pages, the system now tracks **revisions** (`v1`, `v2`, `v3`) and calculates **growth deltas** (`+340 B`, `-120 B`) while preserving the initial discovery timestamp.
   - Added database-preservation compliant selective deletion: Single pages or entire domains can be safely removed with a confirmation modal, without any risk of database wipes.
3. **Multi-Competitor Market Intelligence Dossier & Central Guidebook Generator:**
   - A dedicated multi-site synthesizer powered by `moonshotai/kimi-k3` and `nemotron-3.5-lightning` that compares competing domains stored in ChromaDB.
   - Generates executive landscape summaries, side-by-side comparative matrices, feature/pricing breakdowns, and strategic positioning insights with 1-click Markdown and PDF export.

---

## 2. Key Architecture & File Changes

### A. Data Models & Types (`src/ethical_crawler/types.py`)
- Added `ai_model: str | None` to `CrawlRequest`.
- Added `CompanyProfileSchema` and `ProductOffering` for business intelligence extraction.
- Added `MarketDossierRequest` and `MarketDossierResult` with `competitors_analyzed` and `markdown` accessors.

### B. AI Extractor (`src/ethical_crawler/extractors/ai_extractor.py`)
- Integrated `CompanyProfileSchema` schema handler.
- Added full support for dynamic model override per call.
- Enabled custom user prompt instructions combined with Pydantic JSON schemas.

### C. ChromaDB Vector Store Engine (`src/ethical_crawler/vector_store.py`)
- **Temporal Growth & Revision Tracking**: `upsert_page` checks if a document exists. If updated, it increments `revision_count`, preserves `first_crawled_at`, calculates `growth_delta_bytes = new_size - old_size`, and marks `is_updated = True`.
- **Selective Deletion**: Added `delete_page(url)` and `delete_domain(domain)` that safely purge specified IDs without touching other data.
- **Domain Aggregation**: Added `list_domains_summary(limit)` returning domain groups with total size, page count, AI profiles, and nested pages.

### D. Multi-Competitor Dossier Engine (`src/ethical_crawler/knowledge/dossier_generator.py`)
- Queries ChromaDB for domain contexts across multiple competitors.
- Constructs comprehensive comparative prompts.
- Calls `moonshotai/kimi-k3` or `nemotron-3.5-lightning` via NVIDIA NIM with robust local fallback.

### E. REST API Endpoints (`src/ethical_crawler/api/v1/router.py`)
- `GET /api/v1/history/domains`: Grouped domain summaries.
- `DELETE /api/v1/history/page`: Selective single-page deletion.
- `DELETE /api/v1/history/domain`: Selective domain group deletion.
- `POST /api/v1/history/recrawl`: Live re-crawl forcing network refresh to detect growth and revision increments.
- `POST /api/v1/dossier/generate`: Multi-domain market dossier synthesis.
- `GET /api/v1/dossier/export`: 1-click export of market dossiers to Markdown or PDF.

### F. Modernized UI Dashboard (`src/ethical_crawler/api/app.py`)
- **Glassmorphic KPI Metrics Bar**: 4 stat cards for Tracked Domains, Stored Pages, Vector Memory Size, and AI Profiles.
- **Domain Cards Accordion**: Collapsible cards per domain with domain badges, search focus button, dossier trigger, and domain deletion.
- **Revision Badges**: Visual indicator `v2 (+340 B)` on every updated page row.
- **Live Recrawl Action**: `🔄 Recrawl` button on each page triggers live fetch and updates revision counter.
- **Market Intelligence Dossier Modal**: Interactive domain selector checkboxes, model dropdown, custom strategic focus input, live preview, and PDF/MD export.
- **Safe Confirm Deletion Modal**: User confirmation dialog with clear warnings before deleting any page or domain.

---

## 3. Verification & Validation Results

### Automated Test Suite:
```bash
.venv/bin/pytest tests/
```
**Results:**
- `tests/test_api.py`: 6 passed
- `tests/test_crawler.py`: 7 passed
- `tests/test_headers.py`: 2 passed
- `tests/test_html_cleaner.py`: 5 passed
- `tests/test_rate_limiter.py`: 3 passed
- `tests/test_robots.py`: 5 passed
- `tests/test_scenarios.py`: 7 passed
- `tests/test_scrape_export.py`: 3 passed
- `tests/test_sitemap.py`: 4 passed
- `tests/test_vector_store.py`: 11 passed (including revision tracking, delete_page, delete_domain, list_domains_summary, and dossier generation)
**Total: 47 passed in 23.97s (100% Pass Rate)**

### Code Quality & Formatting:
```bash
.venv/bin/ruff check --fix . && .venv/bin/ruff format .
```
**Result:** All checks passed with 0 errors.

---

## 4. How to Use the New Features

1. **Launch the Server:**
   ```bash
   ./crawler serve --reload
   ```
   Open `http://localhost:8000` in your browser.

2. **Select Any NVIDIA NIM Model:**
   - When crawling or scraping, toggle **AI Structured Extraction**.
   - Choose `🧠 Moonshot Kimi-k3 (2.8T MoE Deep Reasoning)` or `⚡ Nemotron 3.5 Lightning`.
   - Choose Schema: `🏢 Company & Product Profile` to extract business model, value proposition, and product offerings.

3. **Browse Domain Groups & Change History:**
   - Navigate to the **Knowledge & History** tab.
   - See tracked websites grouped under domain accordions (e.g. `plexis.in`).
   - Click `🔄 Recrawl` on any page to fetch it live without cache. Watch its badge transition to `v2 (+340 B)`!

4. **Generate a Market Intelligence Dossier:**
   - Click `📊 Generate Market Dossier` at the top of the history tab.
   - Check the domains you want to compare.
   - Select `moonshotai/kimi-k3`.
   - Click **Generate Competitive Dossier**.
   - Review the executive positioning analysis and export directly to PDF or Markdown!

