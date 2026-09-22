# ChromaDB and on-disk data

## Persist location

- Default directory: `data/chroma` (`CRAWLER_CHROMA_DIR`)
- Collection: `crawled_knowledge` (`CRAWLER_CHROMA_COLLECTION`)
- Distance: **cosine** (`hnsw:space` in collection metadata)
- Access: `get_vector_store()` singleton in `vector_store.py`

This directory is runtime state. Treat it like a database: no `reset` / bulk delete from agent scripts unless the user asked.

## Document identity

`id` = normalized URL (trim, no trailing slash). Upsert updates the same id:

- `revision_count` increases
- `growth_delta_bytes` = new markdown size − previous
- `first_crawled_at` preserved
- `crawled_at` refreshed
- `ai_data_json` / `ai_model_used` overlay when extraction ran

## Field mappings (inspector)

Exposed by `VectorStoreManager.get_store_overview()` and `GET /api/v1/history/store`:

| Field | Source | Role |
|-------|--------|------|
| `id` | Normalized URL | Primary key |
| `url` | Requested URL | Seed |
| `final_url` | After redirects | Canonical |
| `domain` | netloc | Grouping |
| `title` | Page title | Display |
| `document` | Cleaned markdown | Embedded text |
| `cleaned_markdown_size` | len(markdown) | Size / growth |
| `revision_count` | Upsert counter | Recrawl history |
| `growth_delta_bytes` | size delta | Change tracking |
| `ai_data_json` | NIM/OpenAI extract | Structured overlay |
| `ai_model_used` | Model id | Provenance |
| `internal_links_json` | Link extractor | Outbound internals (capped) |
| `strategy` | Engine | http / browser / auto |
| `crawled_at` / `first_crawled_at` | Timestamps | Freshness |

## Cache behavior

`get_cached_page(url, max_age_days)` returns a stored `CrawlResult` if the row is younger than TTL (default 7 days, overridable per request). Dashboard “Use ChromaDB cache” maps to `use_cache`. Live Growth Audit preset turns cache **off** so recrawl measures growth.

## APIs that touch the store

Read: history, page, store, domains, search, ask, dossier.  
Write: crawl/scrape/extract/recrawl upserts.  
Delete: `DELETE /history/page` and `DELETE /history/domain` (UI confirmations).

## Other output

CLI `--output` writes JSON/CSV/MD/TXT/PDF/SQLite next to the command, not into Chroma. `.gitignore` already excludes `*.db` and `crawled_data/`.
