#!/usr/bin/env bash
# Detached, resumable final render (frames already on disk are skipped), then composite + encode.
cd "$(dirname "$0")"
python3 build.py --frames 1-126 > render.log 2>&1
python3 -I encode.py render ../out/tesla_bags_drop.mp4 >> render.log 2>&1
echo DONE >> render.log
