#!/usr/bin/env bash
# Download the ShortVideo dataset sample (100 clips + features + text) and the
# metadata files into data/raw/. Safe to re-run: finished files are skipped.
#
# Dataset: https://github.com/tsinghua-fib-lab/ShortVideo_dataset
# Credentials are published in the upstream README; override with SV_USER/SV_PASS.
set -euo pipefail

BASE="https://fi.ee.tsinghua.edu.cn/datasets/short-video-dataset"
AUTH="${SV_USER:-videodata}:${SV_PASS:-ShortVideo@10000}"
OUT="$(cd "$(dirname "$0")" && pwd)/raw"
MAX_LARGE=3   # server allows 3 concurrent connections for non-.txt files
MAX_TXT=16

mkdir -p "$OUT"

fetch() {  # fetch <remote path> <local path>
  local remote="$1" local_path="$2"
  [[ -s "$local_path" ]] && return 0
  mkdir -p "$(dirname "$local_path")"
  curl -sS --fail --retry 5 --retry-delay 3 -u "$AUTH" -o "$local_path.part" "$BASE/$remote" \
    && mv "$local_path.part" "$local_path"
}
export -f fetch; export BASE AUTH

list_files() {  # list file names (not subdirs) in a remote folder
  curl -sS --fail -u "$AUTH" "$BASE/$1/" | grep -o 'href="[^"]*"' | cut -d'"' -f2 | grep -v '/$' || true
}

echo "==> Metadata"
for f in interaction_sampled.csv categories_cn_en.csv README.md; do
  echo "    $f"; fetch "$f" "$OUT/$f"
done

for dir in sample_title_en sample_asr_en sample_video_feature_total sample_raw_file; do
  files=$(list_files "$dir")
  n=$(echo "$files" | grep -c . || true)
  par=$MAX_LARGE; [[ "$dir" == *_en ]] && par=$MAX_TXT
  echo "==> $dir ($n files, $par parallel)"
  echo "$files" | xargs -P "$par" -I{} bash -c 'fetch "$1/$2" "$3/$1/$2"' _ "$dir" {} "$OUT"
done

echo "==> Done"
du -sh "$OUT"/* | sort -h
