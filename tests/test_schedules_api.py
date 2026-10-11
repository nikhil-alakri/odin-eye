"""Unit tests for Schedules and Diff REST API endpoints."""

import pytest
from httpx import ASGITransport, AsyncClient

from ethical_crawler.api.app import app


@pytest.mark.asyncio
async def test_schedules_crud_api():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Create a monitor schedule
        payload = {
            "url": "https://test-monitor.org/pricing",
            "name": "Test Monitor API",
            "interval": "1h",
            "webhook_url": "https://webhook.site/mock-test",
        }
        res = await client.post("/api/v1/schedules", json=payload)
        assert res.status_code == 200
        data = res.json()
        assert data["id"].startswith("mon_")
        assert data["url"] == "https://test-monitor.org/pricing"
        assert data["interval"] == "1h"
        schedule_id = data["id"]

        # 2. List schedules
        list_res = await client.get("/api/v1/schedules")
        assert list_res.status_code == 200
        items = list_res.json()
        assert any(item["id"] == schedule_id for item in items)

        # 3. Get single schedule
        get_res = await client.get(f"/api/v1/schedules/{schedule_id}")
        assert get_res.status_code == 200
        assert get_res.json()["name"] == "Test Monitor API"

        # 4. Toggle schedule
        toggle_res = await client.post(f"/api/v1/schedules/{schedule_id}/toggle")
        assert toggle_res.status_code == 200
        assert toggle_res.json()["status"] == "paused"

        # 5. Patch schedule
        patch_res = await client.patch(
            f"/api/v1/schedules/{schedule_id}",
            json={"name": "Renamed Monitor", "interval": "24h"},
        )
        assert patch_res.status_code == 200
        assert patch_res.json()["name"] == "Renamed Monitor"
        assert patch_res.json()["interval"] == "24h"

        # 6. Delete schedule
        del_res = await client.delete(f"/api/v1/schedules/{schedule_id}")
        assert del_res.status_code == 200
        assert del_res.json()["status"] == "deleted"

        # 7. Verify deletion
        not_found_res = await client.get(f"/api/v1/schedules/{schedule_id}")
        assert not_found_res.status_code == 404


@pytest.mark.asyncio
async def test_diff_api():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        payload = {
            "old_text": "# Plan A\nPrice: $10",
            "new_text": "# Plan A\nPrice: $15\nNew feature included.",
        }
        res = await client.post("/api/v1/diff", json=payload)
        assert res.status_code == 200
        data = res.json()
        assert data["has_changed"] is True
        assert data["added_lines_count"] > 0
        assert "diff-add" in data["html_diff"]

