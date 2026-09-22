# Dashboard UI

**Location:** `src/ethical_crawler/api/app.py` constant `DASHBOARD_HTML` (served at `GET /`). There is no separate frontend package.

**Stack:** Inter + JetBrains Mono, Tailwind CDN, Font Awesome 6, custom CSS variables (teal / violet glass on `#0b1220`).

## Sections

1. **Header** — product title, **ChromaDB Active** chip (opens store inspector with counts + field mappings), API Docs.
2. **Rule cards** — robots, politeness, identity, sitemaps.
3. **Tabs** (`role="tablist"`)
   - Website Crawler — `crawlerForm` + results grid
   - Single Page Scraper — `scraperForm`
   - Knowledge & History — KPIs, semantic search, Ask AI, domain archive
4. **Footer** — version, docs, health, robots compliance note.

## Crawler / scraper forms

Shared ideas:

- Workflow presets (smoke, competitor intel, RAG ingest, ecommerce, SPA, live growth, polite stealth) + save-current custom presets in `localStorage`.
- Target URL, max pages/depth, delay, engine `auto|http|browser`.
- Toggles: robots, sitemap (crawl only), Chroma cache, AI extract (schema + NIM model + prompt).
- RPA playbook: cookie/modals preset, accordions, annual pricing, NL “Generate” → `/api/v1/rpa/generate`, custom steps.
- Primary CTA: Start Ethical Crawl / scrape equivalent.
- Helpers: Check Robots, View Sitemap.

Live jobs poll `/api/v1/jobs/{id}` and render activity, current URL, and page rows.

## Knowledge tab

- KPIs from `/api/v1/history/domains` + `/api/v1/history`.
- Semantic search and RAG ask.
- Domain cards: page count, size, AI profile count, Search / Dossier / Delete.
- Per-row: status pill, title/URL, revision badge (`vN · ±bytes`), size, date, **Export** `<select>` (pdf/md/txt/json/csv), recrawl, preview, delete.
- Preview modal: markdown + AI JSON if present.
- Dossier modal: pick domains, generate, copy/export.

## Chroma inspector modal

`GET /api/v1/history/store` — documents, domains, cosine space, collection name, field mapping table, stored rows grouped by domain.

## A11y notes (current)

Skip link, `main#mainContent`, toast live region, tab `aria-selected` / `aria-controls`, modal `role="dialog"` + Escape to close, 44px-class close hits, focus rings in teal.

## Theming

Dark-only. Primary actions use `.cta-primary` (teal). History tab uses violet pill (`.hud-tab-history` class name is leftover; styling is a solid violet pill, not a HUD chassis).
