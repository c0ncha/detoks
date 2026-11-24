"""Ranking API. Run: uvicorn detoks.api:app --reload --port 8000  (or `make ranker`).

Flow for one feed:
  POST /sessions                    {user_id, ranker}             -> session_id
  GET  /sessions/{id}/next?n=5                                    -> items + feed status (ok | break | ended)
  POST /sessions/{id}/events        one per video the user leaves -> feed status
  GET  /sessions/{id}/recap                                       -> end-of-feed summary
Interactive docs at /docs.
"""
from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from . import config
from .catalog import Catalog
from .feed import next_batch
from .harm import HARM_LABELS
from .metrics import session_summary
from .rankers import FeedStatus, Ranked, make_rankers
from .session import Session, SessionSettings, SessionStore, WatchEvent
from .users import PERSONAS, UserProfile, load_dataset_users


# ---- request / response models --------------------------------------------------------------
class CreateSession(BaseModel):
    user_id: str = Field(examples=["bob"])
    ranker: str = Field(examples=["detoks"])
    daily_cap_minutes: float | None = None
    feed_size: int | None = None


class EventIn(BaseModel):
    pid: int
    watch_seconds: float = Field(ge=0)
    liked: bool = False
    shared: bool = False
    commented: bool = False
    hated: bool = False


class StatusOut(BaseModel):
    state: str
    reason: str
    message: str
    minutes_watched: float
    served: int
    feed_size: int | None
    cap_minutes: float | None


class ItemOut(BaseModel):
    pid: int
    clip_url: str
    title: str
    category: str
    duration: float
    score: float
    reasons: dict[str, float]
    harm: dict[str, float]
    flagged: bool


class BatchOut(BaseModel):
    items: list[ItemOut]
    status: StatusOut


class UserOut(BaseModel):
    user_id: str
    display_name: str
    description: str
    parent_controls: bool


def _status(s: FeedStatus) -> StatusOut:
    return StatusOut(**{k: getattr(s, k) for k in StatusOut.model_fields})


def _user(u: UserProfile) -> UserOut:
    return UserOut(user_id=u.user_id, display_name=u.display_name, description=u.description,
                   parent_controls=bool(u.blocked_labels or u.blocked_categories))


# ---- app -----------------------------------------------------------------------------------
def create_app(catalog: Catalog | None = None, users: dict[str, UserProfile] | None = None,
               clip_dir: Path = config.CLIP_DIR) -> FastAPI:
    catalog = catalog or Catalog.load()
    users = {**load_dataset_users(), **PERSONAS} if users is None else users
    rankers = make_rankers(catalog)
    store = SessionStore()

    app = FastAPI(title="Detoks ranker", version="0.1.0")
    app.add_middleware(CORSMiddleware, allow_origins=config.CORS_ORIGINS, allow_methods=["*"], allow_headers=["*"])

    def get_session(session_id: str) -> Session:
        s = store.get(session_id)
        if s is None:
            raise HTTPException(404, f"unknown session {session_id}")
        return s

    def item(r: Ranked, request: Request) -> ItemOut:
        v = r.video
        url = f"{config.CLIP_BASE_URL}/{v.pid}.mp4" if config.CLIP_BASE_URL else str(request.url_for("clip", pid=v.pid))
        return ItemOut(pid=v.pid, clip_url=url, title=v.title_en or v.title_cn, category=v.category,
                       duration=v.duration, score=round(r.score, 4), reasons=r.reasons, harm=v.harm, flagged=v.flagged)

    @app.get("/health")
    def health() -> dict:
        return {"ok": True, "videos": len(catalog), "classified": sum(bool(v.harm) for v in catalog.videos)}

    @app.get("/rankers")
    def list_rankers() -> list[dict]:
        return [{"name": r.name, "description": r.description} for r in rankers.values()]

    @app.get("/harm-labels")
    def harm_labels() -> dict[str, str]:
        return HARM_LABELS

    @app.get("/personas", response_model=list[UserOut])
    def personas(dataset_users: int = 3) -> list[UserOut]:
        """Scenario personas first, then a few real dataset users with the most logged interactions."""
        out = [_user(u) for u in PERSONAS.values() if u.user_id in users]
        rest = sorted((u for uid, u in users.items() if uid not in PERSONAS), key=lambda u: u.user_id)
        return out + [_user(u) for u in rest[:dataset_users]]

    @app.post("/sessions")
    def create_session(body: CreateSession) -> dict:
        if body.ranker not in rankers:
            raise HTTPException(400, f"ranker must be one of {sorted(rankers)}")
        if body.user_id not in users:
            raise HTTPException(404, f"unknown user {body.user_id}")
        s = store.add(Session(users[body.user_id], body.ranker,
                              SessionSettings(body.daily_cap_minutes, body.feed_size)))
        return {"session_id": s.id, "ranker": s.ranker, "user": _user(s.user)}

    @app.get("/sessions/{session_id}/next", response_model=BatchOut)
    def next_items(session_id: str, request: Request, n: int = 5) -> BatchOut:
        s = get_session(session_id)
        batch = next_batch(rankers[s.ranker], s, n)
        return BatchOut(items=[item(r, request) for r in batch.items], status=_status(batch.status))

    @app.post("/sessions/{session_id}/events", response_model=StatusOut)
    def post_event(session_id: str, body: EventIn) -> StatusOut:
        s = get_session(session_id)
        if body.pid not in catalog:
            raise HTTPException(404, f"unknown video {body.pid}")
        v = catalog.get(body.pid)
        s.record(WatchEvent(pid=v.pid, root_id=v.root_id, duration=v.duration, **body.model_dump(exclude={"pid"})))
        return _status(rankers[s.ranker].policy.status(s))

    @app.get("/sessions/{session_id}/recap")
    def recap(session_id: str) -> dict:
        s = get_session(session_id)
        return {"ranker": s.ranker, "user": s.user.display_name, **session_summary(s, catalog)}

    @app.get("/clips/{pid}.mp4", name="clip")
    def clip(pid: int) -> FileResponse:
        """Local dev only: streams sample clips from data/raw. Deployed builds set DETOKS_CLIP_BASE_URL."""
        path = clip_dir / f"{pid}.mp4"
        if pid not in catalog or not path.exists():
            raise HTTPException(404, "clip not found")
        return FileResponse(path, media_type="video/mp4")

    return app


def __getattr__(name: str):
    # Lazy so importing detoks.api (e.g. in tests) doesn't require the processed dataset.
    if name == "app":
        globals()["app"] = create_app()
        return globals()["app"]
    raise AttributeError(name)
