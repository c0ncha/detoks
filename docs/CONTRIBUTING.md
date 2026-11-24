# Contributing: where your feature goes

Branch and commit rules are in [CLAUDE.md](../CLAUDE.md). This page covers how the code fits together and where each kind of change belongs.

## Get running (about 10 minutes, plus the ~2 GB download)

```bash
make setup     # .venv + Python deps + web deps
make data      # download the sample, build data/processed, run the harm classifier
make ranker    # terminal 1: API on http://localhost:8000 (try /docs)
make web       # terminal 2: app on http://localhost:3000
make test      # Python tests + typecheck + lint; synthetic catalog, no dataset needed
make e2e       # Playwright: real API + app in a browser on a generated fixture (needs ffmpeg)
```

Requires Python ≥ 3.11, Node ≥ 20.9 and ffmpeg (for e2e fixtures). To use the app from your phone, open `http://<your-laptop-ip>:3000` on the same Wi-Fi; `make ranker` and `make web` both accept LAN connections.

**Write the test first.** See "Tests first" in [CLAUDE.md](../CLAUDE.md). For app behavior, add a spec in `apps/web/e2e/`. The e2e servers run on ports 8100/3100 with their own build dir, so they don't disturb your dev servers. `npx playwright test --ui` (in `apps/web`) is the easiest way to watch and debug a test.

## How a video gets to the screen

```
data/raw  --build_catalog.py-->  data/processed/{catalog.json, embeddings.npy, users.json}
                                      ^ harm_labels.json  <-- services/classify/classify.py
                                      |
              detoks.catalog.Catalog.load()  (one shared, read-only Catalog)
                                      |
  web Feed --POST /sessions-->  Session (user, ranker, settings, events, served)
           --GET  /next------>  feed.next_batch(): ranker.policy.status -> ranker.candidates -> ranker.rank
           <-- items + status   (status: ok | break | ended)
           --POST /events---->  Session.record(WatchEvent)   one per video the user swipes away from
                                      |
  sim/simulate.py ------------------->  same feed.next_batch() with simulated users
```

The API and the simulation share `feed.next_batch`. Any change you make to a ranker shows up in both the app and the metrics.

## The ranker interface

`services/ranker/detoks/rankers/base.py`

- `rank(user, session, candidates) -> list[Ranked]` decides the order. Each `Ranked` has `score` and `reasons` (term → contribution; the contributions sum to the score). The app's "why?" button shows `reasons`.
- `candidates(user, session)` decides what's eligible. The default is playable clips not yet served this session.
- `policy.status(session)` decides whether the feed continues, shows a break card, or ends.

## Recipes

### Change how Detoks scores videos
`detoks/rankers/detoks.py`. Write `def my_term(ctx: RankContext, v: Video) -> float` (return roughly −1 to 1) and append `Term("my_term", weight, my_term)` to `self.terms`. If it needs something computed once per call, put that in `ctx.extras` inside `rank()`. Add a test in `tests/test_rankers.py`.

### Filter videos out completely (e.g., more parent controls)
Same file: write `def my_filter(user, v) -> bool` (True = keep) and append it to `self.filters`. Per-user settings belong on `UserProfile` (`detoks/users.py`).

### Change diversity or topic caps
`MMR_LAMBDA`, `TOPIC_CAP` and `RECENT_WINDOW` on `DetoksRanker`; the algorithm is `mmr_rerank` in `detoks/rankers/signals.py`.

### Change feed length, time limits or break cards
`FiniteDailyFeed` in `base.py`. User-set values travel in `SessionSettings` (`detoks/session.py`) and the `POST /sessions` body.

### Add a session signal (e.g., "late-night viewing")
Add a property or method to `Session` in `detoks/session.py`. That keeps it in one place for every ranker and metric. If it needs new client data, add the field to `WatchEvent`, `EventIn` in `api.py`, and `WatchEventIn` in `apps/web/lib/api.ts`.

### Add a harm label or a real classifier
Labels live in `detoks/harm.py`. Classifiers subclass `HarmClassifier` in `services/classify/classify.py` and register in `CLASSIFIERS`. Then run `python services/classify/classify.py --classifier <name>`. The keyword classifier is a placeholder; don't report its output as a result.

### Add a ranker variant or ablation (e.g., "Detoks without MMR")
Subclass `Ranker` (or `DetoksRanker`), give it a unique `name`, and register it in `detoks/rankers/__init__.py`. The API and the simulation pick it up automatically. The web app's `RankerName` type lists the names it shows.

### Add a metric
Add it to `session_summary` in `detoks/metrics.py` (the in-app recap gets it too), then to the row in `sim/simulate.py`. See [sim/README.md](../sim/README.md).

### Add a screen or card to the app
Start with a Playwright spec in `apps/web/e2e/` that describes what the viewer sees and does.
New routes go in `apps/web/app/<route>/`. A page that reads the URL is a server `page.tsx` that wraps a client component in `<Suspense>` (see `app/feed/`). New in-feed card types (e.g., a challenge prompt) go in the `Row` union in `components/Feed.tsx`. Next 16 differs from older versions, so check `apps/web/node_modules/next/dist/docs/` first.

### Add an API endpoint
Inside `create_app()` in `detoks/api.py`. Add a test in `tests/test_api.py` that uses the `catalog` fixture.

## Things that are deliberately simple for now

| Simplification | Where | Replace when |
|---|---|---|
| Sessions live in memory and are lost on restart | `SessionStore` | Persistent history or multi-instance hosting is needed (Postgres; same methods) |
| One session = one "day" | `FiniteDailyFeed` | Multi-day use in the app matters |
| Catalog = 78 sample clips; JSON + .npy files | `data/build_catalog.py` | The subset is chosen (milestone 0); the sim should use the full pool first, since it needs no clips |
| Clips served by the API from `data/raw` | `/clips/{pid}.mp4` | Deploying: set `DETOKS_CLIP_BASE_URL` to private storage |
| Keyword harm classifier | `services/classify` | The classifier approach is decided |
| Personas' affinities are hand-set | `detoks/users.py` | Never, but document them in the writeup |
