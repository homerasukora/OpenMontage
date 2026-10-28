"""Podcast / lo-fi bed (royalty-free synth): driving four-on-floor intro with pluck arp and filter rise,
then a calm Rhodes + soft swung beat + warm bass + vinyl texture. 92 BPM, F major (Fmaj7–Em7–Dm7–Cmaj7)."""
import sys, numpy as np, soundfile as sf
from numpy.fft import rfft, irfft, rfftfreq
out, DUR, XT = sys.argv[1], float(sys.argv[2]), float(sys.argv[3])     # XT = end of driving intro
SR = 44100; BPM = 92; BEAT = 60 / BPM; BAR = 4 * BEAT; N = int((DUR + 3) * SR)
rng = np.random.default_rng(21 + (len(sys.argv) > 5) * 13); mix = np.zeros((N, 2), np.float32)
def t_(d): return np.arange(int(d * SR)) / SR
def add(sig, at, g=1.0, pan=0.0):
    i = int(at * SR)
    if i >= N or i < 0: return
    sig = sig[: N - i]; mix[i:i + len(sig), 0] += sig * g * np.sqrt(0.5 * (1 - pan)); mix[i:i + len(sig), 1] += sig * g * np.sqrt(0.5 * (1 + pan))
def filt(x, lo=None, hi=None):
    X = rfft(x); f = rfftfreq(len(x), 1 / SR)
    if hi: X *= 1 / np.sqrt(1 + (f / hi) ** 4)
    if lo: X *= 1 / np.sqrt(1 + (lo / np.maximum(f, 1)) ** 4)
    return irfft(X, len(x)).astype(np.float32)
def hz(m): return 440 * 2 ** ((m - 69) / 12)
def noise(d): return rng.standard_normal(int(d * SR)).astype(np.float32)
def kick(g=1.0, punch=1.0):
    t = t_(0.5); f = 48 + 110 * punch * np.exp(-t * 28)
    return (np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 7) * g).astype(np.float32)
def clap():
    t = t_(0.35); e = sum(np.exp(-np.maximum(t - d, 0) * 60) * (t >= d) for d in (0, 0.011, 0.023)) / 3 + np.exp(-t * 14) * 0.5
    return filt(noise(0.35) * e, lo=900, hi=5000)
def hat(d=0.06, g=1.0): t = t_(d); return filt(noise(d) * np.exp(-t * 70), lo=6500) * g
def rim(): t = t_(0.12); return (filt(noise(0.12), lo=1500, hi=4000) * np.exp(-t * 55) + np.sin(2 * np.pi * 820 * t) * np.exp(-t * 60) * 0.4).astype(np.float32)
def rhodes(m, d):                                             # FM electric-piano tine
    t = t_(d); f = hz(m); mod = np.sin(2 * np.pi * f * 14 * t) * 1.4 * np.exp(-t * 9)
    s = np.sin(2 * np.pi * f * t + mod) * np.exp(-t * 1.1) + 0.25 * np.sin(2 * np.pi * 2 * f * t) * np.exp(-t * 2.5)
    s *= np.minimum(1, t / 0.006) * np.minimum(1, (d - t) / 0.25)
    return (s * (1 + 0.15 * np.sin(2 * np.pi * 4.5 * t))).astype(np.float32)     # gentle tremolo
def pluck(m, d=0.28):
    t = t_(d); f = hz(m); s = (2 * ((t * f) % 1.0) - 1) + 0.5 * (2 * ((t * f * 1.005) % 1.0) - 1)
    return filt(s * np.exp(-t * 14), hi=2600)
def bass(m, d, soft=True):
    t = t_(d); f = hz(m); s = np.sin(2 * np.pi * f * t) + (0.15 if soft else 0.35) * np.sin(2 * np.pi * 2 * f * t)
    return (s * np.minimum(1, t / 0.01) * np.minimum(1, (d - t) / 0.05)).astype(np.float32)

