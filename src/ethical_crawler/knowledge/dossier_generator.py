"""Multi-Competitor Market Intelligence Dossier & Central Guidebook Generator.

Leverages long-context and reasoning MoE models (such as Moonshot Kimi-k3 or GLM-5.3)
to synthesize multi-site competitive matrices, pricing comparisons, and executive dossiers
directly from crawled ChromaDB vector knowledge.
"""

import asyncio
import json
import logging
import re
from datetime import datetime
from typing import Any
from urllib.parse import urlparse

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

DOSSIER_TEMPLATES: dict[str, dict[str, str]] = {
    "complete_site_report": {
        "title": "Complete Website Report",
        "role": (
            "You are a senior web analyst producing a thorough, reader-friendly report of "
            "everything important found on the crawled website(s)."
        ),
        "structure": """
# Complete Website Intelligence Report
**Date:** {date} | **Scope:** {domains}

## 1. Site Overview & Purpose
What the site is, who it serves, and the core value proposition.

## 2. Key Pages & Content Map
Summarize major sections, products/services, and notable URLs from the crawl.

## 3. Offerings & Messaging
Products, features, pricing signals, and how the brand positions itself.

## 4. Trust, Contact & Company Signals
About, team, contact, legal, social proof, and credibility cues present in the crawl.

## 5. Content Themes & Gaps
Recurring topics, strengths of the site content, and obvious missing or weak areas.

## 6. Executive Takeaways
Bullet-point summary a stakeholder can act on.
""",
    },
    "market_research": {
        "title": "Market Research Brief",
        "role": (
            "You are a market research analyst summarizing category dynamics and positioning "
            "from the crawled site evidence."
        ),
        "structure": """
# Market Research Brief
**Date:** {date} | **Domains:** {domains}

## 1. Market Category & Problem Space
## 2. Target Customers & Use Cases
## 3. Competitive Landscape (from crawl evidence)
## 4. Pricing & Business Model Signals
## 5. Trends, Opportunities & Risks
## 6. Strategic Recommendations
""",
    },
    "highlights_best": {
        "title": "Best of This Website",
        "role": (
            "You are a product evangelist highlighting the strongest, most distinctive "
            "aspects of the website based only on crawled content."
        ),
        "structure": """
# Best Things on This Website
**Date:** {date} | **Domains:** {domains}

## 1. Top Strengths & Differentiators
## 2. Standout Features & Content
## 3. Best Pages to Read First (with URLs)
## 4. Why Someone Should Care
## 5. Quick Wins for Visitors / Buyers
""",
    },
    "technical_audit": {
        "title": "Content & Structure Audit",
        "role": (
            "You are a technical content auditor reviewing crawl data for structure, "
            "clarity, and information architecture (not live performance testing)."
        ),
        "structure": """
# Website Content & Structure Audit
**Date:** {date} | **Domains:** {domains}

## 1. Information Architecture (sections & navigation themes)
## 2. Content Quality & Consistency
## 3. Messaging Clarity
## 4. SEO-relevant signals visible in text (topics, headings themes)
## 5. Issues & Improvement Opportunities
## 6. Prioritized Action List
""",
    },
    "competitive_matrix": {
        "title": "Competitive Comparison Matrix",
        "role": (
            "You are a principal market intelligence strategist comparing multiple "
            "companies from verified crawl data."
        ),
        "structure": """
# Competitive Intelligence Dossier
**Date:** {date} | **Domains Analyzed:** {domains}

## 1. Executive Summary & Market Landscape
## 2. Competitive Comparison Matrix
| Company / Domain | Core Product | Target Audience | Key Differentiator | Pricing Model |
## 3. Product & Feature Breakdown
## 4. Pricing, Packaging & Commercial Strategy
## 5. Strategic Gaps & Opportunities
""",
    },
}


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
                timeout=httpx.Timeout(90.0, connect=10.0),
            )

    def is_available(self) -> bool:
        """Check if LLM API client is ready."""
        return bool(self.client and self.api_key)

    async def generate_dossier(
        self,
        domains: list[str],
        model: str | None = None,
        custom_focus: str | None = None,
        dossier_type: str = "complete_site_report",
    ) -> MarketDossierResult:
        """Generate a structured intelligence dossier from crawled ChromaDB knowledge."""
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
                        "snippet": (doc or "")[:900],
                    }
                )

            domain_contexts[clean_dom] = {
                "page_count": len(records["ids"]),
                "company_profiles": company_profiles,
                "pages": pages_data[:8],
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
                block += (
                    "Structured Intelligence:\n```json\n"
                    f"{json.dumps(data['company_profiles'][0], indent=2)[:1800]}\n```\n"
                )
            block += "Sample Page Extracts:\n"
            for p in data["pages"][:4]:
                block += f"- **{p['title']}** ({p['url']}):\n{p['snippet'][:350]}...\n\n"
            context_blocks.append(block)

        aggregated_context = "\n---\n".join(context_blocks)

        focus_instruction = f"\nSpecial User Focus Area: {custom_focus}\n" if custom_focus else ""

        template_key = dossier_type if dossier_type in DOSSIER_TEMPLATES else "complete_site_report"
        template = DOSSIER_TEMPLATES[template_key]
        domain_list = ", ".join(domain_contexts.keys())
        date_str = datetime.utcnow().strftime("%d-%b-%Y")
        structure_block = template["structure"].format(date=date_str, domains=domain_list)

        scope_note = ""
        if len(domain_contexts) == 1 and template_key == "complete_site_report":
            scope_note = (
                "\nFocus on a single-domain deep dive: treat this as a complete report of "
                "the website, not a multi-competitor comparison.\n"
            )
        elif template_key == "competitive_matrix" and len(domain_contexts) < 2:
            scope_note = (
                "\nOnly one domain is available; compare internal product lines/pages and "
                "note that external competitors were not in the crawl set.\n"
            )

        system_prompt = (
            f"{template['role']} "
            "Respond only in clean Markdown based on verified crawl data—no scratchpad or preamble."
        )

        user_prompt = f"""Report type: {template['title']}
Analyze the following domain(s): {domain_list}.
{scope_note}{focus_instruction}
CRAWLED KNOWLEDGE CONTEXT:
{aggregated_context}

DOCUMENT STRUCTURE (follow this outline):
{structure_block}

Tone: Objective, clear, and useful. Respond directly with the Markdown report.
"""

        # If LLM is not available, provide structured fallback synthesis
        if not self.is_available():
            fallback_md = self._generate_offline_fallback(
                domain_contexts, dossier_type=template_key, custom_focus=custom_focus
            )
            return MarketDossierResult(
                domains_analyzed=list(domain_contexts.keys()),
                model_used="offline-rule-based",
                dossier_markdown=fallback_md,
                generated_at=datetime.utcnow(),
            )

        # Build candidate chain starting with chosen model
        # One primary attempt, then a single fast fallback. Chaining four
        # short timeouts produced a thin offline report after ~60s.
        candidate_chain = [chosen_model]
        fast_fallback = FALLBACK_MODEL_CHAIN[0]
        if fast_fallback not in candidate_chain:
            candidate_chain.append(fast_fallback)

        dossier_content = ""
        model_used = chosen_model

        assert self.client is not None
        for attempt_idx, candidate in enumerate(candidate_chain):
            try:
                timeout_s = 75.0 if attempt_idx == 0 else 45.0
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
                domain_contexts,
                error="The language model timed out, so this report was built from stored crawl data.",
                dossier_type=template_key,
                custom_focus=custom_focus,
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

    @staticmethod
    def _as_text(value: Any) -> str:
        if value is None:
            return ""
        if isinstance(value, str):
            return value.strip()
        if isinstance(value, list):
            parts = [DossierGenerator._as_text(v) for v in value if DossierGenerator._as_text(v)]
            return "; ".join(parts)
        if isinstance(value, dict):
            bits = []
            for key, val in value.items():
                text = DossierGenerator._as_text(val)
                if text:
                    bits.append(f"{key}: {text}")
            return "; ".join(bits)
        return str(value).strip()

    @staticmethod
    def _best_profile(profiles: list[dict[str, Any]]) -> dict[str, Any]:
        """Prefer a company profile over a stray pricing or product card."""
        if not profiles:
            return {}
        ranked = sorted(
            profiles,
            key=lambda p: (
                bool(p.get("what_they_do")),
                bool(p.get("company_name")),
                bool(p.get("main_product")),
                len(p),
            ),
            reverse=True,
        )
        return ranked[0]

    @staticmethod
    def _clean_plain(text: str, limit: int = 220) -> str:
        text = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", text)
        text = re.sub(r"[#*_`>]+", " ", text)
        text = text.replace("₹", "Rs.")
        text = " ".join(text.split())
        if len(text) > limit:
            text = text[: limit - 1].rsplit(" ", 1)[0] + "..."
        return text

    def _profile_bullets(self, profile: dict[str, Any]) -> list[str]:
        """Short, labeled facts a reader can scan. Skip raw JSON dumps."""
        lines: list[str] = []
        labels = [
            ("company_name", "Company"),
            ("headline_or_tagline", "Headline"),
            ("what_they_do", "What they do"),
            ("main_product", "Main product"),
            ("target_audience", "Audience"),
            ("why_in_market", "Why they exist"),
            ("strategic_purpose", "Best use"),
        ]
        for key, label in labels:
            value = profile.get(key)
            if key == "target_audience" and isinstance(value, list):
                value = value[:4]
            limit = 280 if key in {"what_they_do", "why_in_market", "strategic_purpose"} else 160
            text = self._clean_plain(self._as_text(value), limit)
            if text and text.lower() not in {"n/a", "none", "null"}:
                lines.append(f"- **{label}:** {text}")

        diffs = profile.get("key_differentiators") or []
        if isinstance(diffs, list) and diffs:
            lines.append("- **Stands out for:**")
            for item in diffs[:5]:
                text = self._clean_plain(self._as_text(item), 140)
                if text:
                    lines.append(f"  - {text}")

        products = profile.get("products_and_features") or []
        if isinstance(products, list) and products:
            lines.append("- **Products:**")
            for item in products[:6]:
                if isinstance(item, dict):
                    name = self._clean_plain(self._as_text(item.get("name")), 80)
                    desc = self._clean_plain(self._as_text(item.get("description")), 140)
                    if name and desc:
                        lines.append(f"  - {name}: {desc}")
                    elif name:
                        lines.append(f"  - {name}")
                else:
                    text = self._clean_plain(self._as_text(item), 140)
                    if text:
                        lines.append(f"  - {text}")
        return lines

    def _product_lines(self, profiles: list[dict[str, Any]]) -> list[str]:
        """Turn product-card extractions into a short offerings list."""
        lines = ["- **Offerings found on the site:**"]
        seen: set[str] = set()
        for profile in profiles:
            if profile.get("what_they_do"):
                continue
            name = self._clean_plain(self._as_text(profile.get("name")), 80)
            desc = self._clean_plain(self._as_text(profile.get("description")), 140)
            if not name or name.lower() in seen:
                continue
            seen.add(name.lower())
            detail = f": {desc}" if desc and desc.lower() != name.lower() else ""
            lines.append(f"  - {name}{detail}")
            if len(seen) >= 6:
                break
        return lines if len(lines) > 1 else []

    def _useful_pages(self, pages: list[dict[str, Any]]) -> list[dict[str, str]]:
        skip = (
            "/privacy",
            "/terms",
            "/login",
            "/admin",
            "/refund",
            "/signup",
            "/register",
            "/glossary",
            "/blog",
            "/connect",
            "/contact",
            "/download",
        )

        def rank(url: str) -> int:
            path = urlparse(url).path.rstrip("/") or "/"
            if path == "/":
                return 0
            if any(part in path for part in ("/feature", "/pricing", "/about", "/our-story")):
                return 1
            return 4

        ranked = sorted(pages, key=lambda page: rank(page.get("url") or ""))
        kept: list[dict[str, str]] = []
        for page in ranked:
            url = page.get("url") or ""
            path = urlparse(url).path.lower()
            if any(part in path for part in skip):
                continue
            title = self._clean_plain(page.get("title") or "Untitled", 90)
            snippet = self._clean_plain(page.get("snippet") or "", 160)
            if len(snippet) < 40:
                continue
            kept.append({"title": title, "url": url, "snippet": snippet})
            if len(kept) >= 2:
                break
        return kept

    def _generate_offline_fallback(
        self,
        domain_contexts: dict[str, dict[str, Any]],
        error: str | None = None,
        dossier_type: str = "complete_site_report",
        custom_focus: str | None = None,
    ) -> str:
        """Build a sectioned report from stored pages when the LLM is unavailable."""
        template = DOSSIER_TEMPLATES.get(dossier_type, DOSSIER_TEMPLATES["complete_site_report"])
        domains = list(domain_contexts.keys())
        date_str = datetime.utcnow().strftime("%d-%b-%Y")
        notice = (
            f"> Note: {error} Sections below are assembled from crawled pages and stored profiles.\n\n"
            if error
            else ""
        )
        focus = f"**Extra focus:** {custom_focus}\n\n" if custom_focus else ""

        lines = [
            f"# {template['title']}",
            f"**Date:** {date_str} | **Domains:** {', '.join(domains)}",
            "",
            notice + focus,
            "## 1. Coverage",
            "",
            "| Domain | Pages stored | Structured profile |",
            "| :--- | :--- | :--- |",
        ]
        for dom, data in domain_contexts.items():
            profile = "Yes" if data["company_profiles"] else "Pages only"
            lines.append(f"| {dom} | {data['page_count']} | {profile} |")

        lines.extend(["", "## 2. Site-by-site intelligence", ""])
        for dom, data in domain_contexts.items():
            lines.append(f"### {dom}")
            lines.append(f"*{data['page_count']} pages in the knowledge store.*")
            lines.append("")
            profile = self._best_profile(data["company_profiles"])
            if profile.get("what_they_do") or profile.get("company_name"):
                lines.extend(self._profile_bullets(profile))
            else:
                product_lines = self._product_lines(data["company_profiles"])
                if product_lines:
                    lines.extend(product_lines)
                else:
                    home = next(
                        (
                            page
                            for page in data["pages"]
                            if (urlparse(page.get("url") or "").path.rstrip("/") or "/") == "/"
                        ),
                        data["pages"][0] if data["pages"] else None,
                    )
                    if home:
                        lines.append(
                            "- **From the homepage:** "
                            + self._clean_plain(home.get("snippet") or home.get("title") or "", 240)
                        )
                    else:
                        lines.append("- No readable company summary was stored for this domain.")
            useful = self._useful_pages(data["pages"])
            if useful:
                lines.append("")
                lines.append("**Pages worth reading**")
                for page in useful:
                    lines.append(f"- **{page['title']}**")
                    lines.append(f"  {page['url']}")
                    lines.append(f"  {page['snippet']}")
            lines.append("")

        lines.extend(
            [
                "## 3. Offerings and positioning",
                "",
            ]
        )
        for dom, data in domain_contexts.items():
            profile = self._best_profile(data["company_profiles"])
            product = self._clean_plain(self._as_text(profile.get("main_product")), 120) or "See the site notes above"
            why = self._clean_plain(
                self._as_text(profile.get("why_in_market")) or self._as_text(profile.get("what_they_do")),
                220,
            )
            audience = self._clean_plain(self._as_text(profile.get("target_audience")), 160)
            lines.append(f"- **{dom}:** {product}")
            if why:
                lines.append(f"  - Problem / purpose: {why[:500]}")
            if audience:
                lines.append(f"  - Audience: {audience[:300]}")

        lines.extend(["", "## 4. Cross-site themes", ""])
        if len(domain_contexts) == 1:
            lines.append(
                "Single-domain report. Themes come from the pages listed above rather than a competitor set."
            )
        else:
            lines.append(
                f"This set covers {len(domain_contexts)} domains. Compare products, audiences, "
                "and delivery models in section 2 before treating any one site as the category leader."
            )
            photography_hits = [
                dom
                for dom, data in domain_contexts.items()
                if "photo" in json.dumps(data).lower()
            ]
            if len(photography_hits) >= 2:
                lines.append(
                    f"- Photography / studio workflow language appears on: {', '.join(photography_hits)}."
                )

        lines.extend(
            [
                "",
                "## 5. Takeaways",
                "",
                "- Use each domain block in section 2 as the source of truth for that website.",
                "- Prefer structured profile bullets when present; otherwise use the key-page snippets.",
                "- Re-run with fewer domains or a faster model if you want a narrative written by the language model.",
                "",
            ]
        )
        return "\n".join(lines)
