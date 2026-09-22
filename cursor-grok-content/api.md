# REST API

Router prefix: `/api` + `/v1` → **`/api/v1/...`**  
App: `src/ethical_crawler/api/app.py`  
Routes: `src/ethical_crawler/api/v1/router.py`

Interactive docs: `http://localhost:8000/docs` and `/redoc`.

CORS is currently `allow_origins=["*"]`.

## App-level

| Method | Path | Notes |
|--------|------|--------|
| GET | `/` | Dashboard HTML |
| GET | `/health` | `{status, bot_user_agent, version}` |
| GET | `/docs` | Swagger |
| GET | `/redoc` | ReDoc |

## Crawler & scrape

| Method | Path | Notes |
|--------|------|--------|
| POST | `/api/v1/crawl` | 202 `{job_id, status, message}`; body `CrawlRequest` |
| GET | `/api/v1/jobs/{job_id}` | `CrawlJob` including live progress + results |
| GET | `/api/v1/jobs/{job_id}/export` | `?format=` pdf/md/txt/json/csv |
| POST | `/api/v1/scrape` | Sync single page; optional `extract_ai`, RPA |
| GET/POST | `/api/v1/scrape/export` | Stream file for one URL |

## Ethics helpers

| Method | Path |
|--------|------|
| GET | `/api/v1/robots?url=` |
| GET | `/api/v1/sitemap?url=` |

## AI extract

| Method | Path |
|--------|------|
| POST | `/api/v1/extract` | Fetch (or cache) then structured extract |

## History / Chroma

| Method | Path | Notes |
|--------|------|--------|
| GET | `/api/v1/history` | `?limit=` stored page summaries |
| GET | `/api/v1/history/page?url=` | Full cached page |
| GET | `/api/v1/history/export?url=&format=` | Re-export without recrawl |
| GET | `/api/v1/history/store` | Inspector: collection, mappings, domains, docs |
| GET | `/api/v1/history/domains` | Domain groups + nested pages, revisions, AI counts |
| DELETE | `/api/v1/history/page?url=` | One document |
| DELETE | `/api/v1/history/domain?domain=` | All pages for a host |
| POST | `/api/v1/history/recrawl` | Live fetch + upsert (revision growth) |

Deletes are user-initiated from the dashboard; do not script mass wipes in agent workflows.

## Search, RAG, dossier

| Method | Path |
|--------|------|
| GET | `/api/v1/search?q=&limit=&domain=` |
| POST | `/api/v1/ask` | `{question, domain?}` → answer + citations |
| POST | `/api/v1/dossier/generate` | Multi-domain dossier |
| GET | `/api/v1/dossier/export` | File export of last-style dossier params |

## RPA & DOM

| Method | Path |
|--------|------|
| GET | `/api/v1/rpa/presets` |
| POST | `/api/v1/rpa/generate` | NL → `RPAStep[]` via LLM |
| POST | `/api/v1/elements/check` | `{selector, html? or url?}` |

## Job store caveat

`_JOBS_STORE` is a process dict. Horizontal scale or restart loses in-flight jobs. Persistent knowledge is only Chroma.
