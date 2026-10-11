# 09-Oct-2026 01:25

# Feature Specification: Interactive Point-and-Click Element Picker (Feature 3)

## 1. Executive Summary & Problem Statement
Currently, building RPA steps (clicking a button, typing in a search bar) or scraping targeted DOM fragments requires users to manually open Chrome DevTools, inspect DOM elements, write CSS selectors or XPaths, and test them. This creates friction for non-technical users and slows down workflow creation.

The **Interactive Point-and-Click Element Picker** provides a visual sandbox inside the Single Page Scraper and Custom RPA Step Builder where users can browse the rendered target page, hover over elements to see live highlights, and click any element to automatically generate the most optimal, resilient CSS selector or XPath.

---

## 2. Skill Alignment & Methodology (`.agents/skills`)

| Specialized Agent Skill | Applied Architecture & Operational Discipline |
| :--- | :--- |
| **`engineering-frontend-developer`** | - Secure Sandboxed Iframe with `sandbox="allow-scripts allow-same-origin"`.<br>- Bidirectional `window.postMessage` communication between parent dashboard and the sandboxed preview frame.<br>- Prevents external navigation (intercepts all `<a>` clicks and form submits inside the sandbox). |
| **`design-ui-designer`** | - Interactive element highlighting: Hover state (`outline: 2px dashed #9333ea`, background tint `rgba(147, 51, 234, 0.08)`).<br>- Selection tooltip badge: floating chip displaying tag name, ID, and class count.<br>- Seamless integration with theme design tokens (`--ds-*`). |
| **`engineering-developer-tooling-engineer`** | - Multi-tiered selector generation algorithm:<br>  1. Priority 1: Unique `#id`<br>  2. Priority 2: Semantic test attributes (`[data-testid]`, `[data-cy]`, `[role]` + accessible name)<br>  3. Priority 3: Unique CSS class combinations<br>  4. Priority 4: Shortest unique hierarchical path (`header nav a.nav-link`)<br>  5. Priority 5: Fallback XPath (`//button[contains(text(), 'Submit')]`). |
| **`product-behavioral-nudge-engine`** | - 1-Click Action Bar: "Use in RPA Step", "Use as Scrape Target", "Copy Selector".<br>- Instant validation pill showing `3 matches found` or `Unique target (1 match)`. |
| **`testing-api-tester`** | - Validation against `/v1/elements/check` ensuring generated selectors match exactly the targeted DOM nodes. |

---

## 3. Technical Architecture & Component Specification

```
                                  [Scraper Tab / RPA Modal]
                                             |
                                  Click "🎯 Pick Element"
                                             |
                                             v
                               [Visual Picker Modal / Drawer]
                                             |
                               +-------------+-------------+
                               |                           |
                     [Sandbox Iframe View]        [Selector Action Bar]
                               |                  - Generated Selector Input
                    Fetches cached/live HTML      - Match Counter: "1 Unique"
                    Injects picker_overlay.js     - "Add to RPA Step"
                               |                  - "Copy Selector"
                     User Hovers / Clicks
                               |
                               v
                     [Selector Generator]
                     1. Check ID
                     2. Check data-* attrs
                     3. Check class hierarchy
                     4. Check text content
                               |
                               +-------------------> postMessage to Parent:
                                                     { selector: "#login-btn",
                                                       tag: "BUTTON",
                                                       text: "Sign In",
                                                       matches: 1 }
```

