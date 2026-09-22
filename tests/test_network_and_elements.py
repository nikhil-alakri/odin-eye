"""Tests for Network API Interception and DOM Element Inspection."""

import pytest
from httpx import ASGITransport, AsyncClient

from ethical_crawler.api.app import app
from ethical_crawler.extractors.element_inspector import ElementInspector
from ethical_crawler.types import CrawlResult, NetworkCall

SAMPLE_HTML = """
<!DOCTYPE html>
<html>
<head><title>Test Store & Dashboard</title></head>
<body>
    <header>
        <h1 id="main-heading">Market Analytics Dashboard</h1>
        <h2>Quarterly Projections</h2>
        <h3>Key Metrics</h3>
    </header>
    <main>
        <section class="pricing-card">
            <button id="annual-btn" class="btn-toggle active" role="button">Toggle Annual</button>
            <button class="btn-primary" type="submit">Subscribe Now</button>
            <a href="/login" class="btn btn-secondary">Sign In</a>
        </section>

        <form id="search-form" action="/search" method="GET">
            <input type="text" name="q" placeholder="Search competitors..." id="search-input" required value="AI Agent">
            <select name="category" id="cat-select">
                <option value="tech">Technology</option>
                <option value="finance">Finance</option>
            </select>
            <textarea name="notes" placeholder="Optional notes..."></textarea>
        </form>

        <table id="financial-grid">
            <thead>
                <tr><th>Company</th><th>ARR</th><th>Growth</th></tr>
            </thead>
            <tbody>
                <tr><td>Alpha Inc</td><td>$10M</td><td>45%</td></tr>
                <tr><td>Beta Corp</td><td>$25M</td><td>80%</td></tr>
            </tbody>
        </table>
    </main>
</body>
</html>
"""


def test_element_inspector_discovery():
    """Test extracting structured elements from HTML."""
    res = ElementInspector.inspect_html(SAMPLE_HTML)
    summary = res["summary"]

    assert summary["buttons"] == 3
    assert summary["inputs"] == 3  # input, select, textarea
    assert summary["tables"] == 1
    assert summary["headings"] == 3

    # Check button details
    buttons = res["buttons"]
    assert buttons[0]["id"] == "annual-btn"
    assert buttons[0]["text"] == "Toggle Annual"
    assert buttons[0]["selector"] == "#annual-btn"

    assert buttons[1]["text"] == "Subscribe Now"
    assert "btn-primary" in buttons[1]["selector"]

    # Check input details
    inputs = res["inputs"]
    assert inputs[0]["name"] == "q"
    assert inputs[0]["id"] == "search-input"
    assert inputs[0]["required"] is True
    assert inputs[0]["selector"] == "#search-input"

    # Check table details
    tables = res["tables"]
    assert tables[0]["id"] == "financial-grid"
    assert tables[0]["rows_count"] == 3  # 1 thead tr + 2 tbody tr
    assert "ARR" in tables[0]["headers"]

    # Check headings details
    headings = res["headings"]
    assert headings[0]["level"] == "h1"
    assert headings[0]["text"] == "Market Analytics Dashboard"
    assert headings[0]["selector"] == "#main-heading"


def test_element_inspector_empty_html():
    """Test ElementInspector with empty or None input."""
    res = ElementInspector.inspect_html("")
    assert res["summary"]["total_elements"] == 0
    assert len(res["buttons"]) == 0

    query_res = ElementInspector.query_selector("", "button")
    assert query_res == []


def test_element_inspector_query_selector():
    """Test live CSS selector querying."""
    # Query matching element
    matches = ElementInspector.query_selector(SAMPLE_HTML, "button.btn-primary")
    assert len(matches) == 1
    assert matches[0]["tag"] == "button"
    assert matches[0]["text"] == "Subscribe Now"
    assert matches[0]["attributes"]["type"] == "submit"

    # Query with attributes
    input_matches = ElementInspector.query_selector(SAMPLE_HTML, 'input[name="q"]')
    assert len(input_matches) == 1
    assert input_matches[0]["id"] == "search-input"
    assert input_matches[0]["attributes"]["value"] == "AI Agent"

    # Query nonexistent selector
    empty_matches = ElementInspector.query_selector(SAMPLE_HTML, "span.nonexistent-class")
    assert len(empty_matches) == 0

    # Query invalid selector raises ValueError
    with pytest.raises(ValueError, match="Invalid CSS selector"):
        ElementInspector.query_selector(SAMPLE_HTML, "button[unclosed-selector")


