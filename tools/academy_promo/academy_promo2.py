"""Ganesha Pay Academy promo v2 (16:9, ~23 s, phone-first): hook card -> full-screen trigger phrases from the lessons
with big captions -> ONE English|Hindi split moment (each half fills its side, full height) -> CTA.
usage: academy_promo2.py out_video.mp4 [--preview t1,t2 outdir]; writes timeline2.json for the mix."""
import sys, json, math, subprocess, numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont, ImageFilter
D = "/tmp/claude-0/-home-user/7c5690c1-77ca-5715-b441-4cc8e349293a/scratchpad"; P = f"{D}/promo"
OUT = sys.argv[1]; PREV = [float(x) for x in sys.argv[3].split(",")] if len(sys.argv) > 3 and sys.argv[2] == "--preview" else None
W, H, FPS, S = 1920, 1080, 30, 2
ONYX = (10, 11, 10); EMERALD = (15, 61, 46); GOLD = (207, 165, 74); CHAMP = (230, 214, 168)
EN = {1: f"{D}/w3/lesson1_v4_ganesha.mp4", 2: f"{D}/w5/lesson2_ganesha.mp4", 3: f"{D}/w6/lesson3_ganesha.mp4", 4: f"{D}/w9/lesson4.mp4"}
HI = {2: f"{D}/w7/lesson2_hindi.mp4"}
# clips: (path, src_start, src_end, caption lines [(text, gold?)...], kind)
CLIPS = [
    (EN[1], 7.30, 10.10, [[("What does a processing manager", 0)], [("actually ", 0), ("do?", 1)]], "full"),
    (EN[1], 22.66, 27.08, [[("For every successfully processed transaction,", 0)], [("you receive a ", 0), ("percentage", 1)]], "full"),
    (EN[3], 2.74, 5.32, [[("You don't need a complicated", 0)], [("professional setup", 1)]], "full"),
    (EN[4], 85.30, 90.30, [[("Speed, accuracy, security and discipline", 1)], [("make a reliable processing manager", 0)]], "full"),
    (EN[2], 48.50, 50.45, [[("So why is the training ", 0), ("free?", 1)]], "split_en"),
    (HI[2], 60.30, 61.90, [[("तो ट्रेनिंग फ़्री क्यों है?", 1)]], "split_hi"),
]
T_HOOK = 0.0; T_CLIPS = 2.2; XF = .18
OUTT, t = [], T_CLIPS
for c in CLIPS: OUTT.append(t); t += (c[2] - c[1]) + (.08 if c[4] != "split_en" else 0)
T_CTA = t + .1; TOTAL = T_CTA + 2.7; NF = int(round(TOTAL * FPS))

def font(name, size, weight=None):
    f = ImageFont.truetype(f"{D}/fonts/{name}.ttf", size * S)
    if weight:
        try: f.set_variation_by_name(weight.encode())
        except Exception: pass
    return f
