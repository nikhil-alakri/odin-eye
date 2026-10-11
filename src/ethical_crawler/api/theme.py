"""Centralized Design System & Theme Engine for Ethical Web Crawler.

This module is the single source of truth for all themes, color palettes,
typography pairings, and CSS variables across the dashboard.
To change the default appearance or add new themes, edit this file.
"""

from __future__ import annotations

import json
from typing import Any, Dict


# ==============================================================================
# 1. TYPOGRAPHY PAIRINGS & GOOGLE FONTS
# ==============================================================================
FONT_PAIRINGS: Dict[str, Dict[str, str]] = {
    "default": {
        "name": "Technical Modern (Default)",
        "heading": "'Space Grotesk', system-ui, sans-serif",
        "sans": "'Plus Jakarta Sans', system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif",
        "mono": "'Space Mono', ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace",
        "google_family": "Plus+Jakarta+Sans:wght@400;500;600;700&family=Space+Grotesk:wght@500;600;700&family=Space+Mono:wght@400;700",
    },
    "inter_clean": {
        "name": "Inter & Outfit Clean",
        "heading": "'Outfit', system-ui, sans-serif",
        "sans": "'Inter', system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif",
        "mono": "'JetBrains Mono', ui-monospace, SFMono-Regular, Menlo, Monaco, monospace",
        "google_family": "Inter:wght@400;500;600;700&family=Outfit:wght@500;600;700&family=JetBrains+Mono:wght@400;600",
    },
    "editorial_syne": {
        "name": "Syne & Figtree Editorial",
        "heading": "'Syne', system-ui, sans-serif",
        "sans": "'Figtree', system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif",
        "mono": "'Fira Code', ui-monospace, SFMono-Regular, Menlo, monospace",
        "google_family": "Syne:wght@600;700;800&family=Figtree:wght@400;500;600;700&family=Fira+Code:wght@400;600",
    },
    "system_native": {
        "name": "Native System (Zero External Fonts)",
        "heading": "system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif",
        "sans": "system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif",
        "mono": "ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace",
        "google_family": "",
    },
}


