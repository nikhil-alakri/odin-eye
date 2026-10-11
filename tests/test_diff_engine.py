"""Unit tests for the Content Diff Engine."""

import pytest
from ethical_crawler.knowledge.diff_engine import ContentDiffEngine, ContentDiffResult


def test_diff_engine_identical_content():
    text = "# Pricing Plans\n\n- Basic: $10/mo\n- Pro: $20/mo\n"
    res = ContentDiffEngine.compute_diff(text, text)
    assert not res.has_changed
    assert res.similarity_ratio == 1.0
    assert res.added_lines_count == 0
    assert res.removed_lines_count == 0
    assert "No meaningful content changes" in res.summary


def test_diff_engine_detects_additions_and_deletions():
    old_text = "# Pricing Plans\n\n- Basic: $10/mo\n- Pro: $20/mo\n"
    new_text = "# Pricing Plans\n\n- Basic: $12/mo\n- Pro: $25/mo\n- Enterprise: Custom\n"

    res = ContentDiffEngine.compute_diff(old_text, new_text)
    assert res.has_changed
    assert res.similarity_ratio < 1.0
    assert res.added_lines_count > 0
    assert "Modified:" in res.summary
    assert "diff-add" in res.html_diff


def test_diff_engine_noise_suppression():
    old_text = "Article Title\nUpdated at 2026-10-01T12:00:00Z\nCore article content."
    new_text = "Article Title\nUpdated at 2026-10-09T01:30:00Z\nCore article content."

    # With noise suppression enabled, dynamic timestamp is neutralized
    res = ContentDiffEngine.compute_diff(old_text, new_text, suppress_noise=True)
    assert not res.has_changed
    assert res.similarity_ratio == 1.0


def test_diff_engine_empty_or_none_inputs():
    res1 = ContentDiffEngine.compute_diff(None, "# New Page")
    assert res1.has_changed
    assert res1.added_lines_count > 0

    res2 = ContentDiffEngine.compute_diff("# Old Page", None)
    assert res2.has_changed
    assert res2.removed_lines_count > 0

