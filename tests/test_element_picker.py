"""Unit tests for ElementPicker and sandbox endpoint."""

from bs4 import BeautifulSoup
import pytest
from httpx import ASGITransport, AsyncClient

from ethical_crawler.api.app import app
from ethical_crawler.extractors.element_picker import ElementPicker


def test_sanitize_and_prepare_html():
    raw_html = """<!DOCTYPE html>
<html>
<head><title>Test Page</title></head>
<body>
    <script>if (top.location != location) top.location.href = location.href;</script>
    <button id="cta-btn" data-testid="submit-btn" class="btn btn-primary">Click Me</button>
</body>
</html>"""

    prepared = ElementPicker.sanitize_and_prepare_html(raw_html, target_url="https://example.com/shop")
    assert '<base href="https://example.com/shop">' in prepared
    assert "__ethic_element_picker_script__" in prepared
    assert "top.location.href" not in prepared
    assert "/* breakout muted */" in prepared


def test_generate_selector_from_bs4():
    soup = BeautifulSoup(
        '<div id="container"><button id="pay-btn">Pay</button><input name="email" /><a class="nav-item">Link</a></div>',
        "html.parser",
    )
    btn = soup.find("button")
    assert ElementPicker.generate_selector_from_bs4(btn) == "#pay-btn"

    inp = soup.find("input")
    assert ElementPicker.generate_selector_from_bs4(inp) == '[name="email"]'

    link = soup.find("a")
    assert ElementPicker.generate_selector_from_bs4(link) == "a.nav-item"


@pytest.mark.asyncio
async def test_element_sandbox_api(monkeypatch):
    import httpx

    orig_get = httpx.AsyncClient.get

    async def mock_get(self, url, **kwargs):
        if str(url).startswith("/api") or str(url).startswith("http://test"):
            return await orig_get(self, url, **kwargs)
        return httpx.Response(200, text="<html><head></head><body><h1>Hello World</h1></body></html>")

    monkeypatch.setattr(httpx.AsyncClient, "get", mock_get)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.get("/api/v1/elements/sandbox?url=https://example.com/page")
        assert res.status_code == 200
        assert res.headers["content-type"].startswith("text/html")
        assert "__ethic_element_picker_script__" in res.text
        assert '<base href="https://example.com/page">' in res.text
