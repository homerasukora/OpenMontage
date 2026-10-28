"""Cinematic 'story' cue (royalty-free synth): impact, taiko-style pulse, low strings/brass pads, rising tension, ending in a swell."""
import sys, numpy as np, soundfile as sf

out, DUR = sys.argv[1], float(sys.argv[2])
SR = 44100; N = int((DUR + 3) * SR); BPM = 84; BEAT = 60 / BPM; BAR = 4 * BEAT
rng = np.random.default_rng(9); mix = np.zeros((N, 2), np.float32)
def t_(d): return np.arange(int(d * SR)) / SR
def add(sig, at, g=1.0, pan=0.0):
    i = int(at * SR)
    if i >= N: return
    sig = sig[: N - i]; mix[i:i + len(sig), 0] += sig * g * np.sqrt(0.5 * (1 - pan)); mix[i:i + len(sig), 1] += sig * g * np.sqrt(0.5 * (1 + pan))
def lp(x, cut):
    from numpy.fft import rfft, irfft, rfftfreq
    X = rfft(x); f = rfftfreq(len(x), 1 / SR); X *= 1 / np.sqrt(1 + (f / cut) ** 4); return irfft(X, len(x)).astype(np.float32)
def note(m): return 440 * 2 ** ((m - 69) / 12)
def saw(fr, d, det=0.0): t = t_(d); return (2 * ((t * fr * (1 + det)) % 1.0) - 1).astype(np.float32)
def pad(chord, d, cut=1600, att=1.2):
    s = sum(saw(note(m), d, dt) for m in chord for dt in (-0.006, 0.0, 0.006)) / (3 * len(chord))
    t = t_(d); env = np.minimum(1, t / att) * np.minimum(1, (d - t) / 0.8); return lp(s * env, cut)
def taiko(g=1.0):
    t = t_(1.2); f = 55 + 70 * np.exp(-t * 20)
    body = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 4.5)
    slap = lp(rng.standard_normal(len(t)).astype(np.float32), 1800) * np.exp(-t * 40) * 0.5
    return ((body + slap) * g).astype(np.float32)
def boom():
    t = t_(3.0); f = 32 + 50 * np.exp(-t * 6)
    return (np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 1.3) + lp(rng.standard_normal(len(t)).astype(np.float32), 400) * np.exp(-t * 3) * 0.4).astype(np.float32)

# D minor progression: Dm – Bb – F – C (strings/brass voicings)
PROG = [[50, 57, 62, 65], [46, 53, 58, 62], [41, 48, 53, 57], [48, 55, 60, 64]]
add(boom(), 0.0, 1.0)
b, tb = 0, 0.0
while tb < DUR:
    ch = PROG[b % 4]; prog = min(1.0, tb / DUR + 0.25)
    add(pad(ch, BAR + 0.9, cut=900 + 1800 * prog), tb, 0.55)                              # low strings
    add(pad([m + 12 for m in ch[1:]], BAR + 0.9, cut=2600, att=0.6), tb, 0.18 * prog, 0.3)   # brass-like top, grows
    add(np.sin(2 * np.pi * note(ch[0] - 12) * t_(BAR)).astype(np.float32) * np.minimum(1, t_(BAR) / 0.3), tb, 0.35)  # sub
    for k, g in ((0, 1.0), (1.5, 0.55), (2, 0.85), (3, 0.5), (3.5, 0.45)):                  # taiko pattern
        if b > 0 or k >= 2: add(taiko(g), tb + k * BEAT, 0.55 + 0.3 * prog, -0.2 + 0.4 * (k % 2))
    for k in range(8):                                                                        # ostinato
        m = ch[2] + (12 if k % 2 else 0); tt = t_(BEAT / 2)
        add((saw(note(m), BEAT / 2) * np.exp(-tt * 7)).astype(np.float32), tb + k * BEAT / 2, 0.06 + 0.06 * prog, 0.35 - 0.7 * (k % 2))
    tb += BAR; b += 1
# riser + final swell
rd = 3.0; t = t_(rd); n = rng.standard_normal(len(t)).astype(np.float32)
add((lp(n, 3000) * (t / rd) ** 2 * 0.25).astype(np.float32), DUR - rd - 0.2, 1.0)
add(boom(), DUR - 0.2, 0.8)
# reverb
ir_t = t_(2.2); ir = (rng.standard_normal(len(ir_t)) * np.exp(-ir_t * 2.6)).astype(np.float32); ir /= np.abs(ir).sum() / 5
from numpy.fft import rfft, irfft
L = len(mix) + len(ir)
for c in range(2): mix[:, c] += 0.28 * irfft(rfft(mix[:, c], L) * rfft(ir, L), L)[: len(mix)]
mix = mix[: int((DUR + 2.5) * SR)]
f = int(2.5 * SR); mix[-f:] *= np.linspace(1, 0, f)[:, None]
mix = np.tanh(mix / np.abs(mix).max() * 1.4) * 0.85
sf.write(out, mix, SR); print("epic", len(mix) / SR)
