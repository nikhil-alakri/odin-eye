"""Local cache of Ask AI answers so repeated questions skip the model."""

import json
import re
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

_LOCK = threading.Lock()
_TOKEN_RE = re.compile(r"[a-z0-9]+")


def _normalize(question: str) -> str:
    return " ".join(_TOKEN_RE.findall(question.lower()))


def _tokens(question: str) -> set[str]:
    return set(_normalize(question).split())


def _overlap(left: set[str], right: set[str]) -> float:
    if not left or not right:
        return 0.0
    return len(left & right) / len(left | right)


class AskAnswerCache:
    """JSON file of previous questions, answers, and sources."""

    def __init__(self, path: Path):
        self.path = path

    def _load(self) -> list[dict[str, Any]]:
        if not self.path.exists():
            return []
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return []
        return data if isinstance(data, list) else []

    def _save(self, rows: list[dict[str, Any]]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(rows[-200:], indent=2), encoding="utf-8")

    def lookup(self, question: str, min_overlap: float = 0.72) -> dict[str, Any] | None:
        key = _normalize(question)
        if not key:
            return None
        wanted = _tokens(question)
        best: dict[str, Any] | None = None
        best_score = 0.0
        with _LOCK:
            rows = self._load()
        for row in rows:
            stored = row.get("normalized") or _normalize(row.get("question", ""))
            if stored == key:
                hit = dict(row)
                hit["match"] = "exact"
                return hit
            score = _overlap(wanted, _tokens(row.get("question", "")))
            if score > best_score:
                best_score = score
                best = row
        if best and best_score >= min_overlap:
            hit = dict(best)
            hit["match"] = "similar"
            hit["overlap"] = round(best_score, 2)
            return hit
        return None

    def store(self, question: str, answer: str, sources: list[dict[str, str]]) -> None:
        text = (answer or "").strip()
        if not text or text.startswith("AI Generation failed") or text.startswith("No relevant"):
            return
        row = {
            "question": question.strip(),
            "normalized": _normalize(question),
            "answer": text,
            "sources": sources,
            "saved_at": datetime.now(timezone.utc).isoformat(),
        }
        with _LOCK:
            rows = self._load()
            key = row["normalized"]
            rows = [item for item in rows if item.get("normalized") != key]
            rows.append(row)
            self._save(rows)
