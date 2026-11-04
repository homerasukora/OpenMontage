"""Prep for the pinned Telegram video: stabilise the zooming apartment clips (lock framing to the background),
convert the vertical walk-in into a 16:9 base (blurred fill + centred card), trim tails, 25 fps, 1920x1080."""
import sys, subprocess, json, cv2, numpy as np
P = sys.argv[1]
W, H = 1920, 1080
def run(c): subprocess.run(c, check=True)

def transforms(path, n_used):
    cap = cv2.VideoCapture(path); orb = cv2.ORB_create(4000); bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)
    ok, f0 = cap.read(); g0 = cv2.cvtColor(f0, cv2.COLOR_BGR2GRAY); k0, d0 = orb.detectAndCompute(g0, None)
    Ms = [np.eye(2, 3)]
    for i in range(1, n_used):
        ok, fr = cap.read()
        if not ok: break
        g = cv2.cvtColor(fr, cv2.COLOR_BGR2GRAY); k, d = orb.detectAndCompute(g, None)
        m = sorted(bf.match(d0, d), key=lambda x: x.distance)[:800]
        p0 = np.float32([k0[x.queryIdx].pt for x in m]); p1 = np.float32([k[x.trainIdx].pt for x in m])
        M, _ = cv2.estimateAffinePartial2D(p0, p1, method=cv2.RANSAC, ransacReprojThreshold=2.0)
        Ms.append(M if M is not None else Ms[-1])
    # parametrise (scale, angle, tx, ty) and smooth over time
    par = np.array([[np.hypot(M[0, 0], M[1, 0]), np.arctan2(M[1, 0], M[0, 0]), M[0, 2], M[1, 2]] for M in Ms])
    k = 9; pad = np.pad(par, ((k // 2, k // 2), (0, 0)), mode="edge")
    sm = np.stack([np.convolve(pad[:, j], np.ones(k) / k, mode="valid") for j in range(4)], 1)
    out = []
    for s, a, tx, ty in sm:
        out.append(np.array([[s * np.cos(a), -s * np.sin(a), tx], [s * np.sin(a), s * np.cos(a), ty]]))
    return out

def inv(M): A = np.vstack([M, [0, 0, 1]]); return np.linalg.inv(A)
def full(M): return np.vstack([M, [0, 0, 1]])

def stabilise(src, dst, t_end, margin=1.01):
    cap = cv2.VideoCapture(src); fps = cap.get(cv2.CAP_PROP_FPS); n = int(round(t_end * fps))
    Ms = transforms(src, n)
    n = len(Ms); sw, sh = int(cap.get(3)), int(cap.get(4))
    # reference = the most zoomed-in frame (last); its view fits inside every frame
    Mref = Ms[int(np.argmax([np.hypot(M[0, 0], M[1, 0]) for M in Ms]))]
    S = np.array([[W / sw * margin, 0, -(margin - 1) * W / 2], [0, H / sh * margin, -(margin - 1) * H / 2], [0, 0, 1]])
    cap = cv2.VideoCapture(src)
    enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", f"{W}x{H}", "-r", f"{fps}", "-i", "-",
                            "-ss", "0", "-t", f"{n / fps:.3f}", "-i", src, "-map", "0:v", "-map", "1:a", "-vf", "fps=25,format=yuv420p",
                            "-c:v", "libx264", "-crf", "12", "-preset", "fast", "-c:a", "pcm_s16le", "-ar", "44100", "-ac", "1", "-shortest", dst], stdin=subprocess.PIPE)
    for i in range(n):
        ok, fr = cap.read()
        if not ok: break
        A = (S @ full(Mref) @ inv(Ms[i]))[:2]
        enc.stdin.write(cv2.warpAffine(fr, A, (W, H), flags=cv2.INTER_LANCZOS4, borderMode=cv2.BORDER_REFLECT).tobytes())
    enc.stdin.close(); enc.wait()
    s = [round(float(np.hypot(M[0, 0], M[1, 0])), 3) for M in Ms]
    return dict(frames=n, ref_zoom=round(float(np.hypot(Mref[0, 0], Mref[1, 0])), 3), zoom_first=s[0], zoom_last=s[-1])

def plain(src, dst, t_end):
    run(["ffmpeg", "-v", "error", "-y", "-i", src, "-t", f"{t_end}", "-vf", f"fps=25,scale={W}:{H}:flags=lanczos,format=yuv420p",
         "-c:v", "libx264", "-crf", "12", "-preset", "fast", "-c:a", "pcm_s16le", "-ar", "44100", "-ac", "1", dst])

def vertical(src, dst):
    fc = (f"[0:v]fps=25,split[a][b];[a]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},boxblur=40:2,eq=brightness=-0.22:saturation=0.7[bg];"
          f"[b]scale=-2:960[fg];[bg][fg]overlay=(W-w)/2:60,format=yuv420p[v]")
    run(["ffmpeg", "-v", "error", "-y", "-i", src, "-filter_complex", fc, "-map", "[v]", "-map", "0:a", "-c:v", "libx264", "-crf", "12", "-preset", "fast",
         "-c:a", "pcm_s16le", "-ar", "44100", "-ac", "1", dst])

SRC = f"{P}/src"; info = {}
plan = [("c6f519ff", "stab", 8.85), ("3ae34787", "vert", None), ("a4930160", "stab", 10.08), ("c1a619ec", "stab", 8.65),
        ("c22255c6", "stab", 5.55), ("ac244636", "plain", 8.06), ("ea401fa6", "plain", 9.45), ("c3526e29", "plain", 4.62)]
for i, (f, kind, te) in enumerate(plan, 1):
    dst = f"{P}/seg_{i:02d}.mov"
    if kind == "stab": info[f] = stabilise(f"{SRC}/{f}.mp4", dst, te)
    elif kind == "vert": vertical(f"{SRC}/{f}.mp4", dst)
    else: plain(f"{SRC}/{f}.mp4", dst, te)
    print(i, f, kind, info.get(f, ""), flush=True)
json.dump(info, open(f"{P}/stab.json", "w"))
