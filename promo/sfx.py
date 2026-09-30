"""Sound design for the promo: synthesizes every transition sound and places it on
the exact timeline the video uses (timeline.json from `node render.mjs info`).
All sounds are generated here, so there is nothing to license.

usage: python3 sfx.py timeline.json out_dir
writes out_dir/sfx.wav (48 kHz stereo, float) and out_dir/bed.wav (ambient pad)
"""
import json, sys, wave
import numpy as np
from scipy import signal

SR = 48000
rng = np.random.default_rng(7)


def env_ar(n, a, r, curve=4.0):
    """attack/release envelope over n samples (a, r in samples)."""
    e = np.ones(n)
    a = max(1, int(a)); r = max(1, int(r))
    e[:a] = np.linspace(0, 1, a) ** 2
    tail = np.linspace(0, 1, min(r, n))
    e[n - len(tail):] *= np.exp(-curve * tail) * (1 - tail)
    return e


def pan(x, p):
    """equal-power pan, p in [-1, 1] (scalar or per-sample)."""
    th = (np.asarray(p) + 1) * np.pi / 4
    return np.stack([x * np.cos(th), x * np.sin(th)], 1)


def band_sweep_noise(dur, f0, f1, q0=1.2, q1=1.2, shape=None):
    """noise whose spectral band glides f0 -> f1 (log), via STFT shaping."""
    n = int(dur * SR)
    x = rng.standard_normal(n + 2048)
    f, t, Z = signal.stft(x, SR, nperseg=2048, noverlap=1536)
    k = np.clip(t / dur, 0, 1)
    if shape is not None:
        k = shape(k)
    fc = np.exp(np.log(f0) + (np.log(f1) - np.log(f0)) * k)
    bw = fc / np.interp(k, [0, 1], [q0, q1])
    ff = f[:, None]
    g = np.exp(-0.5 * ((ff - fc[None]) / bw[None]) ** 2)
    _, y = signal.istft(Z * g, SR, nperseg=2048, noverlap=1536)
    y = y[:n]
    return y / (np.abs(y).max() + 1e-9)


def whoosh(dur=0.7, up=True, lo=250, hi=5200, pan_from=-0.6, pan_to=0.6, peak=0.72):
    f0, f1 = (lo, hi) if up else (hi, lo)
    y = band_sweep_noise(dur, f0, f1, 0.9, 2.2, shape=lambda k: np.sin(k * np.pi / 2) ** 1.4)
    n = len(y)
    u = np.linspace(0, 1, n)
    e = np.sin(np.pi * np.clip(u / 0.62, 0, 1) / 2) ** 2 * np.exp(-4.5 * np.clip(u - 0.55, 0, 1) ** 1.3)
    y = y * e
    return pan(y * peak / (np.abs(y).max() + 1e-9), np.linspace(pan_from, pan_to, n))


def swish(dur=0.35, peak=0.28):
    return whoosh(dur, True, 1800, 9000, -0.2, 0.2, peak)


def impact(dur=1.6, f0=62, peak=0.9, click=0.35):
    n = int(dur * SR); t = np.arange(n) / SR
    f = f0 * (1 + 0.9 * np.exp(-t * 28))
    ph = 2 * np.pi * np.cumsum(f) / SR
    body = np.sin(ph) * np.exp(-t * 4.2)
    thump = signal.sosfilt(signal.butter(2, 180, 'lp', fs=SR, output='sos'), rng.standard_normal(n)) * np.exp(-t * 30) * 2.2
    cl = signal.sosfilt(signal.butter(2, [2000, 7000], 'bp', fs=SR, output='sos'), rng.standard_normal(n)) * np.exp(-t * 160) * click
    y = body + thump + cl
    y *= env_ar(n, 0.002 * SR, 0.3 * SR)
    y = y / (np.abs(y).max() + 1e-9) * peak
    return pan(y, 0)


def riser(dur=2.2, peak=0.55):
    n = int(dur * SR); t = np.arange(n) / SR; u = t / dur
    nz = band_sweep_noise(dur, 300, 7000, 1.0, 3.0, shape=lambda k: k ** 1.6)
    f = 110 * 2 ** (u * 2.2)
    tone = sum(np.sin(2 * np.pi * np.cumsum(f * m) / SR) / m for m in (1, 2, 3))
    y = (nz * 0.8 + tone * 0.18) * (u ** 2.4)
    y *= env_ar(n, 0.01 * SR, 0.04 * SR)
    y = y / (np.abs(y).max() + 1e-9) * peak
    return pan(y, np.sin(u * 7) * 0.25)


