"""Teaser soundtrack: 120 BPM trailer-pop beat, cut-synced whips/impacts, VO with ducking.
Everything is synthesized here (no samples, nothing to license).

usage: python3 teaser_audio.py out/audio/tvo out/audio/teaser_premix.wav
"""
import json, sys, wave
import numpy as np
from scipy import signal
import sfx as S

SR = S.SR
rng = np.random.default_rng(11)
BPM = 120; BEAT = 60 / BPM
DROP, SHOT = 2.5, 1.5
G0, L0, C0, END = 14.5, 18.0, 21.3, 26.5
N = int((END + 1.5) * SR)

drums = np.zeros((N, 2)); music = np.zeros((N, 2)); fxb = np.zeros((N, 2)); send = np.zeros((N, 2))


def put(bus, t, x, g=1.0, rev=0.0):
    x = x if x.ndim == 2 else S.pan(x, 0)
    i = int(round(t * SR)); j = min(N, i + len(x))
    if j <= i: return
    bus[i:j] += x[: j - i] * g
    if rev: send[i:j] += x[: j - i] * g * rev


def lp(x, fc, order=2):
    return signal.sosfilt(signal.butter(order, fc, 'lp', fs=SR, output='sos'), x, axis=0)


def hp(x, fc, order=2):
    return signal.sosfilt(signal.butter(order, fc, 'hp', fs=SR, output='sos'), x, axis=0)


def saw(f, n, phase=0.0):
    """band-limited saw (PolyBLEP)."""
    t = (phase + np.arange(n) * f / SR) % 1.0
    y = 2 * t - 1
    dt = f / SR
    m = t < dt; x = t[m] / dt; y[m] -= x + x - x * x - 1
    m = t > 1 - dt; x = (t[m] - 1) / dt; y[m] -= x * x + x + x + 1
    return y


def kick(g=1.0):
    n = int(.42 * SR); t = np.arange(n) / SR
    f = 44 + 120 * np.exp(-t * 32)
    y = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 7.5)
    y += hp(rng.standard_normal(n), 3000) * np.exp(-t * 400) * .25
    y = np.tanh(y * 1.6) / np.tanh(1.6)
    return y * g


def clap(g=1.0):
    n = int(.35 * SR); t = np.arange(n) / SR
    nz = signal.sosfilt(signal.butter(2, [900, 3200], 'bp', fs=SR, output='sos'), rng.standard_normal(n))
    e = np.zeros(n)
    for k, d in enumerate([0, .011, .023]):
        i = int(d * SR); e[i:] += np.exp(-(t[: n - i]) * (160 if k < 2 else 18))
    y = nz * e
    return S.pan(y / np.abs(y).max() * .7 * g, 0)


def hat(open_=False, g=1.0):
    n = int((.28 if open_ else .05) * SR); t = np.arange(n) / SR
    y = hp(rng.standard_normal(n), 7500) * np.exp(-t * (14 if open_ else 90))
    return S.pan(y / (np.abs(y).max() + 1e-9) * .32 * g, rng.uniform(-.25, .25))


def crash(g=1.0, dur=2.2):
    n = int(dur * SR); t = np.arange(n) / SR
    y = hp(rng.standard_normal((n, 2)), 4000) * np.exp(-t * 2.2)[:, None]
    return y / np.abs(y).max() * .45 * g


def bass_note(f, dur, g=1.0, cutoff=380):
    n = int(dur * SR); t = np.arange(n) / SR
    y = saw(f, n) * .7 + np.sin(2 * np.pi * f * t) * .8
    y = lp(y, cutoff, 4)
    y *= S.env_ar(n, .004 * SR, .05 * SR)
    return y * g


def stab(freqs, dur, cutoff, g=1.0):
    n = int(dur * SR)
    out = np.zeros((n, 2))
    for f in freqs:
        for det, side in ((-.08, 0), (.08, 1), (0, 0), (0, 1)):
            out[:, side] += saw(f * (1 + det / 12), n, rng.random())
    out = lp(out, cutoff, 2)
    e = S.env_ar(n, .003 * SR, .12 * SR)[:, None] * np.exp(-np.arange(n) / SR * 5)[:, None]
    return out * e / len(freqs) * .35 * g


def pad(freqs, dur, cutoff=900, g=1.0):
    n = int(dur * SR); t = np.arange(n) / SR
    out = np.zeros((n, 2))
    for i, f in enumerate(freqs):
        for det, side in ((-.1, 0), (.1, 1)):
            out[:, side] += saw(f * (1 + det / 100), n, rng.random()) * .5 + np.sin(2 * np.pi * f * t) * .5
    out = lp(out, cutoff, 2)
    fade = np.minimum(1, np.minimum(t / .6, (dur - t) / .6))[:, None]
    return out * fade / len(freqs) * .3 * g


def braam(dur=3.2, g=1.0):
    n = int(dur * SR); t = np.arange(n) / SR
    out = np.zeros((n, 2))
    for f in (36.71, 73.42, 110.0, 146.83):
        for det, side in ((-.15, 0), (.15, 1)):
            out[:, side] += saw(f * (1 + det / 100), n, rng.random())
    cut = 180 + 2200 * np.exp(-t * 2.5)
    # time-varying LP: process in blocks
    y = np.zeros_like(out); B = 2048
    zi = None
    for s0 in range(0, n, B):
        sos = signal.butter(2, cut[s0], 'lp', fs=SR, output='sos')
        if zi is None: zi = np.zeros((sos.shape[0], 2, 2))
        blk, zi = signal.sosfilt(sos, out[s0:s0 + B], axis=0, zi=zi)
        y[s0:s0 + B] = blk
    y *= (np.exp(-t * .9) * S.env_ar(n, .005 * SR, .4 * SR))[:, None]
    y = np.tanh(y * 1.5)
    return y / np.abs(y).max() * .8 * g


CH = {'Dm': ([293.66, 349.23, 440.0], 73.42), 'Bb': ([233.08, 293.66, 349.23], 58.27),
      'F': ([174.61, 220.0, 261.63], 87.31), 'C': ([261.63, 329.63, 392.0], 65.41)}
PROG = ['Dm', 'Bb', 'F', 'C']
kicks = []


def groove(t0, t1, hats16_from=None, cutoff0=1200, cutoff1=4200, stab_g=1.0, bass_g=1.0, half=False, clap_g=1.0, drum_g=1.0):
    nb = int(round((t1 - t0) / BEAT))
    for b in range(nb):
        t = t0 + b * BEAT
        bar = int((t - DROP) // 2) if t >= DROP else 0
        chord, root = CH[PROG[bar % 4]]
        k = (t - t0) / max(1e-9, (t1 - t0))
        in_bar = b % 4
        if not half or in_bar == 0:
            put(drums, t, kick(drum_g)); kicks.append(t)
        if (not half and in_bar in (1, 3)) or (half and in_bar == 2):
            put(drums, t, clap(clap_g * drum_g), 1, .25)
        put(drums, t + BEAT / 2, hat(open_=(in_bar == 3), g=.9 * drum_g))
        put(drums, t, hat(g=.45 * drum_g))
        if hats16_from is not None and t >= hats16_from:
            put(drums, t + BEAT / 4, hat(g=.35)); put(drums, t + 3 * BEAT / 4, hat(g=.35))
        # bass: eighths
        for e in (0, .5):
            put(music, t + e * BEAT, S.pan(bass_note(root * (2 if e and in_bar == 3 else 1), BEAT * .48, .55 * bass_g), 0))
        # offbeat stab with rising filter
        put(music, t + BEAT / 2, stab(chord, BEAT * .45, lerp(cutoff0, cutoff1, k), stab_g), 1, .3)


def lerp(a, b, k):
    return a + (b - a) * k


# ---------------- arrangement ----------------
# hook: dark drone + reverse-crash swell into the drop
put(music, 0.0, pad([73.42, 110.0, 146.83], 2.6, 500, 1.2), 1, .4)
put(fxb, 0.9, S.riser(1.6, .5), 1, .3)
put(fxb, 0.0, S.impact(1.5, 40, .5, .1), .6, .5)
# DROP
put(fxb, DROP, S.impact(2.2, 42, 1.0, .35), 1, .5)
put(drums, DROP, crash(1.0), 1, .5)
put(music, DROP, braam(2.0, .55), 1, .4)
groove(DROP, G0 - 0.5, hats16_from=DROP + 8, cutoff0=1200, cutoff1=4500)
# fill into the breakdown
for k in range(8):
    put(drums, G0 - .5 + k * BEAT / 8, clap(.35 + .08 * k), 1, .2)
put(fxb, G0 - .5, S.whoosh(.6, True, 300, 8000, -.6, .6, .5), 1, .3)
# montage cuts: whip into every cut + slam thud on the words + pen scribble on circles
shots = [DROP + i * SHOT for i in range(8)]
for i, t in enumerate(shots):
    if i: put(fxb, t - .16, S.whoosh(.32, i % 2 == 0, 500, 9000, (-1) ** i * .7, -(-1) ** i * .7, .55), 1, .15)
    put(fxb, t + .06, S.impact(.5, 90, .35, .45), 1, .2)
for t, cd in ((shots[1], .32), (shots[5], .78), (shots[7], .32)):
    sc = S.band_sweep_noise(.42, 2500, 5200, 3, 5) * np.hanning(int(.42 * SR)) * .12
    put(fxb, t + cd, S.pan(sc, .3), 1, .2)
# google breakdown: filtered pad, quarter bass pulse, fast typing, riser + snare roll
put(fxb, G0 - .05, S.whoosh(.5, False, 7000, 400, .5, -.5, .45), 1, .3)
put(music, G0, pad(CH['Dm'][0], L0 - G0 - .1, 700, 1.3), 1, .5)
for b in range(int((L0 - G0) / BEAT)):
    put(music, G0 + b * BEAT, S.pan(bass_note(73.42, .3, .45, 260), 0))
for k in range(20):
    put(fxb, G0 + .05 + k * .075, S.key_click(.16), 1, .1)
put(fxb, G0 + 2.05, S.shimmer(1.4, 1046.5, .22), 1, .6)
put(fxb, G0 + 2.95, S.pop(1100, 500, .08, .3), 1, .2)
put(fxb, L0 - 1.6, S.riser(1.5, .6), 1, .3)
roll = np.cumsum([BEAT / 2] * 2 + [BEAT / 4] * 2 + [BEAT / 8] * 4)  # accelerating
for k, dt in enumerate(np.linspace(0, 1.0, 16) ** 1.6):
    put(drums, L0 - 1.1 + dt * 1.0, clap(.25 + .05 * k), 1, .2)
# LOGO SLAM (silence gap right before)
gap = slice(int((L0 - .09) * SR), int(L0 * SR))
put(fxb, L0, S.impact(3.0, 38, 1.0, .5), 1, .8)
put(music, L0, braam(3.2, 1.0), 1, .6)
put(drums, L0, crash(1.2, 3.0), 1, .6)
put(fxb, L0 + .02, S.shimmer(2.4, 659.3, .25), 1, .8)
groove(L0 + 2 * BEAT, C0, half=True, cutoff0=1300, cutoff1=2000, stab_g=.4, bass_g=.7, clap_g=.6, drum_g=.6)
# CTA: groove back, lighter, then stinger
put(fxb, C0 - .15, S.whoosh(.45, True, 400, 7000, .4, -.4, .4), 1, .3)
put(drums, C0, crash(.6), 1, .4)
groove(C0, END - 1.0, cutoff0=1600, cutoff1=2400, stab_g=.45, bass_g=.7, clap_g=.6, drum_g=.5)
put(fxb, C0 + .8, S.pop(820, 420, .1, .25), 1, .3)
put(fxb, END - 1.0, S.impact(2.0, 44, .9, .35), 1, .7)
put(music, END - 1.0, stab(CH['Dm'][0] + [587.33], 1.6, 3000, 1.6), 1, .6)
put(drums, END - 1.0, crash(.8), 1, .6)

# sidechain pump on the music bus from every kick
pump = np.ones(N)
tt = np.arange(N) / SR
for k in kicks:
    i = int(k * SR); j = min(N, i + int(.35 * SR))
    pump[i:j] = np.minimum(pump[i:j], 1 - .55 * np.exp(-(tt[i:j] - k) / .09))
music *= pump[:, None]

# reverb bus
ir = S.reverb_ir(2.2, 2.6)
rev = np.stack([signal.fftconvolve(send[:, c], ir[:, c])[:N] for c in (0, 1)], 1)
bed = drums * .9 + music * .85 + fxb * .9 + rev * .5
bed[gap] *= np.linspace(1, 0, gap.stop - gap.start)[:, None] ** 2

# voice-over, ducking the bed underneath
vo_dir = sys.argv[1]
d = json.load(open(f'{vo_dir}/durations.json'))
starts = {'t_hook': .25, 't_search': G0 + .35, 't_logo': L0 + .35, 't_cta': C0 + .15}
vo = np.zeros(N)
for k, s in starts.items():
    a = S_read = None
    with wave.open(f'{vo_dir}/{k}.wav') as w:
        a = np.frombuffer(w.readframes(w.getnframes()), '<i2').astype(np.float32) / 32767
    i = int(s * SR); vo[i:i + len(a)] += a[: N - i]
    print(f'{k:9s} {s:6.2f} -> {s + d[k]:6.2f}')
# VO polish: high-pass, gentle presence, soft compression
vo = hp(vo, 90)
vo = vo + .25 * signal.sosfilt(signal.butter(2, [2500, 5000], 'bp', fs=SR, output='sos'), vo)
env = signal.sosfilt(signal.butter(1, 8, 'lp', fs=SR, output='sos'), np.abs(vo))
thr = .08; comp = np.where(env > thr, (thr + (env - thr) / 3) / (env + 1e-9), 1.0)
vo = vo * comp
rms = np.sqrt(np.mean(vo[np.abs(vo) > .01] ** 2))
vo = vo * (10 ** (-15 / 20) / rms)                       # speech RMS ~ -15 dBFS
# region ducking per VO line: 80 ms attack before the line, 300 ms release after
gate = np.zeros(N)
for k, s0 in starts.items():
    gate[int((s0 - .08) * SR): int((s0 + d[k] + .1) * SR)] = 1
duck_env = signal.sosfilt(signal.butter(1, 3, 'lp', fs=SR, output='sos'), gate)
duck_env = np.maximum(duck_env, signal.sosfilt(signal.butter(1, 3, 'lp', fs=SR, output='sos'), gate[::-1])[::-1])
duck = 1 - .8 * np.clip(duck_env * 1.3, 0, 1)
mix = bed * duck[:, None] * .55 + S.pan(vo, 0)
mix = mix[: int((END + .2) * SR)]
fade = np.ones(len(mix)); nf = int(.3 * SR); fade[-nf:] = np.linspace(1, 0, nf)
mix *= fade[:, None]
S.write(sys.argv[2], mix / np.abs(mix).max() * .95)
