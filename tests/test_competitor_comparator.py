"""Tests for Multi-Domain Competitor Benchmarking and Comparison Engine."""

import io
import pytest
from httpx import ASGITransport, AsyncClient

from ethical_crawler.api.app import app
from ethical_crawler.knowledge.competitor_comparator import (
    CompetitorComparator,
    CompetitorComparisonResult,
    CompetitorDomainProfile,
)


def test_markdown_table_builder():
    """Verify side-by-side Markdown comparison table formatting."""
    comparator = CompetitorComparator()
    profiles = {
        "stripe.com": CompetitorDomainProfile(
            domain="stripe.com",
            page_count=20,
            total_words=12500,
            technologies=["React", "Next.js", "Cloudflare"],
            tech_categories={
                "frameworks": ["React", "Next.js"],
                "infrastructure": ["Cloudflare"],
            },
            value_proposition="Financial Infrastructure for the Internet",
            pricing_model="2.9% + 30¢",
            key_features=["Payments API", "Billing Engine"],
        ),
        "paddle.com": CompetitorDomainProfile(
            domain="paddle.com",
            page_count=15,
            total_words=9800,
            technologies=["Vue.js", "AWS CloudFront"],
            tech_categories={
                "frameworks": ["Vue.js"],
                "infrastructure": ["AWS CloudFront"],
            },
            value_proposition="Complete Merchant of Record for SaaS",
            pricing_model="5% + 50¢",
            key_features=["Global Tax Handling", "Subscription Billing"],
        ),
    }

    table_md = comparator._build_markdown_table(profiles)
    assert "| Criteria | stripe.com | paddle.com |" in table_md
    assert "Financial Infrastructure for the Internet" in table_md
    assert "Complete Merchant of Record for SaaS" in table_md
    assert "Cloudflare" in table_md
    assert "AWS CloudFront" in table_md


@pytest.mark.asyncio
async def test_compare_domains_validation():
    """Verify ValueError when fewer than 2 domains provided."""
    comparator = CompetitorComparator()
    with pytest.raises(ValueError, match="At least 2 unique competitor domains"):
        await comparator.compare_domains(["stripe.com"])


@pytest.mark.asyncio
async def test_compare_domains_mock_data(monkeypatch):
    """Verify complete comparison run with mock domain data."""
    comparator = CompetitorComparator()

    def mock_get_raw_data(domain):
        return {
            "domain": domain,
            "documents": [
                f"Welcome to {domain}. We offer AI solutions for enterprise automation. Pricing: $49/mo."
            ],
            "metadatas": [
                {
                    "url": f"https://{domain}/",
                    "title": f"{domain.capitalize()} - Official AI Platform",
                    "strategy": "http",
                }
            ],
        }

    monkeypatch.setattr(comparator, "get_domain_raw_data", mock_get_raw_data)

    res = await comparator.compare_domains(["alpha.ai", "beta.ai"])
    assert isinstance(res, CompetitorComparisonResult)
    assert len(res.domains) == 2
    assert "alpha.ai" in res.profiles
    assert "beta.ai" in res.profiles
    assert "# Competitive Benchmarking" in res.full_report_md
    assert "| Criteria | alpha.ai | beta.ai |" in res.comparison_table_md

    # Test PDF generation
    pdf_bytes = CompetitorComparator.export_pdf(res)
    assert isinstance(pdf_bytes, bytes)
    assert len(pdf_bytes) > 200
    assert pdf_bytes.startswith(b"%PDF")


@pytest.mark.asyncio
async def test_competitors_api_endpoints(monkeypatch):
    """Verify POST /api/v1/competitors/compare and /export endpoints."""
    comparator = CompetitorComparator()

    def mock_get_raw_data(domain):
        return {
            "domain": domain,
            "documents": [f"Content for {domain}"],
            "metadatas": [{"url": f"https://{domain}/", "title": f"{domain} Title"}],
        }

    monkeypatch.setattr(CompetitorComparator, "get_domain_raw_data", lambda self, d: mock_get_raw_data(d))

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Compare JSON
        payload = {"domains": ["first.io", "second.io"], "custom_focus": "pricing"}
        res = await client.post("/api/v1/competitors/compare", json=payload)
        assert res.status_code == 200
        data = res.json()
        assert "first.io" in data["profiles"]
        assert "second.io" in data["profiles"]

        # Export Markdown
        export_md_payload = {
            "domains": ["first.io", "second.io"],
            "format": "markdown",
        }
        res_md = await client.post("/api/v1/competitors/compare/export", json=export_md_payload)
        assert res_md.status_code == 200
        assert res_md.headers["content-type"].startswith("text/markdown")
        assert "Competitor" in res_md.text

        # Export PDF
        export_pdf_payload = {
            "domains": ["first.io", "second.io"],
            "format": "pdf",
        }
        res_pdf = await client.post("/api/v1/competitors/compare/export", json=export_pdf_payload)
        assert res_pdf.status_code == 200
        assert res_pdf.headers["content-type"] == "application/pdf"
        assert res_pdf.content.startswith(b"%PDF")