TR = int(sys.argv[4]) if len(sys.argv) > 4 else 0
PROG = [[m + TR for m in c] for c in ([[53, 57, 60, 64], [52, 55, 59, 62], [50, 53, 57, 60], [48, 52, 55, 59]] if len(sys.argv) <= 5 else [[50, 53, 57, 60, 64], [43, 53, 57, 59, 64], [48, 52, 55, 59, 62], [45, 52, 55, 60, 64]])]   # B: Dm9 G13 Cmaj9 Am9
ROOT = [r + TR for r in ([41, 40, 38, 36] if len(sys.argv) <= 5 else [38, 31, 36, 33])]
drive = np.zeros((N, 2), np.float32); calm = np.zeros((N, 2), np.float32)
b, tb = 0, 0.0
while tb < DUR + BAR:
    ch, r = PROG[b % 4], ROOT[b % 4]
    if tb < XT + BAR:                                             # ---- driving layer
        save = mix.copy(); mix[:] = 0
        for k in range(4):
            add(kick(1.0, 1.2), tb + k * BEAT, 0.9)
            add(bass(r, BEAT * 0.45, soft=False), tb + k * BEAT + BEAT / 2, 0.32)          # off-beat bass
        for k in (1, 3): add(clap(), tb + k * BEAT, 0.5)
        for k in range(16): add(hat(0.05, 1.0 if k % 2 else 0.55), tb + k * BEAT / 4, 0.16, 0.3 if k % 2 else -0.3)
        arp = [ch[0] + 12, ch[1] + 12, ch[2] + 12, ch[3] + 12, ch[2] + 12, ch[1] + 12, ch[3] + 12, ch[0] + 24]
        for k in range(16): add(pluck(arp[k % 8]), tb + k * BEAT / 4, 0.13, -0.35 + 0.7 * ((k // 2) % 2))
        if b % 2 == 1: add(filt(noise(BAR), lo=2000, hi=9000) * np.linspace(0, 1, int(BAR * SR)) ** 2, tb, 0.06)   # riser
        drive += mix; mix[:] = save
    if tb > XT - 2 * BAR:                                         # ---- calm podcast layer
        save = mix.copy(); mix[:] = 0
        for j, m in enumerate(ch): add(rhodes(m, BAR + 0.4), tb + 0.018 * j + (BEAT * 0.5 if b % 2 else 0) * 0, 0.16, -0.25 + 0.17 * j)
        add(rhodes(ch[3] + 12, BEAT * 1.5), tb + 2.5 * BEAT, 0.07, 0.3)                     # little top answer
        add(bass(r, BEAT * 1.6), tb, 0.36); add(bass(r + 7, BEAT * 0.8), tb + 2.5 * BEAT, 0.24)
        sw = BEAT / 2 * 0.16                                                                 # swing
        for k, g in ((0, 0.85), (1.75, 0.45), (2.5, 0.6)): add(kick(g, 0.7), tb + k * BEAT, 0.7)
        for k in (1, 3): add(rim(), tb + k * BEAT, 0.28, 0.15)
        for k in range(8): add(hat(0.04, 0.9 if k % 2 == 0 else 0.55), tb + k * BEAT / 2 + (sw if k % 2 else 0), 0.09, 0.25)
        calm += mix; mix[:] = save
    tb += BAR; b += 1
t = np.arange(N) / SR
# intro: low-pass sweep opening over the first 2 bars feel -> simple gain ramp + early filtered start
drive[: int(BAR * SR)] = np.stack([filt(drive[: int(BAR * SR), c], hi=900) for c in range(2)], 1) * 0.9
gd = np.clip((XT + 0.6 - t) / 1.6, 0, 1)                         # driving out over ~1.6 s
gc = np.clip((t - (XT - 1.2)) / 2.2, 0, 1)                       # calm in
mix = drive * gd[:, None] + calm * gc[:, None] * 1.25
add(filt(noise(1.2), lo=300, hi=6000) * np.linspace(1, 0, int(1.2 * SR)) ** 2, XT - 0.15, 0.10)   # soft whoosh into calm
vin = filt(noise(N / SR), lo=800, hi=5000) * 0.004 + (rng.random(N) > 0.9993).astype(np.float32) * rng.uniform(-0.25, 0.25, N).astype(np.float32)
mix += (filt(vin, hi=7000) * gc)[:, None] * 0.6                  # vinyl texture only in calm part
ir_t = t_(1.4); ir = (rng.standard_normal(len(ir_t)) * np.exp(-ir_t * 4)).astype(np.float32); ir /= np.abs(ir).sum() / 4
L = len(mix) + len(ir)
for c in range(2): mix[:, c] += 0.18 * irfft(rfft(mix[:, c], L) * rfft(ir, L), L)[: len(mix)]
mix = mix[: int((DUR + 2.5) * SR)]; f = int(3.0 * SR); mix[-f:] *= np.linspace(1, 0, f)[:, None]
mix = np.tanh(mix / np.abs(mix).max() * 1.3) * 0.85
sf.write(out, mix, SR); print("podcast", len(mix) / SR)
