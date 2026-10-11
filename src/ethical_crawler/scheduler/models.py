"""Data models and schemas for scheduled crawling and monitoring."""

from __future__ import annotations

from datetime import datetime, timezone
from enum import StrEnum
from typing import Any, Dict, List, Optional
from uuid import uuid4

from pydantic import BaseModel, Field


class ScheduleInterval(StrEnum):
    """Supported recurrence intervals."""
    EVERY_10_MIN = "10m"
    EVERY_30_MIN = "30m"
    HOURLY = "1h"
    EVERY_6_HOURS = "6h"
    EVERY_12_HOURS = "12h"
    DAILY = "24h"
    WEEKLY = "7d"


INTERVAL_SECONDS: Dict[ScheduleInterval, int] = {
    ScheduleInterval.EVERY_10_MIN: 10 * 60,
    ScheduleInterval.EVERY_30_MIN: 30 * 60,
    ScheduleInterval.HOURLY: 60 * 60,
    ScheduleInterval.EVERY_6_HOURS: 6 * 60 * 60,
    ScheduleInterval.EVERY_12_HOURS: 12 * 60 * 60,
    ScheduleInterval.DAILY: 24 * 60 * 60,
    ScheduleInterval.WEEKLY: 7 * 24 * 60 * 60,
}


class ScheduleStatus(StrEnum):
    """Execution status of a monitor."""
    ACTIVE = "active"
    PAUSED = "paused"
    RUNNING = "running"
    ERROR = "error"


class ScheduleCreateRequest(BaseModel):
    """Payload to create a new scheduled crawl monitor."""
    url: str = Field(..., description="Target URL to monitor")
    name: Optional[str] = Field(None, description="Friendly monitor name (defaults to domain)")
    job_type: str = Field("scrape", description="'scrape' for single page or 'crawl' for recursive")
    strategy: str = Field("auto", description="'auto', 'browser', or 'http'")
    interval: ScheduleInterval = Field(ScheduleInterval.DAILY, description="Recurrence interval")
    webhook_url: Optional[str] = Field(None, description="Optional webhook URL to notify on change")
    notify_on_change_only: bool = Field(True, description="Only dispatch alerts when content changes")
    extract_ai: bool = Field(False, description="Run AI extraction during scheduled run")
    ai_schema: str = Field("custom", description="AI extraction schema if extract_ai is true")


class ScheduleUpdateRequest(BaseModel):
    """Payload to update an existing monitor."""
    name: Optional[str] = None
    interval: Optional[ScheduleInterval] = None
    strategy: Optional[str] = None
    is_active: Optional[bool] = None
    webhook_url: Optional[str] = None
    notify_on_change_only: Optional[bool] = None


class ScheduleJob(BaseModel):
    """Persistent scheduled monitor job definition."""
    id: str = Field(default_factory=lambda: f"mon_{uuid4().hex[:10]}")
    name: str
    url: str
    job_type: str = "scrape"
    strategy: str = "auto"
    interval: ScheduleInterval = ScheduleInterval.DAILY
    interval_seconds: int = 86400
    status: ScheduleStatus = ScheduleStatus.ACTIVE
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    last_run_at: Optional[datetime] = None
    next_run_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    last_status: Optional[str] = None  # "changed", "no_change", "baseline_created", "failed"
    last_similarity_ratio: Optional[float] = None
    last_diff_summary: Optional[str] = None
    last_raw_diff: Optional[str] = None
    webhook_url: Optional[str] = None
    notify_on_change_only: bool = True
    extract_ai: bool = False
    ai_schema: str = "custom"
    consecutive_failures: int = 0
    total_runs: int = 0
    total_changes_detected: int = 0

