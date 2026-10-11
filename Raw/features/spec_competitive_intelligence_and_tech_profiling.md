# 09-Oct-2026 01:25

# Feature Specification: Competitive Intelligence & Technology Stack Profiling (Feature 5)

## 1. Executive Summary & Problem Statement
Currently, the crawler stores crawled pages and can generate individual website dossiers. However, modern competitive intelligence workflows require two critical automated capabilities:
1. **Automated Technology Stack Fingerprinting**: Passively detecting what frontend frameworks (React, Next.js, Vue), CMS (WordPress, Shopify, Webflow), analytics platforms (Google Analytics, Mixpanel), and infrastructure/CDNs (Cloudflare, AWS, Vercel) a competitor uses without active intrusive scanning.
2. **Multi-Domain Side-by-Side Competitive Benchmarking**: Allowing users to select 2 to 5 indexed competitor domains from their ChromaDB knowledge base and automatically generating a unified comparative intelligence report (Feature matrix, Pricing comparison, Target audience breakdown, and Tech stack disparity).

---

## 2. Skill Alignment & Methodology (`.agents/skills`)

| Specialized Agent Skill | Applied Architecture & Operational Discipline |
| :--- | :--- |
| **`product-trend-researcher` & `product-manager`** | - Structured Competitive Analysis Framework:<br>  * Tier 1: Core Value Proposition & Positioning<br>  * Tier 2: Feature Matrix (Present, Partial, Missing)<br>  * Tier 3: Pricing & Packaging Strategy (Freemium, Per-seat, Usage, Enterprise)<br>  * Tier 4: Customer Profile & Industry Focus. |
| **`academic-statistician`** | - Quantitative Benchmarking Metrics:<br>  * Content Depth (average word count, page volume)<br>  * Information Density & Link Ratio (internal vs. external link connectivity)<br>  * Pricing Variance across competitor offerings. |
| **`engineering-knowledge-graph-engineer`** | - Cross-Domain Entity Linking: Extracts common product offerings and identifies market overlaps and gaps.<br>- Graph-structured comparison data models linking competitor nodes by market category. |
| **`engineering-backend-architect`** | - Passive, non-intrusive fingerprinting using regex pattern dictionaries across:<br>  1. HTTP Response Headers (`Server`, `X-Powered-By`, `Via`, `CF-Ray`)<br>  2. HTML Meta Tags (`<meta name="generator">`)<br>  3. DOM Script & CSS CDNs (`_next/static`, `wp-content`, `shopify.com`, `gtag/js`).<br>- High-performance in-memory matching with zero latency penalty. |

---

## 3. Technical Architecture & Component Specification

```
                                  [Crawl / Scrape Result]
                                             |
                         +-------------------+-------------------+
                         |                                       |
                 HTTP Headers                                HTML Content
                         |                                       |
                         v                                       v
             [Passive Header Scanner]                 [HTML & Script Scanner]
             - Cloudflare, Vercel, AWS               - React, Next.js, Vue, Nuxt
             - Nginx, Cloudfront                     - WordPress, Shopify, Webflow
                         |                           - GA4, PostHog, Intercom
                         +-------------------+-------------------+
                                             |
                                             v
                                  [TechProfiler Result]
                                  Category: { CMS, Frameworks, Analytics, CDN }
                                             |
                                             v
                                  Stored in ChromaDB Metadata
                                             |
                               +-------------+-------------+
                               |                           |
                     Single Domain Display        Multi-Domain Benchmark
                     (Tech Stack Badges)          (Select 2-5 Competitors)
                                                           |
                                                           v
                                            [Competitor Comparator Engine]
                                            - Gathers all domain pages & profiles
                                            - Synthesizes Comparative Matrix
                                            - Side-by-Side Table & Insights
                                                           |
                                                           v
                                            PDF / Markdown Dossier Export
```

