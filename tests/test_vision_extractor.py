"""Unit tests for VisionExtractor."""

import pytest
from ethical_crawler.extractors.vision_extractor import (
    VisionExtractor,
    VisionExtractRequest,
    VisionExtractResult,
)


def test_vision_task_prompts():
    assert "chart_to_table" in VisionExtractor.TASK_PROMPTS
    assert "visual_summary" in VisionExtractor.TASK_PROMPTS
    assert "visual_pricing_matrix" in VisionExtractor.TASK_PROMPTS


@pytest.mark.asyncio
async def test_vision_extract_offline_fallback():
    # When no API key is provided, returns offline rule-based message without crashing
    req = VisionExtractRequest(
        image_base64="aW1hZ2VkYXRh",
        task="chart_to_table",
        api_key="",
    )
    res = await VisionExtractor.extract(req)
    assert res.model_used == "offline-rule-based"
    assert "Visual Inspection Result" in res.extracted_text
    assert res.error is None


@pytest.mark.asyncio
async def test_vision_extract_no_image():
    req = VisionExtractRequest(
        image_base64=None,
        image_path=None,
        image_url=None,
    )
    res = await VisionExtractor.extract(req)
    assert res.error is not None
    assert "No valid image payload" in res.error

