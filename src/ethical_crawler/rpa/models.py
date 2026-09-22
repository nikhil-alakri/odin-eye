"""Pydantic data models and schemas for RPA action playbooks."""

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class RPAActionType(StrEnum):
    """Supported interactive browser automation actions."""

    CLICK = "click"
    FILL = "fill"
    SELECT = "select"
    WAIT_FOR = "wait_for"
    PRESS_KEY = "press_key"
    HOVER = "hover"
    SCROLL = "scroll"
    SLEEP = "sleep"


class RPAStep(BaseModel):
    """A single interactive automation step executed in the browser."""

    action: RPAActionType = Field(
        ...,
        description="The action type to perform (click, fill, select, wait_for, etc.)",
    )
    selector: str | None = Field(
        None,
        description="CSS selector, text selector, or XPath target in DOM",
    )
    value: str | None = Field(
        None,
        description="Text to fill, option value to select, key to press, or scroll direction/pixels",
    )
    secret_env: str | None = Field(
        None,
        description="Optional environment variable name to securely pull value for passwords/API keys",
    )
    optional: bool = Field(
        True,
        description="If True, step failures (e.g. element not present) log warnings without failing the job",
    )
    timeout_ms: int = Field(
        3500,
        description="Timeout in milliseconds to wait for element / action before giving up",
        ge=100,
        le=30000,
    )
    wait_after_ms: int = Field(
        300,
        description="Pause in milliseconds after executing action to let DOM/animations settle",
        ge=0,
        le=10000,
    )
    description: str | None = Field(
        None,
        description="Human-readable explanation of this step (e.g. 'Dismiss cookie popup')",
    )


class RPAResult(BaseModel):
    """Execution summary of an RPA playbook run."""

    steps_total: int = 0
    steps_succeeded: int = 0
    steps_skipped_or_warned: int = 0
    success: bool = True
    elapsed_seconds: float = 0.0
    logs: list[str] = Field(default_factory=list)
    error: str | None = None
    extracted_data: dict[str, Any] | None = None
