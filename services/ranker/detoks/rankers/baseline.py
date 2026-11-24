"""Baseline: stands in for current platforms. Maximizes predicted watch time in an endless feed.

Watch time this session feeds straight back into preference (the reinforcement loop we critique),
and there is no diversity, harm handling or stopping point.
"""
from __future__ import annotations

from ..catalog import Catalog, Video
from ..session import Session
from ..users import UserProfile
from .base import EndlessFeed, RankContext, Ranked, Ranker, Term
from .signals import session_preference

WATCH_REINFORCEMENT = 1.5  # how strongly this session's watch time pulls toward more of the same


def predicted_watch_seconds(ctx: RankContext, v: Video) -> float:
    # Expected watch = duration x the video's typical completion x how much this user likes the topic.
    return v.duration * v.stat("mean_watch_ratio", 0.3) * (0.2 + 1.6 * ctx.pref.get(v.root_id, 0.0))


class BaselineRanker(Ranker):
    name = "baseline"
    description = "Maximize predicted watch time; endless feed."

    def __init__(self, catalog: Catalog):
        super().__init__(catalog, EndlessFeed())
        self.terms = [Term("predicted_watch_seconds", 1.0, predicted_watch_seconds)]

    def candidates(self, user: UserProfile, session: Session) -> list[Video]:
        fresh = super().candidates(user, session)
        if fresh:
            return fresh
        # Endless: once everything is seen, recycle the least recently served half.
        last = {pid: i for i, pid in enumerate(session.served)}
        pool = sorted((v for v in self.catalog.videos if v.has_clip), key=lambda v: last.get(v.pid, -1))
        return pool[: max(1, len(pool) // 2)]

    def rank(self, user: UserProfile, session: Session, candidates: list[Video]) -> list[Ranked]:
        pref = session_preference(user, session, self.catalog.root_ids, watch_weight=WATCH_REINFORCEMENT)
        ctx = RankContext(user, session, self.catalog, pref)
        ranked = [self.score_terms(self.terms, ctx, v) for v in candidates]
        return sorted(ranked, key=lambda r: -r.score)
