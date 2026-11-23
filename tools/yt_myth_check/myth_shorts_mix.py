"""Audio for the Myth Check Shorts: voice segments (0.2 s crossfades) + stamp thuds + calm bed -> limiter."""
import subprocess, numpy as np, soundfile as sf, json, sys
M = "/tmp/claude-0/-home-user/7c5690c1-77ca-5715-b441-4cc8e349293a/scratchpad/myth"
SEGS = [(22.20, 59.44), (106.36, 127.60)]; X = .2; SR = 48000
STAMPS = json.loads(sys.argv[1])                     # [[src_time, kind], ...]
v, sr = sf.read(f"{M}/voice.wav", dtype="float32")
if v.ndim > 1: v = v.mean(1)
parts = [v[int(a * sr):int(b * sr)] for a, b in SEGS]
n = int(X * sr); out = parts[0].copy()
for p in parts[1:]:
    fade = np.linspace(0, 1, n, dtype=np.float32)
    out = np.concatenate([out[:-n], out[-n:] * (1 - fade) + p[:n] * fade, p[n:]])
total = len(out) / sr
def thud(strength):
    k = int(.6 * sr); t = np.arange(k) / sr; f = 55 + 95 * np.exp(-t * 22)
    body = np.sin(2 * np.pi * np.cumsum(f) / sr) * np.exp(-t * 9)
    nz = np.convolve(np.random.default_rng(1).standard_normal(k), np.ones(12) / 12, "same") * np.exp(-t * 60) * .35
    return ((body + nz) * strength).astype(np.float32)
sfx = np.zeros_like(out)
o0 = [0.0]
for (a, b) in SEGS[:-1]: o0.append(o0[-1] + (b - a) - X)
for ts, kind in STAMPS:
    for (a, b), oo in zip(SEGS, o0):
        if a <= ts < b:
            i = int((oo + ts - a + .1) * sr); x = thud(.55 if kind == "myth" else .32); sfx[i:i + len(x)] += x[:max(0, len(sfx) - i)]
sf.write(f"{M}/vs_voice.wav", out, sr); sf.write(f"{M}/vs_sfx.wav", sfx, sr)
subprocess.run(["python3", f"{M}/../bn/bed.py", f"{M}/vs_bed.wav", str(total + 1)], check=True, capture_output=True)
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", f"{M}/vs_voice.wav", "-i", f"{M}/vs_bed.wav", "-i", f"{M}/vs_sfx.wav", "-filter_complex",
                f"[0]highpass=f=70,volume=13.5dB[v];[1]atrim=0:{total:.3f},volume=-19.8dB,afade=t=in:d=0.8,afade=t=out:st={total-2.5:.3f}:d=2.5[b];"
                "[2]volume=9dB[s];[v][b][s]amix=inputs=3:normalize=0,alimiter=limit=0.84:attack=3:release=60:level=false[o]",
                "-map", "[o]", "-ar", "48000", "-c:a", "pcm_s16le", f"{M}/vs_mix.wav"], check=True)
print("audio", round(total, 2))
