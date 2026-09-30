"""Fit the video timeline to the voice-over, then lay the VO lines onto that timeline.

  python3 vo_fit.py cfg  out/audio/vo/durations.json            -> writes cfg.js
  python3 vo_fit.py place out/timeline.json out/audio/vo out.wav -> 48k mono voice track
"""
import json, sys, wave
import numpy as np

SR = 48000
VO_LEAD = 0.6        # VO starts this long after a service's freeze begins (title is landing)
VO_TAIL = 1.9        # breathing room after the line before the panel exits


def cfg(dur_path):
    d = json.load(open(dur_path))
    pd = [round(max(10.0, VO_LEAD + d[f's{i + 1}'] + VO_TAIL), 2) for i in range(4)]
    outro = round(max(7.2, 0.75 + d['outro'] + 1.6), 2)
    open('cfg.js', 'w').write(f'window.PROMO_CFG = {json.dumps({"pd": pd, "outroLen": outro})};\n')
    print('pd', pd, 'outro', outro)


def read(path):
    with wave.open(path) as w:
        return np.frombuffer(w.readframes(w.getnframes()), '<i2').astype(np.float32) / 32767


def place(tl_path, vo_dir, out):
    tl = json.load(open(tl_path))
    T, P, SEG, OUT = tl['T'], tl['P'], tl['SEG'], tl['OUT']
    d = json.load(open(f'{vo_dir}/durations.json'))
    starts = {
        'hook': T['hookIn'] - 0.05,
        'search': T['phoneIn'] + 0.55,
        'meet': T['toRec'] + 0.4,
        'roof': None,               # right after "meet"
        's1': P[0]['t0'] + VO_LEAD, 's2': P[1]['t0'] + VO_LEAD,
        's3': P[2]['t0'] + VO_LEAD, 's4': P[3]['t0'] + VO_LEAD,
        'cta': SEG[-1]['t0'] - 0.15,
        'outro': OUT['t0'] + 0.6 + 0.2,
    }
    starts['roof'] = max(starts['meet'] + d['meet'] + 0.45, T['B0'] + 1.9)
    buf = np.zeros(int((tl['d'] + 1) * SR), np.float32)
    order = sorted(starts, key=starts.get)
    prev_end = -1
    for k in order:
        s = starts[k]
        if s < prev_end:
            print(f'WARNING {k} overlaps previous line by {prev_end - s:.2f}s')
        a = read(f'{vo_dir}/{k}.wav')
        i = int(s * SR)
        buf[i:i + len(a)] += a[: len(buf) - i]
        prev_end = s + d[k]
        print(f'{k:7s} {s:7.2f} -> {prev_end:7.2f}')
    buf = buf[: int(tl['d'] * SR)]
    with wave.open(out, 'wb') as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((np.clip(buf, -1, 1) * 32767).astype('<i2').tobytes())


if __name__ == '__main__':
    if sys.argv[1] == 'cfg':
        cfg(sys.argv[2])
    else:
        place(*sys.argv[2:5])
