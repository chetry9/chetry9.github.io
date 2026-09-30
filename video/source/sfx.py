import numpy as np, wave
from scipy.signal import fftconvolve, butter, sosfilt

SR = 48000
DUR = 15.0
N = int(SR * DUR)
rng = np.random.default_rng(3)
L = np.zeros(N); R = np.zeros(N)       # sfx bus
ML = np.zeros(N); MR = np.zeros(N)     # music bus

def tt(d): return np.arange(int(d * SR)) / SR

def place(sig, t0, gain=1.0, pan=0.0, bus='sfx'):
    """sig mono or (2,n); pan -1..1"""
    i = int(t0 * SR)
    if sig.ndim == 1: l, r = sig * np.sqrt((1 - pan) / 2), sig * np.sqrt((1 + pan) / 2)
    else: l, r = sig
    n = min(len(l), N - i)
    if n <= 0: return
    a, b = (L, R) if bus == 'sfx' else (ML, MR)
    a[i:i + n] += gain * l[:n]; b[i:i + n] += gain * r[:n]

def svf_bp(x, fc, q=0.8):
    """time-varying state-variable bandpass; fc array"""
    y = np.zeros_like(x); low = band = 0.0
    f = 2 * np.sin(np.pi * np.clip(fc, 20, SR / 6) / SR)
    for i in range(len(x)):
        high = x[i] - low - q * band
        band += f[i] * high
        low += f[i] * band
        y[i] = band
    return y

def lp(x, fc, order=2):
    return sosfilt(butter(order, fc, 'low', fs=SR, output='sos'), x)
def hp(x, fc, order=2):
    return sosfilt(butter(order, fc, 'high', fs=SR, output='sos'), x)

def env_ad(n, a, curve=2.0):
    t = np.linspace(0, 1, n); ai = max(1, int(a * n))
    e = np.ones(n); e[:ai] = np.linspace(0, 1, ai) ** 1.5
    e[ai:] = (1 - np.linspace(0, 1, n - ai)) ** curve
    return e

def whoosh(d, f0, f1, peak=0.6, q=0.55, stereo_sweep=0.8):
    n = int(d * SR); x = rng.standard_normal(n)
    p = np.linspace(0, 1, n)
    fc = f0 * (f1 / f0) ** p
    y = svf_bp(x, fc, q) + 0.35 * svf_bp(x, fc * 2.1, q * 1.5)
    e = env_ad(n, peak, 2.2)
    y = y * e; y /= np.abs(y).max() + 1e-9
    pan = np.linspace(-stereo_sweep, stereo_sweep, n)
    return np.array([y * np.sqrt((1 - pan) / 2), y * np.sqrt((1 + pan) / 2)])

def boom(d=1.8, f0=110, f1=38, gain_click=0.5):
    t = tt(d)
    f = f1 + (f0 - f1) * np.exp(-t * 9)
    ph = 2 * np.pi * np.cumsum(f) / SR
    sub = np.sin(ph) * np.exp(-t * 2.6)
    nz = lp(rng.standard_normal(len(t)), 900) * np.exp(-t * 7) * 0.9
    click = hp(rng.standard_normal(len(t)), 2500) * np.exp(-t * 90) * gain_click
    y = sub + nz + click
    return np.tanh(y * 1.4) / 1.1

def thud(d=0.5, f0=160, f1=55):
    t = tt(d)
    f = f1 + (f0 - f1) * np.exp(-t * 30)
    y = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 12)
    y += lp(rng.standard_normal(len(t)), 1800) * np.exp(-t * 40) * 0.5
    return y

def pop(d=0.14, f0=1100, f1=520):
    t = tt(d)
    f = f1 + (f0 - f1) * np.exp(-t * 55)
    y = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 38)
    y += hp(rng.standard_normal(len(t)), 4000) * np.exp(-t * 400) * 0.25
    return y

def tick(d=0.06, f=2400):
    t = tt(d)
    return (np.sin(2 * np.pi * f * t) * 0.6 + np.sin(2 * np.pi * f * 1.5 * t) * 0.3) * np.exp(-t * 90)

def bell(freq, d=2.2, br=2.0):
    t = tt(d)
    mod = np.sin(2 * np.pi * freq * 3.5 * t) * br * np.exp(-t * 3)
    y = np.sin(2 * np.pi * freq * t + mod) * np.exp(-t * 2.2)
    y += 0.3 * np.sin(2 * np.pi * freq * 2.01 * t) * np.exp(-t * 4)
    return y * env_ad(len(t), 0.002, 1.0)

def shimmer(d=1.0, density=90):
    n = int(d * SR); y = np.zeros(n)
    for _ in range(int(density * d)):
        st = rng.integers(0, int(n * 0.8)); f = rng.uniform(2600, 7500)
        g = tt(rng.uniform(0.08, 0.3)); gr = np.sin(2 * np.pi * f * g) * np.exp(-g * 22)
        e = min(len(gr), n - st); y[st:st + e] += gr[:e] * rng.uniform(0.2, 1)
    p = np.linspace(0, 1, n); y *= np.sin(np.pi * p) ** 0.7
    return y / (np.abs(y).max() + 1e-9)

def riser(d=1.0, f0=300, f1=5000):
    n = int(d * SR); p = np.linspace(0, 1, n)
    fc = f0 * (f1 / f0) ** (p ** 1.6)
    y = svf_bp(rng.standard_normal(n), fc, 0.35)
    fs = 180 * (8) ** p
    y2 = np.sin(2 * np.pi * np.cumsum(fs) / SR) * 0.25
    y = (y / (np.abs(y).max() + 1e-9) + y2) * p ** 2.2
    return y

def ping(freq=1320, d=2.0):
    t = tt(d)
    y = np.sin(2 * np.pi * freq * t) * np.exp(-t * 3.2) + 0.25 * np.sin(2 * np.pi * freq * 2 * t) * np.exp(-t * 6)
    return y * env_ad(len(t), 0.003, 1.0)

def whistle_fall(d=0.35, f0=1900, f1=700):
    t = tt(d); p = t / d
    f = f0 * (f1 / f0) ** p
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.sin(np.pi * p) ** 1.5

# ---------------- SFX timeline (matches index.html) ----------------
place(pop(0.3, 700, 300), 0.12, 0.35)
place(whoosh(3.5, 180, 2600, peak=0.85, q=0.7, stereo_sweep=0.3), 0.45, 0.30)   # map dive (air)
place(whoosh(1.1, 400, 3800, peak=0.55), 3.05, 0.55)                                # zoom-through
place(whistle_fall(), 4.0, 0.10)                                                     # pin falls
place(thud(), 4.33, 0.95)                                                            # pin lands
place(thud(0.3, 200, 90), 4.65, 0.30)
place(thud(0.2, 240, 120), 4.82, 0.14)
place(ping(1320), 4.6, 0.30, 0.1)                                                    # sonar
place(ping(1320), 5.95, 0.14, 0.1)
place(pop(), 4.72, 0.55)                                                             # callout
place(tick(), 4.95, 0.20, 0.3)
place(riser(0.9, 250, 4500), 5.2, 0.30)
place(whoosh(0.9, 300, 5000, peak=0.75, stereo_sweep=0.0), 5.95, 0.75)             # circle reveal
place(boom(), 6.72, 1.0)
place(whoosh(0.75, 1800, 350, peak=0.35, stereo_sweep=-0.9), 6.5, 0.6)             # poster1 in (from right)
place(shimmer(0.9), 7.4, 0.28, 0.2)
place(bell(2093, 1.6, 1.2), 7.45, 0.10, 0.4)
place(pop(0.12, 1300, 700), 7.2, 0.35, -0.2); place(pop(0.12, 1500, 800), 7.35, 0.35, 0.2)
place(whoosh(0.6, 500, 2800, peak=0.7, stereo_sweep=-0.9), 8.62, 0.55)            # poster1 out
place(whoosh(0.75, 1800, 350, peak=0.35, stereo_sweep=-0.9), 9.0, 0.6)             # poster2 in
place(thud(0.35, 180, 70), 9.55, 0.35)
place(shimmer(0.9), 9.95, 0.28, -0.2)
place(bell(2349, 1.6, 1.2), 10.0, 0.10, -0.4)
place(pop(0.12, 1300, 700), 9.7, 0.35, -0.2); place(pop(0.12, 1500, 800), 9.85, 0.35, 0.2)
place(riser(1.0, 200, 6000), 10.62, 0.42)                                          # build-up
place(whoosh(0.7, 400, 4200, peak=0.8, stereo_sweep=0.0), 10.95, 0.55)
place(boom(2.2, 130, 34, 0.7), 11.58, 1.05)                                         # end card hit
place(shimmer(1.4, 120), 11.5, 0.22)
place(pop(0.2, 900, 380), 11.5, 0.45)                                               # logo
place(tick(0.06, 2000), 11.78, 0.25, -0.3)
place(tick(0.06, 2200), 12.02, 0.2, 0.3)
place(whoosh(0.35, 3000, 600, peak=0.2, stereo_sweep=0), 12.0, 0.4)
place(thud(0.6, 220, 60), 12.2, 0.8)                                                # FREE CLASS slam
place(boom(1.2, 90, 40, 0.3), 12.2, 0.35)
place(shimmer(0.8), 12.25, 0.3)
place(tick(0.06, 2400), 12.48, 0.22)
place(pop(0.18, 1000, 420), 12.72, 0.6)                                             # CTA
place(whoosh(0.5, 2500, 500, peak=0.25, stereo_sweep=0), 12.85, 0.35)             # info card
for k, f in enumerate([1568, 2093, 2637, 3136]):                                     # tagline chime
    place(bell(f, 2.0, 1.0), 13.25 + k * 0.07, 0.10, (k - 1.5) * 0.3)

