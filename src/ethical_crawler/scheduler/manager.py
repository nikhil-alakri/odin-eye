"""Schedule Manager for autonomous crawling, periodic monitoring, and diff tracking."""

from __future__ import annotations

import asyncio
from datetime import datetime, timedelta, timezone
import json
import logging
import os
from pathlib import Path
import threading
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlparse

from ethical_crawler.alerts.webhook import dispatch_webhook_alert
from ethical_crawler.engines.browser_engine import BrowserEngine
from ethical_crawler.engines.http_engine import HTTPEngine
from ethical_crawler.knowledge.diff_engine import ContentDiffEngine, ContentDiffResult
from ethical_crawler.scheduler.models import (
    INTERVAL_SECONDS,
    ScheduleCreateRequest,
    ScheduleInterval,
    ScheduleJob,
    ScheduleStatus,
    ScheduleUpdateRequest,
)
from ethical_crawler.types import CrawlResult
from ethical_crawler.vector_store import get_vector_store

logger = logging.getLogger(__name__)


class ScheduleManager:
    """Thread-safe and async schedule manager with persistent JSON storage and background execution ticker."""

    def __init__(self, storage_path: str = "data/schedules.json") -> None:
        self.storage_path = Path(storage_path)
        self._lock = threading.Lock()
        self._jobs: Dict[str, ScheduleJob] = {}
        self._running = False
        self._ticker_task: Optional[asyncio.Task] = None
        self._load()

    def _load(self) -> None:
        """Load schedules from disk."""
        with self._lock:
            if not self.storage_path.exists():
                self._jobs = {}
                return
            try:
                with open(self.storage_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self._jobs = {
                        item["id"]: ScheduleJob.model_validate(item)
                        for item in data.get("schedules", [])
                    }
                logger.info("Loaded %d scheduled monitors from %s", len(self._jobs), self.storage_path)
            except Exception as exc:
                logger.error("Failed to load schedules from %s: %s", self.storage_path, exc)
                self._jobs = {}

    def _save(self) -> None:
        """Atomically persist schedules to disk."""
        with self._lock:
            self.storage_path.parent.mkdir(parents=True, exist_ok=True)
            payload = {
                "version": "1.0",
                "updated_at": datetime.now(timezone.utc).isoformat(),
                "schedules": [job.model_dump(mode="json") for job in self._jobs.values()],
            }
            tmp_path = self.storage_path.with_suffix(".tmp")
            try:
                with open(tmp_path, "w", encoding="utf-8") as f:
                    json.dump(payload, f, indent=2)
                tmp_path.replace(self.storage_path)
            except Exception as exc:
                logger.error("Failed to save schedules to %s: %s", self.storage_path, exc)
                if tmp_path.exists():
                    tmp_path.unlink()

    def create_schedule(self, req: ScheduleCreateRequest) -> ScheduleJob:
        """Register and persist a new scheduled monitor."""
        interval_secs = INTERVAL_SECONDS.get(req.interval, 86400)
        parsed = urlparse(req.url)
        name = req.name or parsed.netloc or req.url

        job = ScheduleJob(
            name=name,
            url=req.url,
            job_type=req.job_type,
            strategy=req.strategy,
            interval=req.interval,
            interval_seconds=interval_secs,
            status=ScheduleStatus.ACTIVE,
            created_at=datetime.now(timezone.utc),
            next_run_at=datetime.now(timezone.utc),  # Trigger initial baseline immediately
            webhook_url=req.webhook_url,
            notify_on_change_only=req.notify_on_change_only,
            extract_ai=req.extract_ai,
            ai_schema=req.ai_schema,
        )

        with self._lock:
            self._jobs[job.id] = job
        self._save()
        logger.info("Created scheduled monitor %s (%s) every %s", job.id, job.url, job.interval)
        return job

    def list_schedules(self) -> List[ScheduleJob]:
        """List all registered monitors sorted by creation date."""
        with self._lock:
            return sorted(self._jobs.values(), key=lambda j: j.created_at, reverse=True)

    def get_schedule(self, schedule_id: str) -> Optional[ScheduleJob]:
        """Retrieve a single monitor by ID."""
        with self._lock:
            return self._jobs.get(schedule_id)

    def update_schedule(self, schedule_id: str, req: ScheduleUpdateRequest) -> Optional[ScheduleJob]:
        """Update monitor fields and recalculate timing."""
        with self._lock:
            job = self._jobs.get(schedule_id)
            if not job:
                return None

            if req.name is not None:
                job.name = req.name
            if req.interval is not None:
                job.interval = req.interval
                job.interval_seconds = INTERVAL_SECONDS.get(req.interval, job.interval_seconds)
                # Recalculate next run based on new interval
                base = job.last_run_at or datetime.now(timezone.utc)
                job.next_run_at = base + timedelta(seconds=job.interval_seconds)
            if req.strategy is not None:
                job.strategy = req.strategy
            if req.is_active is not None:
                job.status = ScheduleStatus.ACTIVE if req.is_active else ScheduleStatus.PAUSED
            if req.webhook_url is not None:
                job.webhook_url = req.webhook_url or None
            if req.notify_on_change_only is not None:
                job.notify_on_change_only = req.notify_on_change_only

        self._save()
        return job

    def toggle_schedule(self, schedule_id: str) -> Optional[ScheduleJob]:
        """Toggle a monitor between ACTIVE and PAUSED."""
        with self._lock:
            job = self._jobs.get(schedule_id)
            if not job:
                return None
            if job.status == ScheduleStatus.ACTIVE:
                job.status = ScheduleStatus.PAUSED
            else:
                job.status = ScheduleStatus.ACTIVE
                # Resume execution immediately if expired
                if job.next_run_at <= datetime.now(timezone.utc):
                    job.next_run_at = datetime.now(timezone.utc)
        self._save()
        return job

    def delete_schedule(self, schedule_id: str) -> bool:
        """Remove a scheduled monitor."""
        with self._lock:
            if schedule_id not in self._jobs:
                return False
            del self._jobs[schedule_id]
        self._save()
        logger.info("Deleted scheduled monitor %s", schedule_id)
        return True

    async def execute_job(self, job_id: str) -> Tuple[Optional[ScheduleJob], Optional[ContentDiffResult]]:
        """Run a single monitor immediately, compute diffs against previous snapshot, and dispatch alerts."""
        job = self.get_schedule(job_id)
        if not job:
            return None, None

        job.status = ScheduleStatus.RUNNING
        self._save()

        vector_store = get_vector_store()
        # Retrieve previous cached markdown before new crawl
        cached_before = vector_store.get_cached_page(job.url, max_age_days=365)
        old_markdown = None
        if cached_before and isinstance(cached_before, tuple):
            cached_res, _ = cached_before
            old_markdown = cached_res.markdown if cached_res else None

        result: Optional[CrawlResult] = None
        diff_result: Optional[ContentDiffResult] = None
        error_msg: Optional[str] = None

        try:
            # Execute crawl based on engine strategy
            if job.strategy == "browser":
                async with BrowserEngine(headless=True) as engine:
                    result = await engine.crawl(job.url)
            else:
                async with HTTPEngine() as engine:
                    result = await engine.crawl(job.url)

            if result and result.markdown:
                # Compute content diff
                diff_result = ContentDiffEngine.compute_diff(
                    old_text=old_markdown,
                    new_text=result.markdown,
                    old_label=f"Snapshot ({job.last_run_at.isoformat() if job.last_run_at else 'Baseline'})",
                    new_label=f"Latest Run ({datetime.now(timezone.utc).strftime('%H:%M:%S')})",
                )

                # Persist updated page into vector store
                vector_store.upsert_page(result)

                # Update job metrics
                now_utc = datetime.now(timezone.utc)
                job.last_run_at = now_utc
                job.next_run_at = now_utc + timedelta(seconds=job.interval_seconds)
                job.total_runs += 1
                job.consecutive_failures = 0
                job.status = ScheduleStatus.ACTIVE

                if old_markdown is None:
                    job.last_status = "baseline_created"
                    job.last_diff_summary = "Initial baseline snapshot created in knowledge base."
                    job.last_similarity_ratio = 1.0
                    job.last_raw_diff = ""
                elif diff_result.has_changed:
                    job.last_status = "changed"
                    job.total_changes_detected += 1
                    job.last_diff_summary = diff_result.summary
                    job.last_similarity_ratio = diff_result.similarity_ratio
                    job.last_raw_diff = diff_result.raw_diff

                    # Trigger webhook if configured
                    if job.webhook_url:
                        asyncio.create_task(
                            dispatch_webhook_alert(
                                job.webhook_url,
                                {
                                    "event": "content_changed",
                                    "monitor_id": job.id,
                                    "monitor_name": job.name,
                                    "url": job.url,
                                    "timestamp": now_utc.isoformat(),
                                    "similarity_ratio": diff_result.similarity_ratio,
                                    "diff_summary": diff_result.summary,
                                    "additions_count": diff_result.added_lines_count,
                                    "deletions_count": diff_result.removed_lines_count,
                                },
                            )
                        )
                else:
                    job.last_status = "no_change"
                    job.last_diff_summary = "Content unchanged since previous run."
                    job.last_similarity_ratio = diff_result.similarity_ratio
                    job.last_raw_diff = ""

                    if job.webhook_url and not job.notify_on_change_only:
                        asyncio.create_task(
                            dispatch_webhook_alert(
                                job.webhook_url,
                                {
                                    "event": "monitor_checked_no_change",
                                    "monitor_id": job.id,
                                    "monitor_name": job.name,
                                    "url": job.url,
                                    "timestamp": now_utc.isoformat(),
                                    "similarity_ratio": 1.0,
                                    "diff_summary": "Content identical to previous snapshot.",
                                },
                            )
                        )
            else:
                raise RuntimeError(result.error if result else "Zero content returned from target")

        except Exception as exc:
            logger.error("Error executing monitor %s (%s): %s", job.id, job.url, exc)
            job.consecutive_failures += 1
            job.last_status = "failed"
            job.last_diff_summary = f"Execution failed: {str(exc)[:150]}"
            job.status = ScheduleStatus.ERROR if job.consecutive_failures >= 3 else ScheduleStatus.ACTIVE
            job.next_run_at = datetime.now(timezone.utc) + timedelta(seconds=min(job.interval_seconds, 300))

        self._save()
        return job, diff_result

    async def _ticker_loop(self) -> None:
        """Background async ticker evaluating scheduled jobs every 15 seconds."""
        logger.info("Schedule manager ticker loop started.")
        while self._running:
            try:
                now_utc = datetime.now(timezone.utc)
                due_jobs: List[str] = []

                with self._lock:
                    for job in self._jobs.values():
                        if job.status == ScheduleStatus.ACTIVE and job.next_run_at <= now_utc:
                            due_jobs.append(job.id)

                for job_id in due_jobs:
                    if not self._running:
                        break
                    logger.info("Ticker executing scheduled monitor %s", job_id)
                    await self.execute_job(job_id)

            except asyncio.CancelledError:
                logger.info("Schedule manager ticker loop cancelled.")
                break
            except Exception as exc:
                logger.error("Error in schedule manager ticker loop: %s", exc)

            # Sleep in small increments for prompt cancellation response
            for _ in range(15):
                if not self._running:
                    break
                await asyncio.sleep(1.0)

    def start(self) -> None:
        """Start the background ticker loop."""
        if self._running:
            return
        self._running = True
        try:
            loop = asyncio.get_running_loop()
            self._ticker_task = loop.create_task(self._ticker_loop())
        except RuntimeError:
            logger.warning("No running asyncio event loop; scheduler ticker will start when loop is ready.")

    def stop(self) -> None:
        """Stop the background ticker loop cleanly."""
        self._running = False
        if self._ticker_task and not self._ticker_task.done():
            self._ticker_task.cancel()


# Singleton pattern
_manager_instance: Optional[ScheduleManager] = None
_manager_lock = threading.Lock()


def get_schedule_manager(storage_path: str = "data/schedules.json") -> ScheduleManager:
    """Retrieve or initialize the global ScheduleManager singleton."""
    global _manager_instance
    with _manager_lock:
        if _manager_instance is None:
            _manager_instance = ScheduleManager(storage_path=storage_path)
        return _manager_instance
