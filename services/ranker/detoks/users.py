"""Who is watching: user profiles from the dataset, plus the scenario personas from docs/background.md."""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

from . import config


@dataclass
class UserProfile:
    user_id: str
    # Root category id -> long-run preference weight (sums to ~1). Missing categories get `floor`.
    affinity: dict[int, float]
    display_name: str = ""
    description: str = ""
    mean_watch_ratio: float = 0.4
    # Parent controls (Katie): harm labels this profile never sees, and categories that are blocked.
    blocked_labels: set[str] = field(default_factory=set)
    blocked_categories: set[int] = field(default_factory=set)
    floor: float = 0.005

    def pref(self, root_id: int) -> float:
        return self.affinity.get(root_id, self.floor)


def _persona(uid: str, name: str, desc: str, weights: dict[int, float], **kw) -> UserProfile:
    total = sum(weights.values())
    return UserProfile(uid, {c: w / total for c, w in weights.items()}, name, desc, **kw)


# Root category ids: see data/category_labels.csv. Weights are hand-set, not fit from data.
PERSONAS: dict[str, UserProfile] = {
    p.user_id: p for p in [
        _persona("bob", "Bob", "Late-night scroller drifting into a narrow loop (gaming, looks, celebrity).",
                 {3: 6, 8: 4, 6: 3, 9: 1, 18: 1}, mean_watch_ratio=0.6),
        _persona("katie-kid", "Katie's kid", "Synthetic child profile with parent controls on (the dataset has no minors).",
                 {17: 4, 9: 3, 3: 3, 25: 2, 12: 1, 15: 1}, mean_watch_ratio=0.5,
                 blocked_labels={"body_image", "dangerous_activity", "violence", "gambling", "sexualized"},
                 blocked_categories={8, 22, 24, 36}),
        _persona("george", "George", "Social user who shares challenge-style videos with friends.",
                 {7: 4, 12: 3, 10: 2, 9: 2, 15: 2, 11: 1}, mean_watch_ratio=0.45),
    ]
}


def load_dataset_users(data_dir: Path | str = config.DATA_DIR) -> dict[str, UserProfile]:
    path = Path(data_dir) / "users.json"
    if not path.exists():
        return {}
    out = {}
    for r in json.loads(path.read_text()):
        uid = f"u{r['user_id']}"
        out[uid] = UserProfile(
            uid, {int(c): w for c, w in r["affinity"].items()},
            display_name=f"Dataset user {r['user_id']}",
            description=f"{r['n_interactions']} logged interactions; age {r['age']}, {r['gender']}",
            mean_watch_ratio=r["mean_watch_ratio"],
        )
    return out
