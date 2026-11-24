"""Building blocks shared by rankers: preference estimates and diversity reranking."""
from __future__ import annotations

from collections import Counter

import numpy as np

from ..catalog import Catalog
from ..session import Session
from ..users import UserProfile
from .base import Ranked


def session_preference(user: UserProfile, session: Session, root_ids: list[int],
                       watch_weight: float = 0.0, active_weight: float = 0.0) -> dict[int, float]:
    """Blend long-run affinity with what happened this session; returns root_id -> [0, 1] (max = 1).

    watch_weight:  how much raw watch time this session reinforces a category (Baseline: high).
    active_weight: how much likes/shares/comments reinforce a category (Detoks: high).
    """
    secs = session.seconds_by_category()
    total_secs = sum(secs.values()) or 1.0
    active = Counter(e.root_id for e in session.events if e.active)
    total_active = sum(active.values()) or 1
    raw = {
        c: user.pref(c) + watch_weight * secs[c] / total_secs + active_weight * active[c] / total_active
        for c in root_ids
    }
    top = max(raw.values(), default=1.0) or 1.0
    return {c: w / top for c, w in raw.items()}


def mmr_rerank(items: list[Ranked], catalog: Catalog, lam: float = 0.7,
               recent_pids: list[int] | None = None, per_category_cap: int | None = None,
               category_counts: Counter[int] | None = None) -> list[Ranked]:
    """Maximal Marginal Relevance over visual embeddings, with an optional per-category cap.

    Each step picks argmax  lam * score_norm - (1 - lam) * max_sim(selected + recent).
    Items blocked by the cap go to the end (in score order) rather than being dropped, so a small
    catalog never runs dry.
    """
    if not items:
        return []
    scores = np.array([r.score for r in items])
    span = scores.max() - scores.min()
    norm = (scores - scores.min()) / span if span > 0 else np.ones_like(scores)
    emb = catalog.embeddings_for([r.video.pid for r in items])
    recent = [p for p in (recent_pids or []) if p in catalog]
    anchor = catalog.embeddings_for(recent) if recent else np.zeros((0, emb.shape[1]), np.float32)

    counts = Counter(category_counts or {})
    remaining = list(range(len(items)))
    chosen: list[int] = []
    capped: list[int] = []
    while remaining:
        sel = np.vstack([anchor, emb[chosen]]) if chosen else anchor
        max_sim = (emb[remaining] @ sel.T).max(axis=1) if len(sel) else np.zeros(len(remaining))
        mmr = lam * norm[remaining] - (1 - lam) * max_sim
        k = int(np.argmax(mmr))
        i = remaining.pop(k)
        r = items[i]
        if per_category_cap is not None and counts[r.video.root_id] >= per_category_cap:
            capped.append(i)
            continue
        r.reasons["rerank.similarity_to_recent"] = round(float(max_sim[k]), 4)
        counts[r.video.root_id] += 1
        chosen.append(i)
    out = [items[i] for i in chosen]
    out.extend(sorted((items[i] for i in capped), key=lambda r: -r.score))
    return out
