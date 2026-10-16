#!/usr/bin/env bash
# Rebuild the TSLA insert SFX from src/tsla/timing.ts and mux it onto the rendered video (video copied as-is).
set -euo pipefail
cd "$(dirname "$0")/.."
node --experimental-strip-types --no-warnings scripts/export-tsla-timeline.mjs
python3 -I scripts/tsla_sfx.py
ffmpeg -v error -y -i out/tsla_volume.mp4 -i public/sfx/tsla_sfx.wav \
  -map 0:v:0 -map 1:a:0 -c:v copy -c:a aac -b:a 256k -ar 48000 -shortest -movflags +faststart \
  out/tsla_volume_sfx.mp4
echo out/tsla_volume_sfx.mp4
