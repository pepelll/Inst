#!/usr/bin/env bash
# Rebuild the SFX track from the config timeline and mux it onto the rendered video (video stream copied as-is).
set -euo pipefail
cd "$(dirname "$0")/.."
node --experimental-strip-types --no-warnings scripts/export-timeline.mjs > /dev/null
python3 -I scripts/sfx.py
ffmpeg -v error -y -i out/arut_promo.mp4 -i public/sfx/arut_sfx.wav \
  -map 0:v:0 -map 1:a:0 -c:v copy -c:a aac -b:a 256k -ar 48000 -shortest -movflags +faststart \
  out/arut_promo_sfx.mp4
echo out/arut_promo_sfx.mp4
