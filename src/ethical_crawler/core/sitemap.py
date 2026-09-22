"""Ethical Rule #4: Sitemap Discovery & Recursive XML/Gzip Parser.

Enables fast, structured URL discovery directly from sitemap.xml and sitemap indexes,
significantly reducing server overhead compared to brute-force crawling.
"""

import gzip
import logging
import time
from urllib.parse import urlparse

import defusedxml.ElementTree as ET  # noqa: N817
import httpx

from ethical_crawler.config import get_settings
from ethical_crawler.core.headers import get_default_headers
from ethical_crawler.types import SitemapResult, SitemapURL

logger = logging.getLogger("ethical_crawler.sitemap")


class SitemapParser:
    """Parser for XML sitemaps and sitemap indexes."""

    XML_NAMESPACES = {
        "": "http://www.sitemaps.org/schemas/sitemap/0.9",
        "ns": "http://www.sitemaps.org/schemas/sitemap/0.9",
        "image": "http://www.google.com/schemas/sitemap-image/1.1",
        "news": "http://www.google.com/schemas/sitemap-news/0.9",
    }

    def __init__(self, max_nested_depth: int = 2):
        self.max_nested_depth = max_nested_depth

    @staticmethod
    def get_default_sitemap_url(base_url: str) -> str:
        """Derive standard sitemap.xml from any site URL."""
        parsed = urlparse(base_url)
        scheme = parsed.scheme or "https"
        return f"{scheme}://{parsed.netloc}/sitemap.xml"

    async def fetch_and_parse(
        self,
        sitemap_url: str,
        client: httpx.AsyncClient | None = None,
        depth: int = 0,
    ) -> SitemapResult:
        """Fetch and recursively parse an XML or gzipped sitemap."""
        start_time = time.time()
        should_close = False

        if client is None:
            settings = get_settings()
            headers = get_default_headers(user_agent=settings.user_agent)
            client = httpx.AsyncClient(headers=headers, timeout=15.0, follow_redirects=True)
            should_close = True

        urls: list[SitemapURL] = []
        nested: list[str] = []
        error = None

        try:
            resp = await client.get(sitemap_url)
            if resp.status_code != 200:
                return SitemapResult(
                    sitemap_url=sitemap_url,
                    total_urls=0,
                    elapsed_seconds=time.time() - start_time,
                    error=f"HTTP {resp.status_code}",
                )

            content = resp.content

            # Scenario 3: Handle gzipped sitemaps (.xml.gz or gzip magic bytes 0x1f, 0x8b)
            if sitemap_url.endswith(".gz") or content[:2] == b"\x1f\x8b":
                try:
                    content = gzip.decompress(content)
                except Exception as gz_err:
                    logger.warning("Failed to decompress gzip sitemap %s: %s", sitemap_url, gz_err)

            root = ET.fromstring(content)
            tag = root.tag.split("}")[-1]  # Strip namespace

            if tag == "sitemapindex":
                # Multi-tier sitemap index
                for elem in root.findall(".//{http://www.sitemaps.org/schemas/sitemap/0.9}sitemap"):
                    loc_elem = elem.find("{http://www.sitemaps.org/schemas/sitemap/0.9}loc")
                    if loc_elem is not None and loc_elem.text:
                        sub_url = loc_elem.text.strip()
                        nested.append(sub_url)
                # Also try without namespace
                if not nested:
                    for elem in root.findall(".//sitemap"):
                        loc_elem = elem.find("loc")
                        if loc_elem is not None and loc_elem.text:
                            nested.append(loc_elem.text.strip())

                # Recursively parse nested sitemaps if depth allows
                if depth < self.max_nested_depth:
                    for sub_sitemap in nested[:10]:  # Limit top 10 sub-sitemaps
                        sub_result = await self.fetch_and_parse(sub_sitemap, client, depth + 1)
                        urls.extend(sub_result.urls)

            elif tag == "urlset":
                # Standard URL set
                # Try with namespace
                elems = root.findall(".//{http://www.sitemaps.org/schemas/sitemap/0.9}url")
                if not elems:
                    elems = root.findall(".//url")

                for elem in elems:
                    loc = elem.findtext(
                        "{http://www.sitemaps.org/schemas/sitemap/0.9}loc"
                    ) or elem.findtext("loc")
                    if loc:
                        lastmod = elem.findtext(
                            "{http://www.sitemaps.org/schemas/sitemap/0.9}lastmod"
                        ) or elem.findtext("lastmod")
                        changefreq = elem.findtext(
                            "{http://www.sitemaps.org/schemas/sitemap/0.9}changefreq"
                        ) or elem.findtext("changefreq")
                        priority_str = elem.findtext(
                            "{http://www.sitemaps.org/schemas/sitemap/0.9}priority"
                        ) or elem.findtext("priority")
                        priority = float(priority_str) if priority_str else None

                        urls.append(
                            SitemapURL(
                                loc=loc.strip(),
                                lastmod=lastmod.strip() if lastmod else None,
                                changefreq=changefreq.strip() if changefreq else None,
                                priority=priority,
                            )
                        )

        except ET.ParseError as pe:
            logger.warning("XML parse error parsing sitemap %s: %s", sitemap_url, pe)
            error = f"XML parse error: {pe}"
        except Exception as exc:
            logger.warning("Error fetching/parsing sitemap %s: %s", sitemap_url, exc)
            error = str(exc)
        finally:
            if should_close:
                await client.aclose()

        elapsed = time.time() - start_time
        return SitemapResult(
            sitemap_url=sitemap_url,
            total_urls=len(urls),
            urls=urls,
            nested_sitemaps=nested,
            elapsed_seconds=elapsed,
            error=error,
        )


# Global singleton sitemap parser
_global_sitemap_parser: SitemapParser | None = None


def get_sitemap_parser() -> SitemapParser:
    """Get or instantiate global SitemapParser."""
    global _global_sitemap_parser
    if _global_sitemap_parser is None:
        _global_sitemap_parser = SitemapParser()
    return _global_sitemap_parser
