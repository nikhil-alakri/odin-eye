"""Passive Technology Stack Fingerprinting and Profiler.

Non-intrusively analyzes HTTP response headers, HTML DOM structures, script bundles,
and metadata patterns to identify frameworks, CMSs, analytics tools, and hosting/CDNs.
Adheres strictly to ethical scraping principles by inspecting existing response data.
"""

from __future__ import annotations

import logging
import re
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class TechMatchedItem(BaseModel):
    """Details on an individual detected technology."""

    name: str
    category: str  # frameworks | cms | analytics | infrastructure
    confidence: str = "high"  # high | medium
    matched_via: str  # header:name | html:script | html:meta | html:content


class TechProfileResult(BaseModel):
    """Complete technology profiling summary for a page or domain."""

    url: str = ""
    domain: str = ""
    categories: dict[str, list[str]] = Field(
        default_factory=lambda: {
            "frameworks": [],
            "cms": [],
            "analytics": [],
            "infrastructure": [],
        }
    )
    technologies: list[str] = Field(default_factory=list)
    details: list[TechMatchedItem] = Field(default_factory=list)


# Signature catalog for passive detection
TECH_SIGNATURES: dict[str, dict[str, Any]] = {
    # -------------------------------------------------------------------------
    # FRAMEWORKS & LIBRARIES
    # -------------------------------------------------------------------------
    "Next.js": {
        "category": "frameworks",
        "headers": {"x-powered-by": r"Next\.js"},
        "html_regex": [r"__NEXT_DATA__", r"/_next/static/", r"<script[^>]*src=[\"'][^\"']*/_next/"],
    },
    "React": {
        "category": "frameworks",
        "html_regex": [
            r"data-reactroot",
            r"/static/js/main\.[a-f0-9]+\.js",
            r"react\.production\.min\.js",
            r"_reactInternalInstance",
            r"__reactFiber",
        ],
    },
    "Vue.js": {
        "category": "frameworks",
        "html_regex": [
            r"data-v-[a-f0-9]{6,10}",
            r"__vue__",
            r"/vue(?:\.runtime)?(?:\.global)?(?:\.min)?\.js",
            r"<div[^>]+v-data",
        ],
    },
    "Nuxt.js": {
        "category": "frameworks",
        "headers": {"x-powered-by": r"Nuxt"},
        "html_regex": [r"__NUXT__", r"/_nuxt/"],
    },
    "Svelte": {
        "category": "frameworks",
        "html_regex": [r"class=\"svelte-[a-z0-9]+\"", r"__svelte__"],
    },
    "Angular": {
        "category": "frameworks",
        "html_regex": [r"ng-version=", r"<app-root\b", r"ng-controller=", r"angular(?:\.min)?\.js"],
    },
    "Remix": {
        "category": "frameworks",
        "html_regex": [r"window\.__remixContext", r"/_remix/"],
    },
    "Astro": {
        "category": "frameworks",
        "html_regex": [r"<astro-island\b", r"class=\"astro-[a-z0-9]+\""],
    },
    "Gatsby": {
        "category": "frameworks",
        "html_regex": [r"id=\"___gatsby\"", r"gatsby-portal"],
    },
    "Tailwind CSS": {
        "category": "frameworks",
        "html_regex": [r"cdn\.tailwindcss\.com", r"tailwind(?:\.min)?\.css"],
    },
    "Bootstrap": {
        "category": "frameworks",
        "html_regex": [r"bootstrap(?:\.bundle)?(?:\.min)?\.(?:css|js)", r"<link[^>]+href=[\"'][^\"']*bootstrap"],
    },

    # -------------------------------------------------------------------------
    # CONTENT MANAGEMENT SYSTEMS & E-COMMERCE
    # -------------------------------------------------------------------------
    "WordPress": {
        "category": "cms",
        "headers": {"x-pingback": r"xmlrpc\.php"},
        "html_regex": [
            r"/wp-content/(?:themes|plugins)/",
            r"/wp-includes/",
            r"<meta\s+name=[\"']generator[\"']\s+content=[\"']WordPress",
        ],
    },
    "Shopify": {
        "category": "cms",
        "html_regex": [
            r"cdn\.shopify\.com",
            r"Shopify\.theme",
            r"shopify-features",
            r"<link[^>]+href=[\"'][^\"']*cdn\.shopify\.com",
        ],
    },
    "Webflow": {
        "category": "cms",
        "html_regex": [
            r"<html[^>]+data-wf-page",
            r"webflow(?:\.bundle)?(?:\.min)?\.js",
            r"<meta\s+content=[\"']Webflow[\"']\s+name=[\"']generator[\"']",
        ],
    },
    "Ghost": {
        "category": "cms",
        "html_regex": [
            r"<meta\s+name=[\"']generator[\"']\s+content=[\"']Ghost",
            r"ghost-portal",
        ],
    },
    "Squarespace": {
        "category": "cms",
        "html_regex": [
            r"static1\.squarespace\.com",
            r"squarespace\.com",
            r"<!-- This is Squarespace. -->",
        ],
    },
    "Wix": {
        "category": "cms",
        "html_regex": [
            r"wix\.com",
            r"parastorage\.com",
            r"_wixBlobUrl",
        ],
    },
    "Magento": {
        "category": "cms",
        "html_regex": [
            r"mage/cookies\.js",
            r"skin/frontend/",
            r"Magento_Theme",
        ],
    },
    "Drupal": {
        "category": "cms",
        "headers": {"x-generator": r"Drupal"},
        "html_regex": [
            r"<meta\s+name=[\"']Generator[\"']\s+content=[\"']Drupal",
            r"Drupal\.settings",
            r"/sites/default/files/",
        ],
    },

    # -------------------------------------------------------------------------
    # ANALYTICS & MARKETING INTELLIGENCE
    # -------------------------------------------------------------------------
    "Google Analytics 4": {
        "category": "analytics",
        "html_regex": [
            r"googletagmanager\.com/gtag/js\?id=G-",
            r"gtag\([\"']config[\"'],\s*[\"']G-",
            r"google-analytics\.com/analytics\.js",
        ],
    },
    "PostHog": {
        "category": "analytics",
        "html_regex": [
            r"posthog\.com",
            r"posthog\.init\(",
            r"posthog(?:\.min)?\.js",
        ],
    },
    "Segment": {
        "category": "analytics",
        "html_regex": [
            r"cdn\.segment\.com/analytics\.js",
            r"analytics\.load\(",
        ],
    },
    "Mixpanel": {
        "category": "analytics",
        "html_regex": [
            r"cdn\.mxpnl\.com",
            r"mixpanel\.init\(",
        ],
    },
    "Hotjar": {
        "category": "analytics",
        "html_regex": [
            r"static\.hotjar\.com/c/hotjar-",
            r"_hjSettings",
        ],
    },
    "Intercom": {
        "category": "analytics",
        "html_regex": [
            r"widget\.intercom\.io",
            r"window\.Intercom\(",
        ],
    },
    "HubSpot": {
        "category": "analytics",
        "html_regex": [
            r"js\.hs-scripts\.com",
            r"js\.hsforms\.net",
        ],
    },
    "Plausible Analytics": {
        "category": "analytics",
        "html_regex": [
            r"plausible\.io/js/script\.js",
        ],
    },

    # -------------------------------------------------------------------------
    # INFRASTRUCTURE, CDNS & SERVERS
    # -------------------------------------------------------------------------
    "Cloudflare": {
        "category": "infrastructure",
        "headers": {
            "cf-ray": r".+",
            "server": r"cloudflare",
            "cf-cache-status": r".+",
        },
    },
    "Vercel": {
        "category": "infrastructure",
        "headers": {
            "x-vercel-id": r".+",
            "server": r"Vercel",
        },
    },
    "AWS CloudFront": {
        "category": "infrastructure",
        "headers": {
            "x-amz-cf-id": r".+",
            "x-amz-cf-pop": r".+",
            "via": r"CloudFront",
        },
    },
    "Fastly": {
        "category": "infrastructure",
        "headers": {
            "fastly-debug-digest": r".+",
            "x-fastly-request-id": r".+",
        },
    },
    "Netlify": {
        "category": "infrastructure",
        "headers": {
            "x-nf-request-id": r".+",
            "server": r"Netlify",
        },
    },
    "Nginx": {
        "category": "infrastructure",
        "headers": {
            "server": r"nginx",
        },
    },
    "Apache": {
        "category": "infrastructure",
        "headers": {
            "server": r"Apache",
        },
    },
}


