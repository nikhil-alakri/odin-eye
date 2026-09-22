# Walkthrough: Workflow Quick Presets Engine & Custom Preset Memory

**Date & Time:** 22-Sep-2026 02:23  
**Feature Name:** `workflow_quick_presets`  
**Status:** Completed & Validated

---

## 1. Executive Summary

Transformed the simplistic numerical "Quick Presets" bar into an intelligent, 1-click **Workflow Configuration Engine** across both Multi-Page Crawl and Single Page Scrape forms:
- **Crawl Mode Presets**: 7 categorized 1-click workflow macros configuring Pages, Depth, Delay, Engine Strategy (HTTP/Browser/Auto), Sitemap, Vector Cache Mode, AI Extraction On/Off, AI Schema Template, and NVIDIA NIM Model all at once.
- **Scrape Mode Presets**: Introduced 5 dedicated single-page workflow presets (Instant Markdown, Company Profile, Product Details, Clean Article, and Dynamic Chromium).
- **Custom Preset Manager**: Users can save their current customized crawler configurations to browser `localStorage` with a custom label (e.g., *"My Weekly Competitor Scan"*), recalled in 1 click or deleted anytime.
- **Preset Visual Feedback**: Displays a toast badge confirming loaded preset parameters.

---

## 2. Implemented Workflow Presets

### Multi-Page Crawl Presets:
1. **⚡ Quick Smoke Test**: 3 pgs • Depth 1 • Fast HTTP • AI Off
2. **🏢 Competitor & Market Intel**: 8 pgs • Depth 2 • Auto Engine • Kimi-k3 AI • Company Profile Schema
3. **🧠 RAG Knowledge Base Ingest**: 35 pgs • Depth 3 • Sitemap ON • Fast HTTP • Embeddings Indexed
4. **🛍️ E-Commerce Catalog**: 20 pgs • Depth 2 • Auto Engine • Nemotron 3.5 • Product Schema
5. **🌐 Dynamic SPA / React**: 10 pgs • Depth 2 • Headless Chromium Browser • 2.5s Delay
6. **🔄 Live Growth Audit**: 12 pgs • Depth 2 • Cache OFF (forces live revision & byte delta tracking)
7. **🛡️ Polite Stealth**: 15 pgs • Depth 2 • 4.0s Delay • Strict Robots.txt

### Single Page Scraper Presets:
1. **⚡ Instant Markdown**: Fast HTTP • Cache ON • AI Off (1ms export)
2. **🏢 Company Profile**: Auto Engine • Kimi-k3 • Company Profile Schema
3. **🛍️ Product Details**: Auto Engine • Nemotron 3.5 • Product Schema
4. **📰 Clean Article**: Fast HTTP • GLM-5.3 Flash • Article Reading Format
5. **🖥️ Dynamic JS / SPA**: Headless Chromium Browser • Full DOM Rendering

---

## 3. Verification & Validation

- `tests/test_api.py` passed (Dashboard endpoint rendering validated).
- Full test suite passed (47/47 tests).
- Ruff check & format passed cleanly.

