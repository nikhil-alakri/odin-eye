"""Multi-Competitor Market Intelligence Dossier & Central Guidebook Generator.

Leverages long-context and reasoning MoE models (such as Moonshot Kimi-k3 or GLM-5.3)
to synthesize multi-site competitive matrices, pricing comparisons, and executive dossiers
directly from crawled ChromaDB vector knowledge.
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Any

import httpx
from openai import AsyncOpenAI

from ethical_crawler import vector_store
from ethical_crawler.config import get_settings
from ethical_crawler.types import MarketDossierResult

logger = logging.getLogger(__name__)

FALLBACK_MODEL_CHAIN = [
    "deepseek-ai/deepseek-v4.1-flash",
    "meta/llama-3.2-11b-vision-instruct",
    "nvidia/nemotron-3.5-lightning-30b-a3b",
]


class DossierGenerator:
    """Synthesizes executive market dossiers and central guidebooks across crawled domains."""

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        default_model: str = "deepseek-ai/deepseek-v4.1-flash",
    ):
        settings = get_settings()
        self.api_key = api_key or settings.ai_api_key
        self.base_url = base_url or settings.ai_base_url
        self.default_model = default_model
        self.client: AsyncOpenAI | None = None

        if self.api_key:
            self.client = AsyncOpenAI(
                api_key=self.api_key,
                base_url=self.base_url,
                timeout=httpx.Timeout(30.0, connect=8.0),
            )

    def is_available(self) -> bool:
        """Check if LLM API client is ready."""
        return bool(self.client and self.api_key)

    async def generate_dossier(
        self,
        domains: list[str],
        model: str | None = None,
        custom_focus: str | None = None,
    ) -> MarketDossierResult:
        """Generate a structured multi-site market intelligence dossier."""
        chosen_model = model or self.default_model
        store = vector_store.get_vector_store()

        if not domains:
            # Fallback: get all available domains in store
            domains_summary = store.list_domains_summary(limit=50)
            domains = [d["domain"] for d in domains_summary[:5]]

        # Gather domain intelligence from ChromaDB
        domain_contexts: dict[str, dict[str, Any]] = {}
        for dom in domains:
            clean_dom = dom.lower().strip()
            records = store.collection.get(
                where={"domain": clean_dom},
                include=["documents", "metadatas"],
            )

            if not records or not records["ids"]:
                continue

            pages_data = []
            company_profiles = []

            for i in range(len(records["ids"])):
                meta = records["metadatas"][i]
                doc = records["documents"][i] if records["documents"] else ""
                title = meta.get("title", "Untitled")
                url = meta.get("url", "")

                # Check if structured AI profile exists
                ai_json = meta.get("ai_data_json")
                if ai_json and ai_json != "{}":
                    try:
                        parsed_ai = json.loads(ai_json)
                        company_profiles.append(parsed_ai)
                    except Exception:
                        pass

                # Store top snippet
                pages_data.append(
                    {
                        "title": title,
                        "url": url,
                        "snippet": doc[:1500],
                    }
                )

            domain_contexts[clean_dom] = {
                "page_count": len(records["ids"]),
                "company_profiles": company_profiles,
                "pages": pages_data[:6],  # top representative pages
            }

        if not domain_contexts:
            return MarketDossierResult(
                domains_analyzed=domains,
                model_used=chosen_model,
                dossier_markdown="# Market Intelligence Dossier\n\nNo crawled data found in ChromaDB for the specified domains. Please crawl the websites first.",
                generated_at=datetime.utcnow(),
            )

        # Build context prompt
        context_blocks = []
        for dom, data in domain_contexts.items():
            block = f"### Domain: {dom} ({data['page_count']} pages crawled)\n"
            if data["company_profiles"]:
                block += f"Structured Intelligence:\n```json\n{json.dumps(data['company_profiles'][0], indent=2)[:3000]}\n```\n"
            block += "Sample Page Extracts:\n"
            for p in data["pages"]:
                block += f"- **{p['title']}** ({p['url']}):\n{p['snippet'][:400]}...\n\n"
            context_blocks.append(block)

        aggregated_context = "\n---\n".join(context_blocks)

        focus_instruction = f"\nSpecial User Focus Area: {custom_focus}\n" if custom_focus else ""

        system_prompt = (
            "You are a principal market intelligence strategist and enterprise technology analyst. "
            "Provide the final comprehensive Executive Market Intelligence Dossier and Guidebook "
            "directly in clean Markdown format based on the verified website crawl data without scratchpad."
        )

        user_prompt = f"""Generate an Executive Market Dossier comparing and analyzing the following companies/domains: {", ".join(domain_contexts.keys())}.

{focus_instruction}
CRAWLED KNOWLEDGE CONTEXT:
{aggregated_context}

DOCUMENT STRUCTURE REQUIREMENTS:
Please format your response in professional Markdown with the following clear sections:
# 📊 Executive Market Intelligence Dossier & Guidebook
**Date:** {datetime.utcnow().strftime("%d-%b-%Y")} | **Domains Analyzed:** {", ".join(domain_contexts.keys())}

