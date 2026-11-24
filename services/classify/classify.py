"""Batch harm classification: score every catalog video on each label in detoks.harm.HARM_LABELS.

Writes data/processed/harm_labels.json  ({pid: {label: score in [0, 1]}}), which Catalog.load() merges.

The real approach is an open decision in PLAN.md (zero-shot CLIP on frames, an LLM on titles + ASR,
or both). `keyword` is a transparent PLACEHOLDER so the pipeline runs end to end; do not report its
output as a classifier result. To add a classifier, subclass HarmClassifier and add it to CLASSIFIERS.

Usage: python services/classify/classify.py [--classifier keyword] [--data-dir data/processed]
"""
from __future__ import annotations

import argparse
import json
import re
from abc import ABC, abstractmethod
from pathlib import Path

from detoks import config
from detoks.catalog import Catalog, Video
from detoks.harm import HARM_LABELS


class HarmClassifier(ABC):
    name: str = ""

    @abstractmethod
    def score(self, video: Video) -> dict[str, float]:
        """Return {label: score in [0, 1]} for every label in HARM_LABELS."""

    def score_all(self, videos: list[Video]) -> dict[str, dict[str, float]]:
        """Override to batch (e.g. one LLM or CLIP call per batch)."""
        return {str(v.pid): self.score(v) for v in videos}


class KeywordClassifier(HarmClassifier):
    """Placeholder: counts keyword hits in the English title and ASR transcript."""
    name = "keyword"
    KEYWORDS: dict[str, list[str]] = {
        "body_image": ["whitening", "whiten", "slim", "lose weight", "weight loss", "diet", "fat", "skinny",
                       "plastic surgery", "double eyelid", "face shape", "ugly", "beautiful skin", "acne"],
        "dangerous_activity": ["stunt", "challenge", "jump off", "don't try", "do not try", "fire", "explode",
                               "dangerous", "risk", "climb", "speeding"],
        "violence": ["fight", "fighting", "beat", "rob", "robbing", "kill", "knife", "gun", "blood", "attack"],
        "gambling": ["bet", "betting", "lottery", "casino", "jackpot", "get rich", "stock tips", "crypto"],
        "sexualized": ["sexy", "hot girl", "bikini", "seductive", "lingerie"],
    }
    TITLE_WEIGHT, ASR_WEIGHT = 0.5, 0.2  # per hit; title hits count more than transcript hits

    def score(self, video: Video) -> dict[str, float]:
        title, asr = video.title_en.lower(), video.asr_en.lower()
        out = {}
        for label in HARM_LABELS:
            words = self.KEYWORDS.get(label, [])
            hits = sum(self.TITLE_WEIGHT * _count(w, title) + self.ASR_WEIGHT * _count(w, asr) for w in words)
            out[label] = round(min(1.0, hits), 3)
        return out


def _count(word: str, text: str) -> int:
    return len(re.findall(rf"\b{re.escape(word)}\b", text))


CLASSIFIERS: dict[str, type[HarmClassifier]] = {KeywordClassifier.name: KeywordClassifier}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--classifier", default="keyword", choices=sorted(CLASSIFIERS))
    ap.add_argument("--data-dir", default=str(config.DATA_DIR))
    args = ap.parse_args()

    catalog = Catalog.load(args.data_dir)
    labels = CLASSIFIERS[args.classifier]().score_all(catalog.videos)
    out = Path(args.data_dir) / "harm_labels.json"
    out.write_text(json.dumps(labels, indent=1))

    flagged = {pid: s for pid, s in labels.items() if max(s.values(), default=0) >= 0.5}
    print(f"{args.classifier}: scored {len(labels)} videos, {len(flagged)} flagged -> {out}")
    for pid, s in list(flagged.items())[:10]:
        top = max(s, key=s.get)
        print(f"  {pid:>4} {top:<18} {s[top]:.2f}  {catalog.get(int(pid)).title_en[:60]}")


if __name__ == "__main__":
    main()
