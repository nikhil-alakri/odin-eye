# Ethical AI-Native Web Crawler - Project Overview

## 📖 Project Summary

**Ethical AI-Native Web Crawler** is a production-ready, open-source Python framework (v0.1.0) for ethical web crawling and data extraction. Built with Python 3.12+ and strictly following the **4 Rules of Ethical Web Crawling**, it combines high-performance HTTP crawling with headless browser capabilities for JavaScript-rendered sites, and provides LLM-friendly content cleaning and AI-powered structured extraction.

The project is designed to be **AI-native** from the ground up, with built-in compatibility with NVIDIA NIM and OpenAI APIs, vector database caching via ChromaDB, and multiple export formats (JSON, Markdown, PDF, CSV, SQLite).

---

## 🏗️ Architecture

### High-Level Overview

```text
┌─────────────────────────────────────────────────────────────────┐
│                      Ethical Web Crawler                        │
├─────────────────────┬─────────────────────┬─────────────────┤
│       Core          │   Engines           │   Extraction    │
│  (robots, sitemap)  │ (HTTP + Browser)    │ (HTML Cleaner)  │
├─────────────────────┼─────────────────────┼─────────────────┤
│  Rate Limiting      │  AI Extraction      │  Vector Store   │
│  (Concurrency)      │ (NVIDIA NIM / OpenAI)│ (ChromaDB)     │
└─────────────────────┴─────────────────────┴─────────────────┘
                                       │
                                       ▼
                              ┌─────────────────┐
                              │   CLI & API     │
                              │  (Typer + FastAPI)│
                              └─────────────────┘
```

### Key Components

| Component | Description |
|-----------|-------------|
| **Core** | robots.txt parser, sitemap parser, rate limiter, concurrency controller |
| **Engines** | HTTPEngine (httpx-based, fast), BrowserEngine (Playwright-based, JS rendering) |
| **Extraction** | HTMLCleaner (noise removal, markdown conversion), AIExtractor (structured LLM output), MetadataExtractor (OG, JSON-LD) |
| **Vector Store** | ChromaDB-powered semantic cache with zero-network 1ms lookups |
| **CLI** | Typer-based command-line interface with 8+ commands |
| **API** | FastAPI with 20+ REST endpoints for programmatic access |

---

## ✨ Key Features

### 4 Rules of Ethical Web Crawling

1. **Rule 1: Check robots.txt** - Automatic discovery, rule parsing, pre-fetch verification, in-memory cache with TTL
2. **Rule 2: Politeness Delay & Rate Limiting** - Per-domain delays, HTTP 429 Retry-After handling, concurrency throttling, exponential backoff with jitter
3. **Rule 3: Identifiable User-Agent** - Transparent bot identity format, customizable via .env, polite headers (DNT, Accept, gzip)
4. **Rule 4: Sitemap Discovery** - Structured URL discovery from `<urlset>`, compressed sitemap support (.xml.gz), sitemap mode with priority/filtering

### AI-Native Capabilities

- **Dual-Engine Crawling**: Fast async (httpx) + Browser (Playwright) with auto-escalation
- **LLM-Friendly Content Cleaning**: Strips ads, nav bars, cookie banners, tracker scripts, SVG, footer noise
- **Structured Extraction Schemas**: Article, Product, FAQ, Company Profile, Custom prompts
- **NVIDIA NIM & OpenAI Compatibility**: `https://integrate.api.nvidia.com/v1` endpoint support
- **Multiple Export Formats**: JSON (with metadata), JSONL, Markdown, Plain Text, CSV, PDF, SQLite
- **ChromaDB Vector Knowledge Base**: Zero-network cache (1ms), semantic search, RAG Q&A, 1-click historical re-exports

### Reliability & Edge Cases

- Spider trap detection & URL deduplication
- max_depth limits to prevent infinite loops
- Non-HTML/binary file rejection (PDFs, videos, archives)
- JavaScript SPA auto-escalation from HTTP to Browser engine
- Graceful handling of missing/malformed robots.txt

---

## 🚀 Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/your-username/ethical-crawler.git
cd ethical-crawler

# Setup virtual environment and install dependencies
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

# Install browser engine for dynamic JS pages
pip install -e ".[browser]"
playwright install chromium
```

### Configuration

```bash
cp .env.example .env
```

Key `.env` variables:

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

### CLI Usage Examples

```bash
# Single page scrape with PDF export
crawler scrape https://example.com --output page.pdf --format pdf

