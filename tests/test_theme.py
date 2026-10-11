"""Tests for the Centralized Theme & Design System Engine."""

import json
from ethical_crawler.api.theme import (
    DEFAULT_THEME_ID,
    FONT_PAIRINGS,
    THEMES,
    generate_google_fonts_link,
    generate_root_css,
    get_font_pairing,
    get_theme,
    get_themes_json,
)


def test_theme_registry_contains_default():
    assert DEFAULT_THEME_ID in THEMES
    default_theme = get_theme(DEFAULT_THEME_ID)
    assert default_theme["name"] == "Ethic Neo (Light HUD)"
    assert "--ds-bg" in default_theme["tokens"]
    assert "--ds-primary" in default_theme["tokens"]
    assert "--ds-on-surface" in default_theme["tokens"]


def test_fallback_to_default_for_unknown_theme():
    unknown = get_theme("non_existent_theme")
    assert unknown["id"] == DEFAULT_THEME_ID


def test_font_pairings():
    default_fonts = get_font_pairing("default")
    assert "Space Grotesk" in default_fonts["heading"]
    assert "Plus Jakarta Sans" in default_fonts["sans"]
    assert "Space Mono" in default_fonts["mono"]


def test_generate_root_css():
    css = generate_root_css("dark_obsidian")
    assert ":root {" in css
    assert "--ds-font-heading:" in css
    assert "--ds-font-sans:" in css
    assert "--ds-font-mono:" in css
    assert "--ds-bg: #090d16;" in css
    assert "--ds-primary: #38bdf8;" in css


def test_generate_google_fonts_link():
    link_html = generate_google_fonts_link()
    assert "fonts.googleapis.com" in link_html
    assert "Space+Grotesk" in link_html
    assert "Plus+Jakarta+Sans" in link_html


def test_themes_json_serialization():
    raw_json = get_themes_json()
    parsed = json.loads(raw_json)
    assert "themes" in parsed
    assert "fontPairings" in parsed
    assert parsed["defaultThemeId"] == DEFAULT_THEME_ID
    assert len(parsed["themes"]) >= 6

