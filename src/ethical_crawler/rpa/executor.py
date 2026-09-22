"""Playwright-powered RPA Action Executor."""

import asyncio
import logging
import os
import time
from typing import Any

from ethical_crawler.rpa.models import RPAActionType, RPAResult, RPAStep

logger = logging.getLogger("ethical_crawler.rpa.executor")


class RPAExecutor:
    """Executes ordered sequences of interactive browser automation actions."""

    def __init__(self, page: Any):
        self.page = page

    async def execute_step(self, step: RPAStep) -> tuple[bool, str]:
        """Execute an individual RPA step with error isolation and timing."""
        desc = step.description or f"{step.action.value} on '{step.selector or step.value}'"
        val = step.value

        # Resolve secret from environment if requested
        if step.secret_env:
            val = os.environ.get(step.secret_env, val)

        try:
            if step.action == RPAActionType.CLICK:
                if not step.selector:
                    return False, f"Step '{desc}' requires a selector"
                loc = self.page.locator(step.selector).first
                await loc.click(timeout=step.timeout_ms)

            elif step.action == RPAActionType.FILL:
                if not step.selector:
                    return False, f"Step '{desc}' requires a selector"
                text = val or ""
                await self.page.fill(step.selector, text, timeout=step.timeout_ms)

            elif step.action == RPAActionType.SELECT:
                if not step.selector:
                    return False, f"Step '{desc}' requires a selector"
                await self.page.select_option(
                    step.selector, value=val or "", timeout=step.timeout_ms
                )

            elif step.action == RPAActionType.WAIT_FOR:
                if not step.selector:
                    return False, f"Step '{desc}' requires a selector"
                await self.page.wait_for_selector(step.selector, timeout=step.timeout_ms)

            elif step.action == RPAActionType.PRESS_KEY:
                key = val or "Enter"
                if step.selector:
                    await self.page.press(step.selector, key, timeout=step.timeout_ms)
                else:
                    await self.page.keyboard.press(key)

            elif step.action == RPAActionType.HOVER:
                if not step.selector:
                    return False, f"Step '{desc}' requires a selector"
                loc = self.page.locator(step.selector).first
                await loc.hover(timeout=step.timeout_ms)

            elif step.action == RPAActionType.SCROLL:
                if val == "bottom":
                    await self.page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                elif val == "top":
                    await self.page.evaluate("window.scrollTo(0, 0)")
                else:
                    try:
                        px = int(val or 400)
                    except ValueError:
                        px = 400
                    await self.page.evaluate(f"window.scrollBy(0, {px})")

            elif step.action == RPAActionType.SLEEP:
                ms = int(val or 500)
                await asyncio.sleep(max(50, ms) / 1000.0)

            else:
                return False, f"Unknown action type: {step.action}"

            # Post-action settle pause
            if step.wait_after_ms > 0:
                await asyncio.sleep(step.wait_after_ms / 1000.0)

            return True, f"Success: {desc}"

        except Exception as exc:
            msg = f"{desc} -> {type(exc).__name__}: {exc}"
            if step.optional:
                logger.debug("Optional RPA step skipped: %s", msg)
                return False, f"Optional step skipped: {msg}"
            else:
                logger.warning("Required RPA step failed: %s", msg)
                return False, f"Failed: {msg}"

    async def execute_playbook(self, steps: list[RPAStep]) -> RPAResult:
        """Execute a complete sequence of steps and return aggregated results."""
        start_time = time.time()
        result = RPAResult(steps_total=len(steps))

        if not steps:
            result.elapsed_seconds = 0.0
            return result

        logger.info("Executing RPA playbook (%d steps)...", len(steps))

        for idx, step in enumerate(steps, 1):
            success, log_msg = await self.execute_step(step)
            result.logs.append(f"Step {idx}/{len(steps)}: {log_msg}")

            if success:
                result.steps_succeeded += 1
            else:
                if step.optional:
                    result.steps_skipped_or_warned += 1
                else:
                    result.success = False
                    result.error = log_msg
                    logger.error("RPA playbook halted on mandatory step %d: %s", idx, log_msg)
                    break

        result.elapsed_seconds = round(time.time() - start_time, 3)
        return result