# AI-structured extraction
crawler scrape https://example.com/article --extract-ai --schema article --output result.json

# Ethical crawl with progress bar
crawler crawl https://example.com --max-pages 5 --output results.json

# Sitemap inspection
crawler sitemap https://example.com --output urls.csv

# robots.txt verification
crawler robots https://example.com --check /admin/settings

# Semantic search
crawler search "pricing plans and refund policy"

# AI Q&A from crawled pages
crawler ask "What are the core capabilities and API limits?"

# Start web dashboard
crawler serve --host 0.0.0.0 --port 8000
```

---

## 📁 Project Structure

```
web-crawler/
├── .agents/                    # Agent configuration and skills
├── .env.example              # Environment variable template
├── .git/                     # Git version control
├── .gitignore               # Ignored files and directories
├── .venv/                    # Virtual environment
├── Makefile                 # Build/deployment commands
├── README.md                # User-facing documentation
├── pyproject.toml           # Project metadata and dependencies
├── content/                  # Example outputs and implementation plans
│   ├── example_ai.json
│   ├── example_crawl.pdf
│   ├── example_scraped.md
│   ├── example_scraped.pdf
│   ├── example_scraped.txt
│   └── ... (10 files total)
├── crawler/                  # Root for crawler script
├── data/                     # Persistent data
│   └── chroma/               # ChromaDB vector store persistence
├── opencode-glimmer-content/ # ← This folder: AI agent documentation
│   ├── PROJECT_OVERVIEW.md   # ← Project overview (this file)
│   ├── API_REFERENCE.md      # ← REST API documentation
│   ├── USAGE_GUIDES.md       # ← CLI and usage patterns
│   └── TECHNICAL_DESIGN.md   # ← Architectural diagrams and design
├── raw/                      # Raw feature documents
│   └── features/             # 17 implementation plan documents
├── src/                      # Source code (Python package)
│   └── ethical_crawler/      # Main Python package
│       ├── __init__.py       # Package init, version 0.1.0
│       ├── api/              # FastAPI endpoints (20+ REST routes)
│       ├── cli.py            # Typer CLI with 8 commands
│       ├── config.py         # Pydantic-settings configuration
│       ├── crawler.py        # Main EthicalCrawler orchestrator (BFS)
│       ├── core/             # Core rules (robots, sitemap, rate_limiter)
│       ├── engines/          # HTTP + Browser engines
│       ├── extractors/       # HTML cleaner, AI extractor, metadata
│       ├── knowledge/        # Dossier generator
│       ├── rpa/              # RPA executor for browser automation
│       ├── storage.py        # Multi-format export (JSON, PDF, CSV, etc.)
│       ├── types.py          # Pydantic models (CrawlResult, schemas)
│       └── vector_store.py   # ChromaDB integration
├── tests/                    # 15 test files (pytest suite)
│   ├── test_api.py
│   ├── test_crawler.py
│   ├── test_robots.py
│   ├── test_sitemap.py
│   └── ... (11 more)
├── .pytest_cache/            # pytest cache
├── .ruff_cache/              # ruff lint cache
└── Raw/                      # Raw data directory
```

---

## 🛠️ Development & Contributing

### Setup

```bash
# Install in development mode
make install

# Install browser dependencies
make install-browser

# Run the test suite
make test

# Linting
make lint

# Code formatting
make format
```

### Adding New Features

1. **Ethical Rules**: Add compliance checks in `core/` directory
2. **New Engine**: Implement `CrawlEngine` abstract base class in `engines/`
3. **New Extraction Schema**: Add Pydantic model in `types.py`, prompt builder in `ai_extractor.py`
4. **New Export Format**: Add method to `storage.py`, register extension in `save_file()`
5. **New CLI Command**: Add `@app.command()` decorator in `cli.py`
6. **New API Endpoint**: Add route in `api/app.py`, handler in `cli.py` or dedicated handler

### Testing

Run the full test suite:

```bash
make test
# Or directly:
.venv/bin/pytest -v
```

### Code Style

- Ruff linting: `make lint`
- Code formatting: `make format`
- Target Python: 3.12
- Line length: 100 characters (with E501 ignored for long docstrings)

---

## 📄 License

**MIT License** - Free and open-source for personal and commercial use.

Copyright (c) 2024 Nikhil Alakri

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.