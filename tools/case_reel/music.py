"""Synthesized backing track (royalty-free): soft intro, riser, drop on a given time."""
import sys, json, numpy as np, soundfile as sf

out, DUR, DROP = sys.argv[1], float(sys.argv[2]), float(sys.argv[3])
SR = 44100
BPM = 100.0
BEAT = 60 / BPM
BAR = 4 * BEAT
OFF = DROP % BAR - BAR if DROP % BAR > 0.01 else 0.0   # grid offset so a bar starts at DROP
N = int((DUR + 2.0) * SR)
rng = np.random.default_rng(3)
mix = np.zeros((N, 2), np.float32)

def t_(d): return np.arange(int(d * SR)) / SR
def add(sig, at, gain=1.0, pan=0.0):
    i = int(at * SR)
    if i >= N or i + len(sig) <= 0: return
    if i < 0: sig = sig[-i:]; i = 0
    sig = sig[: N - i]
    l, r = np.sqrt(0.5 * (1 - pan)), np.sqrt(0.5 * (1 + pan))
    mix[i:i + len(sig), 0] += sig * gain * l
    mix[i:i + len(sig), 1] += sig * gain * r

def lp(x, cut):  # one-pole low-pass
    a = np.exp(-2 * np.pi * cut / SR); y = np.empty_like(x); s = 0.0
    for k in range(len(x)): s = (1 - a) * x[k] + a * s; y[k] = s
    return y
def hp(x, cut): return x - lp(x, cut)

def kick():
    t = t_(0.45); f = 48 + 90 * np.exp(-t * 28)
    return (np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 7)).astype(np.float32)
def clap():
    t = t_(0.25); n = rng.standard_normal(len(t)).astype(np.float32)
    env = np.exp(-t * 22) + 0.6 * np.exp(-((t - 0.012) * 400) ** 2)
    return hp(lp(n, 3500), 900) * env
def hat(open_=False):
    t = t_(0.18 if open_ else 0.05); n = rng.standard_normal(len(t)).astype(np.float32)
    return hp(n, 7000) * np.exp(-t * (14 if open_ else 70))
def note(f): return 440 * 2 ** ((f - 69) / 12)
def saw(fr, d, det=0.0):
    t = t_(d); ph = (t * fr * (1 + det)) % 1.0
    return (2 * ph - 1).astype(np.float32)
def pad(chord, d):
    s = sum(saw(note(m), d, dt) for m in chord for dt in (-0.004, 0.004)) / (2 * len(chord))
    t = t_(d); env = np.minimum(1, t / 0.6) * np.minimum(1, (d - t) / 0.5)
    return lp(s * env, 1400)
def bass808(m, d):
    t = t_(d); f = note(m)
    return (np.tanh(1.8 * np.sin(2 * np.pi * f * t)) * np.exp(-t * 1.6) * np.minimum(1, t / 0.005)).astype(np.float32)
def pluck(m, d=0.35):
    t = t_(d); s = saw(note(m), d) * 0.6 + saw(note(m + 12), d) * 0.3
    return lp(s * np.exp(-t * 9), 3000)

# A minor progression: Am – F – C – G (one chord per bar)
PROG = [([57, 60, 64], 45), ([53, 57, 60], 41), ([48, 52, 55], 36), ([55, 59, 62], 43)]
ARP = [[69, 72, 76, 72], [65, 69, 72, 69], [64, 67, 72, 67], [62, 67, 71, 67]]

bar_t, b = OFF, 0
while bar_t < DUR + BAR:
    chord, root = PROG[b % 4]
    drop = bar_t >= DROP - 0.01
    if bar_t + BAR > 0:
        add(pad(chord, BAR + 0.3), bar_t, 0.32 if not drop else 0.26)
        for k in range(4):                                   # beats
            bt = bar_t + k * BEAT
            if drop:
                add(kick(), bt, 0.9)
                if k in (1, 3): add(clap(), bt, 0.45, 0.1)
            elif k in (0, 2) and bar_t >= OFF + BAR:          # soft kick in intro (after first bar)
                add(kick(), bt, 0.35)
            for h in range(4 if drop else 2):                 # hats
                add(hat(open_=(drop and h == 2)), bt + h * BEAT / (4 if drop else 2), 0.10 if drop else 0.06, 0.4)
            for h in range(2):                                # arp eighths
                add(pluck(ARP[b % 4][(2 * k + h) % 4]), bt + h * BEAT / 2, 0.16 if drop else 0.10, -0.3 + 0.6 * h)
        if drop:
            add(bass808(root - 12, BAR * 0.5), bar_t, 0.55); add(bass808(root - 12, BAR * 0.5), bar_t + 2.5 * BEAT, 0.4)
    bar_t += BAR; b += 1

# riser into the drop + impact
rd = 2.2
t = t_(rd); n = rng.standard_normal(len(t)).astype(np.float32)
riser = hp(n, 600) * (t / rd) ** 2 * 0.35 + np.sin(2 * np.pi * np.cumsum(200 + 900 * (t / rd) ** 2) / SR) * (t / rd) ** 3 * 0.12
add(riser.astype(np.float32), DROP - rd, 1.0)
tt = t_(1.5); boom = np.sin(2 * np.pi * np.cumsum(30 + 60 * np.exp(-tt * 8)) / SR) * np.exp(-tt * 2.5)
add(boom.astype(np.float32), DROP, 0.7)

# simple stereo reverb (decaying noise IR)
ir_t = t_(1.2); ir = (rng.standard_normal(len(ir_t)) * np.exp(-ir_t * 4.5)).astype(np.float32); ir /= np.abs(ir).sum() / 6
from numpy.fft import rfft, irfft
L = len(mix) + len(ir)
for ch in range(2):
    wet = irfft(rfft(mix[:, ch], L) * rfft(ir, L), L)[: len(mix)]
    mix[:, ch] = mix[:, ch] + 0.18 * wet

mix = mix[: int(DUR * SR)]
fade = int(1.2 * SR); mix[-fade:] *= np.linspace(1, 0, fade)[:, None]
mix = np.tanh(mix / (np.abs(mix).max() + 1e-9) * 1.3) * 0.8
sf.write(out, mix, SR)
print("music", len(mix) / SR, "grid offset", OFF)