# ==============================================================================
# 2. CURATED THEME PRESETS & COLOR PALETTES
# ==============================================================================
THEMES: Dict[str, Dict[str, Any]] = {
    "ethic_neo": {
        "id": "ethic_neo",
        "name": "Ethic Neo (Light HUD)",
        "category": "light",
        "description": "Clean technical cream with energetic lime accents, cyan highlights, and crisp borders.",
        "font_pairing": "default",
        "tokens": {
            "--ds-bg": "#fcf8f8",
            "--ds-surface": "#fcf8f8",
            "--ds-card-bg": "#ffffff",
            "--ds-surface-container": "#f0edec",
            "--ds-surface-container-low": "#f6f3f2",
            "--ds-surface-container-high": "#ebe7e7",
            "--ds-surface-container-highest": "#e5e2e1",
            "--ds-on-surface": "#1c1b1b",
            "--ds-on-surface-variant": "#444932",
            "--ds-outline": "#757a60",
            "--ds-primary": "#536600",
            "--ds-primary-container": "#d4ff00",
            "--ds-on-primary-container": "#5f7400",
            "--ds-secondary": "#00677f",
            "--ds-secondary-container": "#00d2ff",
            "--ds-tertiary": "#bd0042",
            "--ds-error": "#ba1a1a",
            "--ds-error-container": "#ffdad6",
            "--ds-border": "#e5e2e1",
            "--ds-shadow": "0 1px 3px rgba(28, 27, 27, 0.06), 0 4px 12px rgba(28, 27, 27, 0.04)",
            "--ds-modal-overlay": "rgba(28, 27, 27, 0.45)",
            "--ds-radius": "0.75rem",
        },
    },
    "dark_obsidian": {
        "id": "dark_obsidian",
        "name": "Obsidian Cyber (Dark Ops)",
        "category": "dark",
        "description": "Ultra-modern deep dark cybersecurity cockpit with vivid cyan and purple glows.",
        "font_pairing": "default",
        "tokens": {
            "--ds-bg": "#090d16",
            "--ds-surface": "#0f1626",
            "--ds-card-bg": "#121b2d",
            "--ds-surface-container": "#151f33",
            "--ds-surface-container-low": "#0d1320",
            "--ds-surface-container-high": "#1b2740",
            "--ds-surface-container-highest": "#22314f",
            "--ds-on-surface": "#f1f5f9",
            "--ds-on-surface-variant": "#94a3b8",
            "--ds-outline": "#334155",
            "--ds-primary": "#38bdf8",
            "--ds-primary-container": "#0284c7",
            "--ds-on-primary-container": "#ffffff",
            "--ds-secondary": "#2dd4bf",
            "--ds-secondary-container": "#0f766e",
            "--ds-tertiary": "#f59e0b",
            "--ds-error": "#f43f5e",
            "--ds-error-container": "#881337",
            "--ds-border": "#1e293b",
            "--ds-shadow": "0 2px 8px rgba(0, 0, 0, 0.5), 0 8px 24px rgba(0, 0, 0, 0.6)",
            "--ds-modal-overlay": "rgba(3, 7, 18, 0.75)",
            "--ds-radius": "0.75rem",
        },
    },
    "midnight_slate": {
        "id": "midnight_slate",
        "name": "Midnight Slate (Pro Dark)",
        "category": "dark",
        "description": "Sophisticated slate blue dark theme with electric indigo actions and sky highlights.",
        "font_pairing": "inter_clean",
        "tokens": {
            "--ds-bg": "#0f172a",
            "--ds-surface": "#1e293b",
            "--ds-card-bg": "#1e293b",
            "--ds-surface-container": "#243248",
            "--ds-surface-container-low": "#152033",
            "--ds-surface-container-high": "#334155",
            "--ds-surface-container-highest": "#475569",
            "--ds-on-surface": "#f8fafc",
            "--ds-on-surface-variant": "#cbd5e1",
            "--ds-outline": "#475569",
            "--ds-primary": "#818cf8",
            "--ds-primary-container": "#6366f1",
            "--ds-on-primary-container": "#ffffff",
            "--ds-secondary": "#38bdf8",
            "--ds-secondary-container": "#0284c7",
            "--ds-tertiary": "#fbbf24",
            "--ds-error": "#fb7185",
            "--ds-error-container": "#9f1239",
            "--ds-border": "#334155",
            "--ds-shadow": "0 2px 6px rgba(0, 0, 0, 0.4), 0 6px 20px rgba(0, 0, 0, 0.45)",
            "--ds-modal-overlay": "rgba(15, 23, 42, 0.7)",
            "--ds-radius": "0.75rem",
        },
    },
    "emerald_forest": {
        "id": "emerald_forest",
        "name": "Emerald Forest (Clean Light)",
        "category": "light",
        "description": "Refreshing natural mint palette with crisp emerald CTAs and sage accents.",
        "font_pairing": "inter_clean",
        "tokens": {
            "--ds-bg": "#f4fbf7",
            "--ds-surface": "#f4fbf7",
            "--ds-card-bg": "#ffffff",
            "--ds-surface-container": "#e6f6ee",
            "--ds-surface-container-low": "#edf9f2",
            "--ds-surface-container-high": "#d8f0e3",
            "--ds-surface-container-highest": "#c9ead7",
            "--ds-on-surface": "#0f291e",
            "--ds-on-surface-variant": "#2d5a45",
            "--ds-outline": "#5a8c73",
            "--ds-primary": "#047857",
            "--ds-primary-container": "#10b981",
            "--ds-on-primary-container": "#ffffff",
            "--ds-secondary": "#0d9488",
            "--ds-secondary-container": "#5eead4",
            "--ds-tertiary": "#d97706",
            "--ds-error": "#dc2626",
            "--ds-error-container": "#fee2e2",
            "--ds-border": "#d1fae5",
            "--ds-shadow": "0 1px 3px rgba(15, 41, 30, 0.05), 0 4px 12px rgba(15, 41, 30, 0.04)",
            "--ds-modal-overlay": "rgba(15, 41, 30, 0.45)",
            "--ds-radius": "0.75rem",
        },
    },
    "nordic_frost": {
        "id": "nordic_frost",
        "name": "Nordic Frost (Clean Ice)",
        "category": "light",
        "description": "Minimalist ice-blue clarity with crisp sapphire action elements and high legibility.",
        "font_pairing": "default",
        "tokens": {
            "--ds-bg": "#f8fafc",
            "--ds-surface": "#f8fafc",
            "--ds-card-bg": "#ffffff",
            "--ds-surface-container": "#f1f5f9",
            "--ds-surface-container-low": "#f8fafc",
            "--ds-surface-container-high": "#e2e8f0",
            "--ds-surface-container-highest": "#cbd5e1",
            "--ds-on-surface": "#0f172a",
            "--ds-on-surface-variant": "#475569",
            "--ds-outline": "#94a3b8",
            "--ds-primary": "#0369a1",
            "--ds-primary-container": "#0284c7",
            "--ds-on-primary-container": "#ffffff",
            "--ds-secondary": "#0891b2",
            "--ds-secondary-container": "#67e8f9",
            "--ds-tertiary": "#ea580c",
            "--ds-error": "#e11d48",
            "--ds-error-container": "#ffe4e6",
            "--ds-border": "#e2e8f0",
            "--ds-shadow": "0 1px 3px rgba(15, 23, 42, 0.05), 0 4px 12px rgba(15, 23, 42, 0.04)",
            "--ds-modal-overlay": "rgba(15, 23, 42, 0.45)",
            "--ds-radius": "0.75rem",
        },
    },
    "monochrome_minimal": {
        "id": "monochrome_minimal",
        "name": "Monochrome Studio (High Contrast)",
        "category": "light",
        "description": "Gallery-grade stark black-and-white minimalist design with maximum contrast.",
        "font_pairing": "editorial_syne",
        "tokens": {
            "--ds-bg": "#f9f9f9",
            "--ds-surface": "#f9f9f9",
            "--ds-card-bg": "#ffffff",
            "--ds-surface-container": "#f0f0f0",
            "--ds-surface-container-low": "#f6f6f6",
            "--ds-surface-container-high": "#e6e6e6",
            "--ds-surface-container-highest": "#dcdcdc",
            "--ds-on-surface": "#121212",
            "--ds-on-surface-variant": "#555555",
            "--ds-outline": "#888888",
            "--ds-primary": "#121212",
            "--ds-primary-container": "#000000",
            "--ds-on-primary-container": "#ffffff",
            "--ds-secondary": "#262626",
            "--ds-secondary-container": "#e0e0e0",
            "--ds-tertiary": "#b45309",
            "--ds-error": "#b91c1c",
            "--ds-error-container": "#fef2f2",
            "--ds-border": "#e0e0e0",
            "--ds-shadow": "0 2px 4px rgba(0, 0, 0, 0.06), 0 6px 14px rgba(0, 0, 0, 0.04)",
            "--ds-modal-overlay": "rgba(18, 18, 18, 0.5)",
            "--ds-radius": "0.5rem",
        },
    },
}


