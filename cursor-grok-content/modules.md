# Module reference

All paths under `src/ethical_crawler/`.

## `config.Settings`

Env prefix `CRAWLER_`. Notable fields: bot identity, delays, concurrency, robots TTL, sitemap auto-discover, browser fallback, NIM/OpenAI (`ai_base_url`, `ai_api_key`, `ai_model`), `api_host`/`api_port`, `chroma_dir`, `enable_cache`, `cache_ttl_days`, `chroma_collection`.

`get_settings()` is `@lru_cache` — process-wide singleton.

## `types`

Enums: `CrawlStrategy`, `JobStatus`.

Core models: `CrawlRequest`, `CrawlResult`, `CrawlJob`, `PageMetadata`, `PageLink`, `RobotsDirectives`, `SitemapURL`/`SitemapResult`, `StructuredExtractionResult`, article/product/FAQ/company schemas, `MarketDossierRequest`/`MarketDossierResult`, `NetworkCall`.

`CrawlResult` also carries `ai_data`, `rpa_logs`, `network_calls`, `dom_elements`.

## `crawler.EthicalCrawler`

- Seeds queue from URL and optionally sitemap.
- Checks robots before fetch.
- Waits on rate limiter.
- Cache lookup via Chroma when `use_cache`.
- Runs HTTP and/or browser.
- Extracts links for BFS up to `max_depth`.
- Optional per-page AI extract.
- Upserts into Chroma.
- Closes engines in `finally`.

## Engines

- `HTTPEngine.crawl(url)` — GET, status, HTML clean, metadata, links.
- `BrowserEngine.crawl(url, rpa_steps=..., auto_dismiss_modals=...)` — Playwright page, RPA executor, optional XHR listing.

## Extractors

- `HTMLCleaner` — drop `STRIP_TAGS` and `NOISE_SELECTORS`; html2text GFM; SPA heuristics.
- `AIExtractor.extract_structured` — JSON from markdown; fallback models.
- `NemotronParser.parse_image` — vision tasks `markdown_bbox`, `markdown_bbox_with_text_in_pictures`, `detection_only`.
- `ElementInspector.query_selector` / inventory helpers.

## `vector_store.VectorStoreManager`

Methods: `upsert_page`, `get_cached_page`, `semantic_search`, `list_stored_pages`, `delete_page`, `delete_domain`, `list_domains_summary`, `get_store_overview`, `count_pages`.

IDs are normalized URLs. Collection metadata `hnsw:space=cosine`.

## `storage.StorageExporter`

`to_json`, `to_jsonl`, `to_csv`, markdown/text, ReportLab PDF, SQLite. Used by CLI `-o` and API export endpoints.

## `rpa`

Actions: `click`, `fill`, `select`, `wait_for`, `press_key`, `hover`, `scroll`, `sleep`. Optional steps warn instead of failing the job. Presets: cookie banners, accordions, annual pricing.

## `knowledge.DossierGenerator`

`generate_dossier(domains, model, custom_focus)` reads Chroma by domain, then LLM synthesis.
