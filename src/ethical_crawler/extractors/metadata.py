"""Metadata and structured schema (JSON-LD, OpenGraph, Twitter) extractor."""

import json
import logging

from bs4 import BeautifulSoup

from ethical_crawler.types import PageMetadata

logger = logging.getLogger("ethical_crawler.metadata")


class MetadataExtractor:
    """Extracts meta tags, OpenGraph tags, and JSON-LD structured schemas from HTML."""

    @staticmethod
    def extract(html: str) -> PageMetadata:
        """Parse HTML string and extract metadata."""
        if not html:
            return PageMetadata()

        soup = BeautifulSoup(html, "html.parser")
        meta = PageMetadata()

        # Title
        title_tag = soup.find("title")
        if title_tag:
            meta.title = title_tag.get_text(strip=True)

        # Standard Meta Tags
        desc_elem = soup.find("meta", attrs={"name": "description"}) or soup.find(
            "meta", attrs={"property": "description"}
        )
        if desc_elem and desc_elem.get("content"):
            meta.description = desc_elem["content"].strip()

        author_elem = soup.find("meta", attrs={"name": "author"})
        if author_elem and author_elem.get("content"):
            meta.author = author_elem["content"].strip()

        keywords_elem = soup.find("meta", attrs={"name": "keywords"})
        if keywords_elem and keywords_elem.get("content"):
            meta.keywords = [k.strip() for k in keywords_elem["content"].split(",") if k.strip()]

        canonical_elem = soup.find("link", attrs={"rel": "canonical"})
        if canonical_elem and canonical_elem.get("href"):
            meta.canonical = canonical_elem["href"].strip()

        # OpenGraph Tags
        og_title = soup.find("meta", property="og:title")
        if og_title and og_title.get("content"):
            meta.og_title = og_title["content"].strip()

        og_desc = soup.find("meta", property="og:description")
        if og_desc and og_desc.get("content"):
            meta.og_description = og_desc["content"].strip()

        og_img = soup.find("meta", property="og:image")
        if og_img and og_img.get("content"):
            meta.og_image = og_img["content"].strip()

        og_type = soup.find("meta", property="og:type")
        if og_type and og_type.get("content"):
            meta.og_type = og_type["content"].strip()

        # Twitter Card Tags
        tw_card = soup.find("meta", attrs={"name": "twitter:card"})
        if tw_card and tw_card.get("content"):
            meta.twitter_card = tw_card["content"].strip()

        # JSON-LD Structured Data
        for script in soup.find_all("script", attrs={"type": "application/ld+json"}):
            try:
                content = script.string
                if content:
                    data = json.loads(content)
                    if isinstance(data, list):
                        meta.json_ld.extend(data)
                    elif isinstance(data, dict):
                        meta.json_ld.append(data)
            except Exception as e:
                logger.debug("Failed to parse JSON-LD script: %s", e)

        return meta
