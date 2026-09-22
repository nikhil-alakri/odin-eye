"""Link extractor, URL normalizer, and spider-trap preventer."""

from urllib.parse import parse_qs, urlencode, urljoin, urlparse, urlunparse

from bs4 import BeautifulSoup

# Tracking query parameters commonly generating infinite URL permutations
TRACKING_PARAMS = {
    "utm_source",
    "utm_medium",
    "utm_campaign",
    "utm_term",
    "utm_content",
    "gclid",
    "fbclid",
    "ref",
    "source",
    "sessionid",
    "phpsessid",
    "jsessionid",
}

# Non-crawlable URL schemes
IGNORED_SCHEMES = {"mailto", "tel", "javascript", "data", "file", "ftp"}

# Common binary file extensions to avoid downloading as web pages
BINARY_EXTENSIONS = {
    ".pdf",
    ".zip",
    ".tar",
    ".gz",
    ".7z",
    ".iso",
    ".dmg",
    ".exe",
    ".bin",
    ".mp4",
    ".mp3",
    ".avi",
    ".mov",
    ".mkv",
    ".jpg",
    ".jpeg",
    ".png",
    ".gif",
    ".webp",
    ".svg",
    ".ico",
    ".woff",
    ".woff2",
    ".ttf",
}


class LinkExtractor:
    """Extracts and normalizes links from HTML pages."""

    @staticmethod
    def normalize_url(url: str) -> str:
        """Normalize URL: strip tracking params, remove fragments, standardize format.

        Scenario 5: Prevents spider traps and duplicate crawl visits.
        """
        parsed = urlparse(url)
        scheme = parsed.scheme.lower()
        netloc = parsed.netloc.lower()

        # Remove port 80/443 if standard
        if netloc.endswith(":80") and scheme == "http":
            netloc = netloc[:-3]
        elif netloc.endswith(":443") and scheme == "https":
            netloc = netloc[:-4]

        # Path normalization: strip trailing slash if not root
        path = parsed.path or "/"
        if len(path) > 1 and path.endswith("/"):
            path = path[:-1]

        # Filter out tracking parameters
        clean_query = ""
        if parsed.query:
            query_dict = parse_qs(parsed.query, keep_blank_values=False)
            filtered = {k: v for k, v in query_dict.items() if k.lower() not in TRACKING_PARAMS}
            if filtered:
                clean_query = urlencode(filtered, doseq=True)

        return urlunparse((scheme, netloc, path, parsed.params, clean_query, ""))

    @classmethod
    def is_binary_resource(cls, url: str) -> bool:
        """Check if URL points directly to a binary file extension (Scenario 6)."""
        parsed = urlparse(url)
        path = parsed.path.lower()
        return any(path.endswith(ext) for ext in BINARY_EXTENSIONS)

    @classmethod
    def extract_links(cls, html: str, base_url: str) -> tuple[list[str], list[str]]:
        """Extract internal and external links from HTML.

        Returns (internal_links, external_links).
        """
        if not html:
            return [], []

        soup = BeautifulSoup(html, "html.parser")
        base_domain = urlparse(base_url).netloc.lower()

        internal_links: set[str] = set()
        external_links: set[str] = set()

        for a_tag in soup.find_all("a", href=True):
            raw_href = a_tag["href"].strip()
            if not raw_href or raw_href.startswith("#"):
                continue

            # Check ignored schemes
            parsed_raw = urlparse(raw_href)
            if parsed_raw.scheme.lower() in IGNORED_SCHEMES:
                continue

            # Resolve relative URLs
            resolved = urljoin(base_url, raw_href)
            parsed = urlparse(resolved)

            if parsed.scheme.lower() not in ("http", "https"):
                continue

            if cls.is_binary_resource(resolved):
                continue

            normalized = cls.normalize_url(resolved)
            target_domain = parsed.netloc.lower()

            # Internal if same domain or subdomain
            if target_domain == base_domain or target_domain.endswith(f".{base_domain}"):
                internal_links.add(normalized)
            else:
                external_links.add(normalized)

        return sorted(internal_links), sorted(external_links)
