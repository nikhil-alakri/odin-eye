"""Tests for Ethical Rule 3: User-Agent and transparent headers."""

from ethical_crawler.core.headers import build_user_agent, get_default_headers


def test_build_user_agent():
    ua = build_user_agent(
        name="MyBot",
        version="2.1.0",
        url="https://mybot.org",
        email="operator@mybot.org",
    )
    assert ua == "MyBot/2.1.0 (+https://mybot.org; operator@mybot.org)"


def test_default_headers_contain_polite_keys():
    headers = get_default_headers(user_agent="TestAgent/1.0")
    assert headers["User-Agent"] == "TestAgent/1.0"
    assert "Accept" in headers
    assert headers["DNT"] == "1"
    assert "gzip" in headers["Accept-Encoding"]
