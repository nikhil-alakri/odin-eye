# ❓ Frequently Asked Questions (FAQ)

Everything you need to know about the **Ethical AI-Native Web Crawler**, architecture reverse-engineering, compliance, performance, and integrations.

---

## 📌 General & Concept FAQs

### Q1: What makes this crawler "Ethical"?
**A:** The crawler adheres strictly to the **4 Rules of Ethical Web Crawling**:
1. **Rule 1 (`robots.txt`)**: It always fetches and parses the target domain's `robots.txt` before making crawl requests, blocking any paths disallowed for its User-Agent.
2. **Rule 2 (Politeness Delay & Rate Limiting)**: It enforces per-domain rate limits (default 2.0s delay), concurrency throttles, and strictly obeys HTTP 429 `Retry-After` headers and `Crawl-delay` directives.
3. **Rule 3 (Identifiable User-Agent)**: It sends a transparent, informative User-Agent containing the bot name, version, documentation link, and contact email so webmasters know who is crawling and why.
4. **Rule 4 (Sitemap Discovery)**: It discovers and traverses declared sitemaps (`sitemap.xml`) to access public pages directly without blind spidering.

---

### Q2: What is the "Visual Product Reverse-Engineering" feature?
**A:** It is an autonomous capability that analyzes full-page screenshots of web applications and reconstructs their underlying system architecture:
- **Real Color Palette**: Samples screenshot pixels using Pillow (PIL) to detect authentic primary brand, accent, canvas surface, and typography colors.
- **Domain Archetype Detection**: Classifies the platform (e.g., Media & Studio Production, E-Commerce, DevTools, or SaaS) based on route names, widget patterns, and UI text.
- **Relational Schema (ERD)**: Infers database tables, primary/foreign keys, and data types (e.g., `PROJECT`, `CREW_MEMBER`, `QUOTATION` for studio software).
- **REST API Contracts**: Synthesizes endpoints, HTTP methods, query params, request bodies, and expected responses.
- **Atomic Component Hierarchy**: Breaks down views into Organisms, Molecules, and Atoms.
- **Executive PDF Export**: Assembles a publication-grade 6-page boardroom PDF report with clean typography and vector wireframes.

---

### Q3: Why is this better than traditional scrapers like Scrapy or Beautiful Soup?
**A:** Traditional tools only give you raw, uncleaned HTML strings. You are forced to manually write fragile regexes, clean noise, handle dynamic JavaScript SPAs, and build custom database storage.  
**Ethical AI Crawler** provides:
- Dual-engine architecture (lightweight async HTTP + headless Chromium browser).
- Automatic LLM-friendly Markdown cleaning (stripping ads, cookie banners, tracker scripts).
- AI structured data extraction (Pydantic models powered by NVIDIA NIM or OpenAI).
- Built-in local ChromaDB vector database with instant semantic search and offline RAG Q&A.
- Automated scheduled crawling with content diff alerts and webhooks.

---

## ⚙️ Technical & Operational FAQs

### Q4: How does the dual-engine crawling work?
**A:**
- **Fast HTTP Engine (`httpx`)**: By default, pages are fetched using asynchronous HTTP. This is extremely fast (under 100ms per page), lightweight, and consumes minimal CPU and memory.
- **Browser Engine (`playwright`)**: For client-rendered Single Page Applications (React, Vue, Angular), the browser engine spins up a headless Chromium instance to execute JavaScript, dismiss modals, and render the complete DOM.
- **Auto-Escalation**: If the HTTP engine encounters empty root containers (e.g., `<div id="root"></div>`), it automatically escalates to the headless browser engine.

---

### Q5: How does the Content Diff Engine prevent false-alarm alerts?
**A:** Websites frequently change dynamic elements like timestamps, CSRF tokens, session IDs, and rotating advertisements. The Diff Engine:
1. Normalizes the content by stripping boilerplate, navbars, and volatile DOM elements.
2. Generates structural text hashes and calculates a Levenshtein similarity score.
3. Only triggers alerts and webhooks if the content difference exceeds your configured threshold (e.g., > 5% change).

---

### Q6: What AI models are supported?
**A:** The platform is natively optimized for:
- **NVIDIA NIM APIs** (e.g., `meta/llama-3.3-70b-instruct`, `nvidia/nemotron-4-340b-instruct`, `nvidia/nemotron-3-nano-omni-30b-a3b-reasoning` for multimodal vision).
- **OpenAI API format** (`gpt-4o`, `gpt-4o-mini`, etc.).
- **Local Fallback**: If no AI API key is configured or the network is offline, the crawler continues operating using high-accuracy deterministic heuristic algorithms.

---

### Q7: Where is crawled data stored, and will my data ever be wiped?
**A:** All crawled content, embeddings, and vector metadata are persistently stored in your local directory at `data/chroma/`.  
The codebase enforces a strict **Database Preservation Constraint**:
- No destructive `DROP TABLE` or table reset commands are ever executed.
- Pages are saved using non-destructive `upsert` semantics.
- Previously crawled data remains available indefinitely for instant historical re-exports (PDF, Markdown, CSV, JSON).

---

## 🛠️ Usage & Integration FAQs

### Q8: How do I export crawled content to PDF or Markdown?
**A:**
- **From the CLI**:
  ```bash
  # Export to PDF:
  crawler scrape https://example.com --output page.pdf --format pdf

  # Export to Markdown:
  crawler scrape https://example.com --output page.md
  ```
- **From the Web UI**: Every crawled result in the dashboard includes **1-Click Export Buttons** for `PDF`, `Markdown`, `Plain Text`, `JSON`, and `CSV`.

---

### Q9: How do I send change alerts to Slack or Discord?
**A:**
1. In the Web UI, open the **Scheduled Crawls** tab.
2. Enter the URL you want to monitor and set the recurring schedule (e.g. `Every 12 Hours`).
3. Paste your Slack or Discord incoming webhook URL in the **Webhook URL** field.
4. When a significant content diff is detected, an alert payload with a summary of additions and removals is sent to your webhook automatically.

---

### Q10: How do I run the full test suite?
**A:** Run pytest from the root directory:
```bash
PYTHONPATH=src python3 -m pytest tests/ -v
```
All unit tests, scenario tests, and API integration tests run locally without requiring live external internet connections.
