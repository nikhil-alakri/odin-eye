# 09-Oct-2026 01:25

# Feature Specification: Vision & Multimodal Extraction (Feature 2)

## 1. Executive Summary & Problem Statement
Traditional web crawlers are text-blind: they rely solely on DOM HTML text. Modern websites frequently embed critical information in infographics, complex rendered canvas charts, visual pricing tables, or linked downloadable PDF whitepapers. 

This feature extends the Ethical AI Web Crawler into a multimodal ingestion platform:
1. **Full-Page Screenshot Archiving**: Captures high-resolution, full-page screenshots via Playwright during browser runs, cataloged by timestamp.
2. **Visual Before/After Slider**: Enables visual regression inspection comparing page rendering over time.
3. **Vision LLM Document & Chart Extraction**: Connects to Vision-enabled models (e.g. `meta/llama-3.2-11b-vision-instruct` via NVIDIA NIM) to parse infographics, diagrams, and image-based pricing matrices.
4. **Embedded PDF & Document Ingestion**: Automatically detects, downloads, parses, and indexes linked PDF whitepapers into ChromaDB so the RAG "Ask AI" assistant can query and cite external reports.

---

## 2. Skill Alignment & Methodology (`.agents/skills`)

| Specialized Agent Skill | Applied Architecture & Operational Discipline |
| :--- | :--- |
| **`engineering-ai-engineer`** | - Integration with NVIDIA NIM multimodal endpoints (`meta/llama-3.2-11b-vision-instruct`).<br>- Base64 image payload encoding with JPEG compression to minimize bandwidth and token costs.<br>- Graceful fallback to text markdown if vision model quota is exhausted. |
| **`engineering-prompt-engineer`** | - Specialized system prompts designed for visual document understanding (extracting unstructured tables, flowcharts, and visual badges into structured Pydantic schemas). |
| **`engineering-rag-pipeline-engineer`** | - PDF Document Ingestion: Structural chunking that preserves table boundaries, headings, and page numbers.<br>- Embeds PDF chunks with explicit source metadata (`source_type: "pdf"`, `page_number: X`, `parent_url: Y`) into ChromaDB.<br>- Multi-source context retrieval for "Ask AI". |
| **`engineering-data-engineer`** | - Safe pre-fetch streaming: checks `Content-Length` and rejects PDFs larger than 25 MB before memory saturation.<br>- Local disk storage partitioned by domain: `data/screenshots/{domain}/{hash}_{timestamp}.jpg`. |
| **`design-ui-designer` & `design-ux-researcher`** | - Interactive Before/After split comparison slider in `previewModal`.<br>- PDF Document Badge & inline PDF text previewer.<br>- Visual screenshot gallery in domain history. |

---

## 3. Technical Architecture & Component Specification

```
                                      [Crawl / Scrape Execution]
                                                   |
                         +-------------------------+-------------------------+
                         |                                                   |
               HTML & Browser Engine                                Linked PDF URLs
                         |                                                   |
                         v                                                   v
             [Playwright Screenshot]                                 [PDF Streamer]
          (page.screenshot(full_page))                             (Safe size limit check)
                         |                                                   |
          Compress to JPEG (80% Quality)                                     v
                         |                                            [PDF Parser]
                         v                                         (pypdf / pdfplumber)
             [Screenshot Archive]                                            |
        data/screenshots/{domain}/{id}.jpg                                   v
                         |                                          Cleaned PDF Markdown
                         +-------------------------+                         |
                         |                         |                         v
                         v                         v                 [ChromaDB Ingestion]
                [Vision LLM API]            [UI Dashboard]            crawled_knowledge
             (NVIDIA NIM Vision)            - Timeline Slider         (Tagged as PDF doc)
                         |                  - Screenshot Viewer
                         v
           Structured JSON / Chart Data
```

### A. Screenshot Capturer (`src/ethical_crawler/engines/browser_engine.py`)
- Enhances `BrowserEngine` with `capture_screenshot: bool = True`:
  ```python
  screenshot_bytes = await page.screenshot(
      full_page=True,
      type="jpeg",
      quality=80,
  )
  ```
