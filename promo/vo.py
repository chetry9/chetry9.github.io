"""Generate the voice-over line by line with Kokoro (local ONNX), write per-line WAVs
and durations.json so the scene timeline can be fitted to the narration.

usage: python3 vo.py vo_script.json <model.onnx> <voices.bin> out/audio/vo
"""
import json, sys, os, wave
import numpy as np
from kokoro_onnx import Kokoro

script, model, voices, out = sys.argv[1:5]
os.makedirs(out, exist_ok=True)
cfg = json.load(open(script))
k = Kokoro(model, voices)
VO = np.load(voices)


def synth(text, voice, speed):
    """phonemize with kokoro_onnx, run the ONNX graph directly (one pass per sentence)."""
    import re
    parts = [p for p in re.split(r'(?<=[.?!])\s+', text) if p.strip()]
    out = []
    for i, p in enumerate(parts):
        tok = k.tokenizer.tokenize(k.tokenizer.phonemize(p, 'en-us'))[:510]
        st = VO[voice][len(tok)].astype(np.float32)
        a = k.sess.run(None, {'input_ids': np.array([[0, *tok, 0]], dtype=np.int64), 'style': st,
                              'speed': np.array([speed], dtype=np.float32)})[0].reshape(-1)
        assert np.isfinite(a).all(), p
        out.append(a)
        if i < len(parts) - 1:
            out.append(np.zeros(int(0.22 * 24000), np.float32))
    return np.concatenate(out), 24000
SR_OUT = 48000
dur = {}
for ln in cfg['lines']:
    audio, sr = synth(ln['text'], ln.get('voice', cfg['voice']), ln.get('speed', cfg['speed']))
    audio = np.asarray(audio, dtype=np.float32)
    # trim leading/trailing silence, keep 30 ms breathing room
    thr = 0.01 * np.abs(audio).max()
    nz = np.where(np.abs(audio) > thr)[0]
    pad = int(0.03 * sr)
    audio = audio[max(0, nz[0] - pad): nz[-1] + pad]
    # resample to 48k (linear-phase polyphase)
    from scipy.signal import resample_poly
    a48 = resample_poly(audio, SR_OUT, sr)
    a48 = a48 / (np.abs(a48).max() + 1e-9) * 0.89
    with wave.open(f"{out}/{ln['id']}.wav", 'wb') as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR_OUT)
        w.writeframes((a48 * 32767).astype('<i2').tobytes())
    dur[ln['id']] = round(len(a48) / SR_OUT, 3)
    print(ln['id'], dur[ln['id']])
json.dump(dur, open(f'{out}/durations.json', 'w'), indent=1)