DEFAULT_THEME_ID = "ethic_neo"


# ==============================================================================
# 3. CSS GENERATION & EXPORT HELPERS
# ==============================================================================
def get_theme(theme_id: str | None = None) -> Dict[str, Any]:
    """Retrieve a theme configuration by ID, falling back to DEFAULT_THEME_ID."""
    if not theme_id or theme_id not in THEMES:
        return THEMES[DEFAULT_THEME_ID]
    return THEMES[theme_id]


def get_font_pairing(pairing_id: str | None = None) -> Dict[str, str]:
    """Retrieve font pairing definition."""
    if not pairing_id or pairing_id not in FONT_PAIRINGS:
        return FONT_PAIRINGS["default"]
    return FONT_PAIRINGS[pairing_id]


def generate_google_fonts_link() -> str:
    """Generate HTML <link> tags to load all curated Google Fonts families."""
    families = [
        fp["google_family"]
        for fp in FONT_PAIRINGS.values()
        if fp.get("google_family")
    ]
    query_parts = "&family=".join(families)
    return (
        '<link rel="preconnect" href="https://fonts.googleapis.com">\n'
        '  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>\n'
        f'  <link href="https://fonts.googleapis.com/css2?family={query_parts}&display=swap" rel="stylesheet">'
    )


def generate_root_css(theme_id: str = DEFAULT_THEME_ID) -> str:
    """Generate CSS :root block containing all design tokens and typography vars."""
    theme = get_theme(theme_id)
    font_id = theme.get("font_pairing", "default")
    fonts = get_font_pairing(font_id)

    lines = [":root {"]
    # Typography variables
    lines.append(f"  --ds-font-heading: {fonts['heading']};")
    lines.append(f"  --ds-font-sans: {fonts['sans']};")
    lines.append(f"  --ds-font-mono: {fonts['mono']};")

    # Color & surface tokens
    for token_key, token_val in theme["tokens"].items():
        lines.append(f"  {token_key}: {token_val};")

    lines.append("}")
    return "\n".join(lines)


def get_themes_json() -> str:
    """Return JSON string of all themes and font pairings for client-side studio."""
    payload = {
        "themes": THEMES,
        "defaultThemeId": DEFAULT_THEME_ID,
        "fontPairings": FONT_PAIRINGS,
    }
    return json.dumps(payload, indent=2)

