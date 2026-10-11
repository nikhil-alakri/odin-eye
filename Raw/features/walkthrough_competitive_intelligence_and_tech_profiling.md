# Walkthrough: Competitive Intelligence & Technology Stack Profiling (Feature 5)
**Date & Time**: 09-Oct-2026 02:17

---

## 1. Overview & Objectives
The **Competitive Intelligence & Technology Stack Profiling** system provides automated, passive fingerprinting and multi-domain competitive benchmarking directly integrated into the ethical web crawler. Users can:
1. **Passively Fingerprint Technology Stacks**: Detect frontend frameworks, CMSs, analytics platforms, and cloud infrastructure/CDNs without sending invasive probe requests, adhering strictly to ethical data harvesting.
2. **Benchmark 2 to 5 Competitor Domains**: Compare indexed domains side-by-side from their ChromaDB vector knowledge base across value propositions, target audiences, core features, pricing strategies, and tech stacks.
3. **Multi-Format Intelligence Export**: Export unified executive benchmarking dossiers to formatted Markdown or styled, multi-column ReportLab PDFs.
4. **Interactive Dashboard Studio**: Trigger comparisons from domain cards or the header navigation bar via `#competitorModal`.

---

## 2. Key Components Delivered

### A. Technology Profiler (`src/ethical_crawler/extractors/tech_profiler.py`)
- **`TECH_SIGNATURES` Catalog**:
  - **Frameworks**: Next.js (`__NEXT_DATA__`, `/_next/static/`), React (`data-reactroot`, `react.production.min.js`), Vue.js (`data-v-`, `__vue__`), Nuxt.js, Svelte, Angular, Remix, Astro, Gatsby, Tailwind CSS, Bootstrap.
  - **CMS & E-Commerce**: WordPress (`/wp-content/`, meta generator), Shopify (`cdn.shopify.com`, `Shopify.theme`), Webflow (`webflow.js`, `data-wf-page`), Ghost, Squarespace, Wix, Magento, Drupal.
  - **Analytics & Marketing**: Google Analytics 4 (`gtag/js?id=G-`), PostHog (`posthog.com`, `posthog.init`), Segment, Mixpanel, Hotjar, Intercom, HubSpot, Plausible.
  - **Infrastructure & CDNs**: Cloudflare (`cf-ray`, `server: cloudflare`), Vercel (`x-vercel-id`), AWS CloudFront (`x-amz-cf-id`, `via`), Fastly, Netlify, Nginx, Apache.
- **Engine Logic**:
  - `profile(headers, html, url)`: In-memory regex evaluation returning categorized technologies (`TechProfileResult`), match confidence, and evidence paths.
  - `profile_url(url, user_agent)`: Live passive analysis with ethical HTTP headers and timeout controls.

### B. Competitor Comparator (`src/ethical_crawler/knowledge/competitor_comparator.py`)
- **Cross-Domain Data Gathering**:
  - Retrieves stored page summaries, metadata, and extracted content for each domain from ChromaDB.
  - Analyzes domain metrics: indexed pages, estimated content volume, value propositions, key features, pricing signals, and technology stacks.
- **Side-by-Side Matrix Synthesis**:
  - Constructs formatted Markdown tables comparing criteria across 2 to 5 competitors.
  - Generates comprehensive multi-section executive reports.
  - Optional AI enhancement via NVIDIA NIM / OpenAI models when API keys are configured, with deterministic fallback.
- **Executive PDF Export**:
  - Leverages `StorageExporter.to_dossier_pdf()` to compile styled, multi-page PDFs with section headers, metrics tables, and callouts.

### C. REST API Endpoints (`src/ethical_crawler/api/v1/router.py`)
- `POST /v1/tech-profile`: Analyzes supplied headers, HTML, or target URL.
- `POST /v1/competitors/compare`: Generates competitive matrix across 2-5 domains from ChromaDB.
- `POST /v1/competitors/compare/export`: Returns generated report as downloadable PDF (`application/pdf`) or Markdown (`text/markdown`).

### D. Visual Dashboard UI (`src/ethical_crawler/api/app.py`)
- **Header Navigation**: Added `⚔️ BENCHMARK` button next to `MONITORS` and `THEME STUDIO`.
- **Competitor Modal Dialog (`#competitorModal`)**:
  - Checkbox selection populated dynamically with all indexed domains in the ChromaDB knowledge base.
  - Custom focus input (e.g. pricing, AI features, security).
  - Progress state with spinner during synthesis.
  - Formatted side-by-side comparison table and detailed report sections.
  - 1-click Download buttons for PDF and Markdown.
- **Domain Cards in Knowledge View**:
  - Added `Compare` quick-action button to jump directly into benchmarking that domain.
- **Modal Registry**: Updated `MODAL_IDS`, `syncBodyScrollLock()`, and `closeTopModal()`.

---

## 3. Verification & Automated Tests
- **New Test Suites**:
  - `tests/test_tech_profiler.py` (5 tests): Validates framework detection, CMS/analytics detection, header infrastructure detection, empty content handling, and REST endpoint.
  - `tests/test_competitor_comparator.py` (4 tests): Validates table builder, minimum domain validation, mock multi-domain comparison, PDF generation, and export API endpoints.
- **Full Test Suite**: **97 passed in 26.05s** (100% pass rate across the entire repository).
- **Database Preservation**: Verified that `crawled_knowledge` ChromaDB collection count remains at 145 items with zero data loss.

