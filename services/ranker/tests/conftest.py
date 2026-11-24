"""A small synthetic catalog so tests never need the dataset."""
import numpy as np
import pytest

from detoks.catalog import Catalog, Video
from detoks.users import UserProfile

CATS = {1: "Gaming", 2: "Food", 3: "Sports", 4: "Beauty"}


@pytest.fixture
def catalog() -> Catalog:
    rng = np.random.default_rng(0)
    videos, embs = [], []
    centers = {c: rng.normal(size=16) for c in CATS}
    pid = 1
    for c, name in CATS.items():
        for i in range(10):
            harm = {"body_image": 0.9} if (c == 4 and i < 3) else {"body_image": 0.0}
            videos.append(Video(pid=pid, duration=30 + 3 * i, root_id=c, category=name, title_en=f"{name} {i}",
                                stats={"mean_watch_ratio": 0.5, "cvm_like_rate": 0.01 * i,
                                       "forward_rate": 0.001 * i}, harm=harm))
            e = centers[c] + 0.3 * rng.normal(size=16)
            embs.append(e / np.linalg.norm(e))
            pid += 1
    return Catalog(videos, np.array(embs))


@pytest.fixture
def gamer() -> UserProfile:
    return UserProfile("gamer", {1: 0.85, 2: 0.05, 3: 0.05, 4: 0.05}, display_name="Gamer")


@pytest.fixture
def kid() -> UserProfile:
    return UserProfile("kid", {1: 0.25, 2: 0.25, 3: 0.25, 4: 0.25}, blocked_labels={"body_image"})
