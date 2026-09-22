"""AI-Native Structured Extractor.

Connects to NVIDIA NIM (https://integrate.api.nvidia.com/v1) or OpenAI-compatible
LLM APIs to extract structured data from cleaned Markdown with Pydantic validation.
"""

import asyncio
import json
import logging
import re
from typing import Any

import httpx
from openai import AsyncOpenAI

from ethical_crawler.config import get_settings
from ethical_crawler.types import (
    ArticleSchema,
    CompanyProfileSchema,
    FAQSchema,
    ProductSchema,
    StructuredExtractionResult,
)

logger = logging.getLogger("ethical_crawler.ai_extractor")

# Multi-tier fallback waterfall for maximum speed and 99.9% uptime resilience
FALLBACK_MODEL_CHAIN = [
    "deepseek-ai/deepseek-v4.1-flash",
    "meta/llama-3.2-11b-vision-instruct",
    "nvidia/nemotron-3.5-lightning-30b-a3b",
]


class AIExtractor:
    """Extracts structured schemas or custom answers from page markdown using LLMs."""

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        model: str | None = None,
    ):
        settings = get_settings()
        self.api_key = api_key or settings.ai_api_key
        self.base_url = base_url or settings.ai_base_url
        self.model = model or settings.ai_model
        self.client: AsyncOpenAI | None = None

        if self.api_key:
            self.client = AsyncOpenAI(
                api_key=self.api_key,
                base_url=self.base_url,
                timeout=httpx.Timeout(25.0, connect=8.0),
            )

    def is_available(self) -> bool:
        """Check if AI API key is configured."""
        return bool(self.client and self.api_key)

    async def extract_structured(
        self,
        markdown: str,
        url: str,
        schema_type: str = "article",
        custom_prompt: str | None = None,
    ) -> StructuredExtractionResult:
        """Extract structured data from page markdown based on schema type."""
        if not self.is_available():
            return StructuredExtractionResult(
                url=url,
                schema_type=schema_type,
                data={},
                model_used=self.model,
                confidence="LOW",
                notes=[
                    "AI API key not configured. Set CRAWLER_AI_API_KEY in .env or pass as argument."
                ],
            )

        # Scenario 8: Truncate markdown to fit context limits
        truncated_md = markdown[:12000] if markdown else ""

        system_prompt, user_prompt = self._build_prompts(schema_type, custom_prompt, truncated_md)

        # Build ordered candidate chain starting with user's requested model
        candidate_chain = [self.model]
        for fb in FALLBACK_MODEL_CHAIN:
            if fb not in candidate_chain:
                candidate_chain.append(fb)

        model_to_use = self.model
        content = "{}"
        tokens = None
        notes: list[str] = []
        last_error = None

        assert self.client is not None
        for attempt_idx, candidate in enumerate(candidate_chain):
            try:
                # Primary model gets up to 18s; fallbacks get up to 15s
                timeout_s = 18.0 if attempt_idx == 0 else 15.0
                logger.info(
                    "Attempting AI extraction with model %s (attempt %d/%d, timeout %.1fs)",
                    candidate,
                    attempt_idx + 1,
                    len(candidate_chain),
                    timeout_s,
                )

                response = await asyncio.wait_for(
                    self.client.chat.completions.create(
                        model=candidate,
                        messages=[
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_prompt},
                        ],
                        temperature=0.1,
                    ),
                    timeout=timeout_s,
                )
                raw_content = response.choices[0].message.content or ""
                if raw_content.strip():
                    content = raw_content
                    tokens = response.usage.total_tokens if response.usage else None
                    model_to_use = candidate
                    if candidate != self.model:
                        notes.append(
                            f"Auto-fallback applied: {candidate} (primary {self.model} timed out or failed)"
                        )
                    break
                else:
                    logger.warning(
                        "Model %s returned empty content, trying next fallback...", candidate
                    )
            except Exception as candidate_err:
                logger.warning(
                    "Model %s failed or timed out: %s. Trying next in chain...",
                    candidate,
                    candidate_err,
                )
                last_error = candidate_err
        else:
            return StructuredExtractionResult(
                url=url,
                schema_type=schema_type,
                data={},
                model_used=self.model,
                confidence="LOW",
                notes=[f"All AI models in fallback chain failed. Last error: {last_error}"],
            )

        parsed_data = self._clean_and_parse_json(content)

        # Validate against Pydantic models
        confidence = "HIGH"

        if schema_type in ("company_profile", "company"):
            try:
                validated = CompanyProfileSchema.model_validate(parsed_data)
                parsed_data = validated.model_dump()
            except Exception as val_err:
                confidence = "MEDIUM"
                notes.append(f"Validation warning: {val_err}")
        elif schema_type == "article":
            try:
                validated = ArticleSchema.model_validate(parsed_data)
                parsed_data = validated.model_dump()
            except Exception as val_err:
                confidence = "MEDIUM"
                notes.append(f"Validation warning: {val_err}")
        elif schema_type == "product":
            try:
                validated = ProductSchema.model_validate(parsed_data)
                parsed_data = validated.model_dump()
            except Exception as val_err:
                confidence = "MEDIUM"
                notes.append(f"Validation warning: {val_err}")
        elif schema_type == "faq":
            try:
                validated = FAQSchema.model_validate(parsed_data)
                parsed_data = validated.model_dump()
            except Exception as val_err:
                confidence = "MEDIUM"
                notes.append(f"Validation warning: {val_err}")

        return StructuredExtractionResult(
            url=url,
            schema_type=schema_type,
            data=parsed_data,
            model_used=model_to_use,
            tokens_used=tokens,
            confidence=confidence,
            notes=notes,
        )

    def _build_prompts(
        self,
        schema_type: str,
        custom_prompt: str | None,
        markdown: str,
    ) -> tuple[str, str]:
        """Build system and user prompts tailored to the schema mode."""
        custom_note = f"\nAdditional Instructions: {custom_prompt}" if custom_prompt else ""

        if schema_type in ("company_profile", "company"):
            system = (
                "You are a principal business intelligence analyst. Extract a comprehensive, structured "
                "company, product, and market intelligence profile as pure JSON."
            )
            user = (
                f"Analyze this company/website:\n```markdown\n{markdown}\n```\n"
                "Extract:\n"
                "1. company_name (str): The official company or product brand name\n"
                "2. headline_or_tagline (str|null): Main slogan or hero headline\n"
                "3. what_they_do (str): Comprehensive explanation of what the business does\n"
                "4. target_audience (list[str]): Exactly who this product/service is built for\n"
                "5. main_product (str): The primary or flagship solution/product\n"
                "6. products_and_features (list of {name, description, price, features}): All distinct offerings, tiers, or modules\n"
                "7. why_in_market (str): Why this exists, problem it solves, value proposition\n"
                "8. strategic_purpose (str): What it should be used for, ideal customer profile & deployment recommendations\n"
                f"9. key_differentiators (list[str]): Competitive advantages and unique selling points{custom_note}\n\n"
                "Output pure valid JSON ONLY without preamble or markdown fences."
            )
        elif schema_type == "product":
            system = "You are a precise data extraction engine. Extract e-commerce product details as pure JSON."
            user = (
                f"Extract product data from this page:\n```markdown\n{markdown}\n```\n"
                "Return JSON with keys: name (str), brand (str|null), price (float|null), "
                "currency (str|null), original_price (float|null), in_stock (bool|null), "
                "description (str|null), specifications (dict), rating (float|null), review_count (int|null). "
                f"{custom_note}\nOutput JSON ONLY without commentary."
            )
        elif schema_type == "faq":
            system = (
                "You are a data extraction engine. Extract FAQ question-answer pairs as pure JSON."
            )
            user = (
                f"Extract all FAQ items from this page:\n```markdown\n{markdown}\n```\n"
                'Return JSON in format: {"items": [{"question": "...", "answer": "...", "category": "..."}]}. '
                f"{custom_note}\nOutput JSON ONLY without commentary."
            )
        elif schema_type == "custom" or (
            custom_prompt and schema_type not in ("article", "product", "faq")
        ):
            system = "You are an expert AI data extraction engine. Follow the user's instructions and output pure structured JSON."
            instruction = (
                custom_prompt
                if custom_prompt
                else "Extract all key details, products, and core entities as structured JSON."
            )
            user = f"Page Content:\n```markdown\n{markdown}\n```\n\nTask Instructions:\n{instruction}\n\nOutput pure valid JSON ONLY without any surrounding commentary."
        else:  # article default
            system = "You are an expert content analyzer. Extract article metadata and key takeaways as pure JSON."
            user = (
                f"Extract article details from this page:\n```markdown\n{markdown}\n```\n"
                "Return JSON with keys: title (str), author (str|null), date (str|null), "
                "summary (str), key_points (list[str]), tags (list[str]). "
                f"{custom_note}\nOutput JSON ONLY without commentary."
            )

        return system, user

    def _clean_and_parse_json(self, content: str) -> dict[str, Any]:
        """Strip markdown code fences and parse JSON robustly."""
        content = content.strip()
        # Remove ```json ... ``` or ``` ... ```
        if content.startswith("```"):
            content = re.sub(r"^```(?:json)?\n?", "", content)
            content = re.sub(r"\n?```$", "", content)
            content = content.strip()

        try:
            return json.loads(content)
        except json.JSONDecodeError:
            # Try to locate first '{' and last '}'
            match = re.search(r"(\{.*\})", content, re.DOTALL)
            if match:
                try:
                    return json.loads(match.group(1))
                except Exception:
                    pass
            logger.warning("Failed to parse JSON from AI response: %s", content[:200])
            return {"raw_text": content}
