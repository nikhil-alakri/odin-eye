# 🕷️ Ethical AI-Native Web Crawler

A production-ready, open-source, ethical web crawler and data extraction framework built in Python 3.12+, strictly following the **4 Rules of Ethical Web Crawling** with modern AI-native and LLM-friendly extraction capabilities (compatible with **NVIDIA NIM** and **OpenAI** APIs).

---

## 🌟 Key Features & The 4 Ethical Rules

### 1. Check robots.txt (Rule 1)
- **Automatic Discovery**: Derives `{domain}/robots.txt` automatically.
- **Rule Matching**: Parses `User-agent`, `Allow`, `Disallow`, `Crawl-delay`, and `Sitemap` declarations.
- **Pre-fetch Verification**: Validates whether URLs are permitted before any fetch attempt.
- **In-Memory Cache**: High-performance domain policy cache with configurable TTL.
- **Resilient Fallback**: Gracefully handles missing (404), empty, or malformed `robots.txt` files.

### 2. Implement Politeness Delay & Rate Limiting (Rule 2)
- **Per-Domain Delays**: Enforces minimum delay (default 2.0s or honoring robots.txt `Crawl-delay`).
- **HTTP 429 Retry-After**: Parses and honors `Retry-After` response headers (seconds or HTTP-dates).
- **Concurrency Throttling**: Global and per-domain semaphore controls to prevent overwhelming servers.
- **Exponential Backoff**: Jittered backoff upon consecutive server errors (503/500).

### 3. Set Identifiable User-Agent Header (Rule 3)
- **Transparent Bot Identity**: Standard format `BotName/Version (+DocumentationURL; ContactEmail)`.
- **Customizable**: Configurable via `.env` or settings.
- **Polite Headers**: Sends `DNT: 1` (Do Not Track), standard `Accept`, and gzip compression.

### 4. Sitemap Discovery & Recursive Parsing (Rule 4)
- **Structured URL Discovery**: Directly parses `<urlset>` and `<sitemapindex>` to crawl target URLs without blind link crawling.
- **Compressed Sitemap Support**: Handles `.xml.gz` and gzip byte streams seamlessly.
- **Sitemap Mode**: Direct batch crawl from sitemaps with priority and lastmod filtering.

---

## 🤖 Modern AI-Native & Dual-Engine Architecture

- **Dual-Engine Crawling**:
  - **Fast Async Engine (`httpx`)**: Blazing fast, lightweight, and resource-efficient for static pages and APIs.
  - **Browser Engine (`playwright`)**: Headless browser for JavaScript SPAs with auto-escalation when empty DOM containers or loading placeholders are detected.
- **LLM-Friendly Content Cleaning**:
  - Strips ads, navigation bars, cookie banners, tracker scripts, SVG, and footer noise.
  - Generates clean, token-efficient GitHub-Flavored Markdown.
  - Extracts OpenGraph, Twitter cards, and JSON-LD structured schemas.
- **AI Structured Extraction Layer**:
  - Fully compatible with **NVIDIA NIM** (`https://integrate.api.nvidia.com/v1`, models like `meta/llama-3.3-70b-instruct`) and OpenAI API format.
  - Built-in Pydantic extraction schemas for `Article`, `Product`, `FAQ`, and `Custom` prompt instructions.
- **Multiple Export Formats**:
  - Output to JSON (with metadata envelope), JSONL, Markdown, Plain Text, CSV, PDF, or SQLite database.
- **Embedded ChromaDB Vector Knowledge Base & Caching**:
  - **Zero-Network Cache**: Automatically caches crawled pages locally; subsequent requests within TTL (default 7 days) resolve in 1ms with 0 network calls.
  - **Semantic Vector Search**: Search your crawled knowledge base by concepts and meaning (`crawler search "<query>"` or UI).
  - **Local RAG Q&A ("Chat with Crawled Sites")**: Ask natural language questions answered strictly from stored page context with source citations.
  - **1-Click Historical Re-Exports**: Re-export any previously crawled page to PDF, Markdown, Plain Text, JSON, or CSV anytime without re-crawling.
  - **Strict Non-Destructive Storage**: Uses safe `upsert` semantics that preserve all historical data.

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

### 1. Scrape a Single Web Page & Export to Any Format (PDF, MD, TXT, JSON, CSV)

```bash
# Rapid single-page scrape with instant terminal preview
crawler scrape https://example.com

# Scrape and export directly to a styled PDF document
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

### 3. Verify robots.txt Directives (Rule 1)

```bash
# Inspect allowed/disallowed rules and crawl-delay
crawler robots https://example.com

