"""For each clip: does the mouth follow the word-map (clip audio timing) or the clean TTS timing directly?"""
import sys, json, subprocess, numpy as np
sys.argv = [sys.argv[0]] + ["x"]
exec(open("lipcheck.py").read().split("op = np.array(op)")[0].replace("clip = sys.argv[1]", "clip = CLIP"), globals()) if False else None
import cv2
def mouth(clip):
    p = subprocess.Popen(["ffmpeg", "-v", "error", "-i", clip, "-vf", "fps=30,format=gray", "-f", "rawvideo", "-"], stdout=subprocess.PIPE)
    W, H = 1920, 1080; op = []; tmpl = None; pos = None
    while True:
        b = p.stdout.read(W * H)
        if len(b) < W * H: break
        f = np.frombuffer(b, np.uint8).reshape(H, W)
        if tmpl is None: tmpl = f[300:360, 930:1010].copy(); pos = (930, 300)
        x0, y0 = pos; reg = f[y0 - 60:y0 + 120, x0 - 80:x0 + 160]
        r = cv2.matchTemplate(reg, tmpl, cv2.TM_CCOEFF_NORMED); _, _, _, mx = cv2.minMaxLoc(r)
        pos = (x0 - 80 + mx[0], y0 - 60 + mx[1]); nx, ny = pos
        op.append((f[ny + 70:ny + 105, nx - 15:nx + 95] < 60).mean())
    return np.array(op, np.float32)
def env(a_path):
    a = np.frombuffer(subprocess.run(["ffmpeg", "-v", "error", "-i", a_path, "-ac", "1", "-ar", "16000", "-f", "f32le", "-"], capture_output=True).stdout, np.float32)
    n = int(len(a) / 16000 * 30)
    return np.array([np.sqrt(np.mean(a[int(i / 30 * 16000):int((i + 1) / 30 * 16000)] ** 2)) for i in range(n)])
z = lambda v: (v - v.mean()) / (v.std() + 1e-9)
P = "parts"; res = {}
for p in sys.argv[2:] if len(sys.argv) > 2 else "m1 m2 m31 m32 m33 m41 m42 m51 m52 m61 m62".split():
    op = mouth(f"{P}/wan_{p}.mp4"); e = env(f"{P}/{p}.mp3"); mp = json.load(open(f"{P}/map_{p}.json"))
    mt, mv = [q[0] for q in mp], [q[1] for q in mp]
    def fmap(tl):
        if tl <= mt[0]: return mv[0] - (mt[0] - tl)
        if tl >= mt[-1]: return mv[-1] + (tl - mt[-1])
        return float(np.interp(tl, mt, mv))
    out = {}
    for name, f in [("wordmap", fmap), ("identity", lambda tl: tl)]:
        for sh in (0,):
            idx = np.array([f(i / 30) * 30 for i in range(len(e))]); idx = np.clip(idx, 0, len(op) - 1)
            m = np.interp(idx, np.arange(len(op)), op)
            best = max((float(np.mean(z(m)[max(0, L):len(m) + min(0, L)] * z(e)[max(0, -L):len(e) + min(0, -L)])), L) for L in range(-6, 7))
            out[name] = best
    res[p] = out; print(p, {k: (round(v[0], 3), v[1]) for k, v in out.items()}, flush=True)
