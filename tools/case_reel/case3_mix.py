import sys, json, numpy as np, soundfile as sf
vo_f, mu_f, vj, out = sys.argv[1:5]
v, sr = sf.read(vo_f, dtype="float32"); m, msr = sf.read(mu_f, dtype="float32")
# resample VO 24k -> 44.1k (linear is fine for speech at this ratio after we upsample)
x = np.arange(int(len(v) * msr / sr)) * sr / msr; v = np.interp(x, np.arange(len(v)), v).astype(np.float32)
LT = json.load(open(vj))["lines"]; n = len(m); t = np.arange(n) / msr
g = np.full(n, 0.55, np.float32)
for s, e in LT: g[(t >= s - 0.15) & (t < e + 0.15)] = 0.17          # duck under speech
g[t >= LT[-1][1] + 0.1] = 0.6
k = int(0.12 * msr); g = np.convolve(g, np.ones(k) / k, mode="same")
out_a = m * g[:, None]
out_a[: len(v)] += np.repeat(v[: n, None], 2, axis=1) * 1.0
sf.write(out, out_a / np.abs(out_a).max() * 0.9, msr)
