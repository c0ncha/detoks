from collections import Counter

import pytest

from detoks.feed import next_batch
from detoks.metrics import entropy
from detoks.rankers import RANKERS, BaselineRanker, DetoksRanker
from detoks.session import Session, SessionSettings, WatchEvent


def watch_all(session, batch, ratio=0.9):
    for r in batch.items:
        session.record(WatchEvent(r.video.pid, r.video.root_id, r.video.duration, ratio * r.video.duration))


@pytest.mark.parametrize("name", sorted(RANKERS))
def test_contract_returns_unseen_candidates_in_order(name, catalog, gamer):
    ranker = RANKERS[name](catalog)
    s = Session(gamer, name)
    cands = ranker.candidates(gamer, s)
    ranked = ranker.rank(gamer, s, cands)
    pids = [r.video.pid for r in ranked]
    assert len(pids) == len(set(pids))
    assert set(pids) <= {v.pid for v in cands}
    assert all(r.reasons for r in ranked), "every item explains its score"


@pytest.mark.parametrize("name", sorted(RANKERS))
def test_feed_never_repeats_until_catalog_exhausted(name, catalog, gamer):
    ranker, s = RANKERS[name](catalog), Session(gamer, name)
    for _ in range(4):
        watch_all(s, next_batch(ranker, s, 5))
    assert len(s.served) == len(set(s.served))


def test_baseline_exploits_top_category(catalog, gamer):
    ranker, s = BaselineRanker(catalog), Session(gamer, "baseline")
    first = next_batch(ranker, s, 10)
    assert Counter(r.video.root_id for r in first.items).most_common(1)[0][0] == 1


def test_baseline_is_endless(catalog, gamer):
    ranker, s = BaselineRanker(catalog), Session(gamer, "baseline")
    for _ in range(12):  # 60 > 40 videos in catalog
        b = next_batch(ranker, s, 5)
        assert b.status.state == "ok" and b.items
        watch_all(s, b)


def test_detoks_is_more_diverse_than_baseline(catalog, gamer):
    cats = {}
    for cls in (BaselineRanker, DetoksRanker):
        ranker, s = cls(catalog), Session(gamer, cls.name)
        watch_all(s, next_batch(ranker, s, 10))
        cats[cls.name] = Counter(catalog.get(p).root_id for p in s.served)
    assert entropy(cats["detoks"]) > entropy(cats["baseline"])
    assert max(cats["detoks"].values()) <= DetoksRanker.TOPIC_CAP


def test_detoks_parent_controls_filter_blocked_labels(catalog, kid):
    ranker, s = DetoksRanker(catalog), Session(kid, "detoks")
    for _ in range(4):
        watch_all(s, next_batch(ranker, s, 5))
    assert not any(catalog.get(p).flagged for p in s.served)


def test_detoks_feed_ends_at_feed_size(catalog, gamer):
    ranker, s = DetoksRanker(catalog), Session(gamer, "detoks", SessionSettings(feed_size=7))
    total = 0
    for _ in range(5):
        b = next_batch(ranker, s, 5)
        total += len(b.items)
        watch_all(s, b)
    assert total == 7
    assert ranker.policy.status(s).reason == "feed_complete"


def test_detoks_time_cap_ends_feed(catalog, gamer):
    ranker, s = DetoksRanker(catalog), Session(gamer, "detoks", SessionSettings(daily_cap_minutes=1))
    watch_all(s, next_batch(ranker, s, 5))  # ~5 x 30s+ = over a minute
    b = next_batch(ranker, s, 5)
    assert b.status.state == "ended" and b.status.reason == "time_cap" and not b.items


def test_detoks_shows_break_once_per_interval(catalog, gamer):
    ranker, s = DetoksRanker(catalog, break_every_minutes=1), Session(gamer, "detoks")
    watch_all(s, next_batch(ranker, s, 3))  # ~1.6 min
    assert next_batch(ranker, s, 1).status.state == "break"
    assert next_batch(ranker, s, 1).status.state == "ok"
