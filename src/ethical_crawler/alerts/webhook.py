"""Outbound Webhook Dispatcher for crawler alerts and monitoring notifications."""

from __future__ import annotations

import asyncio
import logging
from typing import Any, Dict, Optional

import httpx

logger = logging.getLogger(__name__)


async def dispatch_webhook_alert(
    webhook_url: str,
    payload: Dict[str, Any],
    max_retries: int = 3,
    timeout_seconds: float = 10.0,
) -> bool:
    """Deliver a webhook alert payload with retry backoff and service-specific adaptation."""
    if not webhook_url or not webhook_url.startswith(("http://", "https://")):
        return False

    # Format adaptive payloads for popular chat webhooks (Slack / Discord)
    body: Dict[str, Any] = dict(payload)
    url_lower = webhook_url.lower()

    summary_text = (
        f"🚨 *[CRAWL // ETHIC]* Change Detected on <{payload.get('url')}|{payload.get('url')}>\n"
        f"• *Monitor:* {payload.get('monitor_name', 'Web Monitor')}\n"
        f"• *Summary:* {payload.get('diff_summary', 'Content updated')}\n"
        f"• *Similarity:* {round(float(payload.get('similarity_ratio', 1.0)) * 100, 1)}%\n"
        f"• *Timestamp:* {payload.get('timestamp')}"
    )

    if "hooks.slack.com" in url_lower:
        body = {
            "text": summary_text,
            "blocks": [
                {
                    "type": "section",
                    "text": {"type": "mrkdwn", "text": summary_text},
                }
            ],
            "data": payload,
        }
    elif "discord.com/api/webhooks" in url_lower or "discordapp.com" in url_lower:
        body = {
            "content": summary_text,
            "embeds": [
                {
                    "title": f"Change Detected: {payload.get('monitor_name', 'Web Monitor')}",
                    "url": payload.get("url"),
                    "description": payload.get("diff_summary"),
                    "color": 10040319,  # Purple
                    "fields": [
                        {"name": "Additions", "value": f"+{payload.get('additions_count', 0)} lines", "inline": True},
                        {"name": "Deletions", "value": f"-{payload.get('deletions_count', 0)} lines", "inline": True},
                    ],
                }
            ],
        }

    delay = 1.0
    for attempt in range(1, max_retries + 1):
        try:
            async with httpx.AsyncClient(timeout=timeout_seconds) as client:
                resp = await client.post(
                    webhook_url,
                    json=body,
                    headers={
                        "User-Agent": "EthicalCrawlerBot-WebhookNotifier/1.0",
                        "Content-Type": "application/json",
                    },
                )
                if resp.status_code in (200, 201, 202, 204):
                    logger.info("Webhook alert delivered to %s (attempt %d)", webhook_url, attempt)
                    return True
                logger.warning(
                    "Webhook responded with %d: %s (attempt %d/%d)",
                    resp.status_code,
                    resp.text[:200],
                    attempt,
                    max_retries,
                )
        except Exception as exc:
            logger.warning("Webhook delivery error to %s: %s (attempt %d/%d)", webhook_url, exc, attempt, max_retries)

        if attempt < max_retries:
            await asyncio.sleep(delay)
            delay *= 2.0

    return False

