# Implementation Plan: Competitive Intelligence & Technology Stack Profiling (Feature 5)
**Date & Time**: 09-Oct-2026 02:08

## 1. Goal Description
Implement an automated Competitive Intelligence & Technology Stack Profiling engine that enables:
1. **Passive Technology Fingerprinting (`TechnologyProfiler`)**: Non-intrusively detects frontend frameworks (React, Next.js, Vue, Nuxt, Svelte, Angular), CMS/E-commerce platforms (WordPress, Shopify, Webflow, Squarespace), analytics & marketing tools (Google Analytics, PostHog, Segment, Intercom), and infrastructure/CDNs (Cloudflare, Vercel, AWS CloudFront, Fastly) using HTTP headers and HTML script/bundle patterns.
2. **Multi-Domain Competitor Benchmarking (`CompetitorComparator`)**: Queries ChromaDB across 2 to 5 indexed competitor domains to synthesize a unified side-by-side comparative matrix (Value Proposition, Target Audience, Features, Pricing Structure, and Technology Stacks).
3. **Multi-Format Intelligence Export**: Generates both clean Markdown and styled executive PDF reports via `StorageExporter.to_dossier_pdf()`.
4. **Interactive Dashboard UI**: Adds a Competitor Benchmark modal (`competitorModal`) with domain multi-select, real-time matrix generation, tech stack pill badges, and 1-click PDF/Markdown export.

---

## 2. User Review Required

> [!NOTE]
> Technology stack fingerprinting operates completely passively (in-memory regex inspection on existing crawl responses and headers). It sends zero intrusive or probe requests, strictly adhering to our ethical crawling principles.

> [!IMPORTANT]
> All existing ChromaDB vector records (145 indexed documents) will remain fully intact. Cross-domain queries are purely non-destructive read operations against existing stored collections.

---

## 3. Proposed Changes

### Component 1: Technology Profiler (`src/ethical_crawler/extractors/tech_profiler.py`) [NEW]
- Define signature catalog `TECH_SIGNATURES` categorized into:
  - `frameworks`: Next.js, React, Vue, Nuxt, Svelte, Angular, Remix, Astro, Gatsby.
  - `cms`: Shopify, WordPress, Webflow, Ghost, Squarespace, Wix, Magento, Drupal.
  - `analytics`: Google Analytics 4, PostHog, Segment, Mixpanel, Intercom, HubSpot, Hotjar.
  - `infrastructure`: Cloudflare, Vercel, AWS CloudFront, Fastly, Netlify, Nginx, Apache.
- Class `TechnologyProfiler`:
  - `profile(headers: dict | None, html: str | None, url: str | None) -> TechProfileResult`: Evaluates headers, HTML scripts, meta tags, and bundle tokens to return categorized technologies with confidence and match evidence.
  - `profile_url(url: str, user_agent: str | None) -> TechProfileResult`: Asynchronously fetches and profiles a target URL.

### Component 2: Multi-Domain Competitor Comparator (`src/ethical_crawler/knowledge/competitor_comparator.py`) [NEW]
- Class `CompetitorComparator`:
  - `compare_domains(domains: list[str], custom_focus: str | None = None) -> CompetitorComparisonResult`:
    - Retrieves stored page summaries, metadata, and extracted content for each domain from ChromaDB.
    - Detects tech profiles for each domain.
    - Uses NVIDIA NIM LLM (or deterministic fallback synthesis if API key is not provided) to build a structured comparison matrix across 5 tiers:
      * Core Value Proposition & Positioning
      * Target Customer & Audience
      * Feature & Product Matrix
      * Pricing & Packaging Strategy
      * Technology Stack Disparity
    - Outputs Markdown matrix and structured JSON.
  - `export_pdf(comparison: CompetitorComparisonResult, output_buf_or_path)`: Uses `StorageExporter.to_dossier_pdf()` to compile an executive-grade styled PDF.

### Component 3: API Layer (`src/ethical_crawler/api/v1/router.py`) [MODIFY]
- Models:
  - `TechProfileRequest`, `TechProfileResponse`
  - `CompetitorCompareRequest`, `CompetitorCompareResponse`
- Endpoints:
  - `POST /v1/tech-profile`: Profiles a URL or supplied headers/HTML.
  - `POST /v1/competitors/compare`: Generates side-by-side competitive matrix across 2-5 domains.
  - `POST /v1/competitors/compare/export`: Exports the generated comparison to PDF or Markdown with proper download headers.

### Component 4: Dashboard UI (`src/ethical_crawler/api/app.py`) [MODIFY]
- Header Navigation: Add `⚔️ BENCHMARK` button next to `⏰ MONITORS` and `🎨 THEME STUDIO`.
- Competitor Benchmark Modal (`#competitorModal`):
  - Domain selector with checkboxes for all indexed domains in the knowledge base.
  - "Run Benchmark" button with progress indicator.
  - Side-by-side interactive comparative table card.
  - Download buttons: `📄 Download PDF` and `📝 Download Markdown`.
- Domain Cards in Knowledge View: Render detected Tech Stack Pill Badges.
- Register modal in `MODAL_IDS` and `closeTopModal()`.

---

## 4. Verification Plan

### Automated Tests
1. `tests/test_tech_profiler.py` [NEW]:
   - Test detection of React, Next.js, and WordPress from mock HTML tags and script paths.
   - Test detection of Cloudflare, Vercel, and CloudFront from HTTP response headers.
   - Test handling of empty or minimal HTML without false positives.
2. `tests/test_competitor_comparator.py` [NEW]:
   - Test competitor matrix generation across mock domain knowledge records.
   - Test PDF report generation without errors.
   - Test API endpoints `/v1/tech-profile` and `/v1/competitors/compare`.
3. Full regression run: `pytest tests/` (expecting 92+ tests passing).

### Manual Verification
- Verify `⚔️ BENCHMARK` button in dashboard header opens `competitorModal`.
- Test selecting indexed domains to generate a live side-by-side comparative matrix.
- Test PDF download button to ensure ReportLab generates the styled multi-column report.