### A. Selector Generation Algorithm (`picker_overlay.js`)
When an element is clicked inside the sandbox:
```javascript
function generateBestSelector(el) {
  // 1. Unique ID
  if (el.id && document.querySelectorAll('#' + CSS.escape(el.id)).length === 1) {
    return '#' + CSS.escape(el.id);
  }
  
  // 2. Data attributes
  for (const attr of ['data-testid', 'data-cy', 'data-id', 'name']) {
    if (el.hasAttribute(attr)) {
      const sel = `[${attr}="${CSS.escape(el.getAttribute(attr))}"]`;
      if (document.querySelectorAll(sel).length === 1) return sel;
    }
  }

  // 3. Role + Text for buttons/links
  if (el.tagName === 'BUTTON' || el.tagName === 'A') {
    const text = el.innerText.trim();
    if (text && text.length < 30) {
      const xpath = `//${el.tagName.toLowerCase()}[contains(normalize-space(), "${text}")]`;
      return xpath;
    }
  }

  // 4. Optimal class combination & hierarchical path
  let path = [];
  let curr = el;
  while (curr && curr.nodeType === Node.ELEMENT_NODE && curr !== document.body) {
    let selector = curr.tagName.toLowerCase();
    if (curr.className && typeof curr.className === 'string') {
      const classes = curr.className.split(/\s+/).filter(c => c && !c.includes(':') && !c.startsWith('hover:'));
      if (classes.length > 0) {
        selector += '.' + classes.slice(0, 2).map(CSS.escape).join('.');
      }
    }
    path.unshift(selector);
    const combined = path.join(' > ');
    if (document.querySelectorAll(combined).length === 1) {
      return combined;
    }
    curr = curr.parentElement;
  }

  return path.join(' > ');
}
```

### B. Sandbox HTML Proxy Endpoint (`src/ethical_crawler/api/v1/router.py`)
- Endpoint: `GET /v1/elements/sandbox?url={target_url}`
- Retrieves page HTML (from cache or live scrape).
- Injects `<base href="{target_url}">` to ensure images, fonts, and styles load properly.
- Injects `picker_overlay.js` script.
- Strips any existing breakout scripts (`window.top.location = ...`).
- Returns `HTMLResponse` with `X-Frame-Options: SAMEORIGIN`.

### C. Dashboard UI Integration (`src/ethical_crawler/api/app.py`)
- **Single Page Scraper Tab**:
  - Adds a **"🎯 Visual Element Picker"** button next to the URL input.
- **Custom RPA Step Modal (`customRpaStepModal`)**:
  - Adds a **"🎯 Pick from Page"** icon next to the Target Selector input field.
  - Clicking it opens the picker modal with the target page pre-loaded.
- **Element Picker Modal (`elementPickerModal`)**:
  - Full-screen or large dialog containing:
    - Top toolbar: Current target selector input, match count badge, "Confirm Selection" button, "Close" button.
    - Sandboxed iframe taking remaining viewport height.

---

## 4. Scenarios & Edge Cases

| Scenario | Challenge | Architectural Resolution |
| :--- | :--- | :--- |
| **1. Frame Breakout Scripts (`top.location`)** | Target page contains JS that attempts to break out of iframe and redirect user. | Proxy endpoint sanitizes scripts, removing `top.location` or `window.parent` assignments; iframe uses HTML5 `sandbox` attribute. |
| **2. Dynamic Tailwind State Classes** | Element contains 20 Tailwind classes like `hover:bg-purple-600 focus:outline-none`. | Filter strips pseudo-classes (`hover:`, `focus:`, `sm:`, `dark:`) before constructing selector to prevent fragile classes. |
| **3. Clicks Triggering Real Navigation** | User clicks a `<a href="/logout">` while trying to select it. | Overlay script calls `event.preventDefault()` and `event.stopPropagation()` on all click events in capture phase. |
| **4. Shadow DOM Elements** | Elements located inside Web Components / Shadow Roots. | Traverses `el.assignedSlot` / `getRootNode()` and falls back to path selectors with `>>>` piercing or deep XPath. |

---

## 5. Acceptance Criteria & Test Verification Matrix

- [ ] Selector generator produces unique ID selectors when ID is present.
- [ ] Selector generator prioritizes `[data-testid]` when present.
- [ ] Clicking elements inside sandbox captures tag, text, and selector without triggering external navigation.
- [ ] Selecting an element auto-populates the Custom RPA Step selector input.
- [ ] All existing regression tests continue to pass.

