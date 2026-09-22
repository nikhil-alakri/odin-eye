# Project documentation (Ethical AI Web Crawler)

This folder is a walkthrough of the **ethical-crawler** repository as of 22 Sep 2026.

**Start with [SUMMARY.md](SUMMARY.md)** if you want a non-technical picture of the product. The other files are for people who will run, change, or integrate the code.

**Package:** `ethical-crawler` **v0.1.0** (Python ≥ 3.11, MIT)  
**Author:** Nikhil Alakri  
**Layout:** src-layout (`src/ethical_crawler`)

## How to read this set

| Doc | What it covers |
|-----|----------------|
| [SUMMARY.md](SUMMARY.md) | Plain-language product story (start here) |
| [repository-map.md](repository-map.md) | Every first-party folder and file and what it is for |
| [architecture.md](architecture.md) | Runtime flow: engines, ethics rules, store, jobs |
| [ethics.md](ethics.md) | The four crawling rules and where they live in code |
| [modules.md](modules.md) | Python packages, classes, and important functions |
| [cli.md](cli.md) | `crawler` / `./crawler` commands |
| [api.md](api.md) | FastAPI routes (including ones missing from the root README) |
| [dashboard-ui.md](dashboard-ui.md) | Interactive dashboard in `api/app.py` |
| [configuration.md](configuration.md) | `CRAWLER_*` settings, `.env`, Chroma paths |
| [data-and-chroma.md](data-and-chroma.md) | Vector store schema, upserts, cache TTL, inspector |
| [testing.md](testing.md) | Pytest layout and how to run it |

## What this product is

An ethical web crawler and scraper with:

1. Dual fetch engines (`httpx` and Playwright Chromium, with `auto` escalation).
2. LLM-oriented HTML → Markdown cleaning and optional NVIDIA NIM / OpenAI extraction.
3. Local **ChromaDB** persistence (`data/chroma`, collection `crawled_knowledge`, cosine space).
4. A FastAPI service plus a single-page dashboard (default **http://localhost:8000**).
5. RAG search, “ask AI”, domain grouping, recrawl/revision tracking, market dossiers, and RPA playbooks.

## Quick start (from repo root)

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
# optional JS rendering:
pip install -e ".[browser]"
playwright install chromium

cp .env.example .env   # set CRAWLER_AI_API_KEY if you need extraction / RAG answers
make run-api           # dashboard + API on :8000 with reload
# or:
./crawler crawl https://example.com --max-pages 5
```

Do not treat `.venv/`, `.pytest_cache/`, or `data/chroma` as source. Chroma data is a local knowledge store; agents should not wipe it (see `.agents/rules/database-preservation.md`).
