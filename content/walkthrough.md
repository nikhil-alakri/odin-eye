# 🕷️ Web Scraping, Crawling & Multi-Format Export Walkthrough

## Summary of Completed Work
We have completed the full implementation for **Single-Page Web Scraping** and **Multi-Page Web Crawling** with comprehensive **Multi-Format Exports** (`.pdf`, `.md`, `.txt`, `.json`, `.csv`, `.sqlite`). Users can invoke these features via the CLI, REST API, or the interactive Web UI Dashboard.

---

## 🚀 Key Features Implemented

### 1. Dedicated Single-Page Web Scraping
- **CLI Command**: `crawler scrape <url>`
  - Extracts clean markdown, title, metadata, and link counts.
  - Supports `--format` (`pdf`, `md`, `txt`, `json`, `csv`) or direct file extension inference.
  - Supports simultaneous AI structured extraction: `--extract-ai --schema article|product|faq|custom --prompt "..."`.
  - Respects `robots.txt` directives by default (can be toggled with `--no-respect-robots`).
- **REST API Endpoints**:
  - `POST /api/v1/scrape`: Instant single-page scrape returning structured JSON containing cleaned markdown, metadata, and optional AI extraction.
  - `POST /api/v1/scrape/export`: Scrapes any URL and streams the resulting file download directly as PDF, Markdown, Plain Text, CSV, or JSON.

### 2. Multi-Page Ethical Web Crawling
- **CLI Command**: `crawler crawl <url>`
  - Enhanced with `--format` (`pdf`, `md`, `txt`, `json`, `csv`, `sqlite`) and auto-detection from `--output` filename.
  - Adheres strictly to the **4 Rules of Ethical Web Crawling**:
    1. Robots.txt parser and permission checking.
    2. Politeness delays (per-domain rate limiting, 429 Retry-After header handling).
    3. Transparent bot User-Agent identity with contact details.
    4. Recursive sitemap XML and Gzip discovery.
- **REST API Endpoints**:
  - `POST /api/v1/crawl`: Queues asynchronous crawl job.
  - `GET /api/v1/jobs/{job_id}`: Retrieves real-time status and crawled pages.
  - `GET /api/v1/jobs/{job_id}/export?format=...`: Streams file download of the entire crawl in the requested format.

### 3. Professional ReportLab PDF Generation
- Implemented `StorageExporter.to_pdf()`:
  - Document header with total page count and crawler identification.
  - Formatted metadata box with URL, status code, engine used, link metrics, and elapsed duration.
  - Heading recognition (`#`, `##`, `###`) converted into appropriately sized ReportLab styles.
  - Paragraph formatting, link stripping, and XML entity sanitization (`&amp;`, `&lt;`, `&gt;`).
  - Automatic page breaks between crawled pages with running headers.

### 4. Interactive Web UI Dashboard (`crawler serve`)
- Mode switch tabs:
  - **Website Crawler**: Target URL, max pages, max depth, polite delay, strategy, sitemap toggle.
  - **Single Page Scraper**: Target URL, strategy, robots.txt toggle, AI structured extraction options.
- **1-Click Export Toolbar**:
  - 📄 **Export PDF**: Instant download of styled PDF report.
  - 📝 **Export Markdown**: Full clean markdown file (`.md`).
  - 📃 **Export Plain Text**: Formatted ASCII table and text report (`.txt`).
  - 🗄️ **Export JSON**: Full structured metadata envelope (`.json`).
  - 📊 **Export CSV**: Tabular summary of pages, statuses, sizes, and links (`.csv`).

---

## 🧪 Verification & Test Results