@pytest.mark.asyncio
async def test_api_element_check_endpoint():
    """Test POST /api/v1/elements/check API endpoint."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Success check with HTML
        resp = await client.post(
            "/api/v1/elements/check",
            json={
                "selector": "#annual-btn",
                "html": SAMPLE_HTML,
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["selector"] == "#annual-btn"
        assert data["match_count"] == 1
        assert data["matches"][0]["text"] == "Toggle Annual"

        # Check with no matches
        resp_empty = await client.post(
            "/api/v1/elements/check",
            json={
                "selector": ".non-existent-xyz",
                "html": SAMPLE_HTML,
            },
        )
        assert resp_empty.status_code == 200
        data_empty = resp_empty.json()
        assert data_empty["match_count"] == 0

        # Check invalid selector
        resp_invalid = await client.post(
            "/api/v1/elements/check",
            json={
                "selector": "div[invalid-bracket",
                "html": SAMPLE_HTML,
            },
        )
        assert resp_invalid.status_code == 200
        data_invalid = resp_invalid.json()
        assert data_invalid["error"] is not None


def test_network_call_and_crawl_result_serialization():
    """Test NetworkCall model and CrawlResult fields."""
    net_call = NetworkCall(
        url="https://api.example.com/v1/products",
        method="GET",
        status=200,
        resource_type="fetch",
        content_type="application/json",
        response_data={"products": [{"id": 1, "name": "Item A"}]},
        duration_ms=45.2,
    )
    call_dict = net_call.model_dump()
    assert call_dict["method"] == "GET"
    assert call_dict["status"] == 200
    assert call_dict["response_data"]["products"][0]["name"] == "Item A"

    result = CrawlResult(
        url="https://example.com",
        final_url="https://example.com",
        status_code=200,
        network_calls=[call_dict],
        dom_elements={"summary": {"total_elements": 10}},
    )

    serialized = result.model_dump()
    assert len(serialized["network_calls"]) == 1
    assert serialized["network_calls"][0]["url"] == "https://api.example.com/v1/products"
    assert serialized["dom_elements"]["summary"]["total_elements"] == 10


@pytest.mark.asyncio
async def test_browser_engine_network_interception_logic():
    """Test simulated browser engine network listener response logic."""
    captured_api_calls = []

    async def simulate_on_response(url, method, status, res_type, content_type, body_json):
        is_api = (
            res_type in ("fetch", "xhr")
            or "application/json" in content_type
            or "application/graphql" in content_type
            or url.split("?")[0].endswith(".json")
        )
        if not is_api:
            return

        captured_api_calls.append(
            {
                "url": url,
                "method": method,
                "status": status,
                "resource_type": res_type,
                "content_type": content_type,
                "response_data": body_json,
            }
        )

    # API call: should capture
    await simulate_on_response(
        url="https://example.com/api/pricing.json",
        method="GET",
        status=200,
        res_type="fetch",
        content_type="application/json; charset=utf-8",
        body_json={"plans": ["Free", "Pro", "Enterprise"]},
    )

    # Static CSS: should ignore
    await simulate_on_response(
        url="https://example.com/styles.css",
        method="GET",
        status=200,
        res_type="stylesheet",
        content_type="text/css",
        body_json=None,
    )

    # Static Image: should ignore
    await simulate_on_response(
        url="https://example.com/logo.png",
        method="GET",
        status=200,
        res_type="image",
        content_type="image/png",
        body_json=None,
    )

    assert len(captured_api_calls) == 1
    assert captured_api_calls[0]["url"] == "https://example.com/api/pricing.json"
    assert captured_api_calls[0]["response_data"]["plans"] == ["Free", "Pro", "Enterprise"]
