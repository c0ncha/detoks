"""The shared ranker interface and feed policies.

A ranker has two jobs, kept separate so features can be added to either one:

  rank(user, session, candidates) -> list[Ranked]   what to show next, in order
  policy.status(session)          -> FeedStatus     whether to keep going, show a break, or end

Every Ranked item carries `reasons` (score term -> contribution) so the UI can show
"why am I seeing this" and the simulation can attribute effects to individual terms.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Callable, Literal

from ..catalog import Catalog, Video
from ..session import Session
from ..users import UserProfile


@dataclass
class RankContext:
    """Everything a score term can read for one rank() call. Computed once per call, not per video."""
    user: UserProfile
    session: Session
    catalog: Catalog
    pref: dict[int, float] = field(default_factory=dict)   # root_id -> [0, 1] preference this session
    extras: dict = field(default_factory=dict)              # per-call values a new term needs


# A score term maps (context, video) to a number. Rankers combine weighted terms.
ScoreFn = Callable[[RankContext, Video], float]


@dataclass
class Term:
    name: str
    weight: float
    fn: ScoreFn


@dataclass
class Ranked:
    video: Video
    score: float
    reasons: dict[str, float] = field(default_factory=dict)


@dataclass
class FeedStatus:
    state: Literal["ok", "break", "ended"]
    reason: str = ""            # machine-readable: "", "break_interval", "time_cap", "feed_complete"
    message: str = ""           # shown to the user
    minutes_watched: float = 0.0
    served: int = 0
    feed_size: int | None = None
    cap_minutes: float | None = None


class FeedPolicy(ABC):
    @abstractmethod
    def status(self, session: Session) -> FeedStatus: ...


class EndlessFeed(FeedPolicy):
    """Baseline: never stops, never suggests a break."""

    def status(self, session: Session) -> FeedStatus:
        return FeedStatus("ok", minutes_watched=session.minutes_watched, served=len(session.served))


@dataclass
class FiniteDailyFeed(FeedPolicy):
    """Detoks: a finite set of videos, an optional user-set time cap, and periodic break cards.

    POC simplification: one session stands in for one day.
    """
    default_feed_size: int = 20
    break_every_minutes: float = 10.0

    def status(self, session: Session) -> FeedStatus:
        size = session.settings.feed_size or self.default_feed_size
        cap = session.settings.daily_cap_minutes
        mins = session.minutes_watched
        base = dict(minutes_watched=mins, served=len(session.served), feed_size=size, cap_minutes=cap)
        if cap is not None and mins >= cap:
            return FeedStatus("ended", "time_cap", f"You hit your {cap:g}-minute limit for today.", **base)
        if len(session.served) >= size:
            return FeedStatus("ended", "feed_complete", f"That's today's {size}. See you tomorrow.", **base)
        if mins - session.last_break_at_minutes >= self.break_every_minutes:
            return FeedStatus("break", "break_interval",
                              f"You've been watching for {mins:.0f} minutes. Stretch, text a friend, or keep going.",
                              **base)
        return FeedStatus("ok", **base)


class Ranker(ABC):
    name: str = ""
    description: str = ""

    def __init__(self, catalog: Catalog, policy: FeedPolicy):
        self.catalog = catalog
        self.policy = policy

    def candidates(self, user: UserProfile, session: Session) -> list[Video]:
        """Videos eligible for the next batch. Default: playable and not yet served this session."""
        seen = session.seen
        return [v for v in self.catalog.videos if v.has_clip and v.pid not in seen]

    @abstractmethod
    def rank(self, user: UserProfile, session: Session, candidates: list[Video]) -> list[Ranked]:
        """Return candidates (or a subset, if some are filtered out) in display order."""

    @staticmethod
    def score_terms(terms: list[Term], ctx: RankContext, v: Video) -> Ranked:
        reasons = {t.name: round(t.weight * t.fn(ctx, v), 4) for t in terms}
        return Ranked(v, sum(reasons.values()), reasons)
