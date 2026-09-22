# Testing

**Runner:** pytest (`asyncio_mode = auto`), path `tests/`.  
**Lint:** ruff, line length 100.

```bash
make test          # .venv/bin/pytest -v
make lint
make format
```

Some crawl tests hit the public network (`example.com`). Those can fail in sandboxes without outbound HTTP; that is environmental, not necessarily a product regression.

## Files

| File | Focus |
|------|--------|
| `conftest.py` | Sample robots.txt, HTML, shared snippets |
| `test_robots.py` | Allow/disallow, crawl-delay, UA matching |
| `test_sitemap.py` | urlset / index / gzip |
| `test_rate_limiter.py` | Delays, 429 handling |
| `test_headers.py` | User-Agent construction |
| `test_html_cleaner.py` | Noise strip, markdown, SPA hints |
| `test_crawler.py` | Orchestrator / integration-ish crawl |
| `test_api.py` | FastAPI routes |
| `test_vector_store.py` | Upsert, cache, search, `/history/store` shape |
| `test_rpa.py` | Steps, presets, executor |
| `test_network_and_elements.py` | NetworkCall + ElementInspector |
| `test_scrape_export.py` | Export pipeline |
| `test_scenarios.py` | Broader user scenarios |

## Related product docs (not tests)

`content/` and `Raw/features/` hold implementation plans and walkthrough markdown from feature work. They are historical; if they disagree with `src/`, **trust `src/`**.
