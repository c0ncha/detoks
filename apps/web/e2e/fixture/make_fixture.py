"""Build the synthetic e2e dataset: a small catalog in the data/processed format plus short clips.

Deterministic and dataset-free, so e2e tests run in CI and on any machine with Python + ffmpeg.
Usage: python e2e/fixture/make_fixture.py OUT_DIR   (writes OUT_DIR/data and OUT_DIR/clips)
"""
import json
import shutil
import subprocess
import sys
from pathlib import Path

import numpy as np

CLIP_SECONDS = 3.0
# Real root category ids (data/category_labels.csv) so the scenario personas have matching interests.
CATEGORIES = {3: "Gaming", 8: "Looks", 9: "Comedy", 17: "Animals", 12: "Food", 7: "Sports & fitness"}
PER_CATEGORY = 4


def main(out: Path) -> None:
    data, clips = out / "data", out / "clips"
    if (data / "catalog.json").exists() and any(clips.glob("*.mp4")):
        return  # already built
    shutil.rmtree(out, ignore_errors=True)
    data.mkdir(parents=True)
    clips.mkdir(parents=True)

    base = clips / "_base.mp4"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi",
                    "-i", f"testsrc=size=180x320:rate=15:duration={CLIP_SECONDS}",
                    "-c:v", "libx264", "-pix_fmt", "yuv420p", "-an", "-movflags", "+faststart", str(base)], check=True)

    rng = np.random.default_rng(0)
    videos, embs, harm = [], [], {}
    pid = 1
    for root_id, name in CATEGORIES.items():
        center = rng.normal(size=32)
        for i in range(PER_CATEGORY):
            videos.append({
                "pid": pid, "duration": CLIP_SECONDS, "root_id": root_id, "category": name,
                "title_en": f"{name} clip {i + 1}", "has_clip": True,
                "stats": {"mean_watch_ratio": 0.6, "cvm_like_rate": 0.02, "forward_rate": 0.002 * (i + 1)},
            })
            harm[str(pid)] = {"body_image": 0.9 if (root_id == 8 and i == 0) else 0.0}
            e = center + 0.3 * rng.normal(size=32)
            embs.append(e / np.linalg.norm(e))
            shutil.copy(base, clips / f"{pid}.mp4")
            pid += 1
    base.unlink()

    (data / "catalog.json").write_text(json.dumps(videos, indent=1))
    (data / "harm_labels.json").write_text(json.dumps(harm))
    np.save(data / "embeddings.npy", np.array(embs, dtype=np.float32))


if __name__ == "__main__":
    main(Path(sys.argv[1]))