- Generates image hash and persists to `data/screenshots/{domain}/{url_hash}_{timestamp}.jpg`.
- Records `screenshot_path` and `screenshot_url` in `CrawlResult`.

### B. PDF Extractor & Ingestion Pipeline (`src/ethical_crawler/extractors/pdf_extractor.py`)
- Safe streaming download via `httpx.AsyncClient`:
  - Rejects files over `max_pdf_size_mb` (default 25 MB).
  - Validates `Content-Type: application/pdf` or `%PDF` magic bytes.
- Extracts text page-by-page using `pypdf`:
  - Formats into clean structured Markdown with `## Page 1`, `## Page 2`.
  - Captures PDF metadata (Author, CreationDate, Title).
- Indexes into ChromaDB with metadata:
  ```python
  metadata = {
      "url": pdf_url,
      "domain": domain,
      "source_type": "pdf",
      "parent_page_url": parent_url,
      "pdf_page_count": len(pages),
      "title": pdf_title or filename,
  }
  ```

### C. Vision LLM Extractor (`src/ethical_crawler/extractors/vision_extractor.py`)
- Sends image payload to OpenAI-compatible Vision API:
  ```python
  messages = [
      {
          "role": "user",
          "content": [
              {"type": "text", "text": prompt},
              {
                  "type": "image_url",
                  "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}
              }
          ]
      }
  ]
  ```
- Supported tasks:
  1. `chart_to_table`: Converts visual bar/line/pie charts into Markdown tables.
  2. `infographic_summary`: Summarizes visual banners and diagrams.
  3. `visual_pricing_matrix`: Parses multi-column visual pricing grids with tick/cross feature matrices.

### D. REST API Endpoints (`src/ethical_crawler/api/v1/router.py`)
- `GET /v1/screenshots`: Retrieve list of captured screenshots for a domain or URL.
- `GET /v1/screenshots/file/{filename}`: Stream screenshot image file with caching headers.
- `POST /v1/vision/extract`: Trigger vision model extraction on an uploaded image or existing screenshot.
- `POST /v1/pdf/parse`: Download and extract text/tables from a PDF URL.

### E. Dashboard UI Integration
- **Preview Modal (`previewModal`)**:
  - Adds a new **"🖼️ Screenshot"** tab with full-page scrollable image.
  - Adds a **"Before / After"** split slider if multiple historical screenshots exist for the URL.
  - Adds an **"Extract from Image (Vision AI)"** button.
- **Knowledge Tab**:
  - Displays PDF document badges (`📄 PDF [14 pgs]`) in domain pages list.
  - Filter by document type: All, HTML Pages, PDF Reports.

---

## 4. Scenarios & Edge Cases

| Scenario | Challenge | Architectural Resolution |
| :--- | :--- | :--- |
| **1. Mega PDF Bomb (100MB+ Manual)** | Crawling an academic or corporate site with linked 500-page annual reports. | Pre-fetch header inspection rejects bodies > 25 MB; streaming byte-counter halts immediately if stream exceeds limit. |
| **2. Huge Viewport Infinite Height** | SPA with infinite scroll causing a 50,000px high screenshot crashing Chromium. | Max height clamp (`max_screenshot_height: 12000px`); logs warning and clips cleanly. |
| **3. Vision Model Rate Limits / Costs** | User initiates a 100-page crawl with vision extraction enabled. | Vision extraction is on-demand / opt-in per page or targeted selector, with local JPEG compression to prevent high token costs. |
| **4. Scanned PDF with No Text Layer** | PDF contains pure scanned images with 0 selectable text. | Gracefully detects empty text extraction (`text_length < 50`) and flags document with `ocr_needed: True` instead of crashing. |

---

## 5. Acceptance Criteria & Test Verification Matrix

- [ ] `tests/test_pdf_extractor.py`: Tests text extraction from sample PDF, page numbers, and size limit protection.
- [ ] `tests/test_vision_extractor.py`: Tests base64 image compression, mock vision model request payload formatting.
- [ ] `tests/test_screenshots.py`: Tests Playwright screenshot capture and disk persistence.
- [ ] ChromaDB RAG verification: "Ask AI" successfully retrieves and cites PDF chunks alongside HTML pages.
- [ ] All regression tests passing.

