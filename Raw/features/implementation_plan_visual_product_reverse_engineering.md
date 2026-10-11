# Implementation Plan: Visual Product Blueprint & Reverse-Engineering Engine
**Date & Time**: 11-Oct-2026 01:42

## 1. Goal Description
Build a comprehensive **Visual Product Blueprint & Reverse-Engineering Engine** that inspects multi-page screenshot collections (dashboards, admin portals, settings, public pages) for a domain and generates an exhaustive, production-grade technical and product specification:
1. **Storyboard & Navigation Linkings**: Sequence diagrams and flowcharts mapping screen-to-screen transitions and user journeys.
2. **Frontend Architecture & UI Guidance**: Deconstructed React/Tailwind component hierarchies, design tokens (colors, fonts, spacing), and usability critique.
3. **Backend Architecture & API Contracts**: Inferred Entity-Relationship Diagrams (ERD), REST API endpoints, request/response JSON schemas, and data validation rules.
4. **Product Intelligence & Use Cases**: Feature inventory, persona breakdowns, and detailed Gherkin-style use cases.
5. **Interactive Dashboard Studio (`#blueprintModal`)**: High-res screenshot carousel, tabbed architecture viewer, interactive Mermaid diagram rendering, and 1-click PDF/Markdown export.

---

## 2. Modern Web Guidance Standards Applied (`/modern-web-guidance`)

Following the `/modern-web-guidance` best practices:
* **Native Dialog & Popover Behavior (`<dialog>` & Overlay Standards)**:
  - Accessible top-layer modal overlay with backdrop-blur and light-dismiss (`closedby="any"` / backdrop click).
  - Synchronized body scroll-locking (`overflow: hidden`) and trap-safe keyboard navigation (Escape to close, Tab cycle).
* **Scroll-Snap Carousel & Gallery (`carousel-snap-highlights`)**:
  - Horizontal thumbnail scroller using `scroll-snap-type: x mandatory` and `scroll-snap-align: start`.
  - Snapped item highlight indicators with `@media (prefers-reduced-motion: reduce)` guards to prevent motion sickness.
* **Image Loading & Core Web Vitals Optimization (`optimize-image-priority`)**:
  - Primary inspected screenshot uses `fetchpriority="high"` for immediate Largest Contentful Paint (LCP).
  - Off-screen carousel thumbnails use `fetchpriority="low"` and `loading="lazy"` with explicit `aspect-ratio: 16 / 9` to prevent Cumulative Layout Shift (CLS).
  - Never combining `fetchpriority="high"` with `loading="lazy"`.
* **Accessible Tab Navigation (`accessibility`)**:
  - ARIA tabs pattern: `role="tablist"`, `role="tab"`, `aria-selected="true"`, `aria-controls`, and `role="tabpanel"`.

---

## 3. User Review Required

> [!IMPORTANT]
> The engine can run in two modes:
> 1. **AI Vision Mode**: Uses NVIDIA NIM Multimodal Vision LLM (`meta/llama-3.2-11b-vision-instruct`) for rich, deep visual semantic extraction when `AI_API_KEY` is present.
> 2. **Deterministic Heuristic Mode**: Employs structural screen analysis, route slug parsing, and architectural patterns to generate complete diagrams, ERD, component trees, and API specs even without an active AI key.

> [!NOTE]
> All vector store records (145 ChromaDB documents) remain 100% preserved. This feature operates purely on screenshot assets in `data/screenshots/` and creates non-destructive blueprints.

---

## 4. Proposed Changes

### Component 1: Visual Blueprint Generator Engine (`src/ethical_crawler/extractors/visual_blueprint_generator.py`) [NEW]
- Define Pydantic Models:
  - `ScreenDecomposition`: `filename: str`, `route_name: str`, `view_type: str` (dashboard, admin_table, settings_form, analytics, auth), `widgets: list[str]`, `actions: list[str]`, `tables: list[str]`, `metrics: list[str]`.
  - `ProductBlueprintResult`: `domain: str`, `screens: list[ScreenDecomposition]`, `storyboard_md: str`, `features_list: list[str]`, `use_cases: list[dict]`, `frontend_components: list[dict]`, `design_tokens: dict`, `api_endpoints: list[dict]`, `erd_mermaid: str`, `navigation_mermaid: str`, `full_markdown_dossier: str`.
