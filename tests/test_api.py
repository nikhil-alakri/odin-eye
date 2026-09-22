"""Tests for FastAPI endpoints and web service."""

import pytest
from httpx import ASGITransport, AsyncClient

from ethical_crawler.api.app import app


@pytest.mark.asyncio
async def test_health_endpoint():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "healthy"
        assert "EthicalCrawlerBot" in data["bot_user_agent"]


@pytest.mark.asyncio
async def test_dashboard_endpoint():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/")
        assert resp.status_code == 200
        assert "Ethical AI Web Crawler" in resp.text
        assert "Robots.txt" in resp.text


@pytest.mark.asyncio
async def test_api_robots_endpoint(monkeypatch):
    from ethical_crawler.types import RobotsDirectives

    async def mock_directives(*args, **kwargs):
        return RobotsDirectives(
            domain="example.com",
            robots_url="https://example.com/robots.txt",
            can_fetch=True,
            crawl_delay=2.0,
            sitemaps=["https://example.com/sitemap.xml"],
            user_agent_used="EthicalCrawlerBot",
        )

    from ethical_crawler.api.deps import get_app_robots_parser

    parser = get_app_robots_parser()
    monkeypatch.setattr(parser, "get_directives", mock_directives)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/v1/robots?url=https://example.com")
        assert resp.status_code == 200
        data = resp.json()
        assert data["domain"] == "example.com"
        assert data["crawl_delay"] == 2.0


@pytest.mark.asyncio
async def test_api_crawl_and_job_status():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Start crawl
        post_resp = await client.post(
            "/api/v1/crawl",
            json={
                "url": "https://example.com",
                "max_pages": 1,
                "respect_robots": False,
            },
        )
        assert post_resp.status_code == 202
        job_id = post_resp.json()["job_id"]

        # Fetch status
        get_resp = await client.get(f"/api/v1/jobs/{job_id}")
        assert get_resp.status_code == 200
        assert get_resp.json()["job_id"] == job_id
