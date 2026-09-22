"""Tests for ChromaDB Vector Store, Semantic Search, Caching, and Endpoints."""

from datetime import datetime, timedelta
from pathlib import Path

import pytest
from httpx import ASGITransport, AsyncClient
from typer.testing import CliRunner

from ethical_crawler.api.app import app
from ethical_crawler.cli import app as cli_app
from ethical_crawler.types import CrawlResult, CrawlStrategy, PageMetadata
from ethical_crawler.vector_store import VectorStoreManager


@pytest.fixture
def temp_vector_store(tmp_path: Path):
    """Fixture to provide an isolated temporary ChromaDB VectorStoreManager."""
    chroma_dir = tmp_path / "chroma_test"
    store = VectorStoreManager(persist_dir=chroma_dir, collection_name="test_collection")
    return store


def make_dummy_result(
    url: str = "https://example.com/pricing",
    title: str = "Pricing Plans & Subscriptions",
    markdown: str = "# Pricing\\n\\nWe offer a Free Tier and an Enterprise Plan at $99/mo with priority ethical crawling support.",
    crawled_at: datetime | None = None,
) -> CrawlResult:
    return CrawlResult(
        url=url,
        final_url=url,
        status_code=200,
        title=title,
        markdown=markdown,
        metadata=PageMetadata(title=title, description="Pricing plans"),
        cleaned_markdown_size=len(markdown),
        strategy_used=CrawlStrategy.HTTP,
        crawled_at=crawled_at or datetime.utcnow(),
        internal_links=["https://example.com/features", "https://example.com/about"],
    )


def test_upsert_and_cache_hit(temp_vector_store: VectorStoreManager):
    result = make_dummy_result()
    temp_vector_store.upsert_page(result, ai_data={"tier": "enterprise"})

    assert temp_vector_store.count_pages() == 1

    cached = temp_vector_store.get_cached_page("https://example.com/pricing")
    assert cached is not None
    cached_res, cached_ai = cached
    assert cached_res.title == "Pricing Plans & Subscriptions"
    assert "Enterprise Plan" in cached_res.markdown
    assert cached_ai == {"tier": "enterprise"}
    assert cached_res.internal_links == [
        "https://example.com/features",
        "https://example.com/about",
    ]


def test_cache_miss_when_expired(temp_vector_store: VectorStoreManager):
    old_time = datetime.utcnow() - timedelta(days=10)
    result = make_dummy_result(crawled_at=old_time)
    temp_vector_store.upsert_page(result)

    # TTL is 7 days, so 10 days should be expired
    cached = temp_vector_store.get_cached_page("https://example.com/pricing", max_age_days=7)
    assert cached is None

    # But with a 15-day TTL, it should be retrieved
    cached_valid = temp_vector_store.get_cached_page("https://example.com/pricing", max_age_days=15)
    assert cached_valid is not None


def test_semantic_search(temp_vector_store: VectorStoreManager):
    res1 = make_dummy_result(
        url="https://example.com/pricing",
        title="Pricing Guide",
        markdown="All about subscriptions, payment methods, enterprise licenses and refund policies.",
    )
    res2 = make_dummy_result(
        url="https://example.com/contact",
        title="Contact Engineering Team",
        markdown="Reach out to support, technical contact email, and headquarters location in San Francisco.",
    )
    temp_vector_store.upsert_page(res1)
    temp_vector_store.upsert_page(res2)

    # Search for refund/license -> should rank pricing highest
    matches = temp_vector_store.semantic_search("how much does a license cost?", n_results=2)
    assert len(matches) > 0
    assert matches[0]["url"] == "https://example.com/pricing"
    assert "similarity" in matches[0]
    assert matches[0]["similarity"] > 0.0


def test_list_stored_pages(temp_vector_store: VectorStoreManager):
    res = make_dummy_result(url="https://docs.example.org/api", title="API Documentation")
    temp_vector_store.upsert_page(res)

    pages = temp_vector_store.list_stored_pages()
    assert len(pages) == 1
    assert pages[0]["domain"] == "docs.example.org"
    assert pages[0]["title"] == "API Documentation"


@pytest.mark.asyncio
async def test_ask_crawled_knowledge_fallback(temp_vector_store: VectorStoreManager, monkeypatch):
    from ethical_crawler import config

    settings = config.get_settings()
    monkeypatch.setattr(settings, "ai_api_key", None)

    res = make_dummy_result()
    temp_vector_store.upsert_page(res)

    ans = await temp_vector_store.ask_crawled_knowledge("What are the pricing options?")
    assert "answer" in ans
    assert "Pricing Plans & Subscriptions" in ans["answer"]
    assert len(ans["sources"]) == 1


