"""Pre-built, battle-tested RPA recipes for common interactive web patterns."""

from ethical_crawler.rpa.models import RPAActionType, RPAStep

COOKIE_BANNER_DISMISSAL_STEPS: list[RPAStep] = [
    RPAStep(
        action=RPAActionType.CLICK,
        selector="#onetrust-accept-btn-handler",
        optional=True,
        timeout_ms=1200,
        wait_after_ms=200,
        description="Dismiss OneTrust cookie consent",
    ),
    RPAStep(
        action=RPAActionType.CLICK,
        selector="#CybotCookiebotDialogBodyLevelButtonLevelOptinAllowAll",
        optional=True,
        timeout_ms=1200,
        wait_after_ms=200,
        description="Dismiss Cookiebot banner",
    ),
    RPAStep(
        action=RPAActionType.CLICK,
        selector="button[id*='accept'], button[class*='cookie-accept']",
        optional=True,
        timeout_ms=1200,
        wait_after_ms=200,
        description="Dismiss generic cookie acceptance button",
    ),
    RPAStep(
        action=RPAActionType.CLICK,
        selector="button:has-text('Accept All'), button:has-text('Accept all cookies'), button:has-text('Allow all')",
        optional=True,
        timeout_ms=1200,
        wait_after_ms=200,
        description="Dismiss text-based cookie consent banner",
    ),
    RPAStep(
        action=RPAActionType.CLICK,
        selector="button:has-text('I agree'), button:has-text('Got it')",
        optional=True,
        timeout_ms=1000,
        wait_after_ms=150,
        description="Dismiss acknowledgment banner",
    ),
    RPAStep(
        action=RPAActionType.PRESS_KEY,
        value="Escape",
        optional=True,
        timeout_ms=500,
        wait_after_ms=100,
        description="Send Escape key to close any lingering modal overlays",
    ),
]

EXPAND_ACCORDIONS_STEPS: list[RPAStep] = [
    RPAStep(
        action=RPAActionType.CLICK,
        selector="details:not([open]) > summary",
        optional=True,
        timeout_ms=1500,
        wait_after_ms=250,
        description="Expand collapsed HTML5 details tags",
    ),
    RPAStep(
        action=RPAActionType.CLICK,
        selector="button[aria-expanded='false'][class*='accordion'], button[aria-expanded='false'][class*='faq']",
        optional=True,
        timeout_ms=1500,
        wait_after_ms=250,
        description="Expand collapsed accordion and FAQ sections",
    ),
]

TOGGLE_ANNUAL_PRICING_STEPS: list[RPAStep] = [
    RPAStep(
        action=RPAActionType.CLICK,
        selector="button:has-text('Annual'), button:has-text('Yearly'), input[type='checkbox'][class*='billing'], [data-billing='annual']",
        optional=True,
        timeout_ms=2000,
        wait_after_ms=500,
        description="Toggle pricing table to annual / discounted tier",
    ),
]


def get_preset_recipes() -> dict[str, dict]:
    """Return dictionary of available pre-built RPA recipes for frontend & API."""
    return {
        "auto_dismiss_cookies": {
            "name": "Auto-Dismiss Cookie & Modal Banners",
            "description": "Automatically finds and clicks 'Accept', 'Allow all', or 'Got it' cookie banners, then presses Escape.",
            "steps": [step.model_dump() for step in COOKIE_BANNER_DISMISSAL_STEPS],
        },
        "expand_accordions": {
            "name": "Expand Collapsed Accordions & FAQs",
            "description": "Clicks collapsed <details> elements and FAQ buttons to expose hidden content before crawling.",
            "steps": [step.model_dump() for step in EXPAND_ACCORDIONS_STEPS],
        },
        "toggle_annual_pricing": {
            "name": "Toggle Annual Pricing",
            "description": "Clicks annual/yearly billing switches on SaaS pricing pages to reveal annual discounts.",
            "steps": [step.model_dump() for step in TOGGLE_ANNUAL_PRICING_STEPS],
        },
    }
