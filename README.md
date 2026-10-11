# 🕷️ Ethical AI-Native Web Crawler & Reverse-Engineering Platform

A production-ready, open-source, ethical web crawler, full-stack reverse-engineering suite, and intelligence framework built in Python 3.12+, strictly adhering to the **4 Rules of Ethical Web Crawling** with modern AI-native and multimodal extraction capabilities (compatible with **NVIDIA NIM** and **OpenAI** APIs).

---

## 📚 Quick Documentation Index

- **[📖 USAGE GUIDE (Why, When, Where, How, Time-Saving)](USAGE.md)**: Deep dive into all architectural capabilities, time savings, and step-by-step workflows.
- **[❓ FREQUENTLY ASKED QUESTIONS (FAQ)](FAQ.md)**: Answers regarding ethics, AI vision models, data preservation, and diff alerts.
- **[📁 Architecture & Feature Plans](Raw/features/)**: Detailed implementation plans, specs, and walkthroughs for every system feature.

---

## 🌟 Core System Capabilities

### 1. The 4 Rules of Ethical Web Crawling
- **Rule 1: Check `robots.txt`**: Automatically verifies allowed/disallowed paths and respects `Crawl-delay` and `Sitemap` declarations with in-memory TTL caching.
- **Rule 2: Politeness Delay & Rate Limiting**: Enforces per-domain delays, concurrency semaphores, and exponential backoff, honoring HTTP 429 `Retry-After`.
- **Rule 3: Identifiable User-Agent**: Sends transparent bot identification with version, documentation link, and contact email.
- **Rule 4: Sitemap Discovery**: Automatically parses XML and gzipped (`.xml.gz`) sitemaps for structured, non-invasive URL discovery.

### 2. Autonomous Visual Reverse-Engineering & Blueprint Synthesis
- **Domain Archetype Classification**: Identifies platform categories (Media & Studio Production, E-Commerce, DevTools, Enterprise SaaS).
- **Pixel Palette Extraction**: Samples screenshot pixels using Pillow (PIL) to extract authentic brand primary, accent, surface, and typography colors.
- **Relational Data Architecture (ERD)**: Infers complete backend database models with primary keys, foreign keys, data types, and multiplicities.
- **Inferred REST API Contracts**: Synthesizes endpoints, HTTP methods, headers, query params, request bodies, and expected responses.
- **Frontend Component Hierarchy**: Maps Atomic Design layouts into Organisms, Molecules, and Atoms.
- **Boardroom-Grade Executive PDF Export**: Assembles a publication-ready 6-page boardroom PDF report with clean typography and vector wireframes.

### 3. Scheduled Crawling, Content Diff Engine & Alerts
- **Cron-Scheduled Background Crawling**: Recurring crawlers monitor key pages on customizable cron intervals.
- **Normalized Content Diffing**: Strips dynamic noise, timestamps, and CSRF tokens to compute genuine content deltas.
- **Instant Webhook Alerts**: Dispatches formatted diff summaries to Slack or Discord when changes exceed configured thresholds.

### 4. Interactive CSS Element Selector & Visual Picker
- **Point-and-Click Selector Tool**: Safely loads websites in a sandboxed iframe with scripts stripped.
- **Resilient Selector Engine**: Calculates optimal CSS selectors and verifies matching element counts live in the browser.

### 5. Competitive Intelligence & Technology Profiler
- **Tech Stack Profiling**: Detects 40+ technologies across frameworks (React, Next.js, Vue), CMS (WordPress, Shopify), analytics (PostHog, GA4), and infrastructure.
- **Cross-Domain Competitive Matrix**: Compares multiple competitor websites side-by-side.

### 6. Embedded ChromaDB Vector Knowledge Base & Local RAG Q&A
- **Zero-Network Cache**: Stores crawled pages locally in ChromaDB; recurring queries resolve in 1ms with zero network requests.
- **Semantic Vector Search**: Search crawled knowledge by concept rather than just keywords.
- **Local RAG Q&A ("Chat with Crawled Sites")**: Ask natural language questions answered strictly from stored page context with source citations.
- **Strict Database Preservation**: Non-destructive upsert architecture ensures historical data is never wiped or lost.

---

## 🚀 Quick Start

### 1. Installation

```bash
# Clone repository
git clone https://github.com/your-username/ethical-crawler.git
cd ethical-crawler

# Setup virtual environment and install dependencies
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

# (Optional) Install browser engine for dynamic JS pages:
pip install -e ".[browser]"
playwright install chromium
```

### 2. Configuration (`.env`)

Copy `.env.example` to `.env` and customize as needed:

```bash
cp .env.example .env
```

Key environment variables:

```env
# Bot Identity
CRAWLER_BOT_NAME=EthicalCrawlerBot
CRAWLER_BOT_VERSION=1.0.0
CRAWLER_BOT_EMAIL=crawler-contact@example.com
CRAWLER_BOT_URL=https://github.com/example/ethical-crawler

# Politeness Settings
CRAWLER_DEFAULT_DELAY=2.0
CRAWLER_MAX_CONCURRENCY=5
CRAWLER_RESPECT_ROBOTS_TXT=true

# NVIDIA NIM / OpenAI API
CRAWLER_AI_BASE_URL=https://integrate.api.nvidia.com/v1
CRAWLER_AI_API_KEY=your_nvidia_or_openai_key_here
CRAWLER_AI_MODEL=meta/llama-3.3-70b-instruct
```

---

## 💻 CLI Usage

The CLI command is `./crawler` (or `crawler` when installed, or `python -m ethical_crawler.cli`).

