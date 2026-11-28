#!/bin/bash
# Concatenate rendered parts and mux with the final mix (loudness-normalised to -14 LUFS).
# Usage: mux.sh <render_dir> <mix.wav> <out.mp4>
set -euo pipefail
R=$1; MIX=$2; OUT=$3
ls "$R"/part*.mp4 | sort | sed "s/^/file '/; s/$/'/" > "$R/concat.txt"
ffmpeg -v error -y -f concat -safe 0 -i "$R/concat.txt" -c copy "$R/video_only.mp4"
ffmpeg -v error -y -i "$R/video_only.mp4" -i "$MIX" -map 0:v -map 1:a \
  -c:v libx264 -crf 19 -preset slow -pix_fmt yuv420p \
  -af "loudnorm=I=-14:TP=-1.5:LRA=11" -c:a aac -b:a 256k -ar 48000 -shortest -movflags +faststart "$OUT"
ffprobe -v error -show_entries format=duration,size -of compact "$OUT"
