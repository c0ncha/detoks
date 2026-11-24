"""Session metrics, shared by the in-app recap and the offline simulation."""
from __future__ import annotations

import math
from collections import Counter

from .catalog import Catalog
from .session import Session


def entropy(counts: Counter | dict) -> float:
    """Shannon entropy in bits. Higher = watch time spread over more topics (less echo chamber)."""
    total = sum(counts.values())
    if total <= 0:
        return 0.0
    return -sum((c / total) * math.log2(c / total) for c in counts.values() if c > 0)


def session_summary(session: Session, catalog: Catalog) -> dict:
    by_cat = session.seconds_by_category()
    watched = [e for e in session.events if not e.skipped]
    flagged = [p for p in session.served if p in catalog and catalog.get(p).flagged]
    top = by_cat.most_common(1)
    total = sum(by_cat.values())
    return {
        "minutes_watched": round(session.minutes_watched, 2),
        "videos_served": len(session.served),
        "videos_watched": len(watched),
        "likes": sum(e.liked for e in session.events),
        "shares": sum(e.shared for e in session.events),
        "comments": sum(e.commented for e in session.events),
        "topic_entropy_bits": round(entropy(by_cat), 3),
        "top_category_share": round(top[0][1] / total, 3) if top and total else 0.0,
        "flagged_served": len(flagged),
        "flagged_rate": round(len(flagged) / len(session.served), 3) if session.served else 0.0,
        "minutes_by_category": {
            catalog.category_names.get(c, f"Category {c}"): round(s / 60, 2) for c, s in by_cat.most_common()
        },
    }

