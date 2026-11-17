"""Calm podcast bed, no drums / no noise: warm pad + soft electric piano + sub bass. F major, 72 BPM.
usage: bed.py out.wav seconds"""
import sys, numpy as np, soundfile as sf
from numpy.fft import rfft, irfft, rfftfreq
out, DUR = sys.argv[1], float(sys.argv[2])
SR = 48000; BPM = 72; BAR = 4 * 60 / BPM; CH = 2 * BAR
N = int((DUR + 4) * SR); mix = np.zeros((N, 2), np.float32)
PROG = [[53, 57, 60, 64], [52, 55, 59, 62], [50, 53, 57, 60], [48, 52, 55, 59]]   # Fmaj7 Em7 Dm7 Cmaj7
def hz(m): return 440 * 2 ** ((m - 69) / 12)
def lp(x, hi):
    X = rfft(x, axis=0); f = rfftfreq(len(x), 1 / SR); X *= (1 / np.sqrt(1 + (f / hi) ** 4))[:, None] if x.ndim > 1 else 1 / np.sqrt(1 + (f / hi) ** 4)
    return irfft(X, len(x), axis=0).astype(np.float32)
def env(n, a, r):
    t = np.arange(n) / SR; d = n / SR
    return np.minimum(1, t / a) * np.minimum(1, (d - t) / r)
def pad(notes, d):
    n = int(d * SR); t = np.arange(n) / SR; out = np.zeros((n, 2), np.float32)
    for m in notes:
        for ch, det in ((0, -0.08), (1, 0.08)):                 # gentle chorus by detune per channel
            f = hz(m) * 2 ** (det / 12)
            s = np.sin(2 * np.pi * f * t) + .35 * np.sin(2 * np.pi * 2 * f * t + .3) + .12 * np.sin(2 * np.pi * 3 * f * t)
            out[:, ch] += s
    out *= env(n, 1.6, 1.8)[:, None] / len(notes)
    return out
def ep(m, d):                                                    # soft FM electric piano
    n = int(d * SR); t = np.arange(n) / SR; f = hz(m)
    s = np.sin(2 * np.pi * f * t + 0.8 * np.sin(2 * np.pi * f * 2 * t) * np.exp(-t * 6)) * np.exp(-t * 1.4)
    return (s * env(n, .01, .4)).astype(np.float32)
def bass(m, d):
    n = int(d * SR); t = np.arange(n) / SR
    return (np.sin(2 * np.pi * hz(m) * t) * env(n, .08, .6)).astype(np.float32)
def add(sig, at, g, pan=0.0):
    i = int(at * SR)
    if i >= N: return
    if i < 0: sig = sig[-i:]; i = 0
    sig = sig[:N - i]
    if sig.ndim == 1:
        mix[i:i + len(sig), 0] += sig * g * np.sqrt(.5 * (1 - pan)); mix[i:i + len(sig), 1] += sig * g * np.sqrt(.5 * (1 + pan))
    else: mix[i:i + len(sig)] += sig * g
k = 0; t0 = 0.0
while t0 < DUR + 2:
    ch = PROG[k % 4]
    add(pad([x + 12 for x in ch], CH + 1.5), t0 - .5, .22)
    add(bass(ch[0] - 12, CH - .1), t0, .30)
    for j, (beat, note) in enumerate([(0, ch[1] + 12), (1.5, ch[2] + 12), (4, ch[3] + 12), (6, ch[2] + 12)]):   # sparse EP melody
        add(ep(note, 2.4), t0 + beat * 60 / BPM, .16, pan=(-.3 if j % 2 else .3))
    k += 1; t0 += CH
mix = lp(mix, 2600)
mix = mix[:int(DUR * SR)]; mix /= np.abs(mix).max() / .6
f = int(2 * SR); mix[:f] *= np.linspace(0, 1, f)[:, None]; mix[-f:] *= np.linspace(1, 0, f)[:, None]
sf.write(out, mix, SR); print(out, DUR)
