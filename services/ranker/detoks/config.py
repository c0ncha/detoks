"""Paths and defaults. Override with environment variables; never hard-code machine paths."""
import os
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
DATA_DIR = Path(os.environ.get("DETOKS_DATA_DIR", REPO_ROOT / "data" / "processed"))
# Local dev serves clips from the downloaded sample. In deployment this becomes object storage.
CLIP_DIR = Path(os.environ.get("DETOKS_CLIP_DIR", REPO_ROOT / "data" / "raw" / "sample_raw_file"))
CLIP_BASE_URL = os.environ.get("DETOKS_CLIP_BASE_URL", "")  # e.g. a CDN prefix; empty = served by this API
CORS_ORIGINS = [o for o in os.environ.get("DETOKS_CORS_ORIGINS", "").split(",") if o]
# Dev default: the web app on this machine or on a private network (a phone opening http://<laptop-ip>:3000).
# Set DETOKS_CORS_ORIGIN_REGEX to "" in deployment and list the real origin in DETOKS_CORS_ORIGINS.
CORS_ORIGIN_REGEX = os.environ.get(
    "DETOKS_CORS_ORIGIN_REGEX",
    r"https?://(localhost|127\.0\.0\.1|10(\.\d{1,3}){3}|192\.168(\.\d{1,3}){2}|172\.(1[6-9]|2\d|3[01])(\.\d{1,3}){2})(:\d+)?",
) or None
