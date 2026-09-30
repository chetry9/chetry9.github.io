#!/usr/bin/env bash
# Split the final video into parts that each fit a 30 MB upload, cutting only where no VO line plays.
#   usage: FFMPEG=... ./split.sh <in.mp4> <outprefix> <cut1> <cut2> ... (seconds)
set -euo pipefail
FF=${FFMPEG:-ffmpeg}; IN=$1; PRE=$2; shift 2
CUTS=(0 "$@")
DUR=$( { "$FF" -i "$IN" 2>&1 || true; } | sed -n 's/.*Duration: \([0-9:.]*\).*/\1/p' | awk -F: '{print $1*3600+$2*60+$3}')
CUTS+=("$DUR")
LIMIT_MB=${LIMIT_MB:-28}
for ((i=0;i<${#CUTS[@]}-1;i++)); do
  A=${CUTS[$i]}; B=${CUTS[$((i+1))]}; L=$(echo "$B - $A" | bc -l)
  # total bitrate budget -> video kbps (minus 192k audio, 3% mux overhead)
  VK=$(echo "($LIMIT_MB*8*1024*0.97/$L) - 192" | bc -l | cut -d. -f1)
  OUT="${PRE}_part$((i+1)).mp4"
  for pass in 1 2; do
    if [ $pass = 1 ]; then
      "$FF" -y -loglevel error -ss "$A" -t "$L" -i "$IN" -c:v libx264 -preset slower -tune animation -b:v ${VK}k -pass 1 -passlogfile /tmp/x264p$i -an -f mp4 /dev/null
    else
      "$FF" -y -loglevel error -ss "$A" -t "$L" -i "$IN" -c:v libx264 -preset slower -tune animation -b:v ${VK}k -maxrate $((VK*2))k -bufsize $((VK*4))k -pass 2 -passlogfile /tmp/x264p$i -pix_fmt yuv420p -c:a aac -b:a 192k -af "afade=t=in:d=0.02,afade=t=out:st=$(echo "$L-0.02"|bc -l):d=0.02" -movflags +faststart "$OUT"
    fi
  done
  echo "$OUT  ${A}s-${B}s  ${VK}kbps  $(du -m "$OUT" | cut -f1)MB"
done
