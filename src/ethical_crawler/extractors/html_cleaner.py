"""HTML Cleaner and Markdown Converter.

Extracts main readable content and converts semantic HTML to clean,
token-efficient Markdown for LLM ingestion. Also detects SPA JS-rendered pages.
"""

import re

import html2text
from bs4 import BeautifulSoup


class HTMLCleaner:
    """Cleans HTML and converts to clean Markdown."""

    # Tags that rarely contain main content
    STRIP_TAGS = [
        "script",
        "style",
        "noscript",
        "iframe",
        "svg",
        "canvas",
        "nav",
        "footer",
        "form",
        "button",
        "input",
        "textarea",
        "select",
    ]

    # Selectors commonly associated with ads, banners, modals, and carousel duplicate clones
    NOISE_SELECTORS = [
        ".ad",
        ".ads",
        ".advertisement",
        ".banner",
        ".cookie-banner",
        ".cookie-notice",
        ".popup",
        ".modal",
        "#sidebar",
        ".sidebar",
        ".widget",
        ".social-share",
        ".swiper-slide-duplicate",
        ".slick-cloned",
        "[aria-hidden='true'].swiper-slide",
        ".embla__slide--clone",
    ]

    def __init__(self):
        self.h2t = html2text.HTML2Text()
        self.h2t.ignore_links = False
        self.h2t.ignore_images = True
        self.h2t.ignore_emphasis = False
        self.h2t.body_width = 0  # Do not wrap lines
        self.h2t.protect_links = True
        self.h2t.unicode_snob = True

    def is_js_rendered_spa(self, html: str, soup: BeautifulSoup | None = None) -> bool:
        """Detect if page is an SPA with content rendered solely by JavaScript.

        Scenario 1: Detects empty roots, loading messages, or minimal text.
        """
        if not html:
            return True

        if soup is None:
            soup = BeautifulSoup(html, "html.parser")

        # Check for typical SPA containers with no child text
        for container_id in ("root", "app", "__next", "__nuxt"):
            elem = soup.find(id=container_id)
            if elem and len(elem.get_text(strip=True)) < 50:
                return True

        # Check for noscript messages
        noscript_tags = soup.find_all("noscript")
        for tag in noscript_tags:
            text = tag.get_text().lower()
            if "enable javascript" in text or "requires javascript" in text:
                # If body text outside noscript is very short
                body_text = soup.body.get_text(strip=True) if soup.body else ""
                if len(body_text) < 150:
                    return True

        # Overall text density check
        body = soup.body
        if body:
            text = body.get_text(strip=True)
            if len(text) < 60 and (
                "react" in html.lower() or "webpack" in html.lower() or "vite" in html.lower()
            ):
                return True

        return False

    def clean_and_convert(self, html: str) -> tuple[str, str | None]:
        """Strip noise tags and convert HTML to markdown.

        Returns (cleaned_markdown, page_title).
        """
        if not html:
            return "", None

        soup = BeautifulSoup(html, "html.parser")

        # Extract title
        title = None
        title_tag = soup.find("title")
        if title_tag:
            title = title_tag.get_text(strip=True)

        # Preserve semantic SVGs (checkmarks, crosses, status icons) before stripping generic SVGs
        for svg in soup.find_all("svg"):
            cls_val = svg.get("class", [])
            cls_str = " ".join(cls_val) if isinstance(cls_val, list) else str(cls_val)
            aria = svg.get("aria-label") or svg.get("title") or ""
            svg_text = f"{cls_str} {aria}".lower()

            if any(
                k in svg_text for k in ("check", "tick", "lucide-check", "text-emerald", "success")
            ):
                svg.replace_with(soup.new_string(" ✓ "))
            elif any(k in svg_text for k in ("cross", "close", "lucide-x", "text-red", "cancel")):
                svg.replace_with(soup.new_string(" ✗ "))
            elif any(k in svg_text for k in ("minus", "dash")):
                svg.replace_with(soup.new_string(" — "))
            elif aria:
                svg.replace_with(soup.new_string(f" {aria} "))

        # Remove noisy tags
        for tag_name in self.STRIP_TAGS:
            for s in soup.find_all(tag_name):
                s.decompose()

        # Remove noise classes and carousel duplicates
        for selector in self.NOISE_SELECTORS:
            for el in soup.select(selector):
                el.decompose()

        # Insert space between adjacent inline tags so text does not run together
        for tag in soup.find_all(["span", "a", "strong", "em", "b", "i"]):
            if tag.next_sibling and getattr(tag.next_sibling, "name", None):
                tag.insert_after(" ")

        # Find main content container if present
        main_content = (
            soup.find("main")
            or soup.find("article")
            or soup.find("div", role="main")
            or soup.find(id=re.compile(r"content|main", re.I))
            or soup.find(class_=re.compile(r"content|post|article", re.I))
            or soup.body
            or soup
        )

        html_str = str(main_content)
        markdown = self.h2t.handle(html_str)

        # Normalize markdown whitespace
        markdown = re.sub(r"\n{3,}", "\n\n", markdown).strip()

        # Fallback for JS-rendered SPAs or sparse pages: extract from metadata
        if not markdown and title:
            desc_tag = (
                soup.find("meta", attrs={"name": re.compile(r"description", re.I)})
                or soup.find("meta", attrs={"property": re.compile(r"og:description", re.I)})
                or soup.find("meta", attrs={"name": re.compile(r"twitter:description", re.I)})
            )
            desc_text = desc_tag.get("content", "").strip() if desc_tag else ""
            if desc_text:
                markdown = f"# {title}\n\n{desc_text}"
            else:
                markdown = f"# {title}"

        return markdown, title


# Global cleaner instance
_global_cleaner: HTMLCleaner | None = None


def get_html_cleaner() -> HTMLCleaner:
    """Get or instantiate global HTMLCleaner."""
    global _global_cleaner
    if _global_cleaner is None:
        _global_cleaner = HTMLCleaner()
    return _global_cleaner
