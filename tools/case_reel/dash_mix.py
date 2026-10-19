import sys, json, numpy as np, soundfile as sf
vo_f, mu_f, vj, out = sys.argv[1:5]
v, sr = sf.read(vo_f, dtype="float32"); m, msr = sf.read(mu_f, dtype="float32"); assert sr == msr
LT = json.load(open(vj))["lines"]; n = len(m); t = np.arange(n) / sr
g = np.full(n, 0.28, np.float32)                       # gaps: ~-11 dB
for s, e in LT: g[(t >= s - 0.2) & (t < e + 0.2)] = 0.10   # under speech: -20 dB
g[t >= LT[-1][1] + 0.15] = 0.35                        # CTA tail
k = int(0.15 * sr); g = np.convolve(g, np.ones(k) / k, mode="same")
mix = m * g[:, None]; mix[: len(v)] += np.repeat(v[:n, None], 2, axis=1)
sf.write(out, mix / max(1.0, np.abs(mix).max() / 0.95), sr)
