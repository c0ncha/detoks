"""Serving a feed: ask the policy whether to continue, rank candidates, record what was served.

The API and the simulation both go through next_batch(), so they exercise the same code path.
"""
from __future__ import annotations

from dataclasses import dataclass

from .rankers import FeedStatus, Ranked, Ranker
from .session import Session


@dataclass
class Batch:
    items: list[Ranked]
    status: FeedStatus


def next_batch(ranker: Ranker, session: Session, n: int = 5) -> Batch:
    status = ranker.policy.status(session)
    if status.state == "ended":
        return Batch([], status)
    if status.state == "break":
        session.breaks_shown += 1
        session.last_break_at_minutes = session.minutes_watched
    if status.feed_size is not None:
        n = min(n, status.feed_size - len(session.served))
    ranked = ranker.rank(session.user, session, ranker.candidates(session.user, session))[:n]
    session.served.extend(r.video.pid for r in ranked)
    return Batch(ranked, status)