def shimmer(dur=1.4, base=880, peak=0.2):
    n = int(dur * SR); t = np.arange(n) / SR
    y = np.zeros(n)
    for i, (m, d) in enumerate([(1, 3.2), (1.5, 3.8), (2, 4.5), (3, 5.5), (4.02, 6.5)]):
        delay = int(i * 0.045 * SR)
        tt = t[: n - delay]
        y[delay:] += np.sin(2 * np.pi * base * m * tt + i) * np.exp(-tt * d) / (1 + i * 0.4)
    y *= env_ar(n, 0.004 * SR, 0.2 * SR)
    y = y / (np.abs(y).max() + 1e-9) * peak
    L = y; R = np.concatenate([np.zeros(int(0.011 * SR)), y])[:n]
    return np.stack([L, R], 1)


def key_click(peak=0.16, bright=1.0):
    n = int(0.05 * SR); t = np.arange(n) / SR
    nz = signal.sosfilt(signal.butter(2, [1500 * bright, 6500], 'bp', fs=SR, output='sos'), rng.standard_normal(n))
    body = np.sin(2 * np.pi * (180 + 60 * rng.random()) * t) * np.exp(-t * 90) * 0.5
    y = (nz * np.exp(-t * 260) + body)
    y = y / (np.abs(y).max() + 1e-9) * peak * (0.8 + 0.4 * rng.random())
    return pan(y, rng.uniform(-0.15, 0.15))


def pop(f0=900, f1=420, dur=0.09, peak=0.26):
    n = int(dur * SR); t = np.arange(n) / SR
    f = f1 + (f0 - f1) * np.exp(-t * 60)
    y = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 38)
    y *= env_ar(n, 0.0015 * SR, 0.02 * SR)
    return pan(y / (np.abs(y).max() + 1e-9) * peak, 0)


def tick(peak=0.07):
    n = int(0.03 * SR); t = np.arange(n) / SR
    y = np.sin(2 * np.pi * (2600 + 400 * rng.random()) * t) * np.exp(-t * 220)
    return pan(y * peak, rng.uniform(-0.3, 0.3))


def reverb_ir(dur=1.8, decay=3.2):
    n = int(dur * SR); t = np.arange(n) / SR
    ir = np.stack([rng.standard_normal(n), rng.standard_normal(n)], 1) * np.exp(-t * decay)[:, None]
    ir[:, :] = signal.sosfilt(signal.butter(2, 6500, 'lp', fs=SR, output='sos'), ir, axis=0)
    ir[: int(0.012 * SR)] = 0
    return ir / np.sqrt((ir ** 2).sum(0))


def pad(dur):
    """slow evolving ambient bed (Dmaj9-ish), very soft."""
    n = int(dur * SR); t = np.arange(n) / SR
    notes = [73.42, 110.0, 146.83, 185.0, 220.0, 277.18, 329.63]
    y = np.zeros((n, 2))
    for i, f in enumerate(notes):
        lfo = 0.5 + 0.5 * np.sin(2 * np.pi * (0.03 + i * 0.011) * t + i)
        for det, side in ((-0.12, 0), (0.12, 1)):
            ph = 2 * np.pi * (f + det) * t
            w = np.sin(ph) + 0.25 * np.sin(2 * ph) + 0.1 * np.sin(3 * ph)
            y[:, side] += w * lfo / (1 + i * 0.35)
    y = signal.sosfilt(signal.butter(2, 1800, 'lp', fs=SR, output='sos'), y, axis=0)
    fade = np.minimum(1, np.minimum(t / 2.5, (dur - t) / 3.0))
    y *= np.clip(fade, 0, 1)[:, None]
    return y / (np.abs(y).max() + 1e-9)


