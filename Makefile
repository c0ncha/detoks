# Detoks dev commands. Run `make help` for the list.
PY ?= .venv/bin/python

.PHONY: help setup data classify ranker web sim test lint

help:  ## list commands
	@grep -E '^[a-z]+:.*##' $(MAKEFILE_LIST) | awk -F':.*## ' '{printf "  make %-9s %s\n", $$1, $$2}'

setup:  ## create .venv, install Python and web deps
	test -d .venv || python3 -m venv .venv
	$(PY) -m pip install -q -r requirements.txt
	cd apps/web && npm install

data:  ## download the 100-clip sample (~2 GB, skips finished files) and build data/processed
	bash data/download_sample.sh
	$(PY) data/build_catalog.py
	$(PY) services/classify/classify.py

classify:  ## re-run harm classification only
	$(PY) services/classify/classify.py

ranker:  ## run the ranking API on :8000 (docs at /docs)
	cd services/ranker && ../../$(PY) -m uvicorn detoks.api:app --reload --port 8000

web:  ## run the web app on :3000
	cd apps/web && npm run dev

sim:  ## run the offline simulation (SIMULATION ONLY, see sim/README.md)
	$(PY) sim/simulate.py

test:  ## Python tests (no dataset needed) + web typecheck and lint
	$(PY) -m pytest -q services/ranker
	cd apps/web && npx tsc --noEmit && npm run lint
