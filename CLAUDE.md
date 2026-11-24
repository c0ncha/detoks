# CLAUDE.md

Guidance for Claude Code (and humans) working in this repo.

## Project

Detoks is the CMU 17-200 final project: a proof-of-concept short-form video app comparing a watch-time **Baseline** recommender against a well-being-first **Detoks** recommender.

- [PLAN.md](PLAN.md) is the source of truth for architecture, milestones and open decisions. Read it before proposing structural changes.
- [docs/background.md](docs/background.md) holds the ethical argument (harms, alignment strategy, scenarios, argument maps). Every Detoks feature should trace back to a harm listed there.
- The demo exists to support claims. Never present simulation output as evidence of real well-being outcomes; label it as simulation.

## Repo rules

- **The repo is public.** Never commit secrets, `.env` files, raw dataset files or video clips. The dataset has no published license, so clips stay in private storage.
- Data lives in `data/raw/` and `data/processed/` (gitignored). Commit scripts and small manifests (e.g., subset ID lists), never the data itself.

## Branching

> **Bootstrap phase (current):** until the scaffolding is ready for the team, Nathan (with Claude) commits directly to `main` and pushes. The rules below take effect once this note is removed.

- `main` is always demo-able. Never commit directly to `main`; all changes land through a pull request.
- Branch from an up-to-date `main` and name branches `<type>/<short-topic>`, e.g. `feat/baseline-ranker`, `data/subset-selection`, `docs/plan-milestones`.
  - Types: `feat`, `fix`, `data`, `infra`, `docs`, `chore`, `refactor`, `test`.
- One topic per branch. Keep branches short-lived: open a PR early (draft is fine) and merge within a few days.
- Before opening or updating a PR, bring the branch up to date with `git pull origin main` (merge, not rebase, so shared branches never need a force-push).
- PRs merge with a **merge commit** (not squash), so the incremental commit history below is preserved on `main`.
- Delete the branch after merging.

## Tests first

Write the failing test before the code (red → green), one behavior at a time.

- **Ranker, API, metrics:** pytest in `services/ranker/tests/` against the synthetic catalog in `conftest.py`.
- **Anything a user sees or does in the app:** a Playwright test in `apps/web/e2e/` (`make e2e`). It drives the real API and app on a generated fixture dataset, so it needs ffmpeg but no download. Test through what the user sees (text, roles, playing video), not component internals; shared steps live in `e2e/helpers.ts`.
- Run the new test, watch it fail for the reason you expect, then implement. If a test passes on its first run, break the code briefly to prove it can fail.
- A bug report gets a test that reproduces it before the fix (e.g., `e2e/lan-access.spec.ts`).

## Commits

Commit incrementally as work and design progress. Each commit should be one coherent step that a teammate can understand from the log alone.

- Format (Conventional Commits): `<type>(<scope>): <summary>`
  - Scopes: `web`, `ranker`, `classify`, `sim`, `data`, `infra`, `plan`, `docs`.
  - Summary: imperative, ≤72 chars, e.g. `feat(ranker): add MMR diversity rerank to detoks ranker`.
- Add a body when the *why* isn't obvious, especially for design decisions: what was decided, the alternatives considered, and the reason.
- **Design decisions go in the repo, not just chat.** When a decision is made (e.g., an open item in PLAN.md is resolved), update PLAN.md in the same commit using the `plan` scope: `docs(plan): choose Cloud Run for ranker hosting`.
- Don't mix unrelated changes in one commit (e.g., a ranker change and a README fix).
- Claude: commit after each completed step without being asked, on the current feature branch. Push and open PRs only when asked.

## Layout

```
apps/web/          Next.js 16 frontend (read node_modules/next/dist/docs before unfamiliar APIs)
services/ranker/   `detoks` Python package: catalog, sessions, rankers, metrics, FastAPI app, tests
services/classify/ harm classification (batch CLI)
sim/               offline simulation and metrics
data/              download/processing scripts; raw/ and processed/ are gitignored
infra/             deployment config (not yet)
docs/              background, contributing guide, data notes
```

[docs/CONTRIBUTING.md](docs/CONTRIBUTING.md) maps each kind of feature to the file it belongs in. Commands: `make help`. Run `make test` and `make e2e` before every PR.

## Data

- `make data` = download the sample, run `data/build_catalog.py` (→ `data/processed/`), then run the classifier. Rebuild after changing the build script.
- `data/download_sample.sh` downloads the 100-clip sample plus metadata into `data/raw/` (~2 GB). Re-runnable.
- The full clip set is 3.3 TB. Never bulk-download `raw_file/`. Select a subset from the interaction CSV first.
- Upstream misspells `interaciton` in some filenames; match the actual names on disk.
