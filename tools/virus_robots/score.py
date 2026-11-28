#!/usr/bin/env python3
"""Synthesized mystical score + SFX + mix (royalty-free, deterministic).

Usage: score.py <audio_dir>
Reads  timing.json, events.json, vo.wav, vo_musk.wav from audio_dir.
Writes music.wav, sfx.wav, mix.wav (48 kHz stereo).
"""
import sys, json, numpy as np, soundfile as sf
from scipy.signal import butter, sosfilt, fftconvolve

D = sys.argv[1]
SR = 48000
TM = json.load(open(f"{D}/timing.json")); EV = json.load(open(f"{D}/events.json"))
SEG = {s["key"]: s for s in TM["segments"]}
DUR = TM["dur"] + .3
N = int(DUR * SR)
rng = np.random.default_rng(2027)
t_all = np.arange(N) / SR

def bp(x, lo, hi, order=2): return sosfilt(butter(order, [lo, hi], 'band', fs=SR, output='sos'), x)
def lp(x, f, order=2): return sosfilt(butter(order, f, 'low', fs=SR, output='sos'), x)
def hp(x, f, order=2): return sosfilt(butter(order, f, 'high', fs=SR, output='sos'), x)
def env_ad(n, a, d): e = np.ones(n); ai = int(a * SR); di = int(d * SR); e[:ai] = np.linspace(0, 1, ai) if ai else 1; e[-di:] *= np.linspace(1, 0, di) if di else 1; return e
def midi(m): return 440 * 2 ** ((m - 69) / 12)
def put(buf, sig, at, gain=1., pan=0.):
    i = int(at * SR)
    if i >= len(buf) or i + len(sig) <= 0: return
    if i < 0: sig = sig[-i:]; i = 0
    sig = sig[: len(buf) - i]
    l, r = np.sqrt(.5 * (1 - pan)), np.sqrt(.5 * (1 + pan))
    buf[i:i + len(sig), 0] += sig * gain * l; buf[i:i + len(sig), 1] += sig * gain * r
def reverb(x, secs=2.8, wet=.35, seed=1):
    r = np.random.default_rng(seed); n = int(secs * SR); tt = np.arange(n) / SR
    out = np.zeros_like(x)
    for ch in range(2):
        ir = r.standard_normal(n) * np.exp(-tt * 6.5 / secs); ir = lp(ir, 6000); ir /= np.sqrt((ir ** 2).sum())
        out[:, ch] = fftconvolve(x[:, ch], ir)[: len(x)]
    return x * (1 - wet) + out * wet * 1.4

# ---------------- tension curve ----------------
def key(k, side='s'): return SEG[k][side]
pts = [(0, .18), (key('L2'), .3), (key('L3'), .42), (key('MB'), .5), (key('L5'), .5), (key('L7'), .55), (key('L9'), .62),
       (key('L10'), .7), (key('MC'), .78), (key('L11'), .85), (key('L11', 'e') - .3, 1.0), (key('L11', 'e') + .15, .0),
       (key('L12'), .0), (key('L12') + .3, .7), (key('L13'), .75), (key('L13') + .5, 1.0), (DUR - 1.5, .7), (DUR, .0)]
T = np.interp(t_all, [p[0] for p in pts], [p[1] for p in pts])
silence = np.interp(t_all, [key('L11', 'e') + .05, key('L11', 'e') + .25, key('L12') - .15, key('L12') + .1], [1, 0, 0, 1])

# ---------------- music ----------------
mus = np.zeros((N, 2))
def saw(f, n, det=0.):
    ph = np.cumsum(np.full(n, f * (1 + det) / SR)) % 1.
    return 2 * ph - 1
CHORDS = [[38, 45, 50, 53], [34, 46, 50, 53], [31, 43, 50, 55], [33, 45, 49, 52]]  # Dm, Bb, Gm, A
CL = 8.0
dark = np.zeros(N); bright = np.zeros(N)
for ci, c0 in enumerate(np.arange(0, DUR, CL)):
    ch = CHORDS[ci % 4]; n = int(min(CL + 1.5, DUR - c0 + .5) * SR)
    s = sum(saw(midi(m), n, d) for m in ch for d in (-.003, .0, .004)) / (3 * len(ch))
    e = env_ad(n, 1.4, 1.5)
    i = int(c0 * SR); seg_ = s[: N - i] * e[: N - i]
    dark[i:i + len(seg_)] += seg_; bright[i:i + len(seg_)] += seg_