# Test specific path permission
crawler robots https://example.com --check /admin/settings
```

### 4. Parse and View Sitemap URLs (Rule 4)

```bash
# Inspect sitemap URLs and export to CSV
crawler sitemap https://example.com --output urls.csv
```

### 5. AI-Native Structured Data Extraction

Extract structured data using NVIDIA NIM or OpenAI models:

```bash
# Extract article summary and key points
crawler extract https://example.com/article --schema article --output article.json

# Extract e-commerce product specs and pricing
crawler extract https://store.example.com/product/123 --schema product

# Custom prompt extraction
crawler extract https://example.com/pricing --schema custom --prompt "Extract all pricing tiers, monthly costs, and feature limits"
```

### 6. Visual Document & Screenshot Parsing (Nemotron-Parse 2.0)

For complex document scans, PDF pages, charts, or full-page browser screenshots:

```bash
# Parse visual document image into layout-classified markdown & bounding boxes
crawler parse-image screenshot.png --task markdown_bbox
```

### 7. Semantic Vector Search, RAG Q&A, and Saved History (ChromaDB)

```bash
# Search stored crawled knowledge by semantic meaning
crawler search "pricing plans and refund policy"

# Ask an AI question answered strictly from previously crawled web pages
crawler ask "What are the core capabilities and API limits?"

# View list of all crawled pages stored in the local vector database
crawler history
```

### 8. Start Web Server & UI Dashboard

```bash
# Start FastAPI service and visual dashboard
crawler serve --host 0.0.0.0 --port 8000
```

- Open **Interactive Dashboard**: `http://localhost:8000`
  - Includes **Website Crawler**, **Single Page Scraper**, and **🧠 Knowledge & History** tabs.
  - Interactive **1-Click Export Buttons**: 📄 PDF, 📝 Markdown, 📃 Plain Text, 🗄️ JSON, 📊 CSV.
  - Built-in **Semantic Search Bar** and **Ask AI (RAG)** assistant.
  - Re-export historical crawls instantly without re-crawling.
- Open **Swagger REST API Docs**: `http://localhost:8000/docs`

---

## 🌐 REST API Endpoints

| Method | Endpoint | Description |
|:-------|:---------|:------------|
| `GET` | `/health` | Service health status and bot User-Agent |
| `POST` | `/api/v1/scrape` | Immediate single-page scrape with optional AI extraction |
| `GET/POST`| `/api/v1/scrape/export` | Scrape any URL and stream back as `.pdf`, `.md`, `.txt`, `.json`, or `.csv` |
| `POST` | `/api/v1/crawl` | Start asynchronous crawl job (returns `job_id`) |
| `GET` | `/api/v1/jobs/{job_id}` | Check status and results of a crawl job |
| `GET` | `/api/v1/jobs/{job_id}/export` | Download crawl results in requested format (`?format=pdf\|md\|txt\|json\|csv`) |
| `GET` | `/api/v1/history` | Retrieve list of all pages persistently stored in ChromaDB |
| `GET` | `/api/v1/history/page` | Retrieve full cached markdown and metadata for a stored page |
| `GET` | `/api/v1/history/export`| 1-Click re-export of a cached page to PDF, MD, TXT, JSON, or CSV |
| `GET` | `/api/v1/search` | Semantic vector search across all stored web pages (`?q=...&domain=...`) |
| `POST` | `/api/v1/ask` | RAG Q&A answering questions strictly from crawled web pages with citations |
| `GET` | `/api/v1/robots?url={url}` | Retrieve parsed robots.txt directives |
| `GET` | `/api/v1/sitemap?url={url}` | Retrieve all URLs declared in sitemap.xml |
| `POST` | `/api/v1/extract` | Extract structured schema using NVIDIA NIM / OpenAI |

---

## 🧪 Running Tests

```bash
# Run all unit and scenario tests
make test
# Or directly with pytest:
.venv/bin/pytest -v

# Run code linter and formatter
make lint
make format
```

---

## 🛡️ Edge-Case Handling & Reliability

1. **Spider Traps & Endless Loops**: Tracking parameters (`utm_*`, `ref`, `sessionid`) and URL fragments are stripped; URLs are normalized and deduplicated; strict `max_depth` limits prevent infinite loops.
2. **Non-HTML & Binary Files**: Content-Type header streaming check rejects multi-gigabyte ISOs, PDFs, videos, and archives before downloading bodies.
3. **HTTP 429 Rate Limiting**: Honors `Retry-After` headers and pauses domain workers dynamically.
4. **JavaScript SPAs**: Auto-escalates from lightweight HTTP to Playwright headless browser when empty container roots are detected.

---

## 📄 License

MIT License. Free and open-source for personal and commercial use.