# ---------------- Music bed (F major, 128 bpm) ----------------
BPM = 128; beat = 60 / BPM; bar = beat * 4
def nf(m): return 440 * 2 ** ((m - 69) / 12)
chords = [[53, 57, 60, 65], [50, 57, 62, 65], [46, 53, 58, 62], [48, 55, 60, 64]]  # F Dm Bb C
def pad_note(freq, d):
    t = tt(d); y = np.zeros(len(t))
    for det in (-0.12, 0.0, 0.11):
        f = freq * 2 ** (det / 12)
        for h in range(1, 9): y += np.sin(2 * np.pi * f * h * t + h) / h ** 1.3
    e = np.minimum(1, t / 0.35) * np.minimum(1, (d - t) / 0.4).clip(0)
    return y * e
pad = np.zeros(N)
for b in range(int(DUR / bar) + 1):
    ch = chords[b % 4]; st = b * bar; d = min(bar + 0.3, DUR - st)
    if d <= 0: continue
    s = sum(pad_note(nf(m), d) for m in ch)
    i = int(st * SR); pad[i:i + len(s)] += s[:N - i]
pad = lp(pad, 1400, 4)
place(pad / np.abs(pad).max(), 0, 0.35, bus='music')
# pluck arpeggio after reveal
arp = np.zeros(N)
for k in range(int(DUR / (beat / 2))):
    st = k * beat / 2
    if st < 6.72 - 0.01: continue
    ch = chords[int(st / bar) % 4]; m = ch[[0, 2, 3, 1, 2, 3, 1, 2][k % 8]] + 12
    t = tt(0.4); y = (np.sin(2 * np.pi * nf(m) * t) + 0.4 * np.sin(4 * np.pi * nf(m) * t)) * np.exp(-t * 11)
    i = int(st * SR); n = min(len(y), N - i); arp[i:i + n] += y[:n] * (0.8 if k % 2 else 1)
place(arp / np.abs(arp).max(), 0, 0.22, bus='music')
# kick + sub + hat after the reveal hit; duck envelope
kick = np.zeros(N); duck = np.ones(N); hat = np.zeros(N); sub = np.zeros(N)
for k in range(int(DUR / beat) + 1):
    st = 6.72 + k * beat
    if st >= DUR - 0.2: break
    i = int(st * SR)
    kd = thud(0.35, 150, 48); n = min(len(kd), N - i); kick[i:i + n] += kd[:n]
    dk = 1 - 0.55 * np.exp(-tt(beat) * 9); n = min(len(dk), N - i); duck[i:i + n] = dk[:n]
    ih = int((st + beat / 2) * SR)
    if ih < N:
        h = hp(rng.standard_normal(int(0.05 * SR)), 7000) * np.exp(-tt(0.05) * 80); n = min(len(h), N - ih); hat[ih:ih + n] += h[:n]
    root = chords[int(st / bar) % 4][0] - 12
    tb = tt(beat); sb = np.sin(2 * np.pi * nf(root) * tb) * np.minimum(1, tb / 0.02) * np.exp(-tb * 1.5)
    n = min(len(sb), N - i); sub[i:i + n] += sb[:n]
ML *= duck; MR *= duck
place(sub * 0.9 * duck, 0, 0.30, bus='music')
place(kick, 0, 0.55, bus='music')
place(hat, 0, 0.10, 0.25, bus='music')
# drop music under the end-card slam and at the riser for tension
dyn = np.ones(N); tx = np.arange(N) / SR
dyn *= 1 - 0.7 * np.clip((tx - 10.6) / 0.9, 0, 1) * (tx < 11.58)
dyn *= np.clip(tx / 0.8, 0, 1)
ML *= dyn; MR *= dyn

# ---------------- Reverb + master ----------------
ir_t = tt(1.9)
ir = rng.standard_normal((2, len(ir_t))) * np.exp(-ir_t * 3.4); ir[:, :int(0.012 * SR)] = 0
ir = np.array([lp(c, 6000) for c in ir]); ir /= np.abs(ir).sum(axis=1, keepdims=True) ** 0.5 * 12
wetL = fftconvolve(L, ir[0])[:N]; wetR = fftconvolve(R, ir[1])[:N]
mwL = fftconvolve(ML, ir[1])[:N]; mwR = fftconvolve(MR, ir[0])[:N]
outL = L + 0.55 * wetL + 0.55 * ML + 0.25 * mwL
outR = R + 0.55 * wetR + 0.55 * MR + 0.25 * mwR
out = np.stack([outL, outR])
out = hp(out, 28)
out /= np.abs(out).max()
out = np.tanh(out * 1.6) / np.tanh(1.6)            # glue / soft limit
fade = np.clip((DUR - tx) / 0.8, 0, 1) ** 1.5
out *= fade * 0.93
pcm = (out.T * 32767).astype(np.int16)
with wave.open('sfx.wav', 'wb') as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(pcm.tobytes())
print('ok', out.shape)
