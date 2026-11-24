# Detoks

A proof-of-concept short-form video app that ranks for user well-being instead of watch time.

Built for 17-200 (Ethics and Policy Issues in Computing) at CMU. Detoks runs two recommenders behind the same feed:

- **Baseline**: ranks by predicted watch time in an endless feed, standing in for current platforms.
- **Detoks**: lowers the rank of classified-harmful content, diversifies the feed, ends the feed each day, and adds social features that move people offline.

The demo compares the two, live and in simulation, to support the argument that a platform can put user well-being ahead of watch time and still be worth using.

## Quick start

```bash
make setup    # Python venv + web deps (Python >= 3.11, Node >= 20.9)
make data     # ~2 GB sample download + build the catalog
make ranker   # API on :8000
make web      # app on :3000
```

- [docs/CONTRIBUTING.md](docs/CONTRIBUTING.md): how the code fits together and where each feature goes
- [PLAN.md](PLAN.md): architecture, milestones and open decisions
- [docs/background.md](docs/background.md): the harms, alignment strategy, scenarios and argument maps this project builds on

## Team

Nathan, Caleb, Aayush, Will
