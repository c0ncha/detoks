"""Build the processed catalog the ranker, classifier and simulation read.

Reads data/raw/ (see download_sample.sh) and writes data/processed/:

  catalog.json     one record per video: metadata, English text, smoothed engagement stats
  embeddings.npy   (n_videos, 256) float32, row i = catalog.json[i] (mean-pooled visual features)
  users.json       one record per dataset user: root-category affinity + mean watch ratio

Pool: for now, the 100-clip sample (only those that appear in the interaction log, 78 of them).
When the subset is chosen (PLAN.md open decision), add a pool here that reads the subset manifest.

Usage: python data/build_catalog.py [--raw data/raw] [--out data/processed]
"""
import argparse
import json
import os

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
KEY = ["user_id", "pid", "exposed_time"]
SIGNALS = ["cvm_like", "comment", "forward", "collect", "follow", "hate"]
PRIOR_N = 20  # pseudo-count for empirical-Bayes smoothing of per-video rates


def read_text(path: str) -> str:
    try:
        with open(path, encoding="utf-8") as f:
            return f.read().strip()
    except FileNotFoundError:
        return ""


def load_events(raw: str) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Return (events deduped to one row per interaction, pid -> list of Chinese tags)."""
    df = pd.read_csv(f"{raw}/interaction_sampled.csv", encoding="utf-8-sig")
    tags = df.groupby("pid").tag_name.agg(lambda s: sorted(set(s.dropna())))
    ev = df.drop_duplicates(KEY).copy()
    ev["watch_ratio"] = (ev.watch_time / ev.duration.clip(lower=1)).clip(upper=3)
    return ev, tags


def video_stats(ev: pd.DataFrame) -> pd.DataFrame:
    g = ev.groupby("pid")
    stats = pd.DataFrame({"n_views": g.size(), "mean_watch_ratio": g.watch_ratio.mean()})
    for s in SIGNALS:
        prior = ev[s].mean()
        stats[f"{s}_rate"] = (g[s].sum() + PRIOR_N * prior) / (g.size() + PRIOR_N)
    # Shrink watch ratio toward the global mean too: most videos have few views.
    gm = ev.watch_ratio.mean()
    stats["mean_watch_ratio"] = (g.watch_ratio.sum() + PRIOR_N * gm) / (g.size() + PRIOR_N)
    return stats


def user_profiles(ev: pd.DataFrame, root_ids: list[int]) -> list[dict]:
    """Root-category affinity per user: watch-time share per category, Laplace-smoothed."""
    wt = ev.pivot_table(index="user_id", columns="root_id", values="watch_time", aggfunc="sum", fill_value=0)
    wt = wt.reindex(columns=root_ids, fill_value=0) + 1.0
    aff = wt.div(wt.sum(axis=1), axis=0)
    meta = ev.groupby("user_id").agg(
        mean_watch_ratio=("watch_ratio", "mean"), n=("pid", "size"),
        age=("age", "first"), gender=("gender", "first"),
    )
    out = []
    for uid, row in aff.iterrows():
        m = meta.loc[uid]
        out.append({
            "user_id": int(uid),
            "affinity": {str(c): round(float(v), 5) for c, v in row.items()},
            "mean_watch_ratio": round(float(m.mean_watch_ratio), 4),
            "n_interactions": int(m.n),
            "age": int(m.age) if pd.notna(m.age) else None,
            "gender": m.gender if isinstance(m.gender, str) else None,
        })
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--raw", default=os.path.join(HERE, "raw"))
    ap.add_argument("--out", default=os.path.join(HERE, "processed"))
    args = ap.parse_args()
    raw, out = args.raw, args.out
    os.makedirs(out, exist_ok=True)

    ev, tags = load_events(raw)
    labels = pd.read_csv(os.path.join(HERE, "category_labels.csv")).set_index("root_id").label
    stats = video_stats(ev)
    first = ev.drop_duplicates("pid").set_index("pid")

    clip_dir = f"{raw}/sample_raw_file"
    clips = {int(f.split(".")[0]) for f in os.listdir(clip_dir) if f.endswith(".mp4")}
    pool = sorted(clips & set(first.index))
    print(f"pool: {len(pool)} videos (sample clips present in the interaction log)")

    videos, embs = [], []
    for pid in pool:
        r, s = first.loc[pid], stats.loc[pid]
        feat = np.load(f"{raw}/sample_video_feature_total/{pid}.npy").astype(np.float32)
        embs.append(feat.reshape(-1, feat.shape[-1]).mean(axis=0))
        videos.append({
            "pid": int(pid),
            "duration": float(r.duration),
            "root_id": int(r.root_id),
            "category": labels.get(int(r.root_id), f"Category {r.root_id}"),
            "author_id": int(r.author_id),
            "author_fans": int(r.author_fans_count),
            "title_cn": r.title if isinstance(r.title, str) else "",
            "title_en": read_text(f"{raw}/sample_title_en/{pid}.txt"),
            "asr_en": read_text(f"{raw}/sample_asr_en/{pid}.txt"),
            "tags_cn": tags.get(pid, []),
            "has_clip": True,
            "stats": {k: round(float(v), 5) for k, v in s.items()},
        })

    emb = np.stack(embs)
    emb /= np.linalg.norm(emb, axis=1, keepdims=True).clip(min=1e-8)  # unit-normalize for cosine
    np.save(f"{out}/embeddings.npy", emb.astype(np.float32))
    with open(f"{out}/catalog.json", "w", encoding="utf-8") as f:
        json.dump(videos, f, ensure_ascii=False, indent=1)

    users = user_profiles(ev, [int(c) for c in labels.index])
    with open(f"{out}/users.json", "w", encoding="utf-8") as f:
        json.dump(users, f)
    print(f"wrote {len(videos)} videos, embeddings {emb.shape}, {len(users)} users -> {out}")


if __name__ == "__main__":
    main()