### A. Technology Stack Fingerprint Engine (`src/ethical_crawler/extractors/tech_profiler.py`)
Class `TechnologyProfiler`:
- **Pattern Signatures (`TECH_SIGNATURES`)**:
  - **Frameworks**: Next.js (`__NEXT_DATA__`, `_next/static`), React (`react-dom`, `data-reactroot`), Vue (`v-data`, `__vue__`), Nuxt (`__NUXT__`), Svelte (`svelte-`), Angular (`ng-version`).
  - **CMS & Platforms**: Shopify (`cdn.shopify.com`, `Shopify.theme`), WordPress (`wp-content`, `wp-includes`), Webflow (`webflow.js`), Ghost (`ghost.org`), Squarespace (`squarespace.com`).
  - **Analytics & Marketing**: Google Analytics 4 (`gtag/js`, `google-analytics.com`), PostHog (`posthog.js`), Segment (`analytics.js`), Intercom (`widget.intercom.io`), Hotjar (`hotjar.com`).
  - **Infrastructure & CDN**: Cloudflare (`cf-ray` header), Vercel (`x-vercel-id`), AWS CloudFront (`x-amz-cf-id`), Fastly (`fastly-debug`), Netlify (`x-nf-request-id`).
- **Inspection Logic**:
  ```python
  def profile_technology(headers: dict, html: str) -> dict[str, list[str]]:
      # Evaluates headers and HTML against TECH_SIGNATURES
      # Returns categorized dictionary:
      # {"frameworks": ["Next.js", "React"], "cms": [], "analytics": ["PostHog"], "cdn": ["Vercel"]}
  ```

### B. Multi-Domain Competitor Comparator (`src/ethical_crawler/knowledge/competitor_comparator.py`)
Class `CompetitorComparator`:
- Accepts `domains: list[str]` (e.g. `["stripe.com", "paddle.com", "adyen.com"]`).
- Queries ChromaDB for structured company profiles, product lists, pricing pages, and tech stacks for each domain.
- Generates side-by-side Markdown comparison matrix:
  ```markdown
  | Criteria | Stripe | Paddle | Adyen |
  | :--- | :--- | :--- | :--- |
  | **Core Model** | Developer Payment APIs | Merchant of Record | Omnichannel Enterprise |
  | **Target Customer** | Tech startups to enterprises | SaaS & digital products | Global retail & enterprises |
  | **Pricing Structure** | 2.9% + 30¢ per transaction | 5% + 50¢ (includes tax MoR) | Interchange++ |
  | **Tech Stack** | React, Next.js, Cloudflare | Vue, Nuxt, AWS | React, Akamai |
  ```
- Supports full PDF synthesis using `StorageExporter.to_dossier_pdf()`.

### C. REST API Endpoints (`src/ethical_crawler/api/v1/router.py`)
- `POST /v1/tech-profile`: Passively analyze URL or HTML/headers and return detected technology stack.
- `POST /v1/competitors/compare`: Generate comparative intelligence report across 2–5 indexed domains.
- `GET /v1/competitors/compare/export`: Download comparative dossier as styled PDF or Markdown.

### D. Dashboard UI Integration (`src/ethical_crawler/api/app.py`)
- **Domain Cards in Knowledge View**:
  - Displays Tech Stack Pill Badges (e.g. `Next.js`, `React`, `Cloudflare`, `GA4`).
- **Competitor Benchmark Modal (`competitorModal`)**:
  - Multi-select domain checkboxes from stored knowledge base.
  - "Generate Comparison" button triggering real-time comparison matrix.
  - 1-click Download buttons (PDF and Markdown).

---

## 4. Scenarios & Edge Cases

| Scenario | Challenge | Architectural Resolution |
| :--- | :--- | :--- |
| **1. Obfuscated / Minimalist Stack** | Highly custom corporate site with zero public meta tags or generator strings. | Relies on HTTP response headers and script bundling conventions (`chunk`, `assets`); gracefully reports `Undetected` instead of false positives. |
| **2. Competitor With Incomplete Crawl** | Domain A has 50 pages indexed, but Competitor B only has 1 page indexed. | Highlights data completeness indicators in the matrix (`Stripe (50 pages) vs Competitor B (1 page - Partial)`). |
| **3. Complex Multi-Currency Pricing** | Pricing models span multiple tiers and currencies. | Normalizes comparison to base recurring rate or highlights model type (Usage vs. Seat-based). |

---

## 5. Acceptance Criteria & Test Verification Matrix

- [ ] `tests/test_tech_profiler.py`: Detects Next.js, React, WordPress, Cloudflare, and PostHog on mock headers and HTML with 100% precision.
- [ ] `tests/test_competitor_comparator.py`: Correctly synthesizes comparison matrix across multiple mock domains.
- [ ] PDF export compiles clean multi-column tables with ReportLab.
- [ ] All existing regression tests continue to pass.

