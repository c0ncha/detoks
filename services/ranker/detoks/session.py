"""Session state: everything a ranker may know about the current viewing session.

The app posts one WatchEvent per video the user leaves (swipe, end of feed). Rankers read derived
views of the history (minutes watched, per-category watch time, passive streaks) from here, so
new signals are added as properties on Session rather than recomputed in each ranker.
"""
from __future__ import annotations

import time
import uuid
from collections import Counter
from dataclasses import dataclass, field

from .users import UserProfile


@dataclass
class WatchEvent:
    pid: int
    root_id: int
    duration: float
    watch_seconds: float
    liked: bool = False
    shared: bool = False
    commented: bool = False
    hated: bool = False
    ts: float = field(default_factory=time.time)

    @property
    def watch_ratio(self) -> float:
        return self.watch_seconds / max(self.duration, 1.0)

    @property
    def active(self) -> bool:
        """Did the user do something social with it, rather than only watch?"""
        return self.liked or self.shared or self.commented

    @property
    def skipped(self) -> bool:
        return self.watch_ratio < 0.2


@dataclass
class SessionSettings:
    daily_cap_minutes: float | None = None  # user-set time limit; None = no limit
    feed_size: int | None = None            # finite feed length; None = ranker default


@dataclass
class Session:
    user: UserProfile
    ranker: str
    settings: SessionSettings = field(default_factory=SessionSettings)
    id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    started_at: float = field(default_factory=time.time)
    events: list[WatchEvent] = field(default_factory=list)
    served: list[int] = field(default_factory=list)  # pids in the order they were sent to the client
    breaks_shown: int = 0
    last_break_at_minutes: float = 0.0

    # ---- derived views -------------------------------------------------------------------
    @property
    def seen(self) -> set[int]:
        return set(self.served)

    @property
    def minutes_watched(self) -> float:
        return sum(e.watch_seconds for e in self.events) / 60

    def seconds_by_category(self) -> Counter[int]:
        c: Counter[int] = Counter()
        for e in self.events:
            c[e.root_id] += e.watch_seconds
        return c

    def passive_streak(self, root_id: int | None = None) -> int:
        """Consecutive most-recent events (optionally in one category) watched mostly through with no
        social action. The Detoks ranker treats a long streak as a sign of autopilot scrolling."""
        n = 0
        for e in reversed(self.events):
            if root_id is not None and e.root_id != root_id:
                continue
            if e.active or e.watch_ratio < 0.5:
                break
            n += 1
        return n

    def record(self, event: WatchEvent) -> None:
        self.events.append(event)


class SessionStore:
    """In-memory store. Swap for a Postgres-backed store with the same methods when we deploy."""

    def __init__(self) -> None:
        self._sessions: dict[str, Session] = {}

    def add(self, s: Session) -> Session:
        self._sessions[s.id] = s
        return s

    def get(self, session_id: str) -> Session | None:
        return self._sessions.get(session_id)