### 1. Test Suite Results (33 Passed, 0 Failed)
```
============================== test session starts ==============================
tests/test_api.py::test_health_endpoint PASSED                           [  3%]
tests/test_api.py::test_dashboard_endpoint PASSED                        [  6%]
tests/test_api.py::test_api_robots_endpoint PASSED                       [  9%]
tests/test_api.py::test_api_crawl_and_job_status PASSED                  [ 12%]
tests/test_crawler.py::test_crawler_respects_limits PASSED               [ 15%]
tests/test_headers.py::test_build_user_agent PASSED                      [ 18%]
tests/test_headers.py::test_default_headers_contain_polite_keys PASSED   [ 21%]
tests/test_html_cleaner.py::test_html_clean_and_convert_markdown PASSED  [ 24%]
tests/test_html_cleaner.py::test_metadata_extraction PASSED              [ 27%]
tests/test_html_cleaner.py::test_spa_detection PASSED                    [ 30%]
tests/test_rate_limiter.py::test_domain_limiter_delay PASSED             [ 33%]
tests/test_rate_limiter.py::test_rate_limiter_throttle_context PASSED    [ 36%]
tests/test_rate_limiter.py::test_429_retry_after_handling PASSED         [ 39%]
tests/test_robots.py::test_robots_rule_matching PASSED                   [ 42%]
tests/test_robots.py::test_robots_can_fetch_logic PASSED                 [ 45%]
tests/test_robots.py::test_robots_missing_404_fallback PASSED            [ 48%]
tests/test_scenarios.py::test_scenario_spider_trap_normalization PASSED  [ 51%]
tests/test_scenarios.py::test_scenario_binary_file_filtering PASSED      [ 54%]
tests/test_scenarios.py::test_scenario_storage_exports PASSED            [ 57%]
tests/test_scenarios.py::test_scenario_ai_json_repair PASSED             [ 60%]
tests/test_scenarios.py::test_nemotron_parser_mock PASSED                [ 63%]
tests/test_scrape_export.py::test_storage_to_pdf PASSED                  [ 66%]
tests/test_scrape_export.py::test_storage_to_markdown_single PASSED      [ 69%]
tests/test_scrape_export.py::test_storage_to_markdown_multi PASSED       [ 72%]
tests/test_scrape_export.py::test_storage_to_text PASSED                 [ 75%]
tests/test_scrape_export.py::test_storage_export_bytes PASSED            [ 78%]
tests/test_scrape_export.py::test_storage_save_file_extensions PASSED    [ 81%]
tests/test_scrape_export.py::test_api_scrape_endpoint PASSED             [ 84%]
tests/test_scrape_export.py::test_api_jobs_export_endpoint PASSED        [ 87%]
tests/test_scrape_export.py::test_api_scrape_and_export_endpoint PASSED  [ 90%]
tests/test_scrape_export.py::test_cli_scrape_command PASSED              [ 93%]
tests/test_sitemap.py::test_parse_standard_sitemap_xml PASSED            [ 96%]
tests/test_sitemap.py::test_parse_gzipped_sitemap PASSED                 [100%]
============================== 33 passed in 6.13s ==============================
```

### 2. Code Quality & Linting
```bash
ruff check .
# Output: All checks passed!
```

### 3. Live CLI Verification

#### A. PDF Scrape Export:
```bash
./crawler scrape https://example.com --output content/example_scraped.pdf --format pdf
# Verified: Generated valid ReportLab PDF (%PDF-1.4) in content/example_scraped.pdf
```

#### B. Markdown & Text Scrape Export:
```bash
./crawler scrape https://example.com --output content/example_scraped.md
./crawler scrape https://example.com --output content/example_scraped.txt
# Verified: Saved clean Markdown and ASCII-bordered Plain Text reports
```

#### C. Full Crawl PDF Export:
```bash
./crawler crawl https://example.com --max-pages 2 --output content/example_crawl.pdf --format pdf
# Verified: Multi-page crawl report generated in content/example_crawl.pdf
```

#### D. AI Extraction with NVIDIA NIM:
```bash
./crawler scrape https://example.com --extract-ai --schema article --output content/example_ai.json
# Verified: Extracted structured article schema using meta/llama-3.2-11b-vision-instruct
```

---

## 📖 How to Run

### Command Line:
```bash
# Single page scrape to PDF
./crawler scrape https://example.com -o page.pdf -f pdf

# Single page scrape to Markdown
./crawler scrape https://example.com -o page.md

# Ethical crawl of 10 pages to CSV
./crawler crawl https://example.com -n 10 -o crawl.csv

# Crawl directly from sitemap to PDF
./crawler crawl https://example.com -m -o sitemap_pages.pdf -f pdf
```

### Web UI Dashboard:
```bash
./crawler serve --host 0.0.0.0 --port 8000
```
Open [http://localhost:8000](http://localhost:8000) to use the UI with one-click export buttons, or [http://localhost:8000/docs](http://localhost:8000/docs) for the interactive Swagger documentation.
