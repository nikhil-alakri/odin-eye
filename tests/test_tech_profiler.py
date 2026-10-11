"""Tests for passive Technology Stack Fingerprinting and Profiler."""

import pytest
from httpx import ASGITransport, AsyncClient

from ethical_crawler.api.app import app
from ethical_crawler.extractors.tech_profiler import TechnologyProfiler


def test_framework_detection_html():
    """Verify Next.js, React, and Tailwind detection in HTML."""
    sample_html = """
    <!DOCTYPE html>
    <html>
      <head>
        <script id="__NEXT_DATA__" type="application/json">{"props":{}}</script>
        <link rel="stylesheet" href="/_next/static/css/styles.css">
      </head>
      <body data-reactroot="">
        <div class="bg-blue-500 p-4">Hello Next</div>
        <script src="https://cdn.tailwindcss.com"></script>
      </body>
    </html>
    """
    res = TechnologyProfiler.profile(html=sample_html, url="https://acme-startup.io")
    assert "Next.js" in res.technologies
    assert "React" in res.technologies
    assert "Tailwind CSS" in res.technologies
    assert "Next.js" in res.categories["frameworks"]
    assert res.domain == "acme-startup.io"


def test_cms_and_analytics_detection():
    """Verify WordPress and GA4 / PostHog detection."""
    sample_html = """
    <html>
      <head>
        <meta name="generator" content="WordPress 6.4.2" />
        <script src="https://www.googletagmanager.com/gtag/js?id=G-XYZ123"></script>
        <script src="https://us.i.posthog.com/static/array.js"></script>
      </head>
      <body>
        <div class="content"><a href="/wp-content/themes/twentytwentyfour/">Theme</a></div>
      </body>
    </html>
    """
    res = TechnologyProfiler.profile(html=sample_html)
    assert "WordPress" in res.technologies
    assert "Google Analytics 4" in res.technologies
    assert "PostHog" in res.technologies
    assert "WordPress" in res.categories["cms"]
    assert "Google Analytics 4" in res.categories["analytics"]


def test_header_infrastructure_detection():
    """Verify Cloudflare, Vercel, and CloudFront detection in response headers."""
    headers_cf = {
        "server": "cloudflare",
        "cf-ray": "8d01a912bcf-ORD",
        "content-type": "text/html",
    }
    res_cf = TechnologyProfiler.profile(headers=headers_cf)
    assert "Cloudflare" in res_cf.technologies
    assert "Cloudflare" in res_cf.categories["infrastructure"]

    headers_vercel = {
        "server": "Vercel",
        "x-vercel-id": "iad1::iad1::5m8-1728419",
    }
    res_v = TechnologyProfiler.profile(headers=headers_vercel)
    assert "Vercel" in res_v.technologies
    assert "Vercel" in res_v.categories["infrastructure"]


def test_empty_content_graceful():
    """Verify empty or non-matching content returns empty list without errors."""
    res = TechnologyProfiler.profile(headers={}, html="<html><body>Simple text</body></html>")
    assert res.technologies == []
    assert res.categories["frameworks"] == []


@pytest.mark.asyncio
async def test_tech_profile_api_endpoint():
    """Verify POST /api/v1/tech-profile endpoint."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        payload = {
            "url": "https://example-shop.com",
            "html": '<div class="shopify-features"><script src="https://cdn.shopify.com/theme.js"></script></div>',
            "headers": {"server": "cloudflare", "cf-ray": "12345678"},
        }
        res = await client.post("/api/v1/tech-profile", json=payload)
        assert res.status_code == 200
        data = res.json()
        assert "Shopify" in data["technologies"]
        assert "Cloudflare" in data["technologies"]
        assert data["domain"] == "example-shop.com"

