"""Detoks: relevance plus quality and diversity, minus harm, in a finite daily feed.

The ranking is a pipeline with three extension points. Each maps to a harm in docs/background.md:

  1. FILTERS   drop a video entirely               (parent controls -> harmful content exposure)
  2. TERMS     weighted score terms, summed         (harm penalty, passive-watch fatigue, social signals)
  3. RERANK    reorder the scored list              (MMR diversity + topic cap -> echo chambers)
  plus the FEED POLICY (finite feed, time cap, break cards -> addictive reward loops)

To add a feature, write a function and append it to the matching list in __init__.
"""
from __future__ import annotations

from collections import Counter
from typing import Callable

import numpy as np

from ..catalog import Catalog, Video
from ..harm import FLAG_THRESHOLD
from ..session import Session
from ..users import UserProfile
from .base import FiniteDailyFeed, RankContext, Ranked, Ranker, Term
from .signals import mmr_rerank, session_preference

Filter = Callable[[UserProfile, Video], bool]  # True = keep


# ---- filters ------------------------------------------------------------------------------
def parent_controls(user: UserProfile, v: Video) -> bool:
    if v.root_id in user.blocked_categories:
        return False
    return not any(v.harm.get(label, 0.0) >= FLAG_THRESHOLD for label in user.blocked_labels)


# ---- score terms (each returns roughly [-1, 1]; weights live in __init__) -------------------
def relevance(ctx: RankContext, v: Video) -> float:
    return ctx.pref.get(v.root_id, 0.0)


def quality(ctx: RankContext, v: Video) -> float:
    """Catalog percentile of social engagement (shares and comments weigh most), in [0, 1]."""
    return ctx.extras["quality_pct"].get(v.pid, 0.5)


def harm_penalty(ctx: RankContext, v: Video) -> float:
    return -v.harm_score


def passive_fatigue(ctx: RankContext, v: Video) -> float:
    """Long autopilot streaks in a category count against more of it (vs. Baseline, which rewards them)."""
    return -min(1.0, ctx.session.passive_streak(v.root_id) / 3)


def social_quality_score(v: Video) -> float:
    return (v.stat("cvm_like_rate") + 5 * v.stat("comment_rate") + 10 * v.stat("forward_rate")
            + 2 * v.stat("collect_rate") - 20 * v.stat("hate_rate"))


class DetoksRanker(Ranker):
    name = "detoks"
    description = "Relevance + quality + diversity - harm; finite daily feed with breaks."

    # Rerank knobs
    MMR_LAMBDA = 0.6          # 1.0 = pure score, 0.0 = pure novelty
    TOPIC_CAP = 3             # max videos per root category per session
    RECENT_WINDOW = 5         # served videos the MMR step compares against
    # Preference knobs: shares/comments/likes reinforce a topic; passive watch time barely does.
    WATCH_WEIGHT = 0.2
    ACTIVE_WEIGHT = 1.0

    def __init__(self, catalog: Catalog, feed_size: int = 20, break_every_minutes: float = 10.0):
        super().__init__(catalog, FiniteDailyFeed(feed_size, break_every_minutes))
        self.filters: list[Filter] = [parent_controls]
        self.terms: list[Term] = [
            Term("relevance", 1.0, relevance),
            Term("quality", 0.4, quality),
            Term("harm_penalty", 1.5, harm_penalty),
            Term("passive_fatigue", 0.5, passive_fatigue),
        ]
        q = np.array([social_quality_score(v) for v in catalog.videos])
        pct = q.argsort().argsort() / max(len(q) - 1, 1)
        self._quality_pct = {v.pid: float(p) for v, p in zip(catalog.videos, pct)}

    def candidates(self, user: UserProfile, session: Session) -> list[Video]:
        return [v for v in super().candidates(user, session) if all(f(user, v) for f in self.filters)]

    def rank(self, user: UserProfile, session: Session, candidates: list[Video]) -> list[Ranked]:
        pref = session_preference(user, session, self.catalog.root_ids,
                                  watch_weight=self.WATCH_WEIGHT, active_weight=self.ACTIVE_WEIGHT)
        ctx = RankContext(user, session, self.catalog, pref, {"quality_pct": self._quality_pct})
        scored = sorted((self.score_terms(self.terms, ctx, v) for v in candidates), key=lambda r: -r.score)
        served_counts = Counter(self.catalog.get(p).root_id for p in session.served if p in self.catalog)
        return mmr_rerank(scored, self.catalog, lam=self.MMR_LAMBDA,
                          recent_pids=session.served[-self.RECENT_WINDOW:],
                          per_category_cap=self.TOPIC_CAP, category_counts=served_counts)
