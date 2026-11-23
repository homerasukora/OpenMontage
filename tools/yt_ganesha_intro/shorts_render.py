"""9:16 Shorts/Reels cut of «Who we are» (no income hook): Arnold vertical crop on top, captions in the middle,
the brand graphics card (from the 16:9 scenes, without the speaker circle) below, vertical end card.
usage: shorts_render.py out.mp4 [--preview t1,t2,... outdir]   (t = output seconds)"""
import sys
_argv = sys.argv[:]; sys.argv = ["x", "/dev/null"]
exec(open("/tmp/claude-0/-home-user/7c5690c1-77ca-5715-b441-4cc8e349293a/scratchpad/yt/yt_render.py").read().split("# ---------------- render ----------------")[0])
sys.argv = _argv
OUTV = sys.argv[1]
PREV = [float(x) for x in sys.argv[3].split(",")] if len(sys.argv) > 3 and sys.argv[2] == "--preview" else None
VW, VH = 1080, 1920
# source segments (final 16:9 timeline seconds): who we are + one round, disputes/complaints, CTA + end card
SEGS = [(23.88, 59.62), (97.45, 106.20), (132.27, 146.60)]
XF = 0.2
OUT_T, acc = [], 0.0
for a, b in SEGS:
    OUT_T.append((acc, a, b)); acc += (b - a) - XF
TOTAL_V = acc + XF
NFV = int(round(TOTAL_V * FPS))

# vertical background
vy, vx = np.mgrid[0:VH, 0:VW].astype(np.float32)
vr = np.sqrt(((vx - VW * .5) / (VW * .9)) ** 2 + ((vy - VH * .62) / (VH * .55)) ** 2)
VBG = np.array(ONYX, np.float32) + np.clip(1 - vr, 0, 1)[..., None] ** 1.8 * (np.array(EMERALD, np.float32) * 1.5 - np.array(ONYX, np.float32))
VDITHER = np.random.default_rng(5).uniform(-1, 1, (VH, VW, 1)).astype(np.float32)
AR_H = 1011                                                   # Arnold region (top)
AGRAD = np.clip((np.arange(AR_H, dtype=np.float32)[:, None, None] - AR_H * .55) / (AR_H * .45), 0, 1) ** 1.3 * .85
CARD_Y, CARD_W, CARD_H = 1050, 1000, 563
_cm2 = Image.new("L", (CARD_W * S, CARD_H * S), 0); ImageDraw.Draw(_cm2).rounded_rectangle([0, 0, CARD_W * S - 1, CARD_H * S - 1], radius=28 * S, fill=255)
CMASK2 = np.asarray(_cm2.resize((CARD_W, CARD_H), Image.LANCZOS), np.float32)[..., None] / 255
_cf = Image.new("RGBA", (CARD_W * S, CARD_H * S), (0, 0, 0, 0)); ImageDraw.Draw(_cf).rounded_rectangle([0, 0, CARD_W * S - 1, CARD_H * S - 1], radius=28 * S, outline=GOLD + (230,), width=3 * S)
CFRAME = rgba(down(_cf))
_wmv = Image.open(f"{D}/ganesha_wordmark_noir.png").convert("RGBA"); _wmv = _wmv.resize((300, round(_wmv.height * 300 / _wmv.width)), Image.LANCZOS)
VLOGO = rgba(_wmv)
_vpl = Image.new("RGBA", ((300 + 52) * S, (_wmv.height + 40) * S), (0, 0, 0, 0))
ImageDraw.Draw(_vpl).rounded_rectangle([0, 0, _vpl.width - 1, _vpl.height - 1], radius=22 * S, fill=ONYX + (210,))
VLOGO_PL = rgba(down(_vpl))
HOOK_T = text_img("How P2P processing works", "Cormorant", 76, "SemiBold", CHAMP)
HOOK_T2 = text_img("in India", "Cormorant", 76, "SemiBold", GOLD)

def vover(dst, src, x, y, a=1.0):
    h, w = src.shape[:2]; x0, y0 = max(0, x), max(0, y); x1, y1 = min(VW, x + w), min(VH, y + h)
    if x1 <= x0 or y1 <= y0 or a <= 0: return
    s = src[y0 - y:y1 - y, x0 - x:x1 - x]; al = s[..., 3:] / 255 * a
    dst[y0:y1, x0:x1] = dst[y0:y1, x0:x1] * (1 - al) + s[..., :3] * al

# graphics only: no speaker circle, no corner logo, no burned-in captions inside the card
draw_circle = lambda *a, **k: None
def card_graphics(t, frame):
    fs, cm = mode_at(t)
    img = FS_BG.copy()
    if fs: scene_fs(img, t, frame)
    else: cam_overlays(img, t)
    return img, (fs, cm)

