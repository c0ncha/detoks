"""The video catalog: metadata, embeddings and harm labels, loaded once and shared read-only.

Built by data/build_catalog.py; harm labels by services/classify. A Catalog can also be built
in memory (see tests/conftest.py), so tests and experiments never need the dataset.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

from . import config
from .harm import FLAG_THRESHOLD


@dataclass
class Video:
    pid: int
    duration: float
    root_id: int
    category: str
    title_en: str = ""
    asr_en: str = ""
    title_cn: str = ""
    author_id: int = 0
    author_fans: int = 0
    tags_cn: list[str] = field(default_factory=list)
    has_clip: bool = True
    # Smoothed per-video rates from the interaction log: mean_watch_ratio, cvm_like_rate, ...
    stats: dict[str, float] = field(default_factory=dict)
    # Harm label -> score in [0, 1], from the classifier. Empty means "not classified yet".
    harm: dict[str, float] = field(default_factory=dict)

    @property
    def harm_score(self) -> float:
        return max(self.harm.values(), default=0.0)

    @property
    def flagged(self) -> bool:
        return self.harm_score >= FLAG_THRESHOLD

    def stat(self, name: str, default: float = 0.0) -> float:
        return self.stats.get(name, default)


class Catalog:
    def __init__(self, videos: list[Video], embeddings: np.ndarray):
        assert len(videos) == len(embeddings), "one embedding row per video"
        self.videos = videos
        self.embeddings = embeddings.astype(np.float32)
        self._index = {v.pid: i for i, v in enumerate(videos)}
        self.category_names = {v.root_id: v.category for v in videos}

    def __len__(self) -> int:
        return len(self.videos)

    def __contains__(self, pid: int) -> bool:
        return pid in self._index

    def get(self, pid: int) -> Video:
        return self.videos[self._index[pid]]

    def embedding(self, pid: int) -> np.ndarray:
        return self.embeddings[self._index[pid]]

    def embeddings_for(self, pids: list[int]) -> np.ndarray:
        return self.embeddings[[self._index[p] for p in pids]]

    @property
    def root_ids(self) -> list[int]:
        return sorted({v.root_id for v in self.videos})

    @classmethod
    def load(cls, data_dir: Path | str = config.DATA_DIR) -> "Catalog":
        data_dir = Path(data_dir)
        path = data_dir / "catalog.json"
        if not path.exists():
            raise FileNotFoundError(
                f"{path} not found. Run `make data` (data/download_sample.sh, then data/build_catalog.py)."
            )
        records = json.loads(path.read_text(encoding="utf-8"))
        labels_path = data_dir / "harm_labels.json"
        labels = json.loads(labels_path.read_text()) if labels_path.exists() else {}
        videos = []
        for r in records:
            r["harm"] = labels.get(str(r["pid"]), {})
            videos.append(Video(**r))
        return cls(videos, np.load(data_dir / "embeddings.npy"))
