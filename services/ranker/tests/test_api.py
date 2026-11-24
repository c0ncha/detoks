from fastapi.testclient import TestClient

from detoks.api import create_app


def test_session_flow(catalog, gamer, tmp_path):
    client = TestClient(create_app(catalog, {"gamer": gamer}, clip_dir=tmp_path))
    assert client.get("/health").json()["videos"] == len(catalog)

    sid = client.post("/sessions", json={"user_id": "gamer", "ranker": "detoks", "feed_size": 6}).json()["session_id"]
    batch = client.get(f"/sessions/{sid}/next", params={"n": 4}).json()
    assert len(batch["items"]) == 4 and batch["status"]["state"] == "ok"
    first = batch["items"][0]
    assert first["clip_url"].endswith(f"/clips/{first['pid']}.mp4")

    status = client.post(f"/sessions/{sid}/events", json={"pid": first["pid"], "watch_seconds": 20, "shared": True})
    assert status.status_code == 200

    assert len(client.get(f"/sessions/{sid}/next", params={"n": 4}).json()["items"]) == 2
    ended = client.get(f"/sessions/{sid}/next").json()
    assert ended["status"]["state"] == "ended" and not ended["items"]

    recap = client.get(f"/sessions/{sid}/recap").json()
    assert recap["shares"] == 1 and recap["videos_served"] == 6


def test_rejects_unknown_ranker_and_user(catalog, gamer):
    client = TestClient(create_app(catalog, {"gamer": gamer}))
    assert client.post("/sessions", json={"user_id": "gamer", "ranker": "nope"}).status_code == 400
    assert client.post("/sessions", json={"user_id": "nobody", "ranker": "detoks"}).status_code == 404
