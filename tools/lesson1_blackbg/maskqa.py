"""Mask QA for every frame: background bleed (neon inside the matte), frame-to-frame jumps inside a shot,
sudden loss of the speaker's area. usage: maskqa.py src.mov alpha.mkv shots_csv out.npy"""
import sys, subprocess, numpy as np
src, alpha, shots, outp = sys.argv[1:5]
SH = set(int(x) for x in shots.split(",")) if shots else set()
sys.argv = ['x', src, alpha, 'w5/words.json', 'x', '--fonts', 'fonts', '--logo', 'ganesha_wordmark_noir.png', '--end', '99999']
exec(open('render.py').read().split('# ---------- title + logo')[0])
W, H = 1918, 1080
dec = subprocess.Popen(["ffmpeg", "-v", "error", "-i", src, "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], stdout=subprocess.PIPE)
dea = subprocess.Popen(["ffmpeg", "-v", "error", "-i", alpha, "-f", "rawvideo", "-pix_fmt", "gray", "-"], stdout=subprocess.PIPE)
res, prev, n = [], None, 0
while True:
    b = dec.stdout.read(W * H * 3); ab = dea.stdout.read(W * H)
    if len(b) < W * H * 3 or len(ab) < W * H: break
    f = np.frombuffer(b, np.uint8).reshape(H, W, 3).astype(np.int16)
    a = clean_alpha(np.frombuffer(ab, np.uint8).reshape(H, W))
    neon = (f[..., 1] - np.maximum(f[..., 0], f[..., 2]) > 45) & (f[..., 1] > 110)
    bleed = int(((a > .15) & neon).sum())
    if prev is None or n in SH: jump, changed = 0., 0
    else:
        dd = np.abs(a - prev); jump = float(dd.mean()); changed = int((dd > .5).sum())
    res.append((n, bleed, jump, changed, float(a.mean())))
    prev = a; n += 1
r = np.array(res); np.save(outp, r)
print("frames", n)
print("bleed: max", int(r[:, 1].max()), "at", int(r[r[:, 1].argmax(), 0]), "| frames >150 px:", int((r[:, 1] > 150).sum()))
ch = r[:, 3]; med = np.median(ch[ch > 0]) if (ch > 0).any() else 0
print("frame-to-frame changed px (>0.5): median", int(med), "p99", int(np.percentile(ch, 99)), "max", int(ch.max()), "at", int(r[ch.argmax(), 0]))
print("top-8 jumps:", [(int(r[i, 0]), int(ch[i])) for i in np.argsort(-ch)[:8]])
cov = r[:, 4]; dcov = np.abs(np.diff(cov)); dcov[[i - 1 for i in SH if 0 < i < len(cov)]] = 0
print("coverage jumps >1%:", [(int(i + 1), round(float(cov[i]), 3), round(float(cov[i + 1]), 3)) for i in np.where(dcov > .01)[0]])