def main():
    tl = json.load(open(sys.argv[1]))
    out = sys.argv[2]
    D = tl['d'] + 0.5
    T, P, SEG, OUT = tl['T'], tl['P'], tl['SEG'], tl['OUT']
    buf = np.zeros((int(D * SR) + SR * 3, 2))
    wet = np.zeros_like(buf)

    def at(t, snd, gain=1.0, rev=0.25):
        i = int(round(t * SR))
        if i < 0:
            snd = snd[-i:]; i = 0
        j = min(len(buf), i + len(snd))
        buf[i:j] += snd[: j - i] * gain
        wet[i:j] += snd[: j - i] * gain * rev

    # --- hook
    at(0.0, riser(0.45, 0.35), 1, .4)
    at(0.36, impact(1.8, 48, .8, .15), 1, .5)
    for k, s in enumerate([0.35, 0.9, 1.35]):
        at(s, swish(0.4, 0.22), 1, .5)
    at(T['hookOut'] - 0.05, whoosh(0.75, True, 400, 7000, 0.3, -0.3, .5), 1, .35)
    # --- phone rises + lands
    at(T['phoneIn'] - 0.1, whoosh(0.9, False, 6000, 180, 0, 0, .6), 1, .3)
    at(T['phoneIn'] + 0.55, impact(1.2, 70, .45, .25), 1, .35)
    # --- typing
    q = 'best digital marketing agency in padova'
    for i, ch in enumerate(q):
        at(T['type0'] + i * T['dtc'], key_click(0.14 if ch != ' ' else 0.18, 1.0 if ch != ' ' else .7), 1, .12)
    at(T['enter'], key_click(0.24, .6), 1, .15)
    at(T['enter'] + 0.02, pop(520, 300, .07, .12), 1, .1)
    at(T['res'] + 0.05, swish(0.3, 0.16), 1, .3)
    at(T['glow'], shimmer(1.6, 1046.5, .2), 1, .6)
    at(T['tap'], pop(1100, 500, .08, .3), 1, .2)
    # --- into the site
    at(T['toRec'] - 0.12, whoosh(0.7, True, 300, 6000, -0.4, 0.4, .55), 1, .35)
    at(T['toRec'] + 0.35, impact(1.4, 58, .5, .2), 1, .4)
    A0 = T['A0']
    at(A0 + 0.7, swish(0.45, 0.2), 1, .5)
    at(A0 + 1.4, swish(0.4, 0.16), 1, .5)
    for s in SEG:
        if s.get('cut'):
            at(s['t0'] - 0.18, whoosh(0.5, True, 800, 8000, 0.5, -0.5, .42), 1, .3)
    at(T['B0'] + 2.2, swish(0.45, 0.2), 1, .5)
    # --- services
    for p in P:
        t0, t1 = p['t0'], p['t1']
        a, e = t0 + .55, t1 - 1.35
        at(t0 - 0.05, whoosh(1.1, True, 200, 4200, 0.4, -0.5, .62), 1, .35)
        at(t0 + 0.45, shimmer(1.5, [880, 987.8, 1174.7, 1318.5][p['i']], .17), 1, .6)
        at(a + 0.1, impact(1.2, 64, .38, .18), 1, .4)
        at(a + 0.2, swish(0.5, 0.2), 1, .5)
        at(t0 + 0.9, pop(700, 380, .09, .16), 1, .3)
        at(t0 + 1.25, pop(760, 420, .09, .14), 1, .3)
        nitems = [12, 9, 11, 11][p['i']]
        for j in range(nitems):
            at(a + 1.55 + j * .085, tick(0.055), 1, .3)
        at(e - 0.05, whoosh(0.6, False, 6500, 900, -0.3, 0.3, .32), 1, .35)
        at(t1 - 1.0, whoosh(0.95, True, 250, 4800, -0.5, 0.4, .5), 1, .35)
    # --- outro
    o0 = OUT['t0'] + 0.6
    at(o0 - 2.1, riser(2.2, .5), 1, .4)
    at(o0 - 0.02, impact(2.4, 44, 1.0, .3), 1, .7)
    at(o0 + 0.02, shimmer(2.2, 659.3, .22), 1, .8)
    at(o0 + 0.8, swish(0.5, 0.2), 1, .5)
    at(o0 + 1.6, pop(820, 420, .1, .22), 1, .3)
    at(o0 + 2.6, shimmer(1.2, 1568, .12), 1, .7)

    ir = reverb_ir()
    rv = np.stack([signal.fftconvolve(wet[:, c], ir[:, c])[: len(buf)] for c in (0, 1)], 1)
    mix = buf + rv * 0.55
    mix = mix[: int(D * SR)]
    # gentle glue: soft clip
    mix = np.tanh(mix * 1.1) / np.tanh(1.1)
    write(f'{out}/sfx.wav', mix)
    write(f'{out}/bed.wav', pad(D) * 0.5)


def write(path, x):
    x = np.clip(x, -1, 1)
    pcm = (x * 32767).astype('<i2')
    with wave.open(path, 'wb') as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes(pcm.tobytes())


if __name__ == '__main__':
    main()
