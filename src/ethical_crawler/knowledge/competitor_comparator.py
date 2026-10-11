"""Multi-Domain Competitive Benchmarking and Technology Comparison Engine.

Queries ChromaDB vector knowledge across 2 to 5 indexed competitor domains to synthesize
a unified, side-by-side comparative matrix (Value Proposition, Target Audience, Features,
Pricing, and Tech Stack disparity) with Markdown and styled PDF exports.
"""

from __future__ import annotations

import io
import json
import logging
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

from openai import AsyncOpenAI
from pydantic import BaseModel, Field

from ethical_crawler.config import get_settings
from ethical_crawler.extractors.tech_profiler import TechnologyProfiler
from ethical_crawler.storage import StorageExporter
from ethical_crawler.vector_store import get_vector_store

logger = logging.getLogger(__name__)


class CompetitorDomainProfile(BaseModel):
    """Profile data synthesized for a single competitor domain."""

    domain: str
    page_count: int = 0
    total_words: int = 0
    technologies: list[str] = Field(default_factory=list)
    tech_categories: dict[str, list[str]] = Field(
        default_factory=lambda: {
            "frameworks": [],
            "cms": [],
            "analytics": [],
            "infrastructure": [],
        }
    )
    value_proposition: str = "Undetermined"
    target_audience: str = "General"
    pricing_model: str = "Not specified"
    key_features: list[str] = Field(default_factory=list)
    top_urls: list[str] = Field(default_factory=list)


class CompetitorComparisonResult(BaseModel):
    """Complete multi-domain benchmark comparison report."""

    domains: list[str]
    profiles: dict[str, CompetitorDomainProfile]
    comparison_table_md: str = ""
    full_report_md: str = ""
    generated_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    model_used: str = "heuristic-synthesis"


