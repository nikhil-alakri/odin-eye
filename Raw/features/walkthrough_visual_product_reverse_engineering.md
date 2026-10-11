# Walkthrough: Visual Product Blueprint & Reverse-Engineering Engine
**Date & Time**: 11-Oct-2026 01:50

---

## 1. Overview & Objectives
The **Visual Product Blueprint & Reverse-Engineering Engine** transforms collections of multi-page screenshots from any web application (e.g. public landing pages, authentication flows, dashboards, data tables, analytics charts, and settings/billing portals) into an exhaustive, production-grade **Full-Stack Technical Specification & Product Architecture Blueprint**.

It synthesizes:
1. **Interactive Storyboards & Screen Linkings**: Step-by-step user journey mapping and Mermaid navigation flowcharts.
2. **Product Breakdown & Feature Inventory**: Core value propositions, persona breakdowns, and complete Gherkin-syntax use cases.
3. **Frontend Architecture & UI Guidance**: Atomic Design component trees (`AppShellLayout`, `MetricCard`, `PaginatedDataTable`), design tokens (colors, font hierarchy, spacing), and usability critique.
4. **Backend Architecture & Inferred Data Models**: Inferred Entity-Relationship Diagrams (ERD in Mermaid format) and REST API contracts with mock request/response JSON schemas.
5. **Modern Dashboard Studio (`#blueprintModal`)**: Adheres to `/modern-web-guidance` standards with CSS scroll-snap carousel, lazy-loading image priorities (`fetchpriority="high"` on LCP, `fetchpriority="low"` on thumbnails), accessible tab navigation, and 1-click PDF/Markdown export.

---

## 2. Key Components Delivered

### A. Visual Blueprint Generator (`src/ethical_crawler/extractors/visual_blueprint_generator.py`)
- **Multi-Screen Discovery & Parsing (`scan_domain_screenshots`)**:
  - Automatically indexes screenshot files in `data/screenshots/{domain}/*.jpg`.
  - Discovers domains with captured archives via `list_available_domains()`.
- **Screen View Decomposition (`decompose_screen`)**:
  - Semantic classification into view types: `dashboard`, `admin_table`, `settings_form`, `analytics`, `auth`, `public`.
  - Extracts visible widgets, action buttons, metrics counters, forms, and inferred URL routes (e.g. `/dashboard`, `/admin/users`, `/settings/billing`).
- **Architecture Synthesis Modules**:
  - `build_navigation_diagram()`: Constructs Mermaid `flowchart TD` mapping chronological screen transitions.
  - `build_erd_diagram()`: Infers relational database schemas (`ORGANIZATION`, `USER`, `SUBSCRIPTION`, `INVOICE`, `API_KEY`, `ANALYTICS_EVENT`) into Mermaid `erDiagram`.
  - `build_api_contracts()`: Generates REST endpoints (`GET /api/v1/dashboard/metrics`, `GET /api/v1/users`, `POST /api/v1/users/invite`, `GET /api/v1/billing/subscription`, `POST /api/v1/api-keys`) with query parameters and JSON schema payloads.
  - `build_frontend_components()`: Produces Atomic Design component hierarchies and extracted CSS/Tailwind design tokens.
  - `export_pdf()`: Leverages `StorageExporter.to_dossier_pdf()` to compile executive-grade ReportLab multi-column PDFs.

### B. REST API Endpoints (`src/ethical_crawler/api/v1/router.py`)
- `GET /v1/blueprint/domains`: Returns all domains with screenshot archives and screenshot counts.
- `POST /v1/blueprint/generate`: Generates complete `ProductBlueprintResult` with diagrams, component trees, and API specs.
- `POST /v1/blueprint/export`: Downloads the generated architecture blueprint as styled PDF (`application/pdf`) or Markdown (`text/markdown`).

### C. Visual Dashboard Integration (`src/ethical_crawler/api/app.py`)
- **Header Navigation**: Added `📸 BLUEPRINT` button next to `⚔️ BENCHMARK`.
- **Modal Dialog (`#blueprintModal`)**:
  - Integrated with `MODAL_IDS`, `syncBodyScrollLock()`, and `closeTopModal()`.
  - Domain selector dynamically populates screenshot counts.
  - **Modern CSS Scroll-Snap Carousel**: `scroll-snap-type: x mandatory` with lazy loading and `aspect-video` CLS prevention.
  - **Accessible Tab Navigation (`role="tablist"`)**:
    - 🗺️ **Storyboard & Personas**: Executive overview, features grid, Gherkin use cases.
    - 📊 **Mermaid Diagrams**: Navigation flowchart and Entity-Relationship Diagram (ERD) with "Copy Mermaid" buttons.
    - 💻 **Frontend & UI Guidance**: Atomic component specifications and extracted design tokens.
    - ⚙️ **Backend & API Specs**: Inferred REST endpoint contracts with JSON schemas.
  - 1-Click download buttons: `📄 Download Architecture PDF` and `📝 Download Markdown`.

---

## 3. Modern Web Guidance Compliance (`/modern-web-guidance`)
- **Dialog & Popover Overlays**: Top-layer promotion with backdrop-blur, synchronized body scroll locking (`overflow: hidden`), and Escape/click-outside light dismiss.
- **Scroll-Snap Carousel**: Native `scroll-snap-type: x mandatory`, item `scroll-snap-align: start`, and `@media (prefers-reduced-motion: reduce)` motion protection.
- **Image Priority Optimization**: Selected preview image uses `fetchpriority="high"`, off-screen carousel thumbnails use `fetchpriority="low"` and `loading="lazy"` with explicit aspect-ratio to prevent layout shifts.
- **Accessibility**: Full ARIA tab patterns (`role="tablist"`, `role="tab"`, `aria-selected`, `role="tabpanel"`).

---

## 4. Verification & Automated Tests
- **Test Suite**: `tests/test_visual_blueprint.py` (5 tests):
  - `test_screen_decomposition_and_semantics`: Validates view type categorization and route parsing.
  - `test_mermaid_diagrams_generation`: Validates Navigation flowchart and ERD syntax.
  - `test_api_contracts_and_components_generation`: Validates REST endpoints and Atomic Design components.
  - `test_full_blueprint_generation_and_pdf_export`: Validates end-to-end dossier creation and ReportLab PDF compilation.
  - `test_blueprint_api_endpoints`: Validates REST endpoints `/api/v1/blueprint/*`.
- **Full Regression Suite**: **102 passed in 27.19s** (100% pass rate across the entire repository).
- **Database Preservation**: ChromaDB collection `crawled_knowledge` verified intact with **150 documents preserved** (zero data loss).

