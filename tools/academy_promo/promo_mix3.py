"""Audio for the Academy promo: lesson voice snippets (EN/HI) at their slots, calm bed with ducking, whooshes on transitions."""
import json, subprocess, numpy as np, soundfile as sf
P = "/tmp/claude-0/-home-user/7c5690c1-77ca-5715-b441-4cc8e349293a/scratchpad/promo"; SR = 48000
tl = json.load(open(f"{P}/timeline3.json")); N = int(tl["total"] * SR)
def load(path, a, b):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{a:.3f}", "-i", path, "-t", f"{b - a:.3f}", "-vn", "-ac", "1", "-ar", str(SR), "-f", "f32le", "-"], capture_output=True).stdout
    return np.frombuffer(raw, np.float32).copy()
def lufs_gain(x, target=-16.0):
    rms = np.sqrt(np.mean(x[np.abs(x) > 1e-3] ** 2) + 1e-12); return 10 ** ((target - (20 * np.log10(rms) - 0.7)) / 20)
voice = np.zeros(N, np.float32); vmask = np.zeros(N, np.float32)
for s in tl["segs"]:
    x = load(s["path"], *s["src"])
    f = int(.03 * SR); x[:f] *= np.linspace(0, 1, f); x[-int(.08 * SR):] *= np.linspace(1, 0, int(.08 * SR))
    x *= lufs_gain(x); i = int(s["out"] * SR); voice[i:i + len(x)] += x[:N - i]; vmask[i:i + len(x)] = 1
bed, _ = sf.read(f"{P}/bed3.wav", dtype="float32"); bed = (bed.mean(1) if bed.ndim > 1 else bed)[:N]
duck = np.clip(np.convolve(vmask, np.ones(int(.3 * SR)) / int(.15 * SR), "same"), 0, 1)   # music fully out while the lesson speaks (lessons have their own music)
bed = bed * (10 ** (-6 / 20)) * (1 - duck)
t = np.arange(N) / SR; bed *= np.clip(t / .5, 0, 1) * np.clip((tl["total"] - t) / 1.2, 0, 1)
fx = np.zeros(N, np.float32); rng = np.random.default_rng(4)
def whoosh(at, dur=.55, g=.22):
    n = int(dur * SR); nz = rng.standard_normal(n).astype(np.float32); env = np.sin(np.linspace(0, np.pi, n)) ** 2
    X = np.fft.rfft(nz); fr = np.fft.rfftfreq(n, 1 / SR); X *= np.exp(-((np.log(fr + 1) - np.log(1800)) ** 2) / 1.2); y = np.fft.irfft(X, n) * env
    y = y / (np.abs(y).max() + 1e-9) * g; i = int((at - dur * .6) * SR); i = max(i, 0); fx[i:i + n] += y[:N - i]
def tick(at, g=.18):
    n = int(.12 * SR); tt = np.arange(n) / SR; y = np.sin(2 * np.pi * 180 * tt) * np.exp(-tt * 40) * g; i = int(at * SR); fx[i:i + n] += y[:N - i]
for w in tl["whooshes"]: whoosh(w)
for h in tl["hits"]: tick(h)
mix = voice + bed + fx
sf.write(f"{P}/mix3_raw.wav", mix, SR)
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", f"{P}/mix3_raw.wav", "-af", "highpass=f=50,volume=3.5dB,alimiter=limit=0.84:attack=3:release=60:level=false", "-ar", "48000", "-c:a", "pcm_s16le", f"{P}/mix3.wav"], check=True)
print("ok", round(tl["total"], 2))