F_DEVA = lambda size: ImageFont.truetype(f"{D}/fonts/NotoSansDeva.ttf", size * S)
def rgba(im): return np.asarray(im, np.float32)
def down(im): return im.resize((im.width // S, im.height // S), Image.LANCZOS)
def ease(x): x = min(max(x, 0.0), 1.0); return x * x * (3 - 2 * x)
def over(dst, src, x, y, a=1.0):
    h, w = src.shape[:2]; x0, y0 = max(0, x), max(0, y); x1, y1 = min(dst.shape[1], x + w), min(dst.shape[0], y + h)
    if x1 <= x0 or y1 <= y0 or a <= 0: return
    s = src[y0 - y:y1 - y, x0 - x:x1 - x]; al = s[..., 3:] / 255 * a
    dst[y0:y1, x0:x1] = dst[y0:y1, x0:x1] * (1 - al) + s[..., :3] * al
def is_deva(s): return any("ऀ" <= ch <= "ॿ" for ch in s)
def lines_img(lines, size, maxw, fname="Manrope", weight="ExtraBold", line_gap=1.18):
    """centred multi-line text with per-run gold/champagne colour and a soft shadow -> RGBA"""
    fl = font(fname, size, weight); fd = F_DEVA(size)
    fnt = lambda s: fd if is_deva(s) else fl
    widths = [sum(fnt(s).getlength(s, features=["lnum"] if fname == "Cormorant" and not is_deva(s) else None) for s, _ in ln) for ln in lines]; lh = int(size * line_gap * S)
    w = int(max(widths)) + 80 * S; h = lh * len(lines) + 60 * S
    m = Image.new("L", (w, h), 0); col = Image.new("RGB", (w, h), CHAMP); dm, dc = ImageDraw.Draw(m), ImageDraw.Draw(col)
    for k, (ln, lw) in enumerate(zip(lines, widths)):
        x = (w - lw) / 2; y = 30 * S + k * lh + lh / 2
        for s, g in ln:
            f = fnt(s); ft = ["lnum"] if fname == "Cormorant" and not is_deva(s) else None
            dm.text((x, y), s, font=f, fill=255, anchor="lm", features=ft); dc.text((x, y), s, font=f, fill=GOLD if g else CHAMP, anchor="lm", features=ft); x += f.getlength(s, features=ft)
    mm = np.asarray(m, np.float32) / 255; sh = np.asarray(m.filter(ImageFilter.GaussianBlur(12 * S)), np.float32) / 255 * .85
    a = np.clip(mm + sh * (1 - mm), 0, 1); rgb = np.asarray(col, np.float32) * (mm / np.maximum(a, 1e-4))[..., None]
    im = rgba(down(Image.fromarray(np.dstack([rgb.clip(0, 255), a * 255]).astype(np.uint8), "RGBA")))
    if im.shape[1] > maxw: im = cv2.resize(im, (maxw, int(im.shape[0] * maxw / im.shape[1])), interpolation=cv2.INTER_AREA)
    return im
def pill(t, size, fill, fg, h, padx):
    f = F_DEVA(size) if is_deva(t) else font("Manrope", size, "ExtraBold")
    parts = t.split("|"); fs = [F_DEVA(size) if is_deva(p) else font("Manrope", size, "ExtraBold") for p in parts]
    tw = int(sum(ff.getlength(p) for ff, p in zip(fs, parts)) / S); w = tw + 2 * padx
    im = Image.new("RGBA", (w * S, h * S), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle([0, 0, w * S - 1, h * S - 1], radius=h * S // 2, fill=fill, outline=GOLD + (255,), width=2 * S)
    x = padx * S
    for ff, p in zip(fs, parts):
        d.text((x, h * S // 2 + (2 * S if is_deva(p) else 0)), p, font=ff, fill=fg, anchor="lm"); x += ff.getlength(p)
    return rgba(down(im))

# background + static assets
yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
r = np.sqrt(((xx - W * .5) / (W * .6)) ** 2 + ((yy - H * .5) / (H * .75)) ** 2)
BG = np.array(ONYX, np.float32) + np.clip(1 - r, 0, 1)[..., None] ** 1.7 * (np.array(EMERALD, np.float32) * 1.5 - np.array(ONYX, np.float32))
DITHER = np.random.default_rng(3).uniform(-1, 1, (H, W, 1)).astype(np.float32)
_wm = Image.open(f"{D}/ganesha_wordmark_noir.png").convert("RGBA")
def wordmark(w): return rgba(_wm.resize((w, round(_wm.height * w / _wm.width)), Image.LANCZOS))
WM_L = wordmark(460)
BAND = np.clip((yy[..., None] - H * .66) / (H * .19), 0, 1) ** 1.2   # opaque from y≈890: hides the lessons' own small subtitles          # dark band under the big captions
HOOK = lines_img([[("New to ", 0), ("P2P", 1), (" processing?", 0)]], 120, 1800, "Cormorant", "SemiBold")
HOOK_SUB = lines_img([[("GANESHA PAY ACADEMY  ·  FREE", 1)]], 46, 1600)
CTA1 = lines_img([[("Learn to work ", 0), ("online", 1)]], 128, 1800, "Cormorant", "SemiBold")
CHIPS = [pill(t, 44, ONYX + (230,), CHAMP, 92, 36) for t in ("Free", "Short lessons", "~20 min a day", "English & Hindi")]
LINK = pill("Link below  ↓", 56, GOLD + (255,), ONYX, 118, 58)
TAG_EN = pill("ENGLISH", 52, GOLD + (255,), ONYX, 104, 46)
TAG_HI = pill("हिन्दी|  ·  HINDI", 52, GOLD + (255,), ONYX, 104, 46)
CAPS = [lines_img(c[3], 64, 1800) if c[4] == "full" else lines_img(c[3], 58, 900) for c in CLIPS]

def grab(path, t0, dur, w=W, h=H):
    n = max(1, int(round(dur * FPS)))
    raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{t0:.3f}", "-i", path, "-t", f"{dur + .15:.3f}", "-vf", f"fps={FPS},scale={w}:{h}:flags=lanczos",
                          "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True).stdout
    fr = np.frombuffer(raw, np.uint8).reshape(-1, h, w, 3)
    return fr[:n] if len(fr) >= n else np.concatenate([fr, np.repeat(fr[-1:], n - len(fr), 0)])
FR = [grab(c[0], c[1], c[2] - c[1] + .1) for c in CLIPS]
def half(fr):                                            # centre 960x1080 of a 1920 frame (presenter is centred)
    return fr[:, 480:1440]
def idle(h):
    g = cv2.GaussianBlur(cv2.cvtColor(np.ascontiguousarray(h), cv2.COLOR_RGB2GRAY), (0, 0), 8)
    return np.repeat(g[..., None], 3, 2).astype(np.float32) * .5

def clip_frame(k, t):
    c = CLIPS[k]; j = min(len(FR[k]) - 1, int((t - OUTT[k]) * FPS)); u = (t - OUTT[k]) / (c[2] - c[1])
    if c[4] == "full":
        f = FR[k][j]; sc = 1.0 + .045 * u                                      # slow push-in
        cw, ch = int(W / sc), int(H / sc); x0, y0 = (W - cw) // 2, int((H - ch) * .35)
        img = cv2.resize(f[y0:y0 + ch, x0:x0 + cw], (W, H), interpolation=cv2.INTER_LINEAR).astype(np.float32)
        img = img * (1 - BAND)
        cap = CAPS[k]; over(img, cap, (W - cap.shape[1]) // 2, H - cap.shape[0] - 40, ease((t - OUTT[k]) / .2))
        return img
    # split moment: left = English, right = Hindi; each half fills its side
    ken, khi = (k, k + 1) if c[4] == "split_en" else (k - 1, k)
    img = np.zeros((H, W, 3), np.float32)
    en_live = c[4] == "split_en"
    act = ease((t - OUTT[k]) / .22)
    fen = half(FR[ken][j if en_live else -1]).astype(np.float32)
    fhi = half(FR[khi][0 if en_live else j]).astype(np.float32)
    if en_live:
        left = fen * act + idle(half(FR[ken][j])) * (1 - act) if k > 0 and OUTT[k] > T_CLIPS + 1 else fen
        right = idle(half(FR[khi][0]))
    else:
        left = idle(half(FR[ken][-1])) * act + fen * (1 - act)
        right = fhi * act + idle(half(FR[khi][j])) * (1 - act)
    img[:, :960] = left; img[:, 960:] = right
    img = img * (1 - BAND)
    img[:, 957:963] = np.array(GOLD, np.float32)                               # gold divider
    tag = TAG_EN if en_live else TAG_HI; side = 0 if en_live else 960
    over(img, tag, side + 480 - tag.shape[1] // 2, 30 + int(16 * (1 - act)), act)
    cap = CAPS[k]; over(img, cap, side + 480 - cap.shape[1] // 2, H - cap.shape[0] - 40, act)
    return img

def render(t):
    if t < T_CLIPS:                                                            # hook
        img = BG.copy(); a = ease(t / .4) * (1 - ease((t - (T_CLIPS - .25)) / .25)); sc = 1.05 - .05 * ease(t / 1.0)
        Lh = cv2.resize(HOOK, (int(HOOK.shape[1] * sc), int(HOOK.shape[0] * sc)), interpolation=cv2.INTER_AREA)
        over(img, Lh, (W - Lh.shape[1]) // 2, 400 - Lh.shape[0] // 2, a)
        over(img, HOOK_SUB, (W - HOOK_SUB.shape[1]) // 2, 560, ease((t - .6) / .4) * (1 - ease((t - (T_CLIPS - .25)) / .25)))
        return img
    if t < T_CTA:
        k = max(i for i in range(len(CLIPS)) if OUTT[i] <= t + 1e-6)
        img = clip_frame(k, t)
        if k > 0 and t - OUTT[k] < XF and CLIPS[k][4] != "split_hi":            # short crossfade from the previous clip
            q = ease((t - OUTT[k]) / XF); img = clip_frame(k - 1, OUTT[k] - 1 / FPS) * (1 - q) + img * q
        if k == 0 and t - OUTT[0] < XF: img = img * ease((t - OUTT[0]) / XF) + BG * (1 - ease((t - OUTT[0]) / XF))
        return img
    k = t - T_CTA; img = BG.copy()                                             # CTA
    over(img, WM_L, (W - WM_L.shape[1]) // 2, 150, ease(k / .35))
    over(img, CTA1, (W - CTA1.shape[1]) // 2, 270 + int(30 * (1 - ease(k / .4))), ease(k / .4))
    x = (W - (sum(c.shape[1] for c in CHIPS) + 3 * 26)) // 2
    for i, c in enumerate(CHIPS):
        ci = .3 + i * .12; over(img, c, x, 560 + int(16 * (1 - ease((k - ci) / .3))), ease((k - ci) / .3)); x += c.shape[1] + 26
    bob = int(10 * math.sin(max(0, k - .9) * 2 * math.pi / 1.1))
    over(img, LINK, (W - LINK.shape[1]) // 2, 740 + bob, ease((k - .75) / .35))
    if k < .25: img = img * ease(k / .25)
    if TOTAL - t < .4: img = img * ease((TOTAL - t) / .4)
    return img

def main():
    json.dump(dict(segs=[dict(path=c[0], src=[c[1], c[2]], out=o) for c, o in zip(CLIPS, OUTT)], whooshes=[T_CLIPS] + OUTT[1:5] + [T_CTA], hits=[],
                   total=TOTAL), open(f"{P}/timeline2.json", "w"), indent=1)
    enc = None if PREV else subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                                              "-c:v", "libx264", "-preset", "medium", "-crf", "17", "-pix_fmt", "yuv420p", OUT], stdin=subprocess.PIPE)
    tg = sorted(int(round(x * FPS)) for x in PREV) if PREV else None
    for j in range(NF):
        if tg is not None and j not in tg: continue
        t = j / FPS; out = (render(t) + DITHER).clip(0, 255).astype(np.uint8)
        if enc: enc.stdin.write(out.tobytes())
        else: Image.fromarray(out).save(f"{sys.argv[4]}/q{t:05.2f}.png")
    if enc: enc.stdin.close(); enc.wait()
    print("total", round(TOTAL, 2), "clips at", [round(x, 2) for x in OUTT], "cta", round(T_CTA, 2))
main()
