"""Extractors package: HTML cleaning, metadata, links, and AI extraction."""

from ethical_crawler.extractors.ai_extractor import AIExtractor
from ethical_crawler.extractors.element_inspector import ElementInspector
from ethical_crawler.extractors.html_cleaner import HTMLCleaner, get_html_cleaner
from ethical_crawler.extractors.link_extractor import LinkExtractor
from ethical_crawler.extractors.metadata import MetadataExtractor
from ethical_crawler.extractors.nemotron_parser import NemotronParser

__all__ = [
    "HTMLCleaner",
    "get_html_cleaner",
    "MetadataExtractor",
    "LinkExtractor",
    "AIExtractor",
    "NemotronParser",
    "ElementInspector",
]
