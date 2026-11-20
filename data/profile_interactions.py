"""Profile the ShortVideo interaction log and size candidate subsets.

Usage: python data/profile_interactions.py [data/raw]
"""
import os
import sys

import pandas as pd

RAW = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(__file__), "raw")
KEY = ["user_id", "pid", "exposed_time"]


def load_events(raw: str) -> pd.DataFrame:
    # The CSV has one row per (interaction, tag); dedupe to one row per interaction.
    df = pd.read_csv(f"{raw}/interaction_sampled.csv", encoding="utf-8-sig")
    return df.drop_duplicates(KEY)


def main() -> None:
    ev = load_events(RAW)
    v = ev.drop_duplicates("pid")
    print(f"interactions {len(ev)}  users {ev.user_id.nunique()}  videos {ev.pid.nunique()}  "
          f"dates {ev.p_date.min()}-{ev.p_date.max()}")
    print("duration quantiles (s):", v.duration.quantile([.1, .25, .5, .75, .9]).round(1).to_dict())
    print("median watch_time/duration:", round((ev.watch_time / ev.duration.clip(lower=1)).median(), 2))
    for c in ["cvm_like", "click", "comment", "follow", "collect", "forward", "hate"]:
        print(f"  {c:9s} rate {ev[c].mean():.4f}")

    ipu, ipv = ev.groupby("user_id").size(), ev.groupby("pid").size()
    print("interactions/user quantiles:", ipu.quantile([.1, .5, .9]).to_dict())
    print("interactions/video quantiles:", ipv.quantile([.5, .9, .99]).to_dict())

    cats = pd.read_csv(f"{RAW}/categories_cn_en.csv")
    names = cats.drop_duplicates("category_id").set_index("category_id").category_name_en.str.strip()
    print(f"root categories: {v.root_id.nunique()}")
    print(v.root_id.map(names).value_counts().to_string())

    sample_dir = f"{RAW}/sample_raw_file"
    if os.path.isdir(sample_dir):
        s = {int(f.split(".")[0]) for f in os.listdir(sample_dir)}
        print(f"sample clips present in log: {len(s & set(ev.pid))}/{len(s)}")

    n = ev.groupby("pid").agg(n=("user_id", "size"), dur=("duration", "first"))
    for mx in (60, 90):
        for mn in (3, 5):
            c = n[(n.dur <= mx) & (n.n >= mn)]
            cov = ev[ev.pid.isin(c.index)]
            print(f"dur<={mx}s & >={mn} interactions: {len(c)} videos, "
                  f"{len(cov)} interactions, {cov.user_id.nunique()} users")


if __name__ == "__main__":
    main()
