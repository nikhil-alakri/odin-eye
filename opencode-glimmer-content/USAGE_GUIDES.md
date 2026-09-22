# Ethical Crawler Usage Guides

## 🚀 Getting Started

### Installation Methods

```bash
# Option 1: Full installation with all dependencies
make install-full

# Option 2: Minimal installation (HTTP only, no browser)
make install-minimal

# Option 3: Development mode (editable install)
pip install -e ".[dev]"

# Option 4: Just the Python package
pip install ethical-crawler
```

### Verify Installation

```bash
# Check version
crawler --version

# Check help
crawler --help

# Verify engines available
crawler info
```

---

## 📡 CLI Commands

### `crawler scrape`

Scrape a single page and extract content.

```bash
# Basic scrape
crawler scrape https://example.com

# With output format
crawler scrape https://example.com --output result.json --format json

# AI extraction with schema
crawler scrape https://example.com/article \
  --extract-ai \
  --schema article \
  --output article.json

# PDF export
crawler scrape https://example.com --output page.pdf --format pdf

# With politeness delay
crawler scrape https://example.com --delay 3.0
```

**Flags**:
- `--output` / `-o`: Output file path (default: stdout)
- `--format` / `-f`: Output format (json, markdown, plain, csv, pdf)
- `--extract-ai`: Enable AI-powered structured extraction
- `--schema` / `-s`: Extraction schema (article, product, faq, company, custom)
- `--delay` / `-d`: Override default politeness delay in seconds

---

### `crawler crawl`

Start a multi-page ethical crawl with progress tracking.

```bash
# Basic crawl
crawler crawl https://example.com --max-pages 10

# Full ethical crawl with all rules enabled
crawler crawl https://example.com \
  --max-pages 50 \
  --max-depth 3 \
  --respect-robots \
  --delay 2.0 \
  --export results.json

# AI extraction during crawl
crawler crawl https://example.com \
  --max-pages 20 \
  --extract-ai \
  --schema article \
  --output crawl_results.json

# Custom user-agent and contact
crawler crawl https://example.com \
  --bot-name "MyBot/1.0" \
  --bot-email "contact@mycompany.com" \
  --bot-url "https://mycompany.com" \
  --max-pages 30
```

**Flags**:
- `--max-pages` / `-n`: Maximum number of pages to crawl (default: 20)
- `--max-depth` / `-d`: Maximum link depth (default: 2)
- `--respect-robots` / `-r`: Check robots.txt for each domain (default: true)
- `--delay` / `-d`: Politeness delay in seconds between requests (default: 2.0)
- `--export` / `-e`: Export file path and format suffix
- `--extract-ai`: Enable AI extraction on each page
- `--schema` / `-s`: Schema for AI extraction
- `--bot-name`: Custom bot name (overrides .env)
- `--bot-email`: Contact email for bot identity
- `--bot-url`: URL for bot identity

---

### `crawler sitemap`

Inspect and extract URLs from a website's sitemap.

```bash
# Basic sitemap inspection
crawler sitemap https://example.com

# Output to CSV
crawler sitemap https://example.com --output urls.csv --format csv

# Only URLs with priority > 0.5
crawler sitemap https://example.com --min-priority 0.5

# Gzipped sitemap support (auto-detected)
crawler sitemap https://example.com --output sitemap_urls.txt
```

**Flags**:
- `--output` / `-o`: Output file path
- `--format` / `-f`: Output format (json, csv, txt)
- `--min-priority` / `-p`: Minimum sitemap priority threshold (0.0-1.0, default: 0.0)
- `--max-urls` / `-m`: Maximum URLs to extract (default: all)

---

### `crawler robots`

Verify robots.txt compliance for a domain.

```bash
# Basic robots.txt check
crawler robots https://example.com

# Check specific path
crawler robots https://example.com --path /admin/settings

# Show allowed paths only
crawler robots https://example.com --allowed-only

# Custom user-agent testing
crawler robots https://example.com \
  --bot-name "TestBot" \
  --bot-email "test@example.com"
```

**Flags**:
- `--path` / `-p`: Specific path to check (default: /)
- `--allowed-only` / `-a`: Show only allowed paths
- `--bot-name`: Custom bot name for testing
- `--bot-email`: Custom bot email for testing

---

### `crawler search`

Semantic search over the knowledge base (cached crawled content).

```bash
# Search with natural language query
crawler search "pricing plans and refund policy"

# Search with result limit
crawler search "cookie policy" --limit 5

# Search with source filtering
crawler search "API documentation" --source example.com

# Interactive search mode
crawler search "How do I reset my password?" --interactive
```

**Flags**:
- `--limit` / `-l`: Maximum results to return (default: 10)
- `--source` / `-s`: Filter by source domain
- `--include-metadata` / `-m`: Include source metadata in results
- `--interactive` / `-i`: Interactive prompt mode

---

### `crawler ask`

AI Q&A over crawled content knowledge base.

```bash
# Ask a question about crawled pages
crawler ask "What are the pricing plans mentioned on the website?"

# With context from specific pages
crawler ask "How do I contact support?" --context 5

# Specify model
crawler ask "What is the refund policy?" --model meta/llama-3.3-70b-instruct

# Interactive mode
crawler ask "Summarize the main features" --interactive
```

**Flags**:
- `--context` / `-c`: Number of relevant passages to consider (default: 3)
- `--model` / `-m`: AI model to use (default: from .env)
- `--include-sources` / `-i`: Include source URLs in answer (default: true)
- `--interactive` / `-i`: Interactive prompt mode

---

### `crawler serve`

Start the web dashboard and API server.

```bash
# Default settings
crawler serve

I need to create a comprehensive set of documentation in the required format. I will create the necessary files. Let me first analyze the project requirements and existing files, then create the documentation. I will need to:

1. Review all existing files in the repository to understand the codebase and user requirements.
2. Create a comprehensive documentation set based on the project structure and<tool_call>
<function=glob>
<parameter=pattern>
**/*