# Simulation

**Simulation only.** Simulated users behave according to assumptions we chose (see the docstring in
[simulate.py](simulate.py)). Results show how the rankers behave under those assumptions. They are
not evidence of real well-being outcomes, and every chart or claim built on them must say so.

```bash
make sim                     # or: python sim/simulate.py --users 50 --days 14 --seed 0
```

Writes `sim/out/results.json` (gitignored): overall and per-day means per ranker.

| Metric | Meaning |
|---|---|
| `minutes` | minutes watched per simulated day |
| `topic_entropy` | entropy (bits) of that day's watch time across root categories; higher = more varied |
| `taste_entropy` | entropy of the simulated user's affinity after daily drift; falling = echo-chamber narrowing |
| `flagged_rate` | share of served videos the harm classifier flags (currently the keyword **placeholder**) |
| `relevance` | mean day-0 interest of served videos (max 1): what diversity costs |
| `shares` | simulated shares per day |

## How to extend

- **New metric**: add it to `detoks.metrics.session_summary` (so the in-app recap gets it too), then to the
  row in `simulate()`.
- **New behavior assumption**: change `SimUser` and document it in the module docstring.
- **New ranker or ablation**: register it in `detoks/rankers/__init__.py`; the simulation runs every registered ranker.

## First run (2026-11-24): what it does and doesn't show

53 users (3 personas + 50 dataset users with ≥20 interactions) × 14 days, seed 0, 78-clip sample catalog:

| ranker | minutes | topic_entropy | taste_entropy | flagged_rate | relevance | shares |
|---|---|---|---|---|---|---|
| baseline | 26.7 | 2.31 | 3.04 | 0.061 | 0.26 | 0.10 |
| detoks | 11.0 | 1.77 | 2.74 | 0.001 | 0.28 | 0.05 |

**This run does not show the diversity effect we expect**: Detoks sessions have *lower* topic entropy and
simulated taste narrows more. Likely causes, to fix before we draw anything from these numbers:

1. **Session-length confound.** Entropy rises with the number of videos, and Baseline sessions are ~2.4× longer.
   Compare at equal length (e.g., the first N videos) or normalize.
2. **Baseline is duration-dominated.** Clip lengths run from 13 s to 155 s, so "maximize predicted watch seconds"
   mostly picks long videos from any category, which makes Baseline accidentally diverse. Real watch-time models
   are personalized far more strongly; consider predicting watch ratio per user rather than raw seconds.
3. **Catalog is tiny.** 78 clips over 24 categories, most with 1–3 videos, leaves no room for an echo chamber.
   The simulation doesn't need clips, so it should run on the full subset pool (milestone 0) once embeddings
   for it are downloaded.
4. **Detoks relevance dominates** its score (weight 1.0 vs quality 0.4) and serves the user's top categories first.

The flagged-rate gap reflects the keyword placeholder classifier and the harm penalty working as coded. It is
not a classifier result.
