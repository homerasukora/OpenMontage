import sys, json, numpy as np, soundfile as sf
vo_f, epic_f, groove_f, vj, out = sys.argv[1:6]
v, sr = sf.read(vo_f, dtype="float32"); e, _ = sf.read(epic_f, dtype="float32"); g, _ = sf.read(groove_f, dtype="float32")
LT = json.load(open(vj))["lines"]; n = len(g); t = np.arange(n) / sr
X0 = 23.6                                                        # groove fades in under the epic tail
gin = np.clip((t - X0) / 2.5, 0, 1)[:, None]
mus = g * gin * 0.75; mus[: len(e)] += e[: n] * 1.0
gain = np.full(n, 0.30, np.float32)
for s, en in LT: gain[(t >= s - 0.2) & (t < en + 0.2)] = 0.10   # duck under speech (~-20 dB)
gain[t < 24.3] *= 1.45                                          # story section: music more present (~-17 dB under VO)
gain[t >= LT[-1][1] + 0.1] = 0.45
k = int(0.15 * sr); gain = np.convolve(gain, np.ones(k) / k, mode="same")
mix = mus * gain[:, None]; mix[: len(v)] += np.repeat(v[:n, None], 2, axis=1)
sf.write(out, mix / max(1.0, np.abs(mix).max() / 0.95), sr)
