# Data notes

Findings from profiling `interaction_sampled.csv` and the 100-clip sample (2026-11-20). To reproduce: `python data/profile_interactions.py`.

## What's in the interaction log

| | |
|---|---|
| Interactions | 129,483 (the CSV has 794k rows: **one row per tag**, ~6 tags per interaction, so dedupe on `user_id, pid, exposed_time`) |
| Users / videos / authors | 6,654 / 31,496 / 23,242 |
| Time span | **One week**: 2022-09-16 to 2022-09-22 |
| Interactions per user | median 10 (10th–90th percentile: 2–48) |
| Interactions per video | median 2; only 7,565 videos have ≥5 |
| Video duration | median 56 s; 16,357 videos ≤60 s, 20,197 ≤90 s |
| Watch time / duration | median 0.31 |

Engagement rates per interaction:

| click | like | collect | follow | comment | forward (share) | hate |
|---|---|---|---|---|---|---|
| 60.5% | 2.0% | 0.55% | 0.46% | 0.25% | 0.23% | 0.07% |

## Implications for design

- **The log is sparse.** With a median of 10 interactions per user, we can't faithfully replay a user's whole feed. The simulation needs a **user model** fit from the log (e.g., per-user category affinity plus a watch-ratio model), with the rankers evaluated against it. State this assumption in the writeup.
- **Social signals are rare.** Shares and comments each occur in ~0.25% of interactions. Detoks can use them, but per-video estimates will be noisy; use smoothing or pool at the category level.
- **Watch time is the dominant signal**, which is good: that's exactly what Baseline should optimize, and it reproduces the incentive we critique.
- **Categories are coarse.** Almost every video is tagged only at the root level (36 root categories), so the secondary and tertiary levels are nearly empty. Measure diversity and echo chambers with **root category + visual embedding**, plus `tag_name` for finer topics (tags are in Chinese).
- **Category names are machine-translated.** Example: "quadratic" is 二次元 (anime/ACG). Build a cleaned label map before showing categories in the UI.
- **No users under 18** (median age 46). Katie's kids scenario needs a synthetic persona; the "parent-child" category (1,366 videos) is useful content for it.
- **Visual features** are `(8, 256)` float32 per video, likely 8 frames × 256 dims. Mean-pool to a 256-d embedding for pgvector.
- **English titles are short and useful for the classifier.** Example from the sample: "Exploring Secret Whitening Techniques for 5 Years" is a body-image case.
- **Sample coverage:** 78 of the 100 sample clips (pids 1–100) appear in the interaction log.

## Candidate subset pools

| Filter | Videos | Interactions covered | Users |
|---|---|---|---|
| ≤60 s, ≥5 interactions | 3,761 | 38,012 | 5,412 |
| ≤60 s, ≥3 interactions | 7,738 | 51,473 | 5,685 |
| ≤90 s, ≥5 interactions | 4,604 | 46,887 | 5,715 |
| ≤90 s, ≥3 interactions | 9,526 | 63,564 | 5,958 |

**Proposal:** start from "≤60 s, ≥5 interactions" (3,761 videos). Download clips for ~1,500 of them, stratified by root category so the diversity reranking has room to work and over-sampling categories relevant to the harms (beauty, wear it, healthy, movement, parent-child, emotion). Keep all 3,761 in the database (metadata and embeddings are tiny) for the simulation, which doesn't need the clips.
