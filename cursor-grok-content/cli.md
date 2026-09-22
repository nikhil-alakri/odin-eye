# CLI

Entry points:

- `crawler` after `pip install -e .` (`[project.scripts]` in `pyproject.toml`)
- `./crawler` bash wrapper if `.venv/bin/crawler` exists
- `python -m ethical_crawler.cli`

Implementation: `src/ethical_crawler/cli.py` (Typer + Rich).

## Commands

| Command | Purpose |
|---------|---------|
| `crawl URL` | Multi-page ethical crawl, live table, optional export |
| `scrape URL` | Single page (`max_pages=1`, `max_depth=0`) |
| `search QUERY` | Semantic search over Chroma |
| `ask QUESTION` | RAG answer from stored pages |
| `history` | List stored pages |
| `sitemap URL` | Parse sitemap, optional CSV |
| `robots URL` | Show directives; `--check PATH` for one path |
| `extract URL` | Structured AI extract (`--schema`, `--prompt`) |
| `parse-image FILE` | Nemotron-Parse 2.0 |
| `serve` | Uvicorn `ethical_crawler.api.app:app` |

## `crawl` flags

- `--max-pages` / `-n` (default 10)
- `--max-depth` / `-d` (default 2)
- `--delay` / `-s`
- `--strategy` `auto` \| `http` \| `browser`
- `--sitemap` / `-m`
- `--output` / `-o` (extension or `--format`)
- `--format` / `-f` `pdf` \| `md` \| `txt` \| `json` \| `csv` \| `sqlite`
- `--cache` / `--no-cache`

## `scrape` flags

- `--output` / `-o`, `--format` / `-f`
- `--strategy` / `-s` `auto` \| `http` \| `browser`
- `--extract-ai` / `-a`, `--schema` (`article` \| `product` \| `faq` \| `custom`), `--prompt` / `-p`, `--model` / `-m`, `--api-key`
- `--respect-robots` / `--no-respect-robots`
- `--cache` / `--no-cache`

`search` takes `--limit` / `-n` and `--domain` / `-d`. `history` takes `--limit`. `extract` takes `--schema`, `--prompt`, `--model`, `--api-key`, `--output`.

## `serve`

```bash
crawler serve --host 0.0.0.0 --port 8000 --reload
# Makefile equivalent:
make run-api
```

Default bind matches `CRAWLER_API_HOST` / `CRAWLER_API_PORT` only if you pass them; the Typer defaults are `0.0.0.0:8000`.
