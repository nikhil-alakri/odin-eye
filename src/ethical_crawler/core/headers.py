"""Ethical Rule #3: Custom Bot User-Agent & Polite Request Headers.

Provides identifiable and transparent User-Agent headers indicating the bot's
identity, purpose/documentation URL, and contact information.
"""

from ethical_crawler.config import get_settings


def build_user_agent(
    name: str | None = None,
    version: str | None = None,
    url: str | None = None,
    email: str | None = None,
) -> str:
    """Build a standard ethical bot User-Agent string.

    Format: BotName/Version (+DocumentationURL; ContactEmail)
    Example: EthicalCrawlerBot/1.0.0 (+https://github.com/example/ethical-crawler; bot@example.com)
    """
    settings = get_settings()
    bot_name = name or settings.bot_name
    bot_version = version or settings.bot_version
    bot_url = url or settings.bot_url
    bot_email = email or settings.bot_email

    details: list[str] = []
    if bot_url:
        details.append(f"+{bot_url}")
    if bot_email:
        details.append(bot_email)

    contact_part = f" ({'; '.join(details)})" if details else ""
    return f"{bot_name}/{bot_version}{contact_part}"


def get_default_headers(
    custom_headers: dict[str, str] | None = None,
    user_agent: str | None = None,
) -> dict[str, str]:
    """Generate default headers for ethical HTTP crawling requests."""
    settings = get_settings()
    ua = user_agent or settings.user_agent

    headers = {
        "User-Agent": ua,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate",
        "DNT": "1",  # Do Not Track polite preference
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
    }

    if custom_headers:
        headers.update(custom_headers)

    return headers
