# Repository map

First-party layout only. Ignored for this map: `.venv/`, `.git/`, `__pycache__/`, `.pytest_cache/`, `.ruff_cache/`.

```
web-crawler/
├── crawler                 # Bash wrapper → .venv/bin/crawler
├── Makefile                # install, test, lint, format, run-api
├── pyproject.toml          # package metadata, deps, ruff, pytest
├── README.md               # user-facing product README
├── .env.example            # CRAWLER_* template (no secrets)
├── .env                    # local secrets (gitignored)
├── .gitignore
├── src/ethical_crawler/    # installable Python package
├── tests/                  # pytest
├── data/                   # runtime Chroma persist (typically local)
├── content/                # older plans, walkthroughs, sample exports
├── Raw/features/           # feature plans + walkthroughs
├── .agents/rules/          # Cursor/agent constraints
└── cursor-grok-content/    # this documentation set
```

## Root files

| Path | Role |
|------|------|
| `crawler` | `exec .venv/bin/crawler "$@"` after `make install` |
| `pyproject.toml` | Name `ethical-crawler`, script entry `crawler = ethical_crawler.cli:app`, extras `browser` / `dev` / `all` |
| `Makefile` | `install`, `install-browser`, `test`, `lint`, `format`, `run-api` (`serve --reload` on `:8000`), `clean` |
| `.env.example` | All documented env vars with prefix `CRAWLER_` |
| `.gitignore` | `.env`, `.venv`, `*.db`, `crawled_data/`, pytest/ruff caches |

## `src/ethical_crawler/`

| Path | Role |
|------|------|
| `__init__.py` | `__version__ = "0.1.0"` |
| `config.py` | `Settings` (pydantic-settings), `get_settings()` |
| `types.py` | Pydantic models: crawl request/result, jobs, robots, sitemap, AI schemas, dossier, RPA-related crawl fields |
| `crawler.py` | `EthicalCrawler` orchestrator (queue, robots, sitemap, engines, cache, AI, progress) |
| `cli.py` | Typer CLI |
| `storage.py` | `StorageExporter` (JSON, JSONL, MD, TXT, CSV, PDF, SQLite) |
| `vector_store.py` | `VectorStoreManager` + `get_vector_store()` |

### `api/`

| Path | Role |
|------|------|
| `app.py` | FastAPI app, CORS, `GET /health`, `GET /` dashboard HTML string (`DASHBOARD_HTML`) |
| `deps.py` | DI wrappers for settings, robots, sitemap, rate limiter, AI extractor |
| `v1/router.py` | All `/api/v1/*` endpoints; in-memory `_JOBS_STORE` for async crawls |

### `core/` (ethics + politeness)

| Path | Role |
|------|------|
| `robots.py` | Rule 1: fetch/parse/cache `robots.txt` |
| `rate_limiter.py` | Rule 2: per-domain delay, 429 Retry-After, backoff, semaphores |
| `headers.py` | Rule 3: identifiable User-Agent + polite headers |
| `sitemap.py` | Rule 4: sitemapindex / urlset, gzip |

### `engines/`

| Path | Role |
|------|------|
| `base.py` | `CrawlEngine` ABC |
| `http_engine.py` | Async `httpx` fetch + clean |
| `browser_engine.py` | Playwright Chromium, RPA, network capture |

### `extractors/`

| Path | Role |
|------|------|
| `html_cleaner.py` | Strip noise, Markdown, SPA detection |
| `metadata.py` | Title, OG, Twitter, JSON-LD |
| `link_extractor.py` | Internal/external links, URL normalize |
| `ai_extractor.py` | NVIDIA NIM / OpenAI structured extract + model fallback chain |
| `nemotron_parser.py` | Vision parse (`nvidia/nemotron-parse-2.0`) |
| `element_inspector.py` | DOM inventory + CSS selector query |

### `rpa/`

| Path | Role |
|------|------|
| `models.py` | `RPAStep`, `RPAActionType`, `RPAResult` |
| `presets.py` | Cookie banners, accordions, annual pricing |
| `executor.py` | Run playbook against a Playwright page |

### `knowledge/`

| Path | Role |
|------|------|
| `dossier_generator.py` | Multi-domain market dossier from Chroma + LLM |

## `tests/`

See [testing.md](testing.md). Files: `conftest.py`, `test_robots.py`, `test_sitemap.py`, `test_rate_limiter.py`, `test_headers.py`, `test_html_cleaner.py`, `test_crawler.py`, `test_api.py`, `test_vector_store.py`, `test_rpa.py`, `test_network_and_elements.py`, `test_scrape_export.py`, `test_scenarios.py`.

## Other folders

| Path | Role |
|------|------|
| `content/` | Historical implementation plans, walkthroughs, sample scrape/PDF/JSON |
| `Raw/features/` | Feature-by-feature plans and walkthroughs (UI polish, RPA, Chroma, dossiers, presets, …) |
| `.agents/rules/features-plans-walkthrough.md` | How agents should write plans |
| `.agents/rules/database-preservation.md` | Do not wipe Chroma / stores |
| `data/chroma/` | Default Chroma persist directory (`CRAWLER_CHROMA_DIR`) |

## Intentionally not source

- `.venv/` — installed Playwright and other third-party packages
- Live crawl payloads in Chroma — product data, not documentation
