# Web Scraping, Crawling & Multi-Format Export (PDF, MD, TXT, JSON, CSV)

## Overview
This plan implements end-to-end support for both **Single-Page Web Scraping** and **Multi-Page Web Crawling** with comprehensive **Multi-Format Export options** (`.pdf`, `.md`, `.txt`, `.json`, `.csv`, `.sqlite`). Users can run scraping and crawling through the CLI, REST API, and Web UI Dashboard, and immediately export/download clean, formatted results.

---

## User Review Required
> [!NOTE]
> All exports adhere to ethical standards. Single-page scraping respects `robots.txt` by default unless explicitly disabled, identifies the crawler via transparent User-Agent headers, and properly cleans HTML into structured Markdown and human-readable documents.

---

## Proposed Changes

### 1. CLI Commands (`src/ethical_crawler/cli.py`)
- **`crawler scrape <url>` [NEW COMMAND]**:
  - Purpose: Rapid single-page scraping without full recursive crawl queue overhead.
  - Options:
    - `--output` / `-o`: Target file path.
    - `--format` / `-f`: Export format (`pdf`, `md`, `txt`, `json`, `csv`). Auto-infers from extension or defaults to terminal display + specified format.
    - `--strategy` (`auto` | `http` | `browser`): Engine choice.
    - `--extract-ai` / `-a`: Optional simultaneous AI structured extraction (Article, Product, FAQ, Custom).
    - `--schema-type`, `--prompt`, `--api-key`.
- **`crawler crawl <url>` [ENHANCED]**:
  - Add `--format` / `-f` (`pdf`, `md`, `txt`, `json`, `csv`, `sqlite`) flag in addition to auto-detection from filename.
  - Support automatic `.pdf` generation with styled ReportLab layout.

### 2. REST API Endpoints (`src/ethical_crawler/api/v1/router.py`)
- **`POST /api/v1/scrape` [NEW ENDPOINT]**:
  - Request body: `url`, `strategy`, `extract_ai`, `schema_type`, `prompt`.
  - Performs single-page fetch, HTML cleaning, markdown conversion, metadata and link extraction, and optional AI structured extraction. Returns immediate JSON response.
- **`GET /api/v1/jobs/{job_id}/export` [NEW ENDPOINT]**:
  - Query param: `format` (`pdf`, `md`, `txt`, `json`, `csv`, `jsonl`).
  - Returns `StreamingResponse` / `Response` with proper `Content-Type` (`application/pdf`, `text/markdown`, `text/plain`, `text/csv`, `application/json`) and `Content-Disposition: attachment; filename="..."`.
- **`POST /api/v1/scrape/export` [NEW ENDPOINT]**:
  - Single-call scraper that immediately streams back the exported file in the requested format (PDF, MD, TXT, CSV, JSON).

### 3. Web UI Dashboard (`src/ethical_crawler/api/app.py`)
- **Mode Toggle / Tabs**:
  - Tab 1: **"Single Page Scraper"** (Target URL, Strategy, AI Extraction toggle).
  - Tab 2: **"Website Crawler"** (Max pages, Max depth, Politeness delay, Sitemap mode).
- **Interactive Export Actions**:
  - Under results, provide dynamic export buttons:
    - 📄 **Export PDF** (instant download styled PDF)
    - 📝 **Export Markdown** (`.md`)
    - 📃 **Export Plain Text** (`.txt`)
    - 🗄️ **Export JSON** (`.json`)
    - 📊 **Export CSV** (`.csv`)
- **Scrape Result Card**:
  - Instant preview of title, status, cleaned markdown, internal/external links, and AI extraction data.

### 4. Storage & Formats (`src/ethical_crawler/storage.py`)
- Verify and harden:
  - `to_pdf`: Styled document template with header, metadata box, sanitized markdown headings and paragraphs, page numbers.
  - `to_text`: Clean ascii-bordered report.
  - `to_markdown`: Multi-page or single-page consolidated markdown.
  - `to_csv`: Summary metrics table.
  - `to_json`: Structured envelope with metadata.

---

## Verification Plan

### Automated Tests
- `tests/test_storage.py`: Test PDF, MD, TXT, JSON, CSV export functions with mock `CrawlResult`.
- `tests/test_cli_scrape.py` / `tests/test_scenarios.py`: Test CLI `crawler scrape` and `crawler crawl` with `--format pdf` and `--output`.
- `tests/test_api_export.py`: Test `POST /api/v1/scrape`, `GET /api/v1/jobs/{id}/export?format=pdf`, `POST /api/v1/scrape/export?format=md`.
- Run `pytest -v` across the entire test suite.
- Run `ruff check .` to maintain linting hygiene.

### Manual Verification
- Execute `./crawler scrape https://example.com -o example.pdf --format pdf` and verify PDF generation.
- Execute `./crawler scrape https://example.com -o example.md` and verify Markdown.
- Execute `./crawler scrape https://example.com -o example.txt` and verify Text.
- Start `./crawler serve` and verify Web Dashboard scraping and download buttons.
