"""Configuration settings for the Ethical Crawler application."""

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings with environment variable loading."""

    model_config = SettingsConfigDict(
        env_prefix="CRAWLER_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # 1. Ethical Bot Identification (Rule 3)
    bot_name: str = Field(default="EthicalCrawlerBot", description="Name of the bot in User-Agent")
    bot_version: str = Field(default="1.0.0", description="Bot version string")
    bot_url: str = Field(
        default="https://github.com/example/ethical-crawler",
        description="Public URL with bot info",
    )
    bot_email: str = Field(
        default="crawler-contact@example.com",
        description="Contact email for website operators",
    )

    # 2. Politeness & Rate Limiting (Rule 2)
    default_delay: float = Field(
        default=2.0,
        ge=0.1,
        description="Minimum delay between requests to same domain (seconds)",
    )
    max_concurrency: int = Field(
        default=5,
        ge=1,
        le=50,
        description="Maximum concurrent HTTP requests globally",
    )
    per_domain_concurrency: int = Field(
        default=1,
        ge=1,
        le=5,
        description="Maximum concurrent requests to a single domain",
    )
    max_depth: int = Field(default=3, ge=0, description="Max crawl depth for recursive crawling")
    max_pages: int = Field(default=50, ge=1, description="Maximum total pages to crawl per job")
    request_timeout: float = Field(
        default=15.0,
        ge=1.0,
        description="Network request timeout in seconds",
    )
    max_retries: int = Field(default=3, ge=0, description="Max retries for transient HTTP errors")
    backoff_factor: float = Field(
        default=1.5,
        ge=1.0,
        description="Multiplier for exponential backoff on errors",
    )

    # 3. Robots.txt Policy (Rule 1)
    respect_robots_txt: bool = Field(
        default=True,
        description="Enforce robots.txt allow/disallow/crawl-delay rules",
    )
    robots_cache_ttl: int = Field(
        default=3600,
        ge=60,
        description="In-memory cache TTL for robots.txt in seconds",
    )

    # 4. Sitemap Discovery (Rule 4)
    auto_discover_sitemap: bool = Field(
        default=True,
        description="Attempt to fetch sitemap.xml if available",
    )

    # 5. Browser Automation (Dynamic SPAs)
    enable_browser_fallback: bool = Field(
        default=True,
        description="Auto-escalate to headless browser if JS rendering is detected",
    )
    headless_browser: bool = Field(default=True, description="Run browser in headless mode")

    # 6. AI-Native LLM Extraction
    ai_base_url: str = Field(
        default="https://integrate.api.nvidia.com/v1",
        description="OpenAI-compatible base URL (NVIDIA NIM, OpenAI, Ollama, etc.)",
    )
    ai_api_key: str = Field(
        default="",
        description="API key for NVIDIA NIM or OpenAI compatible provider",
    )
    ai_model: str = Field(
        default="meta/llama-3.2-11b-vision-instruct",
        description="Default LLM model identifier",
    )

    # 7. Web Server
    api_host: str = Field(default="0.0.0.0", description="API server host")
    api_port: int = Field(default=8000, description="API server port")

    # 8. Vector Database & Smart Cache (ChromaDB)
    chroma_dir: str = Field(
        default="data/chroma",
        description="Local directory path where ChromaDB vector database is persisted",
    )
    enable_cache: bool = Field(
        default=True,
        description="Check vector database cache before fetching URLs to avoid re-crawling",
    )
    cache_ttl_days: int = Field(
        default=7,
        ge=1,
        description="Days a cached page is considered fresh before re-fetching",
    )
    chroma_collection: str = Field(
        default="crawled_knowledge",
        description="ChromaDB collection name for crawled web pages",
    )

    @property
    def user_agent(self) -> str:
        """Construct the ethical bot User-Agent string."""
        contact = f"+{self.bot_url}; {self.bot_email}".strip("; ")
        return f"{self.bot_name}/{self.bot_version} ({contact})"


@lru_cache
def get_settings() -> Settings:
    """Singleton getter for application settings."""
    return Settings()
