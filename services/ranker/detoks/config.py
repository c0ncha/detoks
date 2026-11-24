"""Paths and defaults. Override with environment variables; never hard-code machine paths."""
import os
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
DATA_DIR = Path(os.environ.get("DETOKS_DATA_DIR", REPO_ROOT / "data" / "processed"))
# Local dev serves clips from the downloaded sample. In deployment this becomes object storage.
CLIP_DIR = Path(os.environ.get("DETOKS_CLIP_DIR", REPO_ROOT / "data" / "raw" / "sample_raw_file"))
CLIP_BASE_URL = os.environ.get("DETOKS_CLIP_BASE_URL", "")  # e.g. a CDN prefix; empty = served by this API
CORS_ORIGINS = os.environ.get("DETOKS_CORS_ORIGINS", "http://localhost:3000").split(",")
