"""NVIDIA Nemotron-Parse 2.0 Integration.

Specialized vision-language document parser for extracting text, tables,
bounding boxes, and reading-order markdown from document images and screenshots.
"""

import base64
from pathlib import Path
from typing import Any

import httpx

from ethical_crawler.config import get_settings


class NemotronParser:
    """Invokes NVIDIA Nemotron-Parse-2.0 for visual document and image parsing."""

    MODEL_ID = "nvidia/nemotron-parse-2.0"

    def __init__(self, api_key: str | None = None, base_url: str | None = None):
        settings = get_settings()
        self.api_key = api_key or settings.ai_api_key
        self.base_url = base_url or settings.ai_base_url

    def is_available(self) -> bool:
        return bool(self.api_key)

    async def parse_image(
        self,
        image_path_or_bytes: str | Path | bytes,
        task: str = "markdown_bbox",
    ) -> dict[str, Any]:
        """Parse an image (screenshot, PDF page, chart) using Nemotron-Parse 2.0.

        Tasks:
        - 'markdown_bbox': Extract text, layout classes, and bounding boxes
        - 'markdown_bbox_with_text_in_pictures': Include text inside embedded pictures
        - 'detection_only': Class and bounding box only
        """
        if not self.is_available():
            raise ValueError("NVIDIA API key not configured. Set CRAWLER_AI_API_KEY in .env")

        if isinstance(image_path_or_bytes, (str, Path)):
            with open(image_path_or_bytes, "rb") as f:
                img_bytes = f.read()
        else:
            img_bytes = image_path_or_bytes

        b64_img = base64.b64encode(img_bytes).decode("utf-8")

        prompt_token = f"<{task}>" if not task.startswith("<") else task

        payload = {
            "model": self.MODEL_ID,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt_token},
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:image/png;base64,{b64_img}"},
                        },
                    ],
                }
            ],
            "max_tokens": 4096,
            "temperature": 0.1,
        }

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(
                f"{self.base_url}/chat/completions",
                json=payload,
                headers=headers,
            )
            resp.raise_for_status()
            data = resp.json()

        content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
        return {
            "model": self.MODEL_ID,
            "raw_output": content,
            "usage": data.get("usage", {}),
        }