def vsub(img, t):
    for s0, e0, ws in SUBS:
        if s0 <= t < e0:
            L = sub_layer(ws); L = cv2.resize(L, (int(L.shape[1] * 1.22), int(L.shape[0] * 1.22)), interpolation=cv2.INTER_CUBIC)
            if L.shape[1] > VW - 40: L = cv2.resize(L, (VW - 40, int(L.shape[0] * (VW - 40) / L.shape[1])), interpolation=cv2.INTER_AREA)
            vover(img, L, (VW - L.shape[1]) // 2, 930 - L.shape[0] // 2, min(1, (t - s0) / .1 + .35)); return

def vframe(ts, raw, t_out):
    img = VBG.copy()
    crop = raw[20:20 + 569, 681:681 + 608]
    ar = cv2.resize(np.ascontiguousarray(crop), (VW, AR_H), interpolation=cv2.INTER_CUBIC).astype(np.float32)
    bl = cv2.GaussianBlur(ar, (0, 0), 1.4); ar = np.clip(ar * 1.35 - bl * .35, 0, 255)
    img[:AR_H] = ar * (1 - AGRAD) + img[:AR_H] * AGRAD
    g, sig = card_graphics(ts, raw)
    if ts >= END_FS:                                            # vertical end card: buttons fill the lower half
        a = ease((ts - END_FS) / .4); b1 = ease((ts - cue("s10", "already")) / .35); b2 = ease((ts - cue("s10", "new")) / .35)
        key = (round(b1, 2), round(b2, 2)); grp = END_CACHE.get(key)
        if grp is None: grp = END_CACHE.setdefault(key, end_group(b1, b2, ts))
        sc = min(1.0, 840 / grp.shape[0]); grp2 = cv2.resize(grp, (int(grp.shape[1] * sc), int(grp.shape[0] * sc)), interpolation=cv2.INTER_AREA)
        vover(img, grp2, (VW - grp2.shape[1]) // 2, 1010, a)
    else:
        fs_, _ = sig
        if fs_: x0c, y0c, x1c, y1c = 540, 60, 1900, 826          # full-screen scenes (card aspect, right of the removed circle)
        else:   x0c, y0c, x1c, y1c = 763, 110, 1900, 750         # camera scenes: right-hand panel / stat card
        c = cv2.resize(g[y0c:y1c, x0c:x1c], (CARD_W, CARD_H), interpolation=cv2.INTER_AREA)
        x0 = (VW - CARD_W) // 2; reg = img[CARD_Y:CARD_Y + CARD_H, x0:x0 + CARD_W]
        img[CARD_Y:CARD_Y + CARD_H, x0:x0 + CARD_W] = reg * (1 - CMASK2) + c * CMASK2
        vover(img, CFRAME, x0, CARD_Y)
    vover(img, VLOGO_PL, 40, 60); vover(img, VLOGO, 66, 80)
    if t_out < 3.6:                                             # opening title
        a = ease(t_out / .35) * (1 - ease((t_out - 3.2) / .4))
        vover(img, HOOK_T, (VW - HOOK_T.shape[1]) // 2, CARD_Y + 190, a); vover(img, HOOK_T2, (VW - HOOK_T2.shape[1]) // 2, CARD_Y + 290, a)
    if ts < SPEECH_END + .05: vsub(img, ts)
    return img, sig

READERS = {}
def raw_at(ts):
    k = max(i for i, c in enumerate(CLIPS) if c["t0"] <= ts + 1e-6); c = CLIPS[k]
    if PREV:
        rr = Reader(c["f"], W, H, t0=clip_time(c, ts - c["t0"])); f = rr.next(); rr.p.kill(); return f.astype(np.float32)
    if k not in READERS: READERS[k] = SeqReader(c["f"])
    return READERS[k].get(clip_time(c, ts - c["t0"]) * FPS)

def src_times(t):
    """source times active at output time t (two during a crossfade) -> [(ts, weight)]"""
    out = []
    for i, (o0, a, b) in enumerate(OUT_T):
        if o0 <= t < o0 + (b - a):
            out.append((a + t - o0, i))
    if len(out) == 2:
        q = ease((t - OUT_T[out[1][1]][0]) / XF); return [(out[0][0], 1 - q), (out[1][0], q)]
    return [(out[-1][0], 1.0)] if out else [(SEGS[-1][1], 1.0)]

def main():
    enc = None
    if not PREV:
        enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{VW}x{VH}", "-r", str(FPS), "-i", "-",
                                "-c:v", "libx264", "-preset", "medium", "-crf", "17", "-pix_fmt", "yuv420p", OUTV], stdin=subprocess.PIPE)
    targets = sorted(int(round(x * FPS)) for x in PREV) if PREV else None
    prev_img = prev_sig = fade_from = None; fade_t0 = -1
    for j in range(NFV):
        t = j / FPS
        if targets is not None and j not in targets:
            if j > max(targets): break
            continue
        parts = src_times(t); img = None; sig = None
        for ts, wgt in parts:
            fr, sg = vframe(ts, raw_at(ts), t)
            img = fr * wgt if img is None else img + fr * wgt; sig = sg
        if targets is None and len(parts) == 1:
            if prev_sig is not None and sig != prev_sig: fade_from, fade_t0 = prev_img, t
            if fade_from is not None and t - fade_t0 < .24:
                q = ease((t - fade_t0) / .24); img = fade_from * (1 - q) + img * q
            prev_img, prev_sig = img, sig
        out = (img + VDITHER).clip(0, 255).astype(np.uint8)
        if enc: enc.stdin.write(out.tobytes())
        else: Image.fromarray(out).save(f"{sys.argv[4]}/v{t:06.2f}.png")
        if j % 300 == 0: print(j, NFV, flush=True)
    if enc: enc.stdin.close(); enc.wait()

if __name__ == "__main__":
    print("segments", OUT_T, "total", round(TOTAL_V, 2))
    main()