dark = lp(dark, 380, 4); bright = bp(bright, 300, 2600, 2)
pad = dark * (.55 + .45 * T) + bright * (T ** 1.6) * .55
# slow stereo movement
pan = .25 * np.sin(2 * np.pi * t_all / 11)
mus[:, 0] += pad * (1 - pan) * .5; mus[:, 1] += pad * (1 + pan) * .5
# sub drone
sub = np.sin(2 * np.pi * midi(26) * t_all) * (.35 + .4 * T)
mus += sub[:, None] * .35
# heartbeat pulse (double thump), tempo rises with tension
def thump(f0=55, d=.32):
    tt = np.arange(int(d * SR)) / SR; f = f0 + 70 * np.exp(-tt * 30)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-tt * 9)
tb = key('L3') - .2
while tb < DUR - 2:
    lvl = float(np.interp(tb, t_all, T))
    if lvl > .05:
        put(mus, thump(), tb, .55 * lvl); put(mus, thump(48, .28), tb + .19, .38 * lvl)
    tb += 60 / (66 + 40 * lvl)
# bells: minor pentatonic, inharmonic partials, sparse -> denser
BELL = [74, 77, 79, 81, 84, 86]
def bell(f, d=3.2):
    tt = np.arange(int(d * SR)) / SR
    s = sum(a * np.sin(2 * np.pi * f * r * tt) * np.exp(-tt * k) for r, a, k in [(1, 1, 1.6), (2.76, .45, 3.2), (5.4, .25, 5.0), (8.9, .12, 8)])
    return s * np.minimum(1, tt / .004)
