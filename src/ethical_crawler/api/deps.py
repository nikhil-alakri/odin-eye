"""FastAPI dependency injection utilities."""

from ethical_crawler.config import Settings, get_settings
from ethical_crawler.core.rate_limiter import RateLimiter, get_rate_limiter
from ethical_crawler.core.robots import RobotsParser, get_robots_parser
from ethical_crawler.core.sitemap import SitemapParser, get_sitemap_parser
from ethical_crawler.extractors.ai_extractor import AIExtractor


def get_app_settings() -> Settings:
    return get_settings()


def get_app_robots_parser() -> RobotsParser:
    return get_robots_parser()


def get_app_rate_limiter() -> RateLimiter:
    return get_rate_limiter()


def get_app_sitemap_parser() -> SitemapParser:
    return get_sitemap_parser()


def get_app_ai_extractor() -> AIExtractor:
    return AIExtractor()
