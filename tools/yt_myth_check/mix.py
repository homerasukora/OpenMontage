"""Voice timeline + calm bed + stamp thuds -> mix.wav.  usage: mix.py (reads timeline.json written by myth_render.py)"""
import json, subprocess, numpy as np, soundfile as sf
Y = "/tmp/claude-0/-home-user/7c5690c1-77ca-5715-b441-4cc8e349293a/scratchpad/myth"
SR = 48000
tl = json.load(open(f"{Y}/timeline.json"))
def load(f):
    b = subprocess.run(["ffmpeg", "-v", "error", "-i", f, "-ac", "1", "-ar", str(SR), "-f", "f32le", "-"], capture_output=True).stdout
    return np.frombuffer(b, np.float32)
N = int(tl["total"] * SR)
voice = np.zeros(N + SR, np.float32)
for sec, t0 in tl["offsets"].items():
    a = load(f"{Y}/parts/{sec}.mp3"); i = int(round(t0 * SR)); voice[i:i + len(a)] += a
voice = voice[:N]

def thud(strength):
    n = int(.6 * SR); t = np.arange(n) / SR
    f = 55 + 95 * np.exp(-t * 22)                                   # pitch drop
    body = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 9)
    rng = np.random.default_rng(1); nz = rng.standard_normal(n)
    nz = np.convolve(nz, np.ones(12) / 12, "same") * np.exp(-t * 60) * .35  # paper/ink slap
    x = (body + nz) * strength
    return x.astype(np.float32)
sfx = np.zeros(N, np.float32)
for ts, kind in tl["stamps"]:
    x = thud({"myth": .55, "q": .32, "bin": .16}[kind]); i = int((ts + .1) * SR)
    sfx[i:i + len(x)] += x[:max(0, N - i)]

sf.write(f"{Y}/voice.wav", voice, SR); sf.write(f"{Y}/sfx.wav", sfx, SR)
print("ok", round(tl["total"], 2))