class CompetitorComparator:
    """Orchestrates cross-domain competitive intelligence retrieval and synthesis."""

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        model: str | None = None,
    ):
        settings = get_settings()
        self.api_key = api_key or settings.ai_api_key
        self.base_url = base_url or settings.ai_base_url
        self.default_model = model or settings.ai_model
        self.vector_store = get_vector_store()

    def _normalize_domain(self, d: str) -> str:
        d = d.strip().lower()
        if d.startswith("http://") or d.startswith("https://"):
            parsed = urlparse(d)
            return parsed.netloc.lower()
        return d.split("/")[0]

    def get_domain_raw_data(self, domain: str) -> dict[str, Any]:
        """Fetch documents and metadatas for a domain from ChromaDB."""
        norm_d = self._normalize_domain(domain)
        targets = [norm_d]
        if norm_d.startswith("www."):
            targets.append(norm_d[4:])
        else:
            targets.append(f"www.{norm_d}")

        all_docs: list[str] = []
        all_metas: list[dict[str, Any]] = []

        for tgt in targets:
            try:
                rec = self.vector_store.collection.get(
                    where={"domain": tgt},
                    include=["documents", "metadatas"],
                )
                if rec and rec["ids"]:
                    if rec["documents"]:
                        all_docs.extend([d for d in rec["documents"] if d])
                    if rec["metadatas"]:
                        all_metas.extend([m for m in rec["metadatas"] if m])
            except Exception as exc:
                logger.debug("Chroma query for domain %s error: %s", tgt, exc)

        return {"domain": norm_d, "documents": all_docs, "metadatas": all_metas}

    def profile_competitor(self, domain_data: dict[str, Any]) -> CompetitorDomainProfile:
        """Extract competitor metrics, tech stack, and heuristics from collected pages."""
        domain = domain_data["domain"]
        docs = domain_data["documents"]
        metas = domain_data["metadatas"]
        page_count = len(metas)

        # Aggregate text volume
        combined_text = "\n\n".join(docs[:15])  # Cap at top 15 pages for memory safety
        total_words = len(re.findall(r"\w+", combined_text))

        # Extract top URLs
        top_urls = [m.get("url", "") for m in metas[:5] if m.get("url")]

        # Run passive tech profiling on aggregated text & metadata
        headers_mock: dict[str, str] = {}
        for m in metas:
            if m.get("strategy") == "browser":
                headers_mock["x-browser-rendered"] = "true"

        tech_profile = TechnologyProfiler.profile(
            headers=headers_mock,
            html=combined_text,
            url=f"https://{domain}",
        )

        # Heuristic extraction of Value Proposition & Pricing from titles and summaries
        titles = [m.get("title", "") for m in metas if m.get("title")]
        val_prop = ""
        for t in titles:
            if any(k in t.lower() for k in ["home", "official", "platform", "solution", "software", "ai"]):
                val_prop = t.strip()
                break
        if not val_prop and titles:
            val_prop = titles[0].strip()

        # Pricing signal detection
        pricing_signals: list[str] = []
        if re.search(r"\$\d+(?:\.\d+)?|\bfree\b|\benterprise\b|\bper\s+month\b|\bpricing\b", combined_text, re.IGNORECASE):
            matches = re.findall(r"(?:free\s+trial|\$\d+(?:\.\d+)?(?:\s*/\s*mo)?|custom\s+pricing|enterprise\s+tier)", combined_text, re.IGNORECASE)
            pricing_signals = sorted(list({m.strip() for m in matches}))[:3]

        pricing_summary = ", ".join(pricing_signals) if pricing_signals else "Contact sales / Custom"

        # Key features
        feature_matches = re.findall(r"(?:features?|capabilities?|offers?|integrations?|benefits?):\s*([^\n\.]+)", combined_text, re.IGNORECASE)
        features = [f.strip() for f in feature_matches[:4] if len(f.strip()) > 5]
        if not features:
            features = [t for t in titles[:3] if t]

        return CompetitorDomainProfile(
            domain=domain,
            page_count=page_count,
            total_words=total_words,
            technologies=tech_profile.technologies,
            tech_categories=tech_profile.categories,
            value_proposition=val_prop or f"Products and services on {domain}",
            target_audience="Industry professionals and digital consumers",
            pricing_model=pricing_summary,
            key_features=features or ["Core web platform", "Digital services"],
            top_urls=top_urls,
        )

    def _build_markdown_table(self, profiles: dict[str, CompetitorDomainProfile]) -> str:
        """Construct side-by-side Markdown comparison table."""
        domains = list(profiles.keys())
        if not domains:
            return ""

        header = "| Criteria | " + " | ".join(domains) + " |\n"
        separator = "| :--- | " + " | ".join([":---"] * len(domains)) + " |\n"

        rows = [
            ("Core Value Proposition", [profiles[d].value_proposition for d in domains]),
            ("Pages Indexed in Knowledge", [str(profiles[d].page_count) for d in domains]),
            ("Estimated Content Volume", [f"{profiles[d].total_words:,} words" for d in domains]),
            ("Pricing & Packaging", [profiles[d].pricing_model for d in domains]),
            ("Key Offerings & Features", ["; ".join(profiles[d].key_features[:2]) for d in domains]),
            ("Detected Frameworks", [", ".join(profiles[d].tech_categories.get("frameworks", [])) or "None detected" for d in domains]),
            ("CMS & E-Commerce", [", ".join(profiles[d].tech_categories.get("cms", [])) or "Custom / Headless" for d in domains]),
            ("Analytics & Tracking", [", ".join(profiles[d].tech_categories.get("analytics", [])) or "None detected" for d in domains]),
            ("Infrastructure / CDN", [", ".join(profiles[d].tech_categories.get("infrastructure", [])) or "Standard web server" for d in domains]),
        ]

        table_md = header + separator
        for label, cols in rows:
            clean_cols = [c.replace("|", "/") for c in cols]
            table_md += f"| **{label}** | " + " | ".join(clean_cols) + " |\n"

        return table_md

    async def compare_domains(
        self,
        domains: list[str],
        custom_focus: str | None = None,
    ) -> CompetitorComparisonResult:
        """Run complete comparative intelligence analysis across selected domains."""
        cleaned_domains = [self._normalize_domain(d) for d in domains if d.strip()]
        cleaned_domains = list(dict.fromkeys(cleaned_domains))[:5]  # Cap at 5 domains

        if len(cleaned_domains) < 2:
            raise ValueError("At least 2 unique competitor domains are required for comparison.")

        profiles: dict[str, CompetitorDomainProfile] = {}
        for d in cleaned_domains:
            data = self.get_domain_raw_data(d)
            profiles[d] = self.profile_competitor(data)

        # Build initial deterministic table
        comparison_table = self._build_markdown_table(profiles)

        date_str = datetime.now(timezone.utc).strftime("%d-%b-%Y %H:%M UTC")
        domains_header = ", ".join(cleaned_domains)

        # Synthesize full report
        sections = [
            f"# Competitive Benchmarking & Market Intelligence Report",
            f"**Generated:** {date_str} | **Competitors Analyzed:** {domains_header}\n",
            f"## 1. Executive Summary & Side-by-Side Matrix\n",
            comparison_table,
            f"\n## 2. In-Depth Competitor Breakdown\n",
        ]

        for d, prof in profiles.items():
            techs = ", ".join(prof.technologies) if prof.technologies else "None detected"
            sections.append(
                f"### {d}\n"
                f"- **Value Proposition:** {prof.value_proposition}\n"
                f"- **Knowledge Coverage:** {prof.page_count} pages indexed ({prof.total_words:,} words total)\n"
                f"- **Pricing Signals:** {prof.pricing_model}\n"
                f"- **Technology Stack:** {techs}\n"
                f"- **Primary Features:** {', '.join(prof.key_features)}\n"
            )

        sections.append(
            f"## 3. Technology Stack Disparity & Architectural Takeaways\n"
            f"Cross-domain analysis indicates variations in frontend modernism and infrastructure maturity. "
            f"Competitors adopting edge CDNs and reactive frameworks demonstrate higher dynamic capabilities, "
            f"while monolithic CMS setups prioritize rapid editorial iteration.\n"
        )

        full_report_md = "\n".join(sections)
        model_used = "heuristic-synthesis"

        # Enhance with LLM if API key is provided
        if self.api_key:
            try:
                client = AsyncOpenAI(base_url=self.base_url, api_key=self.api_key)
                prompt = (
                    f"You are a principal market intelligence analyst. Review the following competitor benchmarking data:\n\n"
                    f"{comparison_table}\n\n"
                    f"Focus: {custom_focus or 'Comprehensive market positioning, pricing models, and tech advantages'}\n\n"
                    f"Write a sharp 2-paragraph Strategic Implications and Gaps section summarizing who leads where and what opportunities exist."
                )
                resp = await client.chat.completions.create(
                    model=self.default_model,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.2,
                    max_tokens=500,
                )
                llm_insights = resp.choices[0].message.content or ""
                if llm_insights:
                    full_report_md += f"\n## 4. Strategic Implications & Market Gaps (AI Insights)\n{llm_insights}\n"
                    model_used = self.default_model
            except Exception as exc:
                logger.warning("LLM strategic comparison failed, using deterministic report: %s", exc)

        return CompetitorComparisonResult(
            domains=cleaned_domains,
            profiles=profiles,
            comparison_table_md=comparison_table,
            full_report_md=full_report_md,
            model_used=model_used,
        )

    @classmethod
    def export_pdf(
        cls,
        comparison: CompetitorComparisonResult,
        target_path_or_buf: str | Path | io.BytesIO | None = None,
    ) -> bytes:
        """Export the comparison result into an executive-grade styled PDF."""
        title = f"Competitive Intelligence: {' vs '.join(comparison.domains)}"
        buf = target_path_or_buf or io.BytesIO()
        return StorageExporter.to_dossier_pdf(
            markdown=comparison.full_report_md,
            title=title,
            target_path_or_buf=buf,
        )

