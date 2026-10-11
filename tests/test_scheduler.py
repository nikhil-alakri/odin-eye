"""Unit tests for the ScheduleManager and scheduled monitors."""

import os
from pathlib import Path
import pytest

from ethical_crawler.scheduler.manager import ScheduleManager
from ethical_crawler.scheduler.models import (
    ScheduleCreateRequest,
    ScheduleInterval,
    ScheduleStatus,
    ScheduleUpdateRequest,
)


@pytest.fixture
def temp_manager(tmp_path: Path):
    storage_file = str(tmp_path / "schedules_test.json")
    manager = ScheduleManager(storage_path=storage_file)
    return manager


def test_create_and_list_schedules(temp_manager: ScheduleManager):
    req = ScheduleCreateRequest(
        url="https://example.com/pricing",
        name="Example Pricing",
        interval=ScheduleInterval.HOURLY,
        webhook_url="https://webhook.site/test",
    )
    job = temp_manager.create_schedule(req)
    assert job.id.startswith("mon_")
    assert job.name == "Example Pricing"
    assert job.interval == ScheduleInterval.HOURLY
    assert job.interval_seconds == 3600
    assert job.status == ScheduleStatus.ACTIVE

    all_jobs = temp_manager.list_schedules()
    assert len(all_jobs) == 1
    assert all_jobs[0].id == job.id


def test_toggle_and_update_schedule(temp_manager: ScheduleManager):
    req = ScheduleCreateRequest(url="https://example.com/terms")
    job = temp_manager.create_schedule(req)

    # Toggle to paused
    toggled = temp_manager.toggle_schedule(job.id)
    assert toggled.status == ScheduleStatus.PAUSED

    # Toggle to active
    toggled = temp_manager.toggle_schedule(job.id)
    assert toggled.status == ScheduleStatus.ACTIVE

    # Update
    updated = temp_manager.update_schedule(
        job.id,
        ScheduleUpdateRequest(name="Updated Terms", interval=ScheduleInterval.WEEKLY),
    )
    assert updated.name == "Updated Terms"
    assert updated.interval == ScheduleInterval.WEEKLY
    assert updated.interval_seconds == 7 * 86400


def test_delete_schedule(temp_manager: ScheduleManager):
    req = ScheduleCreateRequest(url="https://example.com/blog")
    job = temp_manager.create_schedule(req)
    assert len(temp_manager.list_schedules()) == 1

    deleted = temp_manager.delete_schedule(job.id)
    assert deleted is True
    assert len(temp_manager.list_schedules()) == 0


@pytest.mark.asyncio
async def test_execute_job_mock(temp_manager: ScheduleManager, monkeypatch):
    from ethical_crawler.types import CrawlResult, PageMetadata

    mock_result = CrawlResult(
        url="https://example.com/mock",
        final_url="https://example.com/mock",
        status_code=200,
        content_type="text/html",
        title="Mock Title",
        markdown="# Mock Page\n\nInitial version.",
        raw_html_size=100,
        cleaned_markdown_size=30,
        metadata=PageMetadata(title="Mock"),
        strategy_used="http",
    )

    async def mock_crawl(*args, **kwargs):
        return mock_result

    from ethical_crawler.engines.http_engine import HTTPEngine

    monkeypatch.setattr(HTTPEngine, "crawl", mock_crawl)

    job = temp_manager.create_schedule(ScheduleCreateRequest(url="https://example.com/mock"))

    updated_job, diff_res = await temp_manager.execute_job(job.id)
    assert updated_job is not None
    assert updated_job.last_status in ("baseline_created", "no_change", "changed")
    assert updated_job.total_runs == 1
