import sys, json, numpy as np, soundfile as sf
d, sid, out = sys.argv[1], sys.argv[2], sys.argv[3]
# pause AFTER each line (s); line 8 "The bike." is followed by the bike montage
GAPS = [0.12, 0.30, 0.18, 0.10, 0.18, 0.25, 0.30, 0.22, 0.22, 0.80]
LEAD = 0.25
sr = 24000
parts, t, timing = [np.zeros(int(LEAD * sr))], LEAD, []
for i, g in enumerate(GAPS):
    a, sr = sf.read(f"{d}/v{sid}_{i}.wav", dtype="float32")
    nz = np.where(np.abs(a) > 0.004)[0]
    a = a[max(nz[0] - int(0.08 * sr), 0): nz[-1] + int(0.12 * sr)]
    timing.append([round(t, 3), round(t + len(a) / sr, 3)])
    parts += [a, np.zeros(int(g * sr))]
    t += len(a) / sr + g
v = np.concatenate(parts)
sf.write(out, v / np.abs(v).max() * 0.89, sr)
json.dump(dict(lines=timing, dur=round(t, 3)), open(out.replace(".wav", ".json"), "w"))
print(timing, round(t, 2))
