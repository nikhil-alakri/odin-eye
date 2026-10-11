"""Unit tests for Screenshots and Vision API routes."""

from pathlib import Path
import pytest
from httpx import ASGITransport, AsyncClient

from ethical_crawler.api.app import app


@pytest.mark.asyncio
async def test_screenshots_list_and_stream(tmp_path: Path, monkeypatch):
    # Create fake screenshot in data/screenshots/example.com/test.jpg
    mock_dir = Path("data/screenshots/example.com")
    mock_dir.mkdir(parents=True, exist_ok=True)
    fake_img = mock_dir / "abc_20261009_120000.jpg"
    fake_img.write_bytes(b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x01\x00`\x00`\x00\x00")

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Test list
        res = await client.get("/api/v1/screenshots?domain=example.com")
        assert res.status_code == 200
        items = res.json()
        assert len(items) > 0
        assert items[0]["domain"] == "example.com"
        assert items[0]["filename"] == fake_img.name

        # Test stream
        stream_res = await client.get(f"/api/v1/screenshots/file/example.com/{fake_img.name}")
        assert stream_res.status_code == 200
        assert stream_res.headers["content-type"] == "image/jpeg"
        assert len(stream_res.content) > 0

    # Cleanup
    if fake_img.exists():
        fake_img.unlink()
    if mock_dir.exists():
        try:
            mock_dir.rmdir()
        except OSError:
            pass


@pytest.mark.asyncio
async def test_vision_extract_api():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        payload = {
            "image_base64": "aW1hZ2VkYXRh",
            "task": "chart_to_table",
            "api_key": "",  # force offline fallback
        }
        res = await client.post("/api/v1/vision/extract", json=payload)
        assert res.status_code == 200
        data = res.json()
        assert data["task"] == "chart_to_table"
        assert data["model_used"] == "offline-rule-based"