class TechnologyProfiler:
    """Passive fingerprinting engine for web technologies."""

    @classmethod
    def profile(
        cls,
        headers: dict[str, str] | None = None,
        html: str | None = None,
        url: str | None = None,
    ) -> TechProfileResult:
        """Inspect headers and HTML against TECH_SIGNATURES."""
        domain = ""
        if url:
            parsed = urlparse(url)
            domain = parsed.netloc.lower()

        clean_headers: dict[str, str] = {}
        if headers:
            for k, v in headers.items():
                clean_headers[str(k).lower()] = str(v)

        html_text = html or ""

        matched_details: list[TechMatchedItem] = []
        categories: dict[str, set[str]] = {
            "frameworks": set(),
            "cms": set(),
            "analytics": set(),
            "infrastructure": set(),
        }

        for tech_name, sig in TECH_SIGNATURES.items():
            category = sig.get("category", "frameworks")
            matched = False
            matched_via = ""

            # 1. Check HTTP Headers
            sig_headers = sig.get("headers", {})
            for h_key, pattern in sig_headers.items():
                val = clean_headers.get(h_key.lower())
                if val and re.search(pattern, val, re.IGNORECASE):
                    matched = True
                    matched_via = f"header:{h_key}"
                    break

            # 2. Check HTML Regex if not matched yet
            if not matched and html_text:
                for pat in sig.get("html_regex", []):
                    if re.search(pat, html_text, re.IGNORECASE):
                        matched = True
                        matched_via = "html:pattern"
                        break

            if matched:
                categories[category].add(tech_name)
                matched_details.append(
                    TechMatchedItem(
                        name=tech_name,
                        category=category,
                        confidence="high",
                        matched_via=matched_via,
                    )
                )

        # Build output structure
        categories_list = {k: sorted(list(v)) for k, v in categories.items()}
        all_techs = sorted(list({item.name for item in matched_details}))

        return TechProfileResult(
            url=url or "",
            domain=domain,
            categories=categories_list,
            technologies=all_techs,
            details=matched_details,
        )

    @classmethod
    async def profile_url(cls, url: str, user_agent: str | None = None) -> TechProfileResult:
        """Fetch and passively profile a live URL."""
        import httpx

        ua = user_agent or "EthicalWebCrawler/0.1.0 (+https://example.com/bot)"
        headers: dict[str, str] = {}
        html = ""

        try:
            async with httpx.AsyncClient(
                headers={"User-Agent": ua},
                timeout=12.0,
                follow_redirects=True,
            ) as client:
                resp = await client.get(url)
                headers = dict(resp.headers)
                html = resp.text
        except Exception as exc:
            logger.warning("Failed to fetch %s for tech profiling: %s", url, exc)

        return cls.profile(headers=headers, html=html, url=url)
