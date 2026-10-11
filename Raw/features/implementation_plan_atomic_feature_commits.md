# Implementation Plan: Atomic Feature Commits (Plan + Walkthrough + Code)

**Date & Time**: 12-Oct-2026 03:59 UTC  
**Objective**: Organize and commit all uncommitted features into logical, self-contained atomic git commits where each commit contains:
1. `Raw/features/implementation_plan_[feature].md`
2. `Raw/features/walkthrough_[feature].md`
3. Associated feature specifications / diagrams (if applicable)
4. Source code implementations (`src/...`) and corresponding unit tests (`tests/...`)

---

## User Review Required

> [!IMPORTANT]
> To strictly follow your requirement: **"where implementation plan, walkthrough and its code in one commit"**, the current repository state consists of **8 distinct uncommitted feature modules**. 
> All files have been mapped so that each commit contains its exact documentation triplet/pair and its corresponding implementation code without mixing.

---

## Proposed Commit Sequence

### Commit 1: Scheduled Crawling, Content Diff Engine & Webhook Alerts
- **Commit Message**: `feat(scheduler): scheduled crawling, content diff engine & webhook alerts`
- **Documentation**:
  - `Raw/features/implementation_plan_advanced_features_suite_and_scheduled_diff.md`
  - `Raw/features/walkthrough_scheduled_crawling_and_diff_alerts.md`
  - `Raw/features/spec_scheduled_crawling_and_diff_alerts.md`
- **Code & Tests**:
  - `src/ethical_crawler/scheduler/`
  - `src/ethical_crawler/knowledge/diff_engine.py`
  - `src/ethical_crawler/alerts/`
  - `tests/test_scheduler.py`
  - `tests/test_schedules_api.py`
  - `tests/test_diff_engine.py`

---

### Commit 2: Point-and-Click Interactive Element Selector & Visual Picker
- **Commit Message**: `feat(picker): interactive CSS element selector and visual picker`
- **Documentation**:
  - `Raw/features/walkthrough_point_and_click_element_picker.md`
  - `Raw/features/spec_point_and_click_element_picker.md`
- **Code & Tests**:
  - `src/ethical_crawler/extractors/element_picker.py`
  - `tests/test_element_picker.py`

---

### Commit 3: Competitive Intelligence Comparator, Tech Profiler & PDF Extraction
- **Commit Message**: `feat(intel): competitive intelligence comparator, tech profiler & PDF extraction`
- **Documentation**:
  - `Raw/features/implementation_plan_competitive_intelligence_and_tech_profiling.md`
  - `Raw/features/walkthrough_competitive_intelligence_and_tech_profiling.md`
  - `Raw/features/spec_competitive_intelligence_and_tech_profiling.md`
- **Code & Tests**:
  - `src/ethical_crawler/extractors/tech_profiler.py`
  - `src/ethical_crawler/extractors/pdf_extractor.py`
  - `src/ethical_crawler/knowledge/competitor_comparator.py`
  - `tests/test_tech_profiler.py`
  - `tests/test_pdf_extractor.py`
  - `tests/test_competitor_comparator.py`

---

### Commit 4: Multimodal Vision Extraction with NVIDIA Nemotron Omni
- **Commit Message**: `feat(vision): multimodal vision extraction with NVIDIA Nemotron Omni & screenshot captures`
- **Documentation**:
  - `Raw/features/walkthrough_vision_and_multimodal_extraction.md`
  - `Raw/features/spec_vision_and_multimodal_extraction.md`
- **Code & Tests**:
  - `src/ethical_crawler/extractors/vision_extractor.py`
  - `tests/test_vision_extractor.py`
  - `tests/test_screenshots.py`

---

### Commit 5: Design System Studio with Custom Themes
- **Commit Message**: `feat(theme): design system studio with custom themes and dynamic CSS styling`
- **Documentation**:
  - `Raw/features/implementation_plan_theme_and_design_system_studio.md`
  - `Raw/features/walkthrough_theme_and_design_system_studio.md`
- **Code & Tests**:
  - `src/ethical_crawler/api/theme.py`
  - `tests/test_theme.py`

---

### Commit 6: Visual Product Reverse-Engineering & Architecture Blueprint Generator
- **Commit Message**: `feat(blueprint): visual product reverse-engineering & architecture blueprint generator`
- **Documentation**:
  - `Raw/features/implementation_plan_visual_product_reverse_engineering.md`
  - `Raw/features/walkthrough_visual_product_reverse_engineering.md`
  - `Raw/features/spec_visual_product_reverse_engineering.md`
- **Code & Tests**:
  - Initial `src/ethical_crawler/extractors/visual_blueprint_generator.py`
  - `tests/test_visual_blueprint.py`

---

### Commit 7: Boardroom-Grade Executive PDF Report Builder
- **Commit Message**: `feat(blueprint-pdf): boardroom-grade executive PDF report builder for blueprints`
- **Documentation**:
  - `Raw/features/implementation_plan_visual_blueprint_pdf_styling.md`
  - `Raw/features/walkthrough_visual_blueprint_pdf_styling.md`
- **Code**:
  - Initial `src/ethical_crawler/extractors/visual_blueprint_pdf.py`

---

### Commit 8: Dynamic Domain Archetype Synthesis & Real Pixel Palette Extraction
- **Commit Message**: `feat(blueprint-domain): dynamic domain archetype synthesis & real pixel palette extraction`
- **Documentation**:
  - `Raw/features/implementation_plan_dynamic_blueprint_domain_synthesis.md`
  - `Raw/features/walkthrough_dynamic_blueprint_domain_synthesis.md`
- **Code**:
  - Refined domain synthesis in `src/ethical_crawler/extractors/visual_blueprint_generator.py`
  - Dynamic schema and wireframe adaptations in `src/ethical_crawler/extractors/visual_blueprint_pdf.py`

---

### Commit 9: Complete UI Modernization, Modal Redesign & Platform Core
- **Commit Message**: `feat(ui): complete UI modernization, modal redesign & platform integrations`
- **Documentation**:
  - `Raw/features/implementation_plan_ui_complete_polish.md`
  - `Raw/features/walkthrough_ui_complete_polish.md`
  - `Raw/features/implementation_plan_ui_visual_polish.md`
  - `Raw/features/walkthrough_ui_visual_polish.md`
  - `Raw/features/walkthrough_scrape_knowledge_reflection.md`
  - `Raw/features/diagrams_all_features.md`
- **Code & Core**:
  - `.gitignore` (excludes local caches and temporary sessions)
  - `src/ethical_crawler/knowledge/ask_cache.py`
  - `src/ethical_crawler/api/app.py`
  - `src/ethical_crawler/api/v1/router.py`
  - `src/ethical_crawler/knowledge/dossier_generator.py`
  - `src/ethical_crawler/storage.py`
  - `src/ethical_crawler/vector_store.py`
  - `src/ethical_crawler/crawler.py`
  - `src/ethical_crawler/engines/base.py`
  - `src/ethical_crawler/engines/browser_engine.py`
  - `src/ethical_crawler/extractors/__init__.py`
  - `src/ethical_crawler/types.py`
  - `tests/test_scrape_export.py`
  - `tests/test_vector_store.py`

---

## Verification Plan

### Automated Verification
After applying the commits:
1. Run `git log -n 10 --oneline` to confirm each commit has its clean message and files.
2. Run `git status` to verify working tree is clean.
3. Run test suite across all modules:
   ```bash
   PYTHONPATH=src python3 -m pytest tests/ -v
   ```

