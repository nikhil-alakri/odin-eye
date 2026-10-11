"""Vision LLM Extractor for screenshots, charts, infographics, and visual tables."""

from __future__ import annotations

import base64
import io
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

import httpx
from pydantic import BaseModel, Field

from ethical_crawler.config import get_settings

logger = logging.getLogger(__name__)

try:
    from PIL import Image

    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False


class VisionExtractRequest(BaseModel):
    """Payload to trigger vision extraction on an image or screenshot."""
    image_base64: Optional[str] = None
    image_path: Optional[str] = None
    image_url: Optional[str] = None
    task: str = Field("chart_to_table", description="'chart_to_table', 'visual_summary', 'visual_pricing_matrix', or 'custom'")
    custom_prompt: Optional[str] = None
    model: Optional[str] = None
    api_key: Optional[str] = None


class VisionExtractResult(BaseModel):
    """Result of multimodal vision extraction."""
    task: str
    model_used: str
    extracted_text: str
    structured_data: Optional[Dict[str, Any]] = None
    tokens_used: Optional[int] = None
    error: Optional[str] = None


class VisionExtractor:
    """Multimodal Vision LLM connector utilizing NVIDIA NIM or OpenAI-compatible vision endpoints."""

    DEFAULT_VISION_MODEL = "meta/llama-3.2-90b-vision-instruct"

    TASK_PROMPTS = {
        "chart_to_table": (
            "Analyze this chart or diagram in detail. Extract all data points, series, categories, "
            "and numerical values. Format the extracted data into a clean, markdown table with appropriate headers. "
            "Include a brief 1-2 sentence summary of the key trend or takeaway under the table."
        ),
        "visual_summary": (
            "Analyze this image or web page screenshot. Provide a clear, executive markdown summary of the "
            "main headline, visual hierarchy, key offerings, and content elements visible in the image."
        ),
        "visual_pricing_matrix": (
            "Analyze the pricing table or subscription plans shown in this image. Extract each tier's name, "
            "monthly and annual price, features included, and limits into a clean markdown comparison table. "
            "Note which tier is marked as 'Most Popular' or 'Recommended' if applicable."
        ),
    }

    @classmethod
    def encode_image_file_to_base64(cls, file_path: str, max_dimension: int = 1200) -> str:
        """Read image file, resize/compress to ~50KB to maximize Vision LLM speed and prevent HTTP timeouts."""
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Image not found at {file_path}")

        if PIL_AVAILABLE:
            with Image.open(path) as img:
                img = img.convert("RGB")
                w, h = img.size
                if max(w, h) > max_dimension:
                    scale = max_dimension / max(w, h)
                    new_size = (int(w * scale), int(h * scale))
                    img = img.resize(new_size, Image.Resampling.LANCZOS)

                buffer = io.BytesIO()
                img.save(buffer, format="JPEG", quality=75, optimize=True)
                return base64.b64encode(buffer.getvalue()).decode("utf-8")
        else:
            with open(path, "rb") as f:
                return base64.b64encode(f.read()).decode("utf-8")

    @classmethod
    async def extract(
        cls,
        req: VisionExtractRequest,
    ) -> VisionExtractResult:
        """Submit image to Vision LLM and return structured analysis."""
        settings = get_settings()

        api_key = req.api_key if req.api_key is not None else settings.ai_api_key
        model = req.model or cls.DEFAULT_VISION_MODEL
        task = req.task or "chart_to_table"

        # Determine prompt
        prompt = req.custom_prompt or cls.TASK_PROMPTS.get(task, cls.TASK_PROMPTS["visual_summary"])

        # Acquire base64
        image_b64 = req.image_base64
        if not image_b64 and req.image_path:
            try:
                image_b64 = cls.encode_image_file_to_base64(req.image_path)
            except Exception as e:
                return VisionExtractResult(
                    task=task,
                    model_used=model,
                    extracted_text="",
                    error=f"Failed to read image file: {e}",
                )

        if not image_b64 and req.image_url:
            # Download image URL
            try:
                async with httpx.AsyncClient(timeout=15.0) as client:
                    resp = await client.get(req.image_url)
                    if resp.status_code == 200:
                        image_b64 = base64.b64encode(resp.content).decode("utf-8")
            except Exception as e:
                return VisionExtractResult(
                    task=task,
                    model_used=model,
                    extracted_text="",
                    error=f"Failed to download image URL: {e}",
                )

        if not image_b64:
            return VisionExtractResult(
                task=task,
                model_used=model,
                extracted_text="",
                error="No valid image payload provided (image_base64, image_path, or image_url required)",
            )

        # Offline fallback if API key is not configured
        if not api_key:
            return VisionExtractResult(
                task=task,
                model_used="offline-rule-based",
                extracted_text=(
                    f"### Visual Inspection Result ({task})\n\n"
                    f"*Image payload received ({len(image_b64) // 1024} KB JPEG).*\n\n"
                    f"To enable live AI multimodal vision extraction with `{model}`, "
                    f"configure `CRAWLER_AI_API_KEY` in `.env` with your NVIDIA NIM or OpenAI API key."
                ),
            )

        # Call OpenAI-compatible vision endpoint
        endpoint = f"{settings.ai_base_url.rstrip('/')}/chat/completions"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "model": model,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{image_b64}"
                            },
                        },
                    ],
                }
            ],
            "max_tokens": 1500,
            "temperature": 0.2,
        }

        try:
            async with httpx.AsyncClient(timeout=45.0) as client:
                res = await client.post(endpoint, headers=headers, json=payload)
                if res.status_code != 200:
                    return VisionExtractResult(
                        task=task,
                        model_used=model,
                        extracted_text="",
                        error=f"Vision API returned {res.status_code}: {res.text[:200]}",
                    )

                data = res.json()
                content = data["choices"][0]["message"]["content"]
                usage = data.get("usage", {})
                tokens_used = usage.get("total_tokens")

                return VisionExtractResult(
                    task=task,
                    model_used=model,
                    extracted_text=content,
                    tokens_used=tokens_used,
                )

        except Exception as exc:
            logger.error("Vision extraction error: %s", exc)
            return VisionExtractResult(
                task=task,
                model_used=model,
                extracted_text="",
                error=f"Vision extraction failed: {exc}",
            )