tb, k = 1.2, 0
while tb < DUR - 2:
    lvl = float(np.interp(tb, t_all, T))
    put(mus, bell(midi(BELL[(k * 3 + (k // 4)) % len(BELL)])), tb, .07 + .08 * lvl, pan=(-.5 if k % 2 else .5))
    tb += 2.0 - 1.1 * lvl; k += 1
# "choir": formant-filtered saws entering in the second half
ch_n = N - int(key('L9') * SR)
if ch_n > 0:
    s = sum(saw(midi(m), ch_n, d) for m in (62, 65, 69) for d in (-.006, .006)) / 6
    s = bp(s, 500, 900, 2) + .6 * bp(s, 1100, 1500, 2)
    s *= np.interp(np.arange(ch_n) / SR + key('L9'), t_all, T) ** 2
    put(mus, s * env_ad(ch_n, 3, 2), key('L9'), .45, -.2); put(mus, np.roll(s, 2400) * env_ad(ch_n, 3, 2), key('L9'), .45, .2)
# clock tick under the math section
tb = key('L9')
while tb < key('L10'):
    tick = hp(rng.standard_normal(int(.012 * SR)), 3000) * np.exp(-np.arange(int(.012 * SR)) / SR * 400)
    put(mus, tick, tb, .18, .3 if int(tb * 2) % 2 else -.3); tb += .5
mus *= silence[:, None]
mus = reverb(mus, 3.2, .4, 3)
# final low hit tail stays (added in sfx)

# ---------------- sfx ----------------
sfx = np.zeros((N, 2))
def noise(d): return rng.standard_normal(int(d * SR))
def sweep_noise(d, f0, f1, q=.35):
    n = int(d * SR); x = noise(d); out = np.zeros(n); B = 8
    for b in range(B):
        a, z = b * n // B, (b + 1) * n // B; f = f0 * (f1 / f0) ** ((b + .5) / B)
        out[a:z] = bp(x, max(40, f * (1 - q)), min(20000, f * (1 + q)))[a:z]
    return out
def sparkle(d, dens=180):
    n = int(d * SR); s = np.zeros(n)
    for _ in range(int(dens * d)):
        i = rng.integers(0, n - 400); f = rng.uniform(3000, 9000); tt = np.arange(400) / SR
        s[i:i + 400] += np.sin(2 * np.pi * f * tt) * np.exp(-tt * 300) * rng.uniform(.2, 1)
    return s
for e in EV:
    t0, ty = e["t"], e["type"]
    if ty == 'assemble':
        d = .45 if e.get("short") else 1.1
        s = sweep_noise(d, 800, 6000) * env_ad(int(d * SR), d * .8, d * .2) * .5 + sparkle(d) * np.linspace(0, 1, int(d * SR)) * .25
        put(sfx, s, t0, .55, rng.uniform(-.3, .3))
    elif ty == 'disperse':
        d = .9; s = sweep_noise(d, 5000, 600) * env_ad(int(d * SR), .05, .7) * .5 + sparkle(d) * np.linspace(1, 0, int(d * SR)) * .25
        put(sfx, s, t0, .5)
    elif ty in ('cut', 'glitch'):
        d = .14 if ty == 'cut' else .32; n = int(d * SR)
        x = noise(d); x = np.round(x * 3) / 3; x = bp(x, 400, 7000)
        chirp = np.sign(np.sin(2 * np.pi * np.cumsum(np.linspace(2400, 300, n)) / SR)) * .3
        gate = (np.sin(2 * np.pi * 37 * np.arange(n) / SR) > 0)
        put(sfx, (x * .6 + chirp) * env_ad(n, .003, d * .5) * gate, t0 - .02, .45)
    elif ty == 'build':
        d = 1.0; n = int(d * SR); s = lp(noise(d), 180) * env_ad(n, .3, .6) * 2.5 + sparkle(d, 90) * .3
        put(sfx, s, t0, .5)
    elif ty == 'hit':
        d = 2.4 if e.get("big") else 1.6; tt = np.arange(int(d * SR)) / SR
        f = 34 + 60 * np.exp(-tt * 14); boom = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-tt * (1.6 if e.get("big") else 2.6))
        tr = hp(noise(.06), 1500) * np.exp(-np.arange(int(.06 * SR)) / SR * 70)
        s = boom.copy(); s[: len(tr)] += tr * .6
        put(sfx, s, t0, 1.0 if e.get("big") else .75)
    elif ty == 'counter':
        d = e.get("d", 1.5); tb = 0.
        while tb < d:
            n = int(.008 * SR); c = bp(noise(.008), 1800, 5000) * np.exp(-np.arange(n) / SR * 600)
            put(sfx, c, t0 + tb, .35, .2); tb += .09 - .06 * (tb / d)
    elif ty == 'key':
        n = int(.03 * SR); c = bp(noise(.03), 900, 4000) * np.exp(-np.arange(n) / SR * 180)
        put(sfx, c, t0, .4, .15)
    elif ty == 'riser':
        d = e.get("d", 1.); n = int(d * SR); s = sweep_noise(d, 300, 7000) * np.linspace(0, 1, n) ** 2
        s += np.sin(2 * np.pi * np.cumsum(np.linspace(110, 880, n)) / SR) * np.linspace(0, 1, n) ** 2 * .3
        put(sfx, s, t0, .55)
    elif ty == 'turn':
        for k in range(6):
            d = .28; n = int(d * SR); f = np.linspace(260, 520, n) * rng.uniform(.85, 1.2)
            s = bp(saw(1, n) * 0 + np.sign(np.sin(2 * np.pi * np.cumsum(f) / SR)), 300, 2500) * env_ad(n, .02, .15)
            put(sfx, s, t0 + k * .035, .12, rng.uniform(-.8, .8))
sfx = reverb(sfx, 1.8, .25, 5)

# ---------------- voices ----------------
def load_mono(p):
    a, sr = sf.read(p, dtype='float64'); a = a.mean(1) if a.ndim > 1 else a
    assert sr == SR; out = np.zeros(N); out[: min(N, len(a))] = a[:N]; return out
vo = load_mono(f"{D}/vo.wav"); mk = load_mono(f"{D}/vo_musk.wav")
vo = hp(vo, 70); vo = vo + .25 * lp(vo, 250)   # a touch of chest
mk = bp(mk, 180, 5200); mk = np.tanh(mk * 1.6) / np.tanh(1.6)
hiss = bp(rng.standard_normal(N), 2000, 9000) * .012 * (np.abs(mk) > 1e-4).astype(float)
mk = mk + lp(hiss, 9000)
speech = vo + mk
# sidechain duck for music + sfx bed
envs = np.abs(speech); envs = lp(envs, 6); envs = envs / (envs.max() + 1e-9)
duck = 1 - .45 * np.clip(envs * 5, 0, 1)
sp = speech[:, None] * np.array([1., 1.]) * .95
act = lp(np.abs(speech), 8) > 2e-3
def _db(x): return 20 * np.log10(np.sqrt(np.mean(x ** 2)) + 1e-12)
mbed = mus * duck[:, None]
mbed *= 10 ** ((_db(sp[act]) - 12.5 - _db(mbed[act])) / 20)      # music sits ~12.5 dB under the voice
sbed = sfx * 10 ** ((_db(sp[act]) - 9 - _db(sfx[np.abs(sfx).max(1) > 1e-3])) / 20)
bed = mbed + sbed
print('speech', round(_db(sp[act]), 1), 'bed under speech', round(_db(bed[act]), 1), 'bed overall', round(_db(bed), 1))
mix = bed + sp
mix /= np.abs(mix).max() / .89
sf.write(f"{D}/music.wav", (mus / np.abs(mus).max() * .89).astype(np.float32), SR)
sf.write(f"{D}/sfx.wav", (sfx / np.abs(sfx).max() * .89).astype(np.float32), SR)
sf.write(f"{D}/mix.wav", mix.astype(np.float32), SR)
print("ok", round(DUR, 2))
