"""Interactive Point-and-Click Element Picker for visual DOM element selection."""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse
from bs4 import BeautifulSoup, Tag


# Embedded client-side script injected into sandboxed iframe preview
PICKER_INJECTED_JS = """
<script id="__ethic_element_picker_script__">
(function() {
  if (window.__ethic_picker_installed) return;
  window.__ethic_picker_installed = true;

  let hoveredEl = null;
  let selectedEl = null;

  // Floating inspection badge
  const badge = document.createElement('div');
  badge.id = '__ethic_picker_badge__';
  badge.style.cssText = 'position:fixed;z-index:99999999;background:#1e1b4b;color:#f8fafc;padding:3px 8px;border-radius:4px;font-family:monospace;font-size:11px;font-weight:600;pointer-events:none;display:none;border:1px solid #818cf8;box-shadow:0 4px 12px rgba(0,0,0,0.3);';
  document.body.appendChild(badge);

  function getBestSelector(el) {
    if (!el || el.nodeType !== Node.ELEMENT_NODE) return '';

    // 1. Unique ID
    if (el.id && !/\\d{4,}/.test(el.id)) {
      try {
        const idSel = '#' + CSS.escape(el.id);
        if (document.querySelectorAll(idSel).length === 1) return idSel;
      } catch (e) {}
    }

    // 2. Data Attributes
    for (const attr of ['data-testid', 'data-cy', 'data-qa', 'name', 'aria-label']) {
      if (el.hasAttribute(attr)) {
        try {
          const attrVal = el.getAttribute(attr);
          const sel = `[${attr}="${CSS.escape(attrVal)}"]`;
          if (document.querySelectorAll(sel).length === 1) return sel;
        } catch (e) {}
      }
    }

    // 3. Unique role + tag
    if (el.getAttribute('role')) {
      try {
        const roleSel = `${el.tagName.toLowerCase()}[role="${CSS.escape(el.getAttribute('role'))}"]`;
        if (document.querySelectorAll(roleSel).length === 1) return roleSel;
      } catch (e) {}
    }

    // 4. Classes combination (filtering out transient / tailwind hover states)
    if (el.className && typeof el.className === 'string') {
      const classes = el.className.split(/\\s+/).filter(c => 
        c && !c.includes(':') && !c.startsWith('hover:') && !c.startsWith('focus:') && !c.startsWith('active:') && !c.startsWith('dark:')
      );
      if (classes.length > 0) {
        try {
          const classSel = el.tagName.toLowerCase() + '.' + classes.slice(0, 3).map(CSS.escape).join('.');
          if (document.querySelectorAll(classSel).length === 1) return classSel;
        } catch (e) {}
      }
    }

    // 5. Shortest hierarchical path
    let path = [];
    let curr = el;
    while (curr && curr.nodeType === Node.ELEMENT_NODE && curr !== document.body && curr !== document.documentElement) {
      let sel = curr.tagName.toLowerCase();
      if (curr.id && !/\\d{4,}/.test(curr.id)) {
        try {
          sel = '#' + CSS.escape(curr.id);
          path.unshift(sel);
          break;
        } catch (e) {}
      }
      if (curr.className && typeof curr.className === 'string') {
        const cl = curr.className.split(/\\s+/).filter(c => c && !c.includes(':') && !c.startsWith('hover:'));
        if (cl.length > 0) {
          sel += '.' + CSS.escape(cl[0]);
        }
      }
      path.unshift(sel);
      try {
        const candidate = path.join(' > ');
        if (document.querySelectorAll(candidate).length === 1) return candidate;
      } catch (e) {}
      curr = curr.parentElement;
    }

    // 6. Fallback path
    return path.join(' > ') || el.tagName.toLowerCase();
  }

  // Hover effect
  document.addEventListener('mouseover', function(e) {
    if (e.target === badge || e.target.id === '__ethic_picker_badge__') return;
    if (hoveredEl && hoveredEl !== selectedEl) {
      hoveredEl.style.outline = '';
      hoveredEl.style.outlineOffset = '';
    }
    hoveredEl = e.target;
    if (hoveredEl !== selectedEl) {
      hoveredEl.style.outline = '2px dashed #9333ea';
      hoveredEl.style.outlineOffset = '2px';
      hoveredEl.style.cursor = 'crosshair';
    }

    // Update floating badge
    const rect = hoveredEl.getBoundingClientRect();
    const tag = hoveredEl.tagName.toLowerCase();
    const idStr = hoveredEl.id ? '#' + hoveredEl.id : '';
    badge.innerText = `<${tag}${idStr}>`;
    badge.style.display = 'block';
    badge.style.top = Math.max(4, rect.top - 24) + 'px';
    badge.style.left = Math.max(4, rect.left) + 'px';
  }, true);

  // Click capture
  document.addEventListener('click', function(e) {
    // Intercept clicks to prevent real navigation
    e.preventDefault();
    e.stopPropagation();

    if (selectedEl) {
      selectedEl.style.outline = '';
      selectedEl.style.backgroundColor = '';
    }
    selectedEl = e.target;
    selectedEl.style.outline = '3px solid #7c3aed';
    selectedEl.style.outlineOffset = '2px';
    selectedEl.style.backgroundColor = 'rgba(124, 58, 237, 0.12)';

    const selector = getBestSelector(selectedEl);
    let matchCount = 1;
    try {
      matchCount = document.querySelectorAll(selector).length;
    } catch (err) {}

    const payload = {
      type: 'ELEMENT_PICKED',
      selector: selector,
      tagName: selectedEl.tagName.toUpperCase(),
      innerText: (selectedEl.innerText || selectedEl.value || '').trim().slice(0, 60),
      matchCount: matchCount,
      id: selectedEl.id || '',
      className: typeof selectedEl.className === 'string' ? selectedEl.className : '',
    };

    window.parent.postMessage(payload, '*');
  }, true);

})();
</script>
"""


