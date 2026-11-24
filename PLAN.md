# Detoks Project Plan

Status: **draft**, with a working local proof of concept (2026-11-24). The open decisions at the bottom block dates and some stack choices. To find where a feature goes, see [docs/CONTRIBUTING.md](docs/CONTRIBUTING.md).

## Goal

Build a working web app (mobile and desktop) on a real short-form video dataset. It runs two recommenders side by side, and the demo shows how they differ in behavior and outcomes. Every Detoks feature maps to a harm from our CT3 work (see [docs/background.md](docs/background.md)).

## Dataset

[tsinghua-fib-lab/ShortVideo_dataset](https://github.com/tsinghua-fib-lab/ShortVideo_dataset) (WWW 2025, [paper](https://arxiv.org/pdf/2502.05922)). We use a subset.

What it gives us:
- **Raw videos** (`raw_file/<video_id>.mp4`): real playback in the app.
- **Interaction logs** (`interaciton_filtered.csv`, misspelled upstream): `watch_time`, `cvm_like`, `comment`, `follow`, `collect`, `forward` (share), `effective_view`, `hate`, with timestamps. Baseline trains on `watch_time`. Detoks can use `forward`/`comment` as social signals and `hate` as negative feedback. The simulation replays real user behavior.
- **Video attributes**: 3-level categories (`category_cn_en.csv`), duration, author, tags, title. Categories drive the diversity reranking and the echo-chamber metric (topic entropy).
- **English text** (`title_en/`, `asr_en/`): input for the harm classifier.
- **Precomputed visual features** (`video_feature_total/<video_id>.npy`): video embeddings, so we don't run our own encoder.
- **User attributes** (age, gender, city tier): could seed the demo personas, e.g., a young user for Katie's kids.

Sizes on the Tsinghua server (measured 2026-11-20):

| Item | Files | Size |
|---|---|---|
| `raw_file/` (all clips) | 153,561 | **3.3 TB** (~21.6 MB per clip) |
| `sample_raw_file/` (+ matching `sample_*` features and text) | 100 | 1.6 GB |
| `video_feature_total/` | 153,561 | 1.3 GB |
| `interaction_sampled.csv` | 1 | 153 MB |
| `categories_cn_en.csv` | 1 | 31 KB |
| `title_en/title_en/`, `asr_en/` | 153k each | small `.txt` files |

Notes:
- Download credentials are in the upstream README. Start with the `sample_*` folders on the Tsinghua server.
- The large-file server allows **3 concurrent connections**, so a full download is slow. Subset by user and video IDs first.
- **No license is published.** The repo is public, so we never commit or rehost clips publicly. Host the subset in private storage and serve it only to the demo.
- The content comes from a Chinese platform. English titles and ASR exist, but on-screen text and audio are mostly Chinese, so the classifier should rely on English text and visual features rather than raw audio.

## The two recommenders

Both share one interface: `rank(user, session_state, candidates) -> ordered list`.

| | Baseline | Detoks |
|---|---|---|
| Objective | Maximize predicted watch time | Relevance, plus diversity and quality, minus a harm penalty |
| Feed length | Endless | Finite daily set ("best N today"), then a recap |
| Session signal | Watch time is the only reward | Watching passively for a long time counts against more of the same; shares and comments count for |
| Diversity | None (pure exploitation) | Reranked for diversity (MMR) over video embeddings, with a cap on any one topic per session |
| Harm handling | None | The classifier score lowers the rank of, or filters out, flagged videos |
| Time limits | None | The user sets a daily cap; break cards appear at the cap |

## Features → harms → scenarios

| Feature | Harm addressed | Scenario |
|---|---|---|
| Diversity reranking and topic caps | Echo chambers | Bob |
| Finite daily feed, user-set caps, break cards | Addictive variable reward loops | Bob |
| Harm classification layer (body image, dangerous activities, etc.) | Harmful content exposure | Bob, Katie |
| Parent profile with content filters and suggested real-world activities | Lack of real-world connection | Katie |
| Share to a friend group, turn a video into a challenge, schedule it together | Lack of real-world connection | George |

## Architecture (proposed)

```
Next.js PWA (mobile + desktop)
  ├─ swipe feed, compare mode, parent profile, friends and challenges
  │
  ├──> Ranking service (Python / FastAPI)
  │      ├─ baseline ranker
  │      ├─ detoks ranker
  │      └─ session state, updated on every watch or swipe event
  │
  ├──> Postgres + pgvector (Supabase): users, videos, embeddings, harm labels, events, social
  │
  └──> Object storage + CDN: video subset (~2–5k clips)

Classifier: runs ahead of time over the subset, plus a live path when a video is uploaded
Hosting: Vercel (web) + Cloud Run or Fly (ranker)
```

"Real-time" means each interaction event updates session state, and the next batch is reranked using it. No streaming infrastructure is needed at this scale.

## Demo

1. **Live side-by-side**: the same starting profile running on Baseline and Detoks at once.
2. **Simulation dashboard**: simulated users built from dataset interactions run through both rankers over many sessions. Metrics:
   - minutes watched
   - topic entropy over time (echo-chamber drift)
   - how often harmful content is shown
   - relevance given up for diversity

   **Label this clearly as simulation, not a well-being study.**
3. **Scenario walkthroughs**: Bob, Katie, George.

## Proof-of-concept decisions (2026-11-24)

The skeleton runs locally end to end: sample clips → catalog → both rankers → swipe feed and compare mode → events → recap, plus the simulation. Decisions made to get there:

- **Local-first, no cloud yet.** The catalog is files in `data/processed/` (`catalog.json`, `embeddings.npy`, `users.json`, `harm_labels.json`), and sessions live in memory behind `SessionStore`. Postgres + pgvector stays the plan for deployment. Deferring it keeps setup to `make setup && make data` while the cloud budget is open, and the swap is contained (`Catalog.load`, `SessionStore`).
- **One core Python package (`detoks`, in `services/ranker/`)** shared by the API, the classifier and the simulation, so the app and the metrics run the same ranking code (`feed.next_batch`).
- **Ranker = ranking + feed policy.** `rank()` orders candidates; a separate `FeedPolicy` decides ok / break / ended. Detoks is a pipeline of filters → weighted score terms → rerank (MMR + topic cap), so most features are one function appended to a list. Every ranked item carries per-term `reasons` for the "why?" UI and for ablations.
- **Baseline** maximizes predicted watch seconds, and this session's watch time reinforces preference. **Detoks** reinforces on likes, shares and comments, penalizes passive streaks and harm, and diversifies.
- **Visual embeddings are mean-pooled, then centered** before normalizing. Raw features have pairwise cosine ~0.998, which made MMR a no-op.
- **One session stands in for one day** in the finite feed.
- **The harm classifier is a keyword placeholder** behind a `HarmClassifier` interface, until the classifier decision below is made.
- **The first simulation run does not yet show a diversity gain for Detoks.** See [sim/README.md](sim/README.md) for the numbers and likely causes. Fix the measurement before using any results.

## Milestones

Dates are to be set once the deadline is confirmed.

| # | Milestone | Done when |
|---|---|---|
| 0 | Setup and data | Tiny sample explored, subset selected, metadata and embeddings loaded into Postgres, clips in storage |
| 1 | Feed and Baseline | The swipe feed plays real clips; Baseline ranks them; events are logged |
| 2 | Detoks ranker and classifier | Harm labels on every clip; Detoks ranker live; compare mode works |
| 3 | Features | Caps and break cards, finite feed and recap, parent profile, friends and challenges |
| 4 | Simulation and dashboard | Both rankers evaluated on simulated users; dashboard shows the metrics |
| 5 | Demo polish | Deployed, scripted walkthrough rehearsed |

Progress (2026-11-24), on the 78-clip sample: **M1** done locally (events are in memory, not Postgres). **M2** partial: the Detoks ranker and compare mode work, but the classifier is a placeholder. **M3** partial: caps, break cards, finite feed, recap and parent-control filters work; there's no parent settings UI and no friends or challenges yet. **M4** partial: the simulation harness exists, but there's no dashboard and the metrics need fixing. **M0** remaining: select the subset, set up Postgres and storage.

## Repo layout

```
apps/web/          Next.js 16 frontend: feed, compare, picker
services/ranker/   `detoks` package: catalog, sessions, both rankers, metrics, FastAPI app, tests
services/classify/ harm classification (batch CLI; upload path later)
sim/               offline simulation and metrics
data/              download + catalog build scripts, category label map (no raw data committed)
infra/             deployment config (not yet)
docs/              background, contributing guide, data notes
```

## Open decisions

- [x] **Dataset**: tsinghua-fib-lab ShortVideo_dataset (see above)
- [ ] **Subset size**: how many users and videos (proposal: ~2–5k videos, the users who watched them)
- [ ] **Deadline and deliverables**: live demo, paper, presentation? Rubric?
- [ ] **Team roles and language comfort** (Python / TypeScript)
- [ ] **Cloud budget**: student credits, or free tiers only
- [ ] **Classifier approach**: zero-shot CLIP on frames, an LLM on captions and thumbnails, or both
- [ ] **Simulation metrics**: compare topic entropy at equal session length, and decide how Baseline should predict watch time (raw seconds is dominated by clip duration)
- [ ] **When to move to Postgres**: needed for persistent history and for deployment; not needed for local development

## Notes

- This repo is **public**. Never commit API keys, `.env` files or raw dataset files. Check the dataset license before redistributing any clips.
