"""Offline simulation: run simulated users through each ranker for several days and compare metrics.

THIS IS A SIMULATION, NOT A WELL-BEING STUDY. Simulated users follow the behavior model below, whose
assumptions are ours. Results show how the rankers *behave* under those assumptions, nothing more.

Behavior model (all assumptions; change them in SimUser and say so in the writeup):
  - watch ratio  = video's typical completion x how much the user likes the category, plus noise
  - like/share   = the video's logged rates, scaled up by the user's interest
  - stopping     = small per-video chance, higher after a boring video, plus a nightly time budget
  - drift        = each day, the user's affinity moves toward what they watched (exposure shapes taste)

Usage: python sim/simulate.py [--users 50] [--days 14] [--seed 0] [--out sim/out/results.json]
"""
from __future__ import annotations

import argparse
import copy
import json
import random
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np

from detoks.catalog import Catalog, Video
from detoks.feed import next_batch
from detoks.metrics import entropy, session_summary
from detoks.rankers import make_rankers
from detoks.session import Session, WatchEvent
from detoks.users import PERSONAS, UserProfile, load_dataset_users

BANNER = "SIMULATION ONLY - simulated users under stated assumptions; not evidence of well-being outcomes."


class SimUser:
    BASE_STOP = 0.02          # chance of stopping after any video
    BORED_STOP = 0.08         # extra chance after a video watched < 20%
    BUDGET_MINUTES = 90       # nightly maximum, whatever the feed does
    DRIFT = 0.15              # daily pull of affinity toward the day's watch distribution
    NOISE = 0.15

    def __init__(self, profile: UserProfile, rng: random.Random):
        self.profile = copy.deepcopy(profile)
        self.initial_affinity = dict(profile.affinity)
        self.rng = rng

    def interest(self, root_id: int) -> float:
        top = max(self.profile.affinity.values(), default=1.0) or 1.0
        return self.profile.pref(root_id) / top

    def react(self, v: Video) -> WatchEvent:
        rel = self.interest(v.root_id)
        ratio = v.stat("mean_watch_ratio", 0.3) * (0.3 + 1.7 * rel) + self.rng.gauss(0, self.NOISE)
        ratio = min(max(ratio, 0.02), 1.5)
        boost = 0.5 + 4 * rel
        return WatchEvent(
            pid=v.pid, root_id=v.root_id, duration=v.duration, watch_seconds=ratio * v.duration,
            liked=self.rng.random() < v.stat("cvm_like_rate") * boost,
            shared=self.rng.random() < v.stat("forward_rate") * boost,
            commented=self.rng.random() < v.stat("comment_rate") * boost,
        )

    def stops(self, e: WatchEvent, minutes: float) -> bool:
        p = self.BASE_STOP + (self.BORED_STOP if e.skipped else 0.0)
        return minutes >= self.BUDGET_MINUTES or self.rng.random() < p

    def end_of_day(self, session: Session) -> None:
        secs = session.seconds_by_category()
        total = sum(secs.values())
        if not total:
            return
        cats = set(self.profile.affinity) | set(secs)
        self.profile.affinity = {
            c: (1 - self.DRIFT) * self.profile.pref(c) + self.DRIFT * secs[c] / total for c in cats
        }


def run_day(ranker, sim: SimUser, batch_size: int = 5) -> Session:
    s = Session(sim.profile, ranker.name)
    while True:
        batch = next_batch(ranker, s, batch_size)
        if not batch.items:
            return s
        for r in batch.items:
            e = sim.react(r.video)
            s.record(e)
            if sim.stops(e, s.minutes_watched):
                return s


def relevance_of_served(s: Session, catalog: Catalog, initial: dict[int, float]) -> float:
    """Mean interest (under the user's day-0 taste, max = 1) of what was served: what diversity costs."""
    if not s.served:
        return 0.0
    top = max(initial.values())
    return float(np.mean([initial.get(catalog.get(p).root_id, 0.0) / top for p in s.served]))


def simulate(catalog: Catalog, users: list[UserProfile], days: int, seed: int) -> dict:
    rankers = make_rankers(catalog)
    daily: dict[str, list[list[dict]]] = {name: [[] for _ in range(days)] for name in rankers}
    for name, ranker in rankers.items():
        for i, profile in enumerate(users):
            sim = SimUser(profile, random.Random(seed * 100_003 + i))  # same seed per user across rankers
            for d in range(days):
                s = run_day(ranker, sim)
                summ = session_summary(s, catalog)
                daily[name][d].append({
                    "minutes": summ["minutes_watched"],
                    "topic_entropy": summ["topic_entropy_bits"],
                    "flagged_rate": summ["flagged_rate"],
                    "shares": summ["shares"],
                    "relevance": relevance_of_served(s, catalog, sim.initial_affinity),
                    "taste_entropy": entropy(Counter(sim.profile.affinity)),
                })
                sim.end_of_day(s)

    def mean(rows, k):
        return round(float(np.mean([r[k] for r in rows])), 3)

    keys = ["minutes", "topic_entropy", "taste_entropy", "flagged_rate", "relevance", "shares"]
    by_day = {name: [{k: mean(rows, k) for k in keys} | {"day": d + 1} for d, rows in enumerate(days_)]
              for name, days_ in daily.items()}
    overall = {name: {k: mean([r for rows in days_ for r in rows], k) for k in keys} for name, days_ in daily.items()}
    return {"disclaimer": BANNER, "n_users": len(users), "days": days, "seed": seed,
            "overall": overall, "by_day": by_day}


def pick_users(n: int, seed: int) -> list[UserProfile]:
    pool = [u for u in load_dataset_users().values() if int(u.description.split()[0]) >= 20]
    rng = random.Random(seed)
    return list(PERSONAS.values()) + rng.sample(pool, min(n, len(pool)))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--users", type=int, default=50, help="dataset users to sample (personas are always added)")
    ap.add_argument("--days", type=int, default=14)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--out", default=str(Path(__file__).parent / "out" / "results.json"))
    args = ap.parse_args()

    catalog = Catalog.load()
    res = simulate(catalog, pick_users(args.users, args.seed), args.days, args.seed)
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text(json.dumps(res, indent=1))

    print(f"\n{BANNER}\n{res['n_users']} users x {res['days']} days, seed {res['seed']}\n")
    cols = ["minutes", "topic_entropy", "taste_entropy", "flagged_rate", "relevance", "shares"]
    print(f"{'ranker':<10}" + "".join(f"{c:>15}" for c in cols))
    for name, m in res["overall"].items():
        print(f"{name:<10}" + "".join(f"{m[c]:>15}" for c in cols))
    print("\ntaste entropy (bits) on day 1 -> last day:")
    for name, rows in res["by_day"].items():
        print(f"  {name:<10} {rows[0]['taste_entropy']} -> {rows[-1]['taste_entropy']}")
    print(f"\nwrote {args.out}")


if __name__ == "__main__":
    main()
