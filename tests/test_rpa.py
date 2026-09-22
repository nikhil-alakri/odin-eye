"""Tests for Robotic Process Automation (RPA) action models, presets, and executor."""

from unittest.mock import AsyncMock, MagicMock

import pytest
from httpx import ASGITransport, AsyncClient

from ethical_crawler.api.app import app
from ethical_crawler.rpa.executor import RPAExecutor
from ethical_crawler.rpa.models import RPAActionType, RPAResult, RPAStep
from ethical_crawler.rpa.presets import get_preset_recipes


def test_rpa_models():
    """Verify RPAStep Pydantic validation and defaults."""
    step = RPAStep(action=RPAActionType.CLICK, selector="button.submit")
    assert step.action == RPAActionType.CLICK
    assert step.selector == "button.submit"
    assert step.optional is True
    assert step.timeout_ms == 3500
    assert step.wait_after_ms == 300

    dumped = step.model_dump()
    assert dumped["action"] == "click"
    assert dumped["selector"] == "button.submit"


def test_rpa_presets():
    """Verify built-in recipes contain valid steps."""
    presets = get_preset_recipes()
    assert "auto_dismiss_cookies" in presets
    assert "expand_accordions" in presets
    assert "toggle_annual_pricing" in presets

    cookie_steps = presets["auto_dismiss_cookies"]["steps"]
    assert len(cookie_steps) > 0
    assert any("onetrust" in s.get("selector", "") for s in cookie_steps)


@pytest.mark.asyncio
async def test_rpa_executor_success():
    """Test RPAExecutor successfully executing a playbook on a mock Playwright Page."""
    mock_page = MagicMock()
    mock_locator = MagicMock()
    mock_locator.first.click = AsyncMock()
    mock_locator.first.hover = AsyncMock()
    mock_page.locator.return_value = mock_locator
    mock_page.fill = AsyncMock()
    mock_page.select_option = AsyncMock()
    mock_page.wait_for_selector = AsyncMock()
    mock_page.press = AsyncMock()
    mock_page.evaluate = AsyncMock()

    executor = RPAExecutor(mock_page)

    steps = [
        RPAStep(
            action=RPAActionType.CLICK, selector="#onetrust-accept", optional=True, wait_after_ms=0
        ),
        RPAStep(
            action=RPAActionType.FILL,
            selector="input[name='q']",
            value="search query",
            wait_after_ms=0,
        ),
        RPAStep(
            action=RPAActionType.SELECT, selector="select#currency", value="USD", wait_after_ms=0
        ),
        RPAStep(action=RPAActionType.WAIT_FOR, selector="#results-ready", wait_after_ms=0),
        RPAStep(
            action=RPAActionType.PRESS_KEY, selector="#search-box", value="Enter", wait_after_ms=0
        ),
        RPAStep(action=RPAActionType.HOVER, selector=".menu-item", wait_after_ms=0),
        RPAStep(action=RPAActionType.SCROLL, value="500", wait_after_ms=0),
        RPAStep(action=RPAActionType.SLEEP, value="50", wait_after_ms=0),
    ]

    result: RPAResult = await executor.execute_playbook(steps)
    assert result.success is True
    assert result.steps_total == 8
    assert result.steps_succeeded == 8
    assert result.steps_skipped_or_warned == 0
    assert len(result.logs) == 8


@pytest.mark.asyncio
async def test_rpa_executor_optional_failure():
    """Verify optional step failure is non-fatal and recorded as skipped."""
    mock_page = MagicMock()
    mock_locator = MagicMock()
    mock_locator.first.click = AsyncMock(side_effect=TimeoutError("Element not found"))
    mock_page.locator.return_value = mock_locator

    executor = RPAExecutor(mock_page)
    steps = [
        RPAStep(
            action=RPAActionType.CLICK,
            selector="#non-existent-banner",
            optional=True,
            description="Dismiss non-existent cookie banner",
            wait_after_ms=0,
        )
    ]

    result: RPAResult = await executor.execute_playbook(steps)
    assert result.success is True
    assert result.steps_total == 1
    assert result.steps_succeeded == 0
    assert result.steps_skipped_or_warned == 1
    assert "Optional step skipped" in result.logs[0]


@pytest.mark.asyncio
async def test_rpa_executor_mandatory_failure():
    """Verify mandatory step failure halts the playbook and sets success=False."""
    mock_page = MagicMock()
    mock_locator = MagicMock()
    mock_locator.first.click = AsyncMock(side_effect=RuntimeError("Target unclickable"))
    mock_page.locator.return_value = mock_locator

    executor = RPAExecutor(mock_page)
    steps = [
        RPAStep(
            action=RPAActionType.CLICK,
            selector="#required-checkout-btn",
            optional=False,
            description="Click checkout button",
            wait_after_ms=0,
        ),
        RPAStep(
            action=RPAActionType.CLICK,
            selector="#subsequent-step",
            optional=True,
            wait_after_ms=0,
        ),
    ]

    result: RPAResult = await executor.execute_playbook(steps)
    assert result.success is False
    assert result.steps_succeeded == 0
    assert "Failed" in result.logs[0]
    assert len(result.logs) == 1  # halted early


@pytest.mark.asyncio
async def test_rpa_executor_secret_env(monkeypatch):
    """Verify secret environment variable substitution in fill action."""
    monkeypatch.setenv("TEST_LOGIN_SECRET", "super_secret_123")
    mock_page = MagicMock()
    mock_page.fill = AsyncMock()

    executor = RPAExecutor(mock_page)
    step = RPAStep(
        action=RPAActionType.FILL,
        selector="#password",
        secret_env="TEST_LOGIN_SECRET",
        wait_after_ms=0,
    )

    success, msg = await executor.execute_step(step)
    assert success is True
    mock_page.fill.assert_called_once_with("#password", "super_secret_123", timeout=3500)


@pytest.mark.asyncio
async def test_api_rpa_presets_endpoint():
    """Test GET /api/v1/rpa/presets returns the preset dictionary."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/v1/rpa/presets")
        assert resp.status_code == 200
        data = resp.json()
        assert "auto_dismiss_cookies" in data
        assert "expand_accordions" in data
        assert "toggle_annual_pricing" in data


@pytest.mark.asyncio
async def test_api_rpa_generate_endpoint(monkeypatch):
    """Test POST /api/v1/rpa/generate with mocked OpenAI client response."""
    from ethical_crawler.config import get_settings

    settings = get_settings()
    settings.ai_api_key = "test-mock-key"

    fake_json_output = """
    {
      "steps": [
        {"action": "click", "selector": "button:has-text('Annual')", "optional": true, "wait_after_ms": 300, "description": "Toggle annual billing"},
        {"action": "wait_for", "selector": ".pricing-card", "optional": false, "timeout_ms": 3000, "description": "Wait for cards to update"}
      ],
      "notes": "Generated steps to toggle annual billing"
    }
    """

    class MockChoice:
        message = MagicMock(content=fake_json_output)

    class MockCompletion:
        choices = [MockChoice()]

    mock_client = MagicMock()
    mock_client.chat.completions.create = AsyncMock(return_value=MockCompletion())

    monkeypatch.setattr("openai.AsyncOpenAI", lambda *args, **kwargs: mock_client)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            "/api/v1/rpa/generate",
            json={
                "instruction": "Toggle annual pricing",
                "url": "https://saas.example.com/pricing",
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["steps"]) == 2
        assert data["steps"][0]["action"] == "click"
        assert data["steps"][0]["selector"] == "button:has-text('Annual')"
        assert data["notes"] == "Generated steps to toggle annual billing"