### 1. Scrape & Export
```bash
# Rapid single-page scrape with instant terminal preview
crawler scrape https://example.com

# Scrape and export directly to a boardroom-grade PDF document
crawler scrape https://example.com --output page.pdf --format pdf

# Scrape and export to clean Markdown or Plain Text
crawler scrape https://example.com --output article.md
crawler scrape https://example.com --output summary.txt

# Scrape with simultaneous AI structured extraction (NVIDIA NIM / OpenAI)
crawler scrape https://example.com/article --extract-ai --schema article --output result.json
```

### 2. Crawl a Website Ethically
```bash
# Basic ethical crawl with live progress bar and table output
crawler crawl https://example.com --max-pages 5 --output results.json

# Crawl and export the entire site report into a consolidated PDF
crawler crawl https://example.com --max-pages 10 --output crawl_report.pdf --format pdf

# Crawl directly from sitemap.xml
crawler crawl https://example.com --sitemap --max-pages 10 --output sitemap_crawl.csv

# Crawl using Headless Browser for JavaScript-rendered sites
crawler crawl https://spa-example.com --strategy browser --output results.md
```

### 3. Verify robots.txt Directives
```bash
# Inspect allowed/disallowed rules and crawl-delay
crawler robots https://example.com

# Test specific path permission
crawler robots https://example.com --check /admin/settings
```

### 4. Semantic Search & Local RAG Q&A
```bash
# Search stored crawled knowledge by semantic meaning
crawler search "pricing plans and refund policy"

# Ask an AI question answered strictly from previously crawled web pages
crawler ask "What are the core capabilities and API limits?"

# View list of all crawled pages stored in the local vector database
crawler history
```

### 5. Launch Web Server & Visual Dashboard
```bash
crawler serve --host 0.0.0.0 --port 8000
```

- Open **Interactive Dashboard**: `http://localhost:8000`
- Open **Swagger REST API Docs**: `http://localhost:8000/docs`

---

## 🌐 REST API Endpoints

| Method | Endpoint | Description |
|:---|:---|:---|
| `GET` | `/health` | Service health status and bot User-Agent |
| `POST` | `/api/v1/scrape` | Immediate single-page scrape with optional AI extraction |
| `GET/POST` | `/api/v1/scrape/export` | Scrape any URL and stream back as `.pdf`, `.md`, `.txt`, `.json`, or `.csv` |
| `POST` | `/api/v1/crawl` | Start asynchronous crawl job (returns `job_id`) |
| `GET` | `/api/v1/jobs/{job_id}` | Check status and results of a crawl job |
| `GET` | `/api/v1/jobs/{job_id}/export` | Download crawl results in requested format (`?format=pdf\|md\|txt\|json\|csv`) |
| `GET` | `/api/v1/history` | Retrieve list of all pages persistently stored in ChromaDB |
| `GET` | `/api/v1/history/page` | Retrieve full cached markdown and metadata for a stored page |
| `GET` | `/api/v1/history/export` | 1-Click re-export of a cached page to PDF, MD, TXT, JSON, or CSV |
| `GET` | `/api/v1/search` | Semantic vector search across all stored web pages (`?q=...&domain=...`) |
| `POST` | `/api/v1/ask` | RAG Q&A answering questions strictly from crawled web pages with citations |
| `GET` | `/api/v1/robots?url={url}` | Retrieve parsed robots.txt directives |
| `GET` | `/api/v1/sitemap?url={url}` | Retrieve all URLs declared in sitemap.xml |
| `POST` | `/api/v1/extract` | Extract structured schema using NVIDIA NIM / OpenAI |
| `GET` | `/api/v1/blueprints/domains` | List domains with available screenshot collections for blueprinting |
| `POST` | `/api/v1/blueprints/generate` | Generate full reverse-engineered architecture blueprint from screenshots |
| `GET` | `/api/v1/blueprints/export/pdf` | Export publication-grade 6-page boardroom PDF blueprint |
| `POST` | `/api/v1/schedules` | Create automated cron crawl schedule with diff monitoring & webhooks |
| `GET` | `/api/v1/schedules` | List active crawl schedules and historical diff alerts |
| `GET` | `/api/v1/element-picker/sandbox` | Load URL inside interactive CSS selector picker sandbox |
| `POST` | `/api/v1/tech-profile` | Scan target website for frameworks, CMS, analytics & infrastructure |
| `GET` | `/api/v1/themes` | List available Design System Studio themes and styling presets |

---

## 🧪 Running Tests

```bash
# Run all unit and scenario tests
PYTHONPATH=src python3 -m pytest tests/ -v

# Run specific feature tests
PYTHONPATH=src python3 -m pytest tests/test_visual_blueprint.py -v
PYTHONPATH=src python3 -m pytest tests/test_diff_engine.py -v
PYTHONPATH=src python3 -m pytest tests/test_element_picker.py -v
PYTHONPATH=src python3 -m pytest tests/test_tech_profiler.py -v
```

---

## 🛡️ Edge-Case Handling & Reliability

1. **Spider Traps & Endless Loops**: Tracking parameters (`utm_*`, `ref`, `sessionid`) and URL fragments are stripped; URLs are normalized and deduplicated; strict `max_depth` limits prevent infinite loops.
2. **Non-HTML & Binary Files**: Content-Type header streaming check rejects multi-gigabyte ISOs, PDFs, videos, and archives before downloading bodies.
3. **HTTP 429 Rate Limiting**: Honors `Retry-After` headers and pauses domain workers dynamically.
4. **JavaScript SPAs**: Auto-escalates from lightweight HTTP to Playwright headless browser when empty container roots are detected.
5. **Database Preservation**: Strict non-destructive upsert policy guarantees zero data loss and persistent local caching.

---

## 📄 License

MIT License. Free and open-source for personal and commercial use.
