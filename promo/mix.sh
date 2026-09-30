#!/usr/bin/env bash
# Final audio mix + mux.
#   usage: FFMPEG=... ./mix.sh <video.mp4> <out.mp4> [voice.wav]
# voice (optional) must already be edited to the video timeline (same start = 0s).
# Chain:
#   voice : high-pass 80Hz -> FFT denoise -> de-mud/presence EQ -> de-ess -> compressor -> -16 LUFS
#   sfx   : ducked ~9dB under the voice (sidechain)        bed : ambient pad, ducked harder
#   master: -14 LUFS integrated, true peak -1 dBTP (YouTube / Instagram / Facebook friendly)
set -euo pipefail
cd "$(dirname "$0")"
FF=${FFMPEG:-ffmpeg}
V=$1; OUTF=$2; VO=${3:-}
A=out/audio

if [ -n "$VO" ]; then
  "$FF" -y -loglevel error -i "$VO" -af "highpass=f=80,afftdn=nr=14:nf=-42:tn=1,equalizer=f=250:t=q:w=1.2:g=-2.5,equalizer=f=3200:t=q:w=1.4:g=2.5,equalizer=f=11000:t=h:w=0.8:g=1.5,deesser=i=0.35,acompressor=threshold=-20dB:ratio=3:attack=8:release=160:makeup=3dB,loudnorm=I=-16:TP=-2:LRA=7,aresample=48000" -ac 2 "$A/voice_clean.wav"
  "$FF" -y -loglevel error -i "$A/voice_clean.wav" -i "$A/sfx.wav" -i "$A/bed.wav" -filter_complex "
    [0:a]asplit=3[vo][sc1][sc2];
    [1:a]volume=-6dB[sfx];
    [2:a]volume=-25dB[bed];
    [sfx][sc1]sidechaincompress=threshold=0.03:ratio=6:attack=15:release=350:makeup=1[sfxd];
    [bed][sc2]sidechaincompress=threshold=0.02:ratio=10:attack=30:release=600[bedd];
    [vo][sfxd][bedd]amix=inputs=3:normalize=0:duration=longest,loudnorm=I=-14:TP=-1:LRA=11,alimiter=limit=0.89[m]" \
    -map "[m]" -ar 48000 "$A/mix.wav"
else
  "$FF" -y -loglevel error -i "$A/sfx.wav" -i "$A/bed.wav" -filter_complex "
    [0:a]volume=-3dB[sfx];[1:a]volume=-22dB[bed];
    [sfx][bed]amix=inputs=2:normalize=0:duration=longest,loudnorm=I=-16:TP=-1:LRA=15,alimiter=limit=0.89[m]" \
    -map "[m]" -ar 48000 "$A/mix.wav"
fi
"$FF" -y -loglevel error -i "$V" -i "$A/mix.wav" -map 0:v -map 1:a -c:v copy -c:a aac -b:a 256k -shortest -movflags +faststart "$OUTF"
"$FF" -hide_banner -i "$OUTF" -af ebur128=peak=true -f null - 2>&1 | grep -A12 Summary | grep -E "I:|Peak:" || true
