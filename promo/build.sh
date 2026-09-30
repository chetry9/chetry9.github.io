#!/usr/bin/env bash
# Render the promo in parallel chunks, then join and encode the delivery files.
# usage: REC_DIR=... FFMPEG=... ./build.sh [fps] [workers] [outdir]
set -euo pipefail
cd "$(dirname "$0")"
FPS=${1:-60}; W=${2:-4}; OUT=${3:-out}
FF=${FFMPEG:-ffmpeg}
mkdir -p "$OUT/chunks"
DUR=$(node render.mjs info | node -e 'let s="";process.stdin.on("data",d=>s+=d).on("end",()=>console.log(JSON.parse(s).d))')
FRAMES=$(node -e "console.log(Math.round($DUR*$FPS))")
echo "duration ${DUR}s -> ${FRAMES} frames @${FPS}fps, ${W} workers"
PER=$(( (FRAMES + W - 1) / W ))
rm -f "$OUT/chunks/list.txt"
for i in $(seq 0 $((W-1))); do
  A=$(( i*PER )); B=$(( (i+1)*PER )); [ $B -gt $FRAMES ] && B=$FRAMES
  F=$(node -e "console.log($A/$FPS)"); T=$(node -e "console.log($B/$FPS)")
  node render.mjs video "$FPS" "$F" "$T" "$OUT/chunks/c$i.mp4" &
  echo "file 'c$i.mp4'" >> "$OUT/chunks/list.txt"
done
wait
"$FF" -y -loglevel error -f concat -safe 0 -i "$OUT/chunks/list.txt" -c copy "$OUT/master_${FPS}fps.mp4"
# delivery: high-quality H.264 + silent stereo track (drop the voice-over in later)
"$FF" -y -loglevel error -i "$OUT/master_${FPS}fps.mp4" -f lavfi -i anullsrc=r=48000:cl=stereo -shortest \
  -c:v libx264 -preset slow -crf 14 -profile:v high -pix_fmt yuv420p -movflags +faststart -c:a aac -b:a 192k \
  "$OUT/upscoretech_promo_${FPS}fps.mp4"
ls -la "$OUT"
