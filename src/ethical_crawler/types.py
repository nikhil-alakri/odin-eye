"""Data types and Pydantic schemas for the Ethical Crawler application."""

from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class CrawlStrategy(StrEnum):
    """Crawl execution strategies."""

    HTTP = "http"
    BROWSER = "browser"
    AUTO = "auto"


class JobStatus(StrEnum):
    """Status of background crawl jobs."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class PageMetadata(BaseModel):
    """Extracted HTML metadata and structured schemas."""

    title: str | None = None
    description: str | None = None
    canonical: str | None = None
    author: str | None = None
    keywords: list[str] = Field(default_factory=list)
    og_title: str | None = None
    og_description: str | None = None
    og_image: str | None = None
    og_type: str | None = None
    twitter_card: str | None = None
    json_ld: list[dict[str, Any]] = Field(default_factory=list)


class PageLink(BaseModel):
    """Discovered link on a page."""

    url: str
    text: str = ""
    is_internal: bool = True


class CrawlResult(BaseModel):
    """Result of crawling an individual page."""

    url: str
    final_url: str
    status_code: int
    content_type: str = "text/html"
    title: str | None = None
    markdown: str = ""
    raw_html_size: int = 0
    cleaned_markdown_size: int = 0
    metadata: PageMetadata = Field(default_factory=PageMetadata)
    internal_links: list[str] = Field(default_factory=list)
    external_links: list[str] = Field(default_factory=list)
    strategy_used: CrawlStrategy = CrawlStrategy.HTTP
    elapsed_seconds: float = 0.0
    crawled_at: datetime = Field(default_factory=datetime.utcnow)
    error: str | None = None
    confidence: str = "HIGH"
    ai_data: dict[str, Any] | None = None
    ai_model_used: str | None = None
    rpa_logs: list[str] = Field(default_factory=list)
    network_calls: list[dict[str, Any]] = Field(default_factory=list)
    dom_elements: dict[str, Any] = Field(default_factory=dict)


class NetworkCall(BaseModel):
    """Captured background HTTP/Fetch/XHR API call."""

    url: str
    method: str = "GET"
    status: int = 200
    resource_type: str = "fetch"
    content_type: str = "application/json"
    request_data: str | None = None
    response_data: Any | None = None
    duration_ms: float = 0.0


class RobotsDirectives(BaseModel):
    """Robots.txt parsed directives for a domain."""

    domain: str
    robots_url: str
    can_fetch: bool
    crawl_delay: float | None = None
    sitemaps: list[str] = Field(default_factory=list)
    user_agent_used: str
    fetched_at: datetime = Field(default_factory=datetime.utcnow)
    status_code: int = 200
    raw_rules: str = ""


class SitemapURL(BaseModel):
    """Single URL entry extracted from sitemap.xml."""

    loc: str
    lastmod: str | None = None
    changefreq: str | None = None
    priority: float | None = None


class SitemapResult(BaseModel):
    """Result of sitemap parsing."""

    sitemap_url: str
    total_urls: int
    urls: list[SitemapURL] = Field(default_factory=list)
    nested_sitemaps: list[str] = Field(default_factory=list)
    elapsed_seconds: float = 0.0
    error: str | None = None


class CrawlRequest(BaseModel):
    """Parameters for initiating a crawl job."""

    url: str
    max_pages: int = Field(default=20, ge=1, le=1000)
    max_depth: int = Field(default=2, ge=0, le=10)
    delay: float | None = Field(default=None, description="Delay between requests (seconds)")
    strategy: CrawlStrategy = CrawlStrategy.AUTO
    use_sitemap: bool = Field(default=False, description="Extract and crawl from sitemap.xml")
    respect_robots: bool = True
    extract_ai: bool = False
    ai_schema: str = "article"
    ai_prompt: str | None = None
    ai_model: str | None = None
    allowed_domains: list[str] = Field(default_factory=list)
    use_cache: bool = Field(
        default=True, description="Check local vector store cache to prevent re-crawling"
    )
    cache_ttl_days: int | None = Field(
        default=None, description="Custom cache validity duration in days"
    )
    rpa_steps: list[dict[str, Any]] = Field(
        default_factory=list, description="Interactive RPA steps to execute in browser engine"
    )
    auto_dismiss_modals: bool = Field(
        default=True, description="Automatically dismiss common cookie and dialog banners"
    )


class CrawlJob(BaseModel):
    """State of an ongoing or completed crawl job."""

    job_id: str
    request: CrawlRequest
    status: JobStatus = JobStatus.PENDING
    started_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: datetime | None = None
    pages_crawled: int = 0
    pages_discovered: int = 0
    pages_skipped: int = 0
    results: list[CrawlResult] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)
    current_activity: str | None = None
    current_url: str | None = None


# AI Extraction Schemas
class ArticleSchema(BaseModel):
    """Structured schema for article extraction."""

    title: str
    author: str | None = None
    date: str | None = None
    summary: str
    key_points: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)


class ProductSchema(BaseModel):
    """Structured schema for e-commerce product extraction."""

    name: str
    brand: str | None = None
    price: float | None = None
    currency: str | None = None
    original_price: float | None = None
    in_stock: bool | None = None
    description: str | None = None
    specifications: dict[str, str] = Field(default_factory=dict)
    rating: float | None = None
    review_count: int | None = None


class FAQItem(BaseModel):
    """Single question-answer pair."""

    question: str
    answer: str
    category: str | None = None


class FAQSchema(BaseModel):
    """Structured schema for FAQ extraction."""

    items: list[FAQItem] = Field(default_factory=list)


class ProductOffering(BaseModel):
    """Product, tier, or feature offering."""

    name: str
    description: str | None = None
    price: str | None = None
    features: list[str] = Field(default_factory=list)


class CompanyProfileSchema(BaseModel):
    """Structured schema for complete website, business, and product intelligence."""

    company_name: str
    headline_or_tagline: str | None = None
    what_they_do: str
    target_audience: list[str] = Field(default_factory=list)
    main_product: str
    products_and_features: list[ProductOffering] = Field(default_factory=list)
    why_in_market: str = Field(default="", description="Value proposition and problem solved")
    strategic_purpose: str = Field(
        default="", description="What this should be used for and best use cases"
    )
    key_differentiators: list[str] = Field(default_factory=list)


class StructuredExtractionResult(BaseModel):
    """Result of an AI structured extraction."""

    url: str
    schema_type: str
    data: dict[str, Any]
    model_used: str
    tokens_used: int | None = None
    confidence: str = "HIGH"
    notes: list[str] = Field(default_factory=list)


class MarketDossierRequest(BaseModel):
    """Parameters for generating an executive market intelligence dossier."""

    domains: list[str] = Field(..., description="Target domains to analyze and compare")
    model: str = Field(
        default="moonshotai/kimi-k3",
        description="NVIDIA NIM model to synthesize the multi-site dossier",
    )
    custom_focus: str | None = Field(
        default=None, description="Optional custom questions or focus areas"
    )


class MarketDossierResult(BaseModel):
    """Result of an executive market intelligence dossier synthesis."""

    domains_analyzed: list[str]
    model_used: str
    dossier_markdown: str
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    competitors_analyzed: list[str] = Field(default_factory=list)
    markdown: str = ""

    def model_post_init(self, __context: Any) -> None:
        if not self.competitors_analyzed:
            self.competitors_analyzed = self.domains_analyzed
        if not self.markdown:
            self.markdown = self.dossier_markdown
