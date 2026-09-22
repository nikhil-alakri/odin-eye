"""Robotic Process Automation (RPA) package for Ethical AI Crawler."""

from ethical_crawler.rpa.executor import RPAExecutor
from ethical_crawler.rpa.models import RPAActionType, RPAResult, RPAStep
from ethical_crawler.rpa.presets import get_preset_recipes

__all__ = ["RPAActionType", "RPAStep", "RPAResult", "RPAExecutor", "get_preset_recipes"]