## 1. Executive Summary & Market Landscape
High-level overview of this market category, industry dynamics, and the core problems these platforms solve.

## 2. Competitive Comparison Matrix
Create a detailed Markdown comparison table with columns:
| Company / Domain | Core Product | Primary ICP / Target Audience | Key Differentiator | Pricing Model / Starting Tier |

## 3. Product & Feature-by-Feature Breakdown
Analyze key capabilities, modules, and technological advantages of each company. Highlight proprietary or unique features.

## 4. Pricing, Packaging & Commercial Strategy
Compare business models, tiers, transparency, and value-for-money across the platforms.

## 5. Strategic Gaps, Market Opportunities & Takeaways
Unmet customer needs, competitive weaknesses, and actionable recommendations.

Tone: Objective, data-driven, strategic, and polished. Respond directly with the Markdown report.
"""

        # If LLM is not available, provide structured fallback synthesis
        if not self.is_available():
            fallback_md = self._generate_offline_fallback(domain_contexts)
            return MarketDossierResult(
                domains_analyzed=list(domain_contexts.keys()),
                model_used="offline-rule-based",
                dossier_markdown=fallback_md,
                generated_at=datetime.utcnow(),
            )

        # Build candidate chain starting with chosen model
        candidate_chain = [chosen_model]
        for fb in FALLBACK_MODEL_CHAIN:
            if fb not in candidate_chain:
                candidate_chain.append(fb)

        dossier_content = ""
        model_used = chosen_model

        assert self.client is not None
        for attempt_idx, candidate in enumerate(candidate_chain):
            try:
                # Primary gets 22s cutoff; fallbacks get 20s
                timeout_s = 22.0 if attempt_idx == 0 else 20.0
                logger.info(
                    "Attempting dossier synthesis with model %s (attempt %d/%d, timeout %.1fs)",
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
                        temperature=0.2,
                        max_tokens=4000,
                    ),
                    timeout=timeout_s,
                )
                raw_text = response.choices[0].message.content or ""
                if not raw_text.strip() and hasattr(
                    response.choices[0].message, "reasoning_content"
                ):
                    raw_text = getattr(response.choices[0].message, "reasoning_content", "") or ""

                if raw_text.strip():
                    dossier_content = raw_text
                    model_used = candidate
                    break
                else:
                    logger.warning(
                        "Dossier model %s returned empty content, trying next fallback...",
                        candidate,
                    )
            except Exception as exc:
                logger.warning(
                    "Dossier model %s failed or timed out: %s. Trying next in chain...",
                    candidate,
                    exc,
                )
        else:
            logger.error("All models in dossier fallback chain failed. Using rule-based fallback.")
            fallback_md = self._generate_offline_fallback(
                domain_contexts, error="All LLM fallback models timed out or failed"
            )
            return MarketDossierResult(
                domains_analyzed=list(domain_contexts.keys()),
                model_used="offline-rule-based",
                dossier_markdown=fallback_md,
                generated_at=datetime.utcnow(),
            )

        return MarketDossierResult(
            domains_analyzed=list(domain_contexts.keys()),
            model_used=model_used,
            dossier_markdown=dossier_content,
            generated_at=datetime.utcnow(),
        )

    def _generate_offline_fallback(
        self,
        domain_contexts: dict[str, dict[str, Any]],
        error: str | None = None,
    ) -> str:
        """Generate formatted tabular summary when AI API is unavailable."""
        err_banner = f"> [!WARNING] AI Model Error: {error}\n\n" if error else ""
        lines = [
            "# 📊 Executive Market Intelligence Dossier",
            f"{err_banner}*Synthesized from local ChromaDB vector knowledge across {len(domain_contexts)} domains.*\n",
            "## 1. Domain Coverage Summary\n",
            "| Domain | Pages Stored | AI Profile Available | Key Themes / Focus |",
            "| :--- | :--- | :--- | :--- |",
        ]

        for dom, data in domain_contexts.items():
            has_ai = "Yes (Company Profile)" if data["company_profiles"] else "Raw Content"
            sample_titles = ", ".join([p["title"] for p in data["pages"][:3]])
            lines.append(
                f"| **{dom}** | {data['page_count']} | {has_ai} | {sample_titles[:60]}... |"
            )

        lines.append("\n## 2. Stored Profile Extracts\n")
        for dom, data in domain_contexts.items():
            lines.append(f"### 🏢 {dom}")
            if data["company_profiles"]:
                cp = data["company_profiles"][0]
                lines.append(f"- **What they do:** {cp.get('what_they_do', 'N/A')}")
                lines.append(f"- **Main Product:** {cp.get('main_product', 'N/A')}")
                lines.append(f"- **Why in market:** {cp.get('why_in_market', 'N/A')}")
            else:
                for p in data["pages"][:2]:
                    lines.append(f"- **{p['title']}**: {p['snippet'][:200]}...")
            lines.append("")

        return "\n".join(lines)