- Class `VisualBlueprintGenerator`:
  - `scan_domain_screenshots(domain: str) -> list[Path]`: Discovers captured screenshots in `data/screenshots/{domain}/`.
  - `decompose_screen(image_path: Path, domain: str) -> ScreenDecomposition`: Runs Vision LLM or structural heuristics to categorize the view.
  - `build_navigation_diagram(screens: list[ScreenDecomposition]) -> str`: Constructs Mermaid `flowchart TD` or `stateDiagram-v2`.
  - `build_erd_diagram(screens: list[ScreenDecomposition]) -> str`: Infers data entities from tables/forms and synthesizes Mermaid `erDiagram`.
  - `build_api_contracts(screens: list[ScreenDecomposition]) -> list[dict]`: Infers REST CRUD endpoints with headers and JSON schemas.
  - `build_frontend_components(screens: list[ScreenDecomposition]) -> dict`: Generates Atomic Design component tree and design tokens.
  - `generate_blueprint(domain: str) -> ProductBlueprintResult`: Orchestrates full analysis and formats executive Markdown report.
  - `export_pdf(result: ProductBlueprintResult, buf)`: Compiles styled ReportLab PDF.

### Component 2: REST API Endpoints (`src/ethical_crawler/api/v1/router.py`) [MODIFY]
- `GET /v1/blueprint/domains`: Returns list of all domains that have captured screenshots available.
- `POST /v1/blueprint/generate`: Accepts `{ domain: str, custom_focus: str | None }` and returns complete `ProductBlueprintResult`.
- `POST /v1/blueprint/export`: Accepts `{ domain: str, format: 'pdf' | 'markdown' }` and streams downloadable PDF or Markdown report.

### Component 3: Dashboard UI Integration (`src/ethical_crawler/api/app.py`) [MODIFY]
- Header Navigation: Add `📸 BLUEPRINT` button next to `⚔️ BENCHMARK`.
- Modal Dialog (`#blueprintModal`):
  - Domain selector dropdown showing screenshot counts per domain.
  - Modern CSS scroll-snap thumbnail carousel with lazy loaded thumbnails and aspect ratio preservation.
  - "Generate Full Product Blueprint" button with progress spinner.
  - Accessible tabbed viewer (`role="tablist"`):
    1. 🗺️ **Storyboard & Product Overview**: Value proposition, personas, user flows.
    2. 📊 **Mermaid Diagrams**: Live rendered Navigation Flowchart and Entity-Relationship Diagram (ERD).
    3. 💻 **Frontend & UI Guidance**: Component tree, design tokens, and usability critique.
    4. ⚙️ **Backend & API Specs**: Inferred REST endpoints with request/response schemas.
  - Download buttons: `📄 Download Architecture PDF` and `📝 Download Markdown`.
- Modal registry: Add to `MODAL_IDS`, `syncBodyScrollLock()`, and `closeTopModal()`.

---

## 5. Verification Plan

### Automated Tests
1. `tests/test_visual_blueprint.py` [NEW]:
   - Test screenshot discovery for mock domains.
   - Test screen decomposition for admin, dashboard, and settings screens.
   - Test Mermaid Navigation flowchart generation.
   - Test Mermaid Entity-Relationship Diagram (ERD) generation.
   - Test REST API endpoint inference and schemas.
   - Test PDF report generation with ReportLab.
   - Test API endpoints `GET /v1/blueprint/domains`, `POST /v1/blueprint/generate`, and `POST /v1/blueprint/export`.
2. Full test suite: `pytest tests/` (expecting 100+ tests passing).

### Manual Verification
- Open dashboard at `http://localhost:8000`.
- Click `📸 BLUEPRINT` in header to open modal.
- Verify screenshot gallery and generate blueprint for any indexed domain.
- Confirm Mermaid diagrams and API specs render properly.
- Verify PDF download generates the styled architecture blueprint.