@pytest.mark.asyncio
async def test_api_history_and_search_endpoints(temp_vector_store: VectorStoreManager, monkeypatch):
    import ethical_crawler.vector_store as vs_module

    monkeypatch.setattr(vs_module, "get_vector_store", lambda: temp_vector_store)

    res = make_dummy_result()
    temp_vector_store.upsert_page(res, ai_data={"category": "pricing"})

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. GET /api/v1/history
        resp = await client.get("/api/v1/history")
        assert resp.status_code == 200
        history_list = resp.json()
        assert len(history_list) == 1
        assert history_list[0]["url"] == "https://example.com/pricing"

        # 2. GET /api/v1/history/page
        resp_page = await client.get("/api/v1/history/page?url=https://example.com/pricing")
        assert resp_page.status_code == 200
        page_data = resp_page.json()
        assert page_data["result"]["title"] == "Pricing Plans & Subscriptions"
        assert page_data["ai_data"] == {"category": "pricing"}

        # 3. GET /api/v1/history/export
        resp_export = await client.get(
            "/api/v1/history/export?url=https://example.com/pricing&format=md"
        )
        assert resp_export.status_code == 200
        assert "attachment; filename=" in resp_export.headers.get("content-disposition", "")
        assert b"Pricing Plans & Subscriptions" in resp_export.content

        # 4. GET /api/v1/search
        resp_search = await client.get("/api/v1/search?q=subscription")
        assert resp_search.status_code == 200
        search_results = resp_search.json()
        assert len(search_results) == 1
        assert search_results[0]["title"] == "Pricing Plans & Subscriptions"

        # 5. POST /api/v1/ask
        resp_ask = await client.post("/api/v1/ask", json={"question": "What is the cost?"})
        assert resp_ask.status_code == 200
        ask_data = resp_ask.json()
        assert "answer" in ask_data
        assert len(ask_data["sources"]) == 1

        # 6. GET /api/v1/history/store
        resp_store = await client.get("/api/v1/history/store")
        assert resp_store.status_code == 200
        store = resp_store.json()
        assert store["status"] == "active"
        assert store["collection"]
        assert store["document_count"] == 1
        assert store["domain_count"] == 1
        assert store["documents"][0]["id"] == "https://example.com/pricing"
        assert any(row["field"] == "id" for row in store["field_mappings"])
        assert store["domains"][0]["domain"]


def test_cli_search_and_history(temp_vector_store: VectorStoreManager, monkeypatch):
    import ethical_crawler.vector_store as vs_module

    monkeypatch.setattr(vs_module, "get_vector_store", lambda: temp_vector_store)

    res = make_dummy_result()
    temp_vector_store.upsert_page(res)

    runner = CliRunner()

    # Test cli history
    hist_res = runner.invoke(cli_app, ["history"])
    assert hist_res.exit_code == 0
    assert "Pricing" in hist_res.output
    assert "200" in hist_res.output

    # Test cli search
    search_res = runner.invoke(cli_app, ["search", "subscription"])
    assert search_res.exit_code == 0
    assert "Pricing" in search_res.output

    # Test cli ask
    ask_res = runner.invoke(cli_app, ["ask", "What are the plans?"])
    assert ask_res.exit_code == 0
    assert "Pricing" in ask_res.output


def test_revision_and_growth_tracking(temp_vector_store: VectorStoreManager):
    """Test that recrawling an existing page tracks revision count and calculates growth delta in bytes."""
    initial_text = "# Initial Page\nThis is the first crawl of the homepage."
    res_v1 = make_dummy_result(
        url="https://acme.org/about",
        title="About Acme Corp",
        markdown=initial_text,
    )
    temp_vector_store.upsert_page(res_v1)

    # First crawl: revision_count = 1, delta = 0
    pages = temp_vector_store.list_stored_pages()
    assert len(pages) == 1
    assert pages[0]["revision_count"] == 1
    assert pages[0]["growth_delta_bytes"] == 0

    # Second crawl: expanded content
    updated_text = (
        "# Expanded Acme Corp\n"
        "This is the updated page with new features, enterprise pricing, and team member bios. Much larger size!"
    )
    res_v2 = make_dummy_result(
        url="https://acme.org/about",
        title="About Acme Corp - Expanded",
        markdown=updated_text,
    )
    temp_vector_store.upsert_page(res_v2)

    pages = temp_vector_store.list_stored_pages()
    assert len(pages) == 1
    assert pages[0]["revision_count"] == 2
    expected_delta = len(updated_text) - len(initial_text)
    assert pages[0]["growth_delta_bytes"] == expected_delta
    assert pages[0]["growth_delta_bytes"] > 0
    assert pages[0]["title"] == "About Acme Corp - Expanded"


