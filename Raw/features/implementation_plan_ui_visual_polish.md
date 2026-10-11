# Implementation Plan: UI & Preview Modal Visual Overhaul

**Date & Time**: 08-Oct-2026 02:10

## User Review Required

> [!IMPORTANT]
> The uploaded screenshot (`media_1791405046332.png`) revealed critical UI weaknesses and JavaScript bugs:
> 1. **Visual Mismatch ("Frankenstein Patchwork")**: The modal header is dark slate, the body is stark white, and inside sits a pitch-black `<pre>` block with low-contrast dark blue text.
> 2. **Overflowing Header Tabs**: The 5 preview tabs (`Markdown`, `AI Extraction`, `RPA Logs`, `Network APIs`, `DOM Elements`) squeeze together, causing "DOM..." to be cut off and pushing the modal close `[✕]` button partially off-screen.
> 3. **Unrendered Raw Markdown**: The content is presented as raw, unformatted markdown text with `#`, `*`, `**`, `[link](url)` syntax rather than an elegant, readable page.
> 4. **Runtime Crashes**: `renderPreviewMarkdown()` and `togglePreviewSource()` are invoked in the code but were never implemented, causing runtime `ReferenceError` crashes.

## Proposed Changes

### Component 1: Preview Modal Complete Redesign (`src/ethical_crawler/api/app.py`)

#### 1.1 Modal Header & Navigation Redesign
- Expand modal container width from `max-w-4xl` (896px) to `max-w-5xl` (1024px) with generous breathing room.
- Add a **Fullscreen / Maximize toggle** (`[⤢]` / `[⤡]`) next to the close button so users can inspect long documents comfortably.
- Split the header into two clean, organized tiers:
  - **Tier 1 (Title & Meta)**: Page Title, external link icon `[↗]` pointing to live URL, status code badge (e.g. `200 OK`), content size badge, engine badge, fullscreen button, and close `[✕]` button.
  - **Tier 2 (Tabs & Tools)**: Smooth pill tab navigation with count badges:
    - 📖 **Reader View** (formatted HTML)
    - 💻 **Raw Markdown** (syntax-styled monospace with line numbers)
    - 🧠 **AI Extraction** (structured cards + JSON toggle)
    - 🤖 **RPA Logs** (timeline trace)
    - 🌐 **Network APIs** (interception table)
    - 🔍 **DOM Elements** (hierarchical inspector + CSS selector tester)
- Responsive wrapping: tabs will never overflow or squeeze out the close button.

#### 1.2 Formatted Reader Mode (Markdown to HTML)
- Implement a robust, secure, client-side Markdown-to-HTML parser (`renderPreviewMarkdown`):
  - Formatted headings (H1–H4) with clean proportional sizing and anchor tags.
  - Clean typography for paragraphs, bold, italic, and blockquotes with left accent borders.
  - Clickable links with external link indicator (`target="_blank" rel="noopener"`).
  - Formatted bullet and numbered lists.
  - Code blocks with copy-to-clipboard button and dark background syntax container.
  - Formatted tables with clean borders and subtle zebra striping.
  - Quick meta bar at the top of the reading view: Word count, character count, and estimated reading time (e.g. `⏱️ 3 min read`).

#### 1.3 Raw Markdown Source Mode
- Implement `togglePreviewSource()`:
  - Allows instant 1-click toggle between "📖 Reader View" and "💻 Markdown Source".
  - Monospace code view with proper high-contrast text (`text-emerald-300` or `text-slate-200` on dark background).
  - "Copy Markdown" button with instant checkmark feedback animation.

#### 1.4 Unified Theme & Visual Cohesion
- Eliminate the jarring white-and-black patchwork:
  - The modal card, header, body, and content containers will share a cohesive, premium dark aesthetic (or cohesive light aesthetic matching the dashboard).
  - Support a **Theme Switcher (Dark / Light)** in the top header that toggles between:
    - **Obsidian Dark** (modern cyberpunk/sleek developer dark theme with slate-900, glass borders, and teal/emerald accents).
    - **Clean Editorial Light** (crisp zinc/slate surfaces with high contrast and subtle borders).
  - Persist user preference to `localStorage`.

#### 1.5 Polish for AI, Network, DOM, and RPA Tabs
- **AI Extraction Tab**: Visual schema card summary for `company_profile` / `product` + formatted JSON view with syntax highlighting and 1-click copy.
- **Network APIs Tab**: Filterable table with search box, HTTP method badges (GET in cyan, POST in purple), status code pills, payload size, and response viewer.
- **DOM Elements Tab**: Interactive categorized inspector (Headings outline, Links count, Buttons, Forms, Images) + live CSS selector testing tool.
- **RPA Logs Tab**: Visual step-by-step automation timeline with action icons and pass/fail badges.

---

## Verification Plan

### Automated Verification
- Run existing test suite to ensure zero regressions:
  ```bash
  .venv/bin/pytest tests/ -v
  ```
- Run linter and formatting checks:
  ```bash
  .venv/bin/ruff check src/ tests/
  ```

### Manual Verification
1. Open dashboard in browser (`http://localhost:8000`).
2. Run a crawl or scrape on a test URL.
3. Click "Preview" on a crawled result.
4. Verify:
   - Header tabs are cleanly aligned and no elements are truncated.
   - Close button `[✕]` is prominently positioned and fully clickable.
   - Modal background and body colors are completely cohesive (no jarring white/black patches).
   - Reader View displays formatted HTML with headings, lists, links, and reading time.
   - "Show Source" toggle switches smoothly between Reader View and Raw Markdown.
   - "Copy Markdown" works with toast feedback.
   - Fullscreen toggle smoothly expands modal to edge-to-edge layout.
   - All 5 tabs (`Reader`, `AI Extraction`, `RPA Logs`, `Network APIs`, `DOM Elements`) render cleanly without any console errors.
