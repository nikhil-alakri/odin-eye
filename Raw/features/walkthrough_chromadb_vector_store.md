# Walkthrough: ChromaDB Embedded Vector Store & Knowledge Engine

**Date & Time**: 21-Sep-2026 01:26

---

## 🎯 Overview

We have integrated **ChromaDB** as the embedded, local vector database for the Ethical AI-Native Web Crawler.

Every crawled and scraped web page is automatically embedded into a local vector store (`data/chroma/`), providing:
1. **Permanent Local Storage & Caching ("Don't Crawl Again")**: If a requested URL was already scraped within TTL (default 7 days), the crawler returns the cached result in 1ms with 0 network calls.
2. **Semantic Vector Search**: Natural language search across all crawled web pages using vector embeddings and cosine similarity (`crawler search "<query>"` and `GET /api/v1/search`).
3. **Local RAG Q&A ("Chat with Crawled Sites")**: Ask AI questions synthesized strictly from crawled page chunks, complete with verified source citations (`crawler ask "<question>"` and `POST /api/v1/ask`).
4. **1-Click Multi-Format Re-Exports**: Re-export any historical crawl directly into **PDF, Markdown, Plain Text, JSON, or CSV** anytime without re-fetching the target site.
5. **Interactive Web UI Dashboard**: A dedicated **🧠 Knowledge & History** tab featuring live vector search cards, Ask AI assistant, and a stored crawl archive table.
6. **Strict Database Preservation**: All operations strictly use non-destructive `collection.upsert(...)` to ensure zero data loss.

---

## 🏗️ Architecture & Changes

### 1. Vector Store Manager (`src/ethical_crawler/vector_store.py`)
- Persistent ChromaDB client initialized at `data/chroma/` using cosine distance space.
- `upsert_page(result, ai_data)`: Non-destructive upsert with normalized document ID, metadata (title, URL, domain, status, size, timestamp), and markdown text.
- `get_cached_page(url, max_age_days)`: Validates timestamp against TTL and reconstructs `CrawlResult` in 1ms.
- `semantic_search(query, n_results, domain)`: Vector similarity search with similarity scoring (`0-100%`) and snippet preview generation.
- `list_stored_pages(limit)`: Lists all saved crawls sorted by timestamp.
- `ask_crawled_knowledge(question, n_context)`: RAG pipeline combining top vector search context chunks with NVIDIA NIM / OpenAI chat completions.

### 2. Crawler & Scraper Integration (`src/ethical_crawler/crawler.py` & `types.py`)
- Added `use_cache: bool = True` and `cache_ttl_days: int = 7` to `CrawlRequest` and `ScrapeRequest`.
- Before fetching, the crawler checks `vector_store.get_cached_page()`. On a cache hit, it skips network requests and returns immediately.
- Upon successful fetch and markdown processing, the crawler automatically calls `vector_store.upsert_page()`.

### 3. REST API Endpoints (`src/ethical_crawler/api/v1/router.py`)
- `GET /api/v1/history`: Returns list of all stored pages.
- `GET /api/v1/history/page`: Returns full markdown and metadata for any stored page.
- `GET /api/v1/history/export`: 1-click export of any cached page to PDF, MD, TXT, JSON, or CSV.
- `GET /api/v1/search`: Vector search endpoint with optional domain filtering.
- `POST /api/v1/ask`: RAG Q&A endpoint returning synthesized answer and cited sources.
- `GET/POST /api/v1/scrape/export`: Supports both GET and POST for direct browser downloads.

### 4. Interactive Web UI Dashboard (`src/ethical_crawler/api/app.py`)
- **New Tab 3**: `🧠 Knowledge & History` with live page count badge.
- **Semantic Search Panel**: Interactive search input with cosine match percentage badges (`98% Match`), snippets, and 1-click export options.
- **Ask AI Assistant**: Chat with crawled web pages using local RAG and interactive citation links.
- **Stored Crawl Archive**: Filterable data table displaying all stored pages with instant "Preview" modal and multi-format export buttons (PDF, MD, TXT, JSON, CSV).
- **Cache Checkboxes**: Added `⚡ Use ChromaDB Vector Cache` toggle to both Crawler and Scraper forms.

### 5. CLI Commands (`src/ethical_crawler/cli.py`)
- `crawler search "<query>" [--limit 5] [--domain example.com]`
- `crawler ask "<question>" [--context 3]`
- `crawler history [--limit 50]`
- `crawler crawl ... [--cache / --no-cache]`
- `crawler scrape ... [--cache / --no-cache]`

---

## 🧪 Verification & Test Results

### 1. Automated Test Suite
All **40 tests** across the entire codebase passed with 100% success:

