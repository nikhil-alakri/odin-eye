"""Content Diff Engine for comparing crawl snapshots and detecting semantic changes."""

from __future__ import annotations

import difflib
import html
import re
from typing import Any, Dict, List, Tuple
from pydantic import BaseModel, Field


class ContentDiffResult(BaseModel):
    """Result of content comparison between two revisions."""
    has_changed: bool
    similarity_ratio: float
    added_lines_count: int
    removed_lines_count: int
    total_diff_lines: int
    summary: str
    raw_diff: str
    html_diff: str
    added_snippets: List[str] = Field(default_factory=list)
    removed_snippets: List[str] = Field(default_factory=list)


class ContentDiffEngine:
    """Smart content comparison engine with noise suppression and syntax-colored HTML generation."""

    # Regex patterns for volatile tokens to suppress during diffing
    TIMESTAMP_PATTERNS = [
        re.compile(r"\b\d{4}-\d{2}-\d{2}[T\s]\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:?\d{2})?\b"),
        re.compile(r"\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{1,2},\s+\d{4}\b", re.IGNORECASE),
        re.compile(r"\b(?:csrf[-_]?token|nonce|session[-_]?id)=['\"][a-zA-Z0-9_-]+['\"]", re.IGNORECASE),
    ]

    @classmethod
    def clean_noise(cls, text: str) -> str:
        """Strip volatile dynamic tokens like timestamps and CSRF nonces to prevent false positives."""
        if not text:
            return ""
        cleaned = text
        for pattern in cls.TIMESTAMP_PATTERNS:
            cleaned = pattern.sub("[TIMESTAMP_MUTED]", cleaned)
        return cleaned

    @classmethod
    def compute_diff(
        cls,
        old_text: str | None,
        new_text: str | None,
        old_label: str = "Previous Snapshot",
        new_label: str = "Latest Snapshot",
        suppress_noise: bool = True,
    ) -> ContentDiffResult:
        """Compare two markdown snapshots and return detailed diff metrics."""
        old_raw = old_text or ""
        new_raw = new_text or ""

        if suppress_noise:
            old_proc = cls.clean_noise(old_raw)
            new_proc = cls.clean_noise(new_raw)
        else:
            old_proc = old_raw
            new_proc = new_raw

        old_lines = [line.strip() for line in old_proc.splitlines()]
        new_lines = [line.strip() for line in new_proc.splitlines()]

        # Filter out multiple consecutive blank lines for cleaner matching
        old_filtered = [l for l in old_lines if l]
        new_filtered = [l for l in new_lines if l]

        matcher = difflib.SequenceMatcher(None, old_filtered, new_filtered)
        similarity = round(matcher.ratio(), 4)

        # Generate unified diff on original lines (with proper line endings)
        diff_generator = difflib.unified_diff(
            old_raw.splitlines(keepends=True),
            new_raw.splitlines(keepends=True),
            fromfile=old_label,
            tofile=new_label,
            n=3,
        )
        diff_lines = list(diff_generator)
        raw_diff = "".join(diff_lines)

        added_lines: List[str] = []
        removed_lines: List[str] = []

        html_blocks: List[str] = []

        for line in diff_lines:
            raw_line = line.rstrip("\r\n")
            escaped = html.escape(raw_line)

            if raw_line.startswith("+++") or raw_line.startswith("---"):
                html_blocks.append(
                    f'<div class="diff-line diff-meta font-mono text-[11px] text-slate-500 py-0.5 px-2 bg-slate-100">{escaped}</div>'
                )
            elif raw_line.startswith("@@"):
                html_blocks.append(
                    f'<div class="diff-line diff-chunk font-mono text-[11px] text-purple-700 py-0.5 px-2 bg-purple-50 font-bold">{escaped}</div>'
                )
            elif raw_line.startswith("+"):
                added_lines.append(raw_line[1:].strip())
                html_blocks.append(
                    f'<div class="diff-line diff-add font-mono text-[11px] text-emerald-800 py-0.5 px-2 bg-emerald-50 border-l-2 border-emerald-500">{escaped}</div>'
                )
            elif raw_line.startswith("-"):
                removed_lines.append(raw_line[1:].strip())
                html_blocks.append(
                    f'<div class="diff-line diff-del font-mono text-[11px] text-rose-800 py-0.5 px-2 bg-rose-50 border-l-2 border-rose-500">{escaped}</div>'
                )
            else:
                html_blocks.append(
                    f'<div class="diff-line diff-ctx font-mono text-[11px] text-slate-700 py-0.5 px-2">{escaped}</div>'
                )

        added_count = len(added_lines)
        removed_count = len(removed_lines)
        has_changed = (added_count > 0 or removed_count > 0) and similarity < 0.999

        if not has_changed:
            summary = "No meaningful content changes detected (100% match)."
        else:
            sim_pct = round(similarity * 100, 1)
            summary = f"Modified: +{added_count} lines, -{removed_count} lines ({sim_pct}% similarity)"

        return ContentDiffResult(
            has_changed=has_changed,
            similarity_ratio=similarity,
            added_lines_count=added_count,
            removed_lines_count=removed_count,
            total_diff_lines=len(diff_lines),
            summary=summary,
            raw_diff=raw_diff,
            html_diff="\n".join(html_blocks),
            added_snippets=added_lines[:5],
            removed_snippets=removed_lines[:5],
        )