def test_delete_page_and_delete_domain(temp_vector_store: VectorStoreManager):
    """Test safe selective deletion for single pages and entire domain groups."""
    p1 = make_dummy_result(url="https://alpha.com/page1", title="Alpha Page 1")
    p2 = make_dummy_result(url="https://alpha.com/page2", title="Alpha Page 2")
    p3 = make_dummy_result(url="https://beta.com/home", title="Beta Home")

    temp_vector_store.upsert_page(p1)
    temp_vector_store.upsert_page(p2)
    temp_vector_store.upsert_page(p3)

    assert temp_vector_store.count_pages() == 3

    # Delete single page
    del_ok = temp_vector_store.delete_page("https://alpha.com/page1")
    assert del_ok is True
    assert temp_vector_store.count_pages() == 2
    assert temp_vector_store.get_cached_page("https://alpha.com/page1") is None
    assert temp_vector_store.get_cached_page("https://alpha.com/page2") is not None

    # Delete remaining domain pages
    deleted_count = temp_vector_store.delete_domain("alpha.com")
    assert deleted_count == 1
    assert temp_vector_store.count_pages() == 1

    # Only beta remains
    remaining = temp_vector_store.list_stored_pages()
    assert len(remaining) == 1
    assert remaining[0]["domain"] == "beta.com"


def test_list_domains_summary(temp_vector_store: VectorStoreManager):
    """Test domain-level aggregation and metrics."""
    p1 = make_dummy_result(url="https://store.dev/item1", title="Item 1")
    p2 = make_dummy_result(url="https://store.dev/item2", title="Item 2")
    p3 = make_dummy_result(url="https://blog.dev/post1", title="Post 1")

    temp_vector_store.upsert_page(p1, ai_data={"sku": "123"})
    temp_vector_store.upsert_page(p2)
    temp_vector_store.upsert_page(p3)

    summaries = temp_vector_store.list_domains_summary()
    assert len(summaries) == 2

    store_sum = next(s for s in summaries if s["domain"] == "store.dev")
    assert store_sum["total_pages"] == 2
    assert store_sum["ai_profile_count"] == 1
    assert len(store_sum["pages"]) == 2

    blog_sum = next(s for s in summaries if s["domain"] == "blog.dev")
    assert blog_sum["total_pages"] == 1
    assert blog_sum["ai_profile_count"] == 0


@pytest.mark.asyncio
async def test_api_domain_summary_and_deletion_endpoints(
    temp_vector_store: VectorStoreManager, monkeypatch
):
    """Test API endpoints for domain grouping, page/domain deletion, and dossier generation."""
    import ethical_crawler.vector_store as vs_module

    monkeypatch.setattr(vs_module, "get_vector_store", lambda: temp_vector_store)

    p1 = make_dummy_result(url="https://competitor-a.com/features", title="Competitor A")
    p2 = make_dummy_result(url="https://competitor-b.com/features", title="Competitor B")
    temp_vector_store.upsert_page(p1, ai_data={"tier": "enterprise"})
    temp_vector_store.upsert_page(p2)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. GET /api/v1/history/domains
        resp_domains = await client.get("/api/v1/history/domains")
        assert resp_domains.status_code == 200
        domains = resp_domains.json()
        assert len(domains) == 2

        # 2. POST /api/v1/dossier/generate
        resp_dossier = await client.post(
            "/api/v1/dossier/generate",
            json={
                "domains": ["competitor-a.com", "competitor-b.com"],
                "model": "moonshotai/kimi-k3",
            },
        )
        assert resp_dossier.status_code == 200
        dossier = resp_dossier.json()
        assert "markdown" in dossier
        assert "competitors_analyzed" in dossier
        assert len(dossier["competitors_analyzed"]) == 2

        # 3. GET /api/v1/dossier/export?format=md
        resp_export_md = await client.get(
            "/api/v1/dossier/export?domains=competitor-a.com&domains=competitor-b.com&format=md"
        )
        assert resp_export_md.status_code == 200
        assert b"Intelligence Dossier" in resp_export_md.content

        # 4. DELETE /api/v1/history/page
        resp_del_page = await client.delete(
            "/api/v1/history/page?url=https://competitor-a.com/features"
        )
        assert resp_del_page.status_code == 200
        assert resp_del_page.json()["deleted"] is True

        # 5. DELETE /api/v1/history/domain
        resp_del_domain = await client.delete("/api/v1/history/domain?domain=competitor-b.com")
        assert resp_del_domain.status_code == 200
        assert resp_del_domain.json()["deleted_count"] == 1
        assert temp_vector_store.count_pages() == 0