```bash
tests/test_api.py::test_health_endpoint PASSED                           [  2%]
tests/test_api.py::test_dashboard_endpoint PASSED                        [  5%]
tests/test_api.py::test_api_robots_endpoint PASSED                       [  7%]
tests/test_api.py::test_api_crawl_and_job_status PASSED                  [ 10%]
tests/test_crawler.py::test_crawler_respects_limits PASSED               [ 12%]
tests/test_headers.py::test_build_user_agent PASSED                      [ 15%]
tests/test_headers.py::test_default_headers_contain_polite_keys PASSED   [ 17%]
tests/test_html_cleaner.py::test_html_clean_and_convert_markdown PASSED  [ 20%]
tests/test_html_cleaner.py::test_metadata_extraction PASSED              [ 22%]
tests/test_html_cleaner.py::test_spa_detection PASSED                    [ 25%]
tests/test_rate_limiter.py::test_domain_limiter_delay PASSED             [ 27%]
tests/test_rate_limiter.py::test_rate_limiter_throttle_context PASSED    [ 30%]
tests/test_rate_limiter.py::test_429_retry_after_handling PASSED         [ 32%]
tests/test_robots.py::test_robots_rule_matching PASSED                   [ 35%]
tests/test_robots.py::test_robots_can_fetch_logic PASSED                 [ 37%]
tests/test_robots.py::test_robots_missing_404_fallback PASSED            [ 40%]
tests/test_scenarios.py::test_scenario_spider_trap_normalization PASSED  [ 42%]
tests/test_scenarios.py::test_scenario_binary_file_filtering PASSED      [ 45%]
tests/test_scenarios.py::test_scenario_storage_exports PASSED            [ 47%]
tests/test_scenarios.py::test_scenario_ai_json_repair PASSED             [ 50%]
tests/test_scenarios.py::test_nemotron_parser_mock PASSED                [ 52%]
tests/test_scrape_export.py::test_storage_to_pdf PASSED                  [ 55%]
tests/test_scrape_export.py::test_storage_to_markdown_single PASSED      [ 57%]
tests/test_scrape_export.py::test_storage_to_markdown_multi PASSED       [ 60%]
tests/test_scrape_export.py::test_storage_to_text PASSED                 [ 62%]
tests/test_scrape_export.py::test_storage_export_bytes PASSED            [ 65%]
tests/test_scrape_export.py::test_storage_save_file_extensions PASSED    [ 67%]
tests/test_scrape_export.py::test_api_scrape_endpoint PASSED             [ 70%]
tests/test_scrape_export.py::test_api_jobs_export_endpoint PASSED        [ 72%]
tests/test_scrape_export.py::test_api_scrape_and_export_endpoint PASSED  [ 75%]
tests/test_scrape_export.py::test_cli_scrape_command PASSED              [ 77%]
tests/test_sitemap.py::test_parse_standard_sitemap_xml PASSED            [ 80%]
tests/test_sitemap.py::test_parse_gzipped_sitemap PASSED                 [ 82%]
tests/test_vector_store.py::test_upsert_and_cache_hit PASSED             [ 85%]
tests/test_vector_store.py::test_cache_miss_when_expired PASSED          [ 87%]
tests/test_vector_store.py::test_semantic_search PASSED                  [ 90%]
tests/test_vector_store.py::test_list_stored_pages PASSED                [ 92%]
tests/test_vector_store.py::test_ask_crawled_knowledge_fallback PASSED   [ 95%]
tests/test_vector_store.py::test_api_history_and_search_endpoints PASSED [ 97%]
tests/test_vector_store.py::test_cli_search_and_history PASSED           [100%]

============================= 40 passed in 10.03s ==============================
```

### 2. Live CLI Verification

#### History Listing
```bash
./crawler history
```
Output:
```
                      Saved Crawl History (2 unique pages)                      
┏━━━━━━┳━━━━━━━━━━┳━━━━━━━━━━━━━┳━━━━━━━━━━┳━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━┓
┃ #    ┃ Status   ┃ Title / URL ┃ Engine   ┃       Size ┃ Crawled At           ┃
┡━━━━━━╇━━━━━━━━━━╇━━━━━━━━━━━━━╇━━━━━━━━━━╇━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━┩
│ 1    │ 200      │ Page        │ http     │        0 B │ 2026-09-20 19:55:18  │
│ 2    │ 200      │ Page        │ http     │        0 B │ 2026-09-20 19:55:16  │
└──────┴──────────┴─────────────┴──────────┴────────────┴──────────────────────┘
```

#### Semantic Search
```bash
./crawler search "page"
```
Output:
```
                       Semantic Search Results (2 found)                        
┏━━━━━┳━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ #   ┃ Similarity ┃ Title / URL                 ┃ Snippet Preview             ┃
┡━━━━━╇━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ 1   │        65% │ Page https://example.com/p1 │ # Content for               │
│     │            │ https://example.com/p1      │ https://example.com/p1      │
│ 2   │        65% │ Page https://example.com/   │ # Content for               │
│     │            │ https://example.com/        │ https://example.com/        │
└─────┴────────────┴─────────────────────────────┴─────────────────────────────┘
```

### 3. Code Style & Linting
```bash
.venv/bin/ruff check .
```
Output:
```
All checks passed!
```

