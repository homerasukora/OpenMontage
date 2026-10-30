"""Trailer cue (royalty-free synth): boom open, pulsing low drone + ticking, hits on each cut, riser into a final impact with a long tail."""
import sys, json, numpy as np, soundfile as sf
from numpy.fft import rfft, irfft, rfftfreq
out, DUR = sys.argv[1], float(sys.argv[2]); HITS = json.loads(sys.argv[3]); FINAL = float(sys.argv[4])
SR = 44100; N = int((DUR + 1) * SR); rng = np.random.default_rng(77); mix = np.zeros((N, 2), np.float32)
def t_(d): return np.arange(int(d * SR)) / SR
def add(sig, at, g=1.0, pan=0.0):
    i = int(at * SR)
    if i >= N: return
    sig = sig[: N - i]; mix[i:i + len(sig), 0] += sig * g * np.sqrt(0.5 * (1 - pan)); mix[i:i + len(sig), 1] += sig * g * np.sqrt(0.5 * (1 + pan))
def filt(x, lo=None, hi=None):
    X = rfft(x); f = rfftfreq(len(x), 1 / SR)
    if hi: X *= 1 / np.sqrt(1 + (f / hi) ** 4)
    if lo: X *= 1 / np.sqrt(1 + (lo / np.maximum(f, 1)) ** 4)
    return irfft(X, len(x)).astype(np.float32)
def noise(d): return rng.standard_normal(int(d * SR)).astype(np.float32)
def hz(m): return 440 * 2 ** ((m - 69) / 12)
def boom(d=3.0, g=1.0):
    t = t_(d); f = 30 + 55 * np.exp(-t * 7)
    return ((np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 1.4) + filt(noise(d), hi=500) * np.exp(-t * 3.5) * 0.5) * g).astype(np.float32)
def hit(g=1.0):
    t = t_(1.6); body = boom(1.6, 0.9); crack = filt(noise(1.6), lo=1500, hi=9000) * np.exp(-t * 9) * 0.5
    return (body + crack) * g
def swell(d):  # reversed-cymbal style rise into a hit
    t = t_(d); return filt(noise(d), lo=2500, hi=11000) * (t / d) ** 3 * 0.35
def taiko(g=1.0):
    t = t_(0.9); f = 60 + 80 * np.exp(-t * 22)
    return ((np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 5.5) + filt(noise(0.9), hi=1600) * np.exp(-t * 35) * 0.4) * g).astype(np.float32)
def drone(m, d, cut=600):
    t = t_(d); s = sum((2 * ((t * hz(m) * (1 + dt)) % 1.0) - 1) for dt in (-0.004, 0, 0.004)) / 3
    s += 0.6 * np.sin(2 * np.pi * hz(m - 12) * t)
    return filt((s * np.minimum(1, t / 0.6)).astype(np.float32), hi=cut)
add(boom(3.2, 1.0), 0.0)
add(drone(38, FINAL + 0.2, 500), 0.0, 0.35)                     # D drone
add(drone(45, FINAL - 4.5, 900), 4.4, 0.18, 0.3)                 # fifth enters after the hook
BEAT = 60 / 112
k = 0; tb = 0.5
while tb < FINAL - 0.3:                                          # pulse + tick, tighter toward the end
    add(taiko(0.8 if k % 4 == 0 else 0.45), tb, 0.55, -0.2 + 0.4 * (k % 2))
    t = t_(0.05); add(filt(noise(0.05), lo=5000) * np.exp(-t * 90), tb + BEAT / 2, 0.15, 0.4)
    tb += BEAT if tb < FINAL - 2.6 else BEAT / 2; k += 1
for h in HITS: add(swell(0.6), h - 0.6, 1.0); add(hit(0.75), h, 0.9)
rd = 1.8; t = t_(rd)                                             # riser into the end card
add(filt(noise(rd), lo=800, hi=9000) * (t / rd) ** 2.5 * 0.45, FINAL - rd, 1.0)
add((np.sin(2 * np.pi * np.cumsum(200 + 900 * (t / rd) ** 2) / SR) * (t / rd) ** 2 * 0.12).astype(np.float32), FINAL - rd, 1.0)
add(hit(1.0), FINAL, 1.2); add(boom(3.5, 1.0), FINAL, 0.9)
add(drone(50, DUR - FINAL + 0.5, 2200) * np.exp(-t_(DUR - FINAL + 0.5) * 0.9), FINAL, 0.3)   # ringing chord tail
add(drone(57, DUR - FINAL + 0.5, 2600) * np.exp(-t_(DUR - FINAL + 0.5) * 0.9), FINAL, 0.2, 0.3)
ir_t = t_(2.0); ir = (rng.standard_normal(len(ir_t)) * np.exp(-ir_t * 2.8)).astype(np.float32); ir /= np.abs(ir).sum() / 5
L = len(mix) + len(ir)
for c in range(2): mix[:, c] += 0.25 * irfft(rfft(mix[:, c], L) * rfft(ir, L), L)[: len(mix)]
mix = mix[: int(DUR * SR)]; f = int(0.8 * SR); mix[-f:] *= np.linspace(1, 0, f)[:, None]
mix = np.tanh(mix / np.abs(mix).max() * 1.5) * 0.85
sf.write(out, mix, SR); print("trailer", len(mix) / SR)