class ElementPicker:
    """Helper for sandboxing target page HTML and generating optimal CSS selectors."""

    # Patterns that attempt frame-breakout
    BREAKOUT_PATTERNS = [
        re.compile(r"\b(?:window\.)?(?:top|parent)\.location\b", re.IGNORECASE),
        re.compile(r"\b(?:window\.)?frameElement\b", re.IGNORECASE),
    ]

    @classmethod
    def sanitize_and_prepare_html(cls, html: str, target_url: str) -> str:
        """Inject base href, neutralize frame breakouts, and inject interactive picker script."""
        if not html:
            return "<html><body><p>No content available to preview.</p></body></html>"

        # Neutralize frame-breakout scripts
        sanitized = html
        for pattern in cls.BREAKOUT_PATTERNS:
            sanitized = pattern.sub("/* breakout muted */ void(0)", sanitized)

        # Ensure <base href="..."> is present for relative assets
        base_tag = f'<base href="{target_url}">'
        if "<head>" in sanitized.lower():
            head_idx = sanitized.lower().find("<head>") + 6
            sanitized = sanitized[:head_idx] + "\n" + base_tag + "\n" + sanitized[head_idx:]
        else:
            sanitized = f"<head>{base_tag}</head>\n" + sanitized

        # Inject picker overlay script before </body>
        if "</body>" in sanitized.lower():
            body_idx = sanitized.lower().rfind("</body>")
            sanitized = sanitized[:body_idx] + "\n" + PICKER_INJECTED_JS + "\n" + sanitized[body_idx:]
        else:
            sanitized += "\n" + PICKER_INJECTED_JS

        return sanitized

    @classmethod
    def generate_selector_from_bs4(cls, element: Tag) -> str:
        """Server-side heuristic selector generator for a BeautifulSoup element."""
        if not element or not isinstance(element, Tag):
            return ""

        # Check unique ID
        if element.get("id"):
            clean_id = element["id"].strip()
            if not re.search(r"\d{4,}", clean_id):
                return f"#{clean_id}"

        # Check test attributes
        for attr in ["data-testid", "data-cy", "name"]:
            if element.get(attr):
                return f'[{attr}="{element[attr]}"]'

        # Check class
        classes = element.get("class", [])
        if classes:
            filtered = [c for c in classes if not any(c.startswith(p) for p in ["hover:", "focus:", "dark:"])]
            if filtered:
                return f"{element.name}.{'.'.join(filtered[:2])}"

        return element.name

