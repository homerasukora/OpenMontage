import sys, json, numpy as np, soundfile as sf
vo_f, mus_f, vj, out, XT = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4], float(sys.argv[5])
v, sr = sf.read(vo_f, dtype="float32"); m, _ = sf.read(mus_f, dtype="float32")
LT = json.load(open(vj))["lines"]; n = len(m); t = np.arange(n) / sr
gain = np.full(n, 0.30, np.float32)
for s, en in LT: gain[(t >= s - 0.2) & (t < en + 0.2)] = 0.11   # duck under speech (~-19 dB)
gain[t < XT] *= 1.5                                              # driving intro: more present, still under VO
gain[t >= LT[-1][1] + 0.1] = 0.45
k = int(0.15 * sr); gain = np.convolve(gain, np.ones(k) / k, mode="same")
mix = m * gain[:, None]; mix[: len(v)] += np.repeat(v[:n, None], 2, axis=1)
sf.write(out, mix / max(1.0, np.abs(mix).max() / 0.95), sr)
