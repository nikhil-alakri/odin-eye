# Implementation Plan: Dynamic Domain Synthesis & Real Visual Extraction

**Date & Time**: 12-Oct-2026 03:25 UTC  
**Target Feature**: Domain-Specific Dynamic Reverse-Engineering & Palette Extraction

---

## 1. Problem Statement & User Feedback

The user correctly noticed that the generated PDF architecture dossier for `www.revepod.com` (and other websites) outputs generic B2B SaaS mock templates (e.g., *Stripe Billing, User Invites, Organization/Subscription entities, Indigo #4F46E5*) instead of reflecting the actual website:
* **Revepod is a podcast & media production studio management system** with:
  - Crew Scheduling (`dashboard-crew-scheduling`)
  - Quotations & Estimates (`dashboard-quotations`, `dashboard-quotations-new`)
  - Inbound Client Enquiries (`dashboard-enquiries-enquiries`, `dashboard-enquiries-quotations`)
  - Post-Production Pipeline (`dashboard-post-production`)
  - Production Projects (`dashboard-projects`)
  - Studio Client Requests (`dashboard-client-requests`)
* However, `VisualBlueprintGenerator` and `VisualBlueprintPDFBuilder` had hardcoded mock templates for ERD, API specs, features, user journeys, wireframe labels, and design tokens.

---

## 2. Proposed Changes

### A. Intelligent Domain & Route Archetype Synthesis
* In `VisualBlueprintGenerator`:
  - Dynamically analyze screenshot filenames and route tokens to determine the true domain archetype (e.g., Media/Studio Production, E-commerce, Project Management, Healthcare, Dev Tools, or General SaaS).
  - Generate domain-accurate screen titles, widgets, actions, tables, and metrics:
    - `crew-scheduling` &rarr; Crew Roster, Call Sheets, Recording Dates.
    - `quotations` &rarr; Client Quotations, Line Items, Production Estimates.
    - `enquiries` &rarr; Inbound Leads Pipeline, Project Scope, Budget.
    - `post-production` &rarr; Audio/Video Editing Queue, Sound Mix, Final Master.
    - `projects` &rarr; Production Projects, Episode Deliverables.

### B. Dynamic Entity-Relationship Diagram (ERD) & Entity Models
* Replace hardcoded `ORGANIZATION / USER / SUBSCRIPTION / INVOICE` in both `VisualBlueprintGenerator` and `VisualBlueprintPDFBuilder`:
  - Synthesize entity models directly from the detected domain and screens:
    - E.g. For Revepod: `PROJECT`, `CREW_MEMBER`, `QUOTATION`, `ENQUIRY`, `POST_PRODUCTION_TASK`.
  - Pass structured entities in `ProductBlueprintResult` so `VisualBlueprintPDFBuilder._render_relational_schema()` dynamically renders the actual entities.

### C. Dynamic REST API Contracts
* Synthesize API endpoints that mirror the detected routes:
  - `GET /api/v1/projects`
  - `GET /api/v1/crew/schedules`
  - `POST /api/v1/quotations`
  - `GET /api/v1/enquiries`
  - `PATCH /api/v1/post-production/tasks/:id`

### D. Dominant Color Palette Extraction from Screenshots (PIL)
* Implement `extract_dominant_palette_from_images(image_paths)`:
  - Sample pixels from the screenshots using PIL.
  - Dynamically detect:
    - Primary Brand Color (most frequent saturated accent color, e.g. Revepod's Deep Indigo/Violet `#402090`).
    - Secondary Accent Color (e.g. Vibrant Emerald `#20D060` or Cyan).
    - Canvas / Background surface colors.
    - Dark typography color (e.g. `#101030`).
  - Feed these real extracted colors directly into `ProductBlueprintResult.design_tokens["colors"]`.

### E. Domain-Aware Wireframe Blueprint & User Journeys
* Update `_render_component_wireframe_drawing()` in `VisualBlueprintPDFBuilder` to use the domain's real route names (e.g., `Crew Scheduling`, `Post Production`, `Quotations`, `Projects`).
* Generate domain-accurate executive capabilities and user journeys on Page 1.

---

## 3. Files to Modify

1. `[MODIFY]` `src/ethical_crawler/extractors/visual_blueprint_generator.py`:
   - Add `extract_dominant_palette_from_images()` using PIL.
   - Make `decompose_screen()` dynamically recognize rich domain vocabulary (studio/media, e-commerce, CRM, devtools, finance).
   - Make `build_erd_diagram()`, `build_api_contracts()`, `build_frontend_components()`, `features`, and `use_cases` dynamically synthesized from the detected screen set.
   - Update `ProductBlueprintResult` to include `entities: list[dict[str, Any]]`.
2. `[MODIFY]` `src/ethical_crawler/extractors/visual_blueprint_pdf.py`:
   - Make `_render_relational_schema()` dynamically render `self.bp.entities` from the blueprint.
   - Make `_render_component_wireframe_drawing()` adapt its navigation labels to the domain's actual routes.
   - Use dynamic colors throughout the PDF flowables.

---

## 4. Verification Plan

1. Run blueprint generation on `www.revepod.com`:
   - Verify that ERD reflects `PROJECT`, `CREW_MEMBER`, `QUOTATION`, `ENQUIRY`, `POST_PRODUCTION_TASK`.
   - Verify that REST APIs reflect `/api/v1/projects`, `/api/v1/crew/schedules`, `/api/v1/quotations`, `/api/v1/enquiries`.
   - Verify that design tokens reflect real sampled colors (`#402090`, `#20D060`, `#101030`).
   - Verify user journeys reflect podcast/production workflows.
2. Render PDF pages to PNG and visually inspect.
3. Run `pytest tests/test_visual_blueprint.py` to ensure all tests pass.

