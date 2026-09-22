# ChromaDB Local Vector Database Integration: Persistent Storage, Semantic Search & Caching

**Date & Time:** 21-Sep-2026 01:15  
**Feature:** `chromadb_vector_store`

---

## Overview
This feature integrates **ChromaDB** as an embedded, serverless local Vector Database into the Ethical Web Crawler and Scraper. It provides:
1. **Permanent Local Vector Storage (`data/chroma/`)**: Every scraped or crawled page is embedded and stored locally without external database server dependencies.
2. **Smart Caching ("Don't Crawl Again")**: Before hitting any external website, the crawler checks if the URL has already been crawled within a configurable TTL (e.g. 7 days). If present, it loads the cached result in 1 millisecond with zero network traffic.
3. **Semantic Search**: Natural language search across all crawled web pages (e.g., searching *"how to cancel membership"* finds pages about *"Billing & Cancellation"* even without exact keyword matches).
4. **"Chat with Crawled Sites" (RAG)**: Ask questions across all crawled pages using your configured **NVIDIA NIM** LLM (`meta/llama-3.2-11b-vision-instruct`), returning accurate answers with direct source citations.
5. **Saved History & Knowledge Hub in the Web Dashboard**: An interactive UI tab allowing users to browse previously crawled pages, search knowledge, ask AI questions, and re-export to **PDF, MD, TXT, JSON, and CSV** anytime.

---

## User Review Required

> [!IMPORTANT]
> **Dependency Installation:** This feature requires adding `chromadb>=0.5.0` to `pyproject.toml`. Installing `chromadb` will be executed in `.venv` with user approval.
>
> **Database Preservation Rule Compliance:** All vector operations will use non-destructive `upsert` semantics (`collection.upsert`). Existing records are never cleared or truncated.

---

## Proposed Changes

### 1. Dependencies & Configuration
#### [MODIFY] [pyproject.toml](file:///Users/nikhilalakri/Developer/web-crawler/pyproject.toml)
- Add `chromadb>=0.5.0` to `dependencies`.

#### [MODIFY] [src/ethical_crawler/config.py](file:///Users/nikhilalakri/Developer/web-crawler/src/ethical_crawler/config.py)
- Add settings:
  - `chroma_dir: Path = Path("data/chroma")`
  - `enable_cache: bool = True`
  - `cache_ttl_days: int = 7`
  - `chroma_collection_name: str = "crawled_knowledge"`

---

### 2. Core Vector Database Layer
#### [NEW] [src/ethical_crawler/vector_store.py](file:///Users/nikhilalakri/Developer/web-crawler/src/ethical_crawler/vector_store.py)
- Implement `VectorStoreManager`:
  - `get_client()`: Initializes `chromadb.PersistentClient(path=settings.chroma_dir)`.
  - `upsert_page(result: CrawlResult, ai_data: dict | None = None)`: Chunking long markdown content, extracting document embeddings, and safely storing metadata (`url`, `title`, `status_code`, `strategy`, `crawled_at`, `size`).
  - `get_cached_page(url: str, max_age_days: int = 7) -> CrawlResult | None`: Fast cache lookup to bypass live HTTP requests if already crawled.
  - `semantic_search(query: str, limit: int = 5, domain: str | None = None)`: Natural language search returning relevance score, title, url, and text snippet.
  - `list_stored_pages(limit: int = 100)`: Retrieves list of all unique crawled URLs stored in ChromaDB for UI history.
  - `ask_crawled_knowledge(query: str, ai_extractor: AIExtractor)`: Retrieves top relevant page chunks, constructs prompt context, and queries NVIDIA NIM to produce an answer with source citations.

---

### 3. Crawler & Scraper Integration
#### [MODIFY] [src/ethical_crawler/crawler.py](file:///Users/nikhilalakri/Developer/web-crawler/src/ethical_crawler/crawler.py)
- Integrate cache checking: Before fetching, check `VectorStoreManager.get_cached_page()`. If present and valid, skip network fetch and return cached `CrawlResult`.
- After fetching: Automatically persist newly crawled pages into ChromaDB using `upsert_page()`.

---

### 4. CLI Commands
#### [MODIFY] [src/ethical_crawler/cli.py](file:///Users/nikhilalakri/Developer/web-crawler/src/ethical_crawler/cli.py)
- **`crawler search <query>`**: Run semantic search over all crawled pages directly from terminal.
- **`crawler ask <question>`**: Ask questions across crawled websites with NVIDIA NIM grounded answers and citations.
- **`crawler history`**: View all pages stored in local ChromaDB.
- **`crawler scrape` & `crawler crawl`**: Add `--cache / --no-cache` options.

---

### 5. REST API Endpoints
#### [MODIFY] [src/ethical_crawler/api/v1/router.py](file:///Users/nikhilalakri/Developer/web-crawler/src/ethical_crawler/api/v1/router.py)
- `GET /api/v1/history`: List all pages in the vector database.
- `GET /api/v1/search?q=...&limit=5`: Semantic search endpoint.
- `POST /api/v1/ask`: RAG Q&A endpoint.

---

### 6. Web UI Dashboard
#### [MODIFY] [src/ethical_crawler/api/app.py](file:///Users/nikhilalakri/Developer/web-crawler/src/ethical_crawler/api/app.py)
- Add **Tab 3: "🧠 Knowledge & History"**:
  - **Saved Pages History Table**: View all previously crawled sites with dates, titles, sizes, and instant 1-click export buttons (PDF, Markdown, Plain Text, JSON, CSV).
  - **Semantic Search Input**: Real-time natural language query against stored pages.
  - **"Ask AI" Interface**: Interactive chat with crawled web pages using NVIDIA NIM.
  - **"Use Cache" Checkbox** added to Crawl & Scrape parameter forms.

---

## Verification Plan

### Automated Tests
- `tests/test_vector_store.py`:
  - Test ChromaDB persistent initialization.
  - Test `upsert_page` and non-destructive overwrites.
  - Test `get_cached_page` hit and expired TTL miss.
  - Test `semantic_search` ranking.
  - Test API endpoints `/api/v1/history` and `/api/v1/search`.
- Run `pytest -v` across all 33+ tests.
- Run `ruff check .` for formatting and linting hygiene.

### Manual Verification
- Scrape a page: `./crawler scrape https://example.com`
- Scrape again with cache: verify it loads instantly from ChromaDB without making network requests.
- Run semantic search: `./crawler search "domain documentation"`
- Open Web Dashboard (`./crawler serve`) and test the new **Knowledge & History** tab.

