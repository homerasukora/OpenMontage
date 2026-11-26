"""Ganesha Pay Academy promo (16:9, ~17 s): hook text -> 'Learn it for free' -> flash of 4 lessons ->
split screen English | Hindi (active half in colour with a language tag, idle half frozen, b/w, blurred) -> CTA.
usage: academy_promo.py out_video.mp4 [--preview t1,t2 outdir]; writes timeline.json for the audio mix."""
import sys, json, math, subprocess, numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont, ImageFilter
D = "/tmp/claude-0/-home-user/7c5690c1-77ca-5715-b441-4cc8e349293a/scratchpad"; P = f"{D}/promo"
OUT = sys.argv[1]; PREV = [float(x) for x in sys.argv[3].split(",")] if len(sys.argv) > 3 and sys.argv[2] == "--preview" else None
W, H, FPS, S = 1920, 1080, 30, 2
ONYX = (10, 11, 10); EMERALD = (15, 61, 46); GOLD = (207, 165, 74); CHAMP = (230, 214, 168)
L = {1: (f"{D}/w3/lesson1_v4_ganesha.mp4", f"{D}/hi/lesson1_hindi.mp4"), 2: (f"{D}/w5/lesson2_ganesha.mp4", f"{D}/w7/lesson2_hindi.mp4"),
     3: (f"{D}/w6/lesson3_ganesha.mp4", f"{D}/w8/lesson3_hindi.mp4"), 4: (f"{D}/w9/lesson4.mp4", f"{D}/w10/lesson4_hindi.mp4")}
# ---------- timeline (output seconds) ----------
T_HOOK, T_FREE, T_FLASH = 0.0, 1.9, 3.7
FLASH = [(1, 0, 14.0), (2, 0, 30.0), (3, 0, 20.0), (4, 0, 60.0)]          # (lesson, lang 0=EN 1=HI, source second), 0.25 s each
T_SPLIT = T_FLASH + 4 * .25
# split segments: (lesson, lang, src_start, src_end)
SEGS = [(2, 0, 48.50, 50.62), (2, 1, 60.30, 61.88), (4, 0, 25.20, 28.00), (4, 1, 31.12, 33.62)]
seg_t, t = [], T_SPLIT
for s in SEGS: seg_t.append(t); t += s[3] - s[2] + .12
T_CTA = t + .15; TOTAL = T_CTA + 3.3; NF = int(round(TOTAL * FPS))

def font(name, size, weight=None):
    f = ImageFont.truetype(f"{D}/fonts/{name}.ttf", size * S)
    if weight:
        try: f.set_variation_by_name(weight.encode())
        except Exception: pass
    return f
def rgba(im): return np.asarray(im, np.float32)
def down(im): return im.resize((im.width // S, im.height // S), Image.LANCZOS)
def ease(x): x = min(max(x, 0.0), 1.0); return x * x * (3 - 2 * x)
def over(dst, src, x, y, a=1.0):
    h, w = src.shape[:2]; x0, y0 = max(0, x), max(0, y); x1, y1 = min(W, x + w), min(H, y + h)
    if x1 <= x0 or y1 <= y0 or a <= 0: return
    s = src[y0 - y:y1 - y, x0 - x:x1 - x]; al = s[..., 3:] / 255 * a
    dst[y0:y1, x0:x1] = dst[y0:y1, x0:x1] * (1 - al) + s[..., :3] * al
def text(lines, w=W, h=None, gap=0):
    """lines: [(font, text, colour)] centred, shadowed -> RGBA"""
    hs = [int(f.size / S * 1.25) for f, _, _ in lines]; h = h or sum(hs) + gap * (len(lines) - 1) + 40
    m = Image.new("L", (w * S, h * S), 0); col = Image.new("RGB", m.size, CHAMP); dm, dc = ImageDraw.Draw(m), ImageDraw.Draw(col)
    y = 20
    for (f, t, c), hh in zip(lines, hs):
        if isinstance(t, list):                                    # mixed colours in one line: [(text, colour)]
            tw = sum(f.getlength(x, features=["lnum"] if "Cormorant" in f.path else None) for x, _ in t); x = (w * S - tw) / 2
            for part, cc in t:
                ft = ["lnum"] if "Cormorant" in f.path else None
                dm.text((x, (y + hh / 2) * S), part, font=f, fill=255, anchor="lm", features=ft); dc.text((x, (y + hh / 2) * S), part, font=f, fill=cc, anchor="lm", features=ft); x += f.getlength(part, features=ft)
        else:
            dm.text((w * S / 2, (y + hh / 2) * S), t, font=f, fill=255, anchor="mm", features=["lnum"] if "Cormorant" in f.path else None)
            dc.text((w * S / 2, (y + hh / 2) * S), t, font=f, fill=c, anchor="mm", features=["lnum"] if "Cormorant" in f.path else None)
        y += hh + gap
    mm = np.asarray(m, np.float32) / 255; sh = np.asarray(m.filter(ImageFilter.GaussianBlur(14 * S)), np.float32) / 255 * .7
    a = np.clip(mm + sh * (1 - mm), 0, 1); rgb = np.asarray(col, np.float32) * (mm / np.maximum(a, 1e-4))[..., None]
    return rgba(down(Image.fromarray(np.dstack([rgb.clip(0, 255), a * 255]).astype(np.uint8), "RGBA")))
def pill(t, size=34, fill=ONYX + (225,), fg=CHAMP, h=72, padx=30, fname="Manrope", bold="Bold"):
    f = font(fname, size, bold); tw = int(f.getlength(t) / S); w = tw + 2 * padx
    im = Image.new("RGBA", (w * S, h * S), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle([0, 0, w * S - 1, h * S - 1], radius=h * S // 2, fill=fill, outline=GOLD + (240,), width=2 * S)
    d.text((w * S // 2, h * S // 2), t, font=f, fill=fg, anchor="mm"); return rgba(down(im))

# background
yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
r = np.sqrt(((xx - W * .5) / (W * .6)) ** 2 + ((yy - H * .5) / (H * .75)) ** 2)
BG = np.array(ONYX, np.float32) + np.clip(1 - r, 0, 1)[..., None] ** 1.7 * (np.array(EMERALD, np.float32) * 1.5 - np.array(ONYX, np.float32))
_ln = Image.new("L", (W, H), 0); dl = ImageDraw.Draw(_ln)
for i in range(9): dl.line([(0, 140 + i * 100), (W, 140 + i * 100)], fill=9)
BG = BG + np.asarray(_ln, np.float32)[..., None] / 255 * np.array(GOLD, np.float32) * .5
DITHER = np.random.default_rng(3).uniform(-1, 1, (H, W, 1)).astype(np.float32)
_wm = Image.open(f"{D}/ganesha_wordmark_noir.png").convert("RGBA")
def wordmark(w): return rgba(_wm.resize((w, round(_wm.height * w / _wm.width)), Image.LANCZOS))
WM_S, WM_L = wordmark(250), wordmark(430)

F_HOOK = font("Cormorant", 118, "SemiBold"); F_SUB = font("Manrope", 40, "ExtraBold")
HOOK = text([(F_HOOK, [("New to ", CHAMP), ("P2P", GOLD), (" processing?", CHAMP)], None)])
FREE = text([(font("Cormorant", 124, "SemiBold"), [("Learn it for ", CHAMP), ("free", GOLD)], None), (F_SUB, "G A N E S H A   P A Y   A C A D E M Y", GOLD)], gap=6)
CTA = text([(font("Cormorant", 130, "SemiBold"), [("Learn to work ", CHAMP), ("online", GOLD)], None)])
CHIPS = [pill(t, 34) for t in ("Free", "Short lessons", "~20 min a day", "English & Hindi")]
LINK = pill("Link below  ↓", 46, fill=GOLD + (255,), fg=ONYX, h=104, padx=52)
TAG_EN = pill("ENGLISH", 30, fill=GOLD + (255,), fg=ONYX, h=62, padx=26, bold="ExtraBold")
_fh = ImageFont.truetype(f"{D}/fonts/NotoSansDeva.ttf", 30 * S)
def tag_hi():
    t1, f1 = "HINDI · ", font("Manrope", 30, "ExtraBold"); w = int((f1.getlength(t1) + _fh.getlength("हिन्दी")) / S) + 52; h = 62
    im = Image.new("RGBA", (w * S, h * S), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle([0, 0, w * S - 1, h * S - 1], radius=h * S // 2, fill=GOLD + (255,), outline=GOLD, width=2 * S)
    d.text((26 * S, h * S // 2), t1, font=f1, fill=ONYX, anchor="lm"); d.text((26 * S + f1.getlength(t1), h * S // 2 + 2 * S), "हिन्दी", font=_fh, fill=ONYX, anchor="lm")
    return rgba(down(im))
TAG_HI = tag_hi()
_fd = ImageFont.truetype(f"{D}/fonts/NotoSansDeva.ttf", 44 * S)
def caption(t, deva=False):
    f = _fd if deva else font("Manrope", 44, "Bold"); tw = int(f.getlength(t) / S) + 60; h = 90
    m = Image.new("L", (tw * S, h * S), 0); ImageDraw.Draw(m).text((tw * S // 2, h * S // 2), t, font=f, fill=255, anchor="mm")
    mm = np.asarray(m, np.float32) / 255; sh = np.asarray(m.filter(ImageFilter.GaussianBlur(10 * S)), np.float32) / 255 * .8
    a = np.clip(mm + sh * (1 - mm), 0, 1); rgb = np.ones(mm.shape + (3,), np.float32) * np.array(CHAMP, np.float32) * (mm / np.maximum(a, 1e-4))[..., None]
    return rgba(down(Image.fromarray(np.dstack([rgb.clip(0, 255), a * 255]).astype(np.uint8), "RGBA")))
CAPS = [caption("So why is the training free?"), caption("तो ट्रेनिंग फ़्री क्यों है?", True), caption("Accuracy is extremely important."), caption("एक्यूरेसी बेहद ज़रूरी है", True)]
TITLE_SPLIT = text([(font("Manrope", 34, "ExtraBold"), "G A N E S H A   P A Y   A C A D E M Y", GOLD)])

# ---------- source frames ----------
def grab(path, t0, dur, w, h):
    n = max(1, int(round(dur * FPS)))
    raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{t0:.3f}", "-i", path, "-t", f"{dur + .1:.3f}", "-vf", f"fps={FPS},scale={w}:{h}:flags=lanczos",
                          "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True).stdout
    fr = np.frombuffer(raw, np.uint8).reshape(-1, h, w, 3)
    return fr[:n] if len(fr) >= n else np.concatenate([fr, np.repeat(fr[-1:], n - len(fr), 0)])
HW, HH = 900, 506                                       # half-screen video size
SEGF = [grab(L[l][lang], a, b - a + .12, HW, HH) for l, lang, a, b in SEGS]
FLASHF = [grab(L[l][lang], s, .3, W, H) for l, lang, s in FLASH]
def idle(fr):                                           # frozen half: b/w, blurred, dimmed
    g = cv2.cvtColor(fr, cv2.COLOR_RGB2GRAY); g = cv2.GaussianBlur(g, (0, 0), 7)
    return (np.repeat(g[..., None], 3, 2).astype(np.float32) * .55)
def frame_box(img, fr, x, y, active_a):
    h, w = fr.shape[:2]; img[y:y + h, x:x + w] = fr
    fb = Image.new("RGBA", ((w + 12) * S, (h + 12) * S), (0, 0, 0, 0))
    ImageDraw.Draw(fb).rounded_rectangle([0, 0, fb.width - 1, fb.height - 1], radius=18 * S, outline=GOLD + (255,), width=(3 if active_a > .5 else 1) * S)
    over(img, rgba(down(fb)), x - 6, y - 6, .35 + .65 * active_a)
XL, XR, YV = (W // 2 - HW) // 2 + 10, W // 2 + (W // 2 - HW) // 2 - 10, 250

def render(t):
    img = BG.copy()
    if t < T_FREE:                                                       # hook
        a = ease(t / .45) * (1 - ease((t - (T_FREE - .3)) / .3)); sc = 1.04 - .04 * ease(t / .9)
        Lh = cv2.resize(HOOK, (int(HOOK.shape[1] * sc), int(HOOK.shape[0] * sc)), interpolation=cv2.INTER_AREA)
        over(img, Lh, (W - Lh.shape[1]) // 2, (H - Lh.shape[0]) // 2, a)
    elif t < T_FLASH:                                                    # learn it for free
        k = t - T_FREE; a = ease(k / .4) * (1 - ease((t - (T_FLASH - .25)) / .25))
        over(img, WM_L, (W - WM_L.shape[1]) // 2, 250, a)
        over(img, FREE, (W - FREE.shape[1]) // 2, (H - FREE.shape[0]) // 2 + 60 + int(30 * (1 - ease(k / .45))), a)
    elif t < T_SPLIT:                                                    # flash of the 4 lessons
        i = min(3, int((t - T_FLASH) / .25)); fr = FLASHF[i]; j = min(len(fr) - 1, int((t - T_FLASH - i * .25) * FPS))
        sc = 1.08 - .08 * ((t - T_FLASH - i * .25) / .25); f = fr[j]
        cw, ch = int(W / sc), int(H / sc); x0, y0 = (W - cw) // 2, (H - ch) // 2
        img = cv2.resize(f[y0:y0 + ch, x0:x0 + cw], (W, H), interpolation=cv2.INTER_LINEAR).astype(np.float32)
        if t - T_FLASH - i * .25 < .05: img = img * .6 + 255 * .4 * np.array(GOLD, np.float32) / 255
    elif t < T_CTA:                                                      # split screen
        k = max(i for i in range(len(SEGS)) if seg_t[i] <= t + 1e-6); l, lang, a0, b0 = SEGS[k]
        j = min(len(SEGF[k]) - 1, int((t - seg_t[k]) * FPS))
        # pair partner (same lesson, other language): before its turn -> its first frame; after -> its last frame
        pk = k + 1 if lang == 0 else k - 1
        pf = SEGF[pk][0] if pk > k else SEGF[pk][-1]
        act = ease((t - seg_t[k]) / .25)
        live = SEGF[k][j].astype(np.float32)
        cur = live * act + idle(SEGF[k][j]) * (1 - act)                 # active half wakes up in colour
        other = idle(pf) if lang == 0 else idle(pf) * act + pf.astype(np.float32) * (1 - act)   # partner falls asleep
        left, right = (cur, other) if lang == 0 else (other, cur)
        frame_box(img, left, XL, YV, 1.0 if lang == 0 else 0.0); frame_box(img, right, XR, YV, 1.0 if lang == 1 else 0.0)
        tag = TAG_EN if lang == 0 else TAG_HI; tx = (XL if lang == 0 else XR) + HW // 2 - tag.shape[1] // 2
        over(img, tag, tx, YV - 86 + int(14 * (1 - act)), act)
        cp = CAPS[k]; cx = (XL if lang == 0 else XR) + HW // 2 - cp.shape[1] // 2
        over(img, cp, cx, YV + HH + 18, act)
        over(img, TITLE_SPLIT, (W - TITLE_SPLIT.shape[1]) // 2, 70, ease((t - T_SPLIT) / .4))
        x = (W - (sum(c.shape[1] for c in CHIPS[:3]) + 2 * 22)) // 2                    # feature chips
        for i, c in enumerate(CHIPS[:3]):
            ci = T_SPLIT + .4 + i * .9; over(img, c, x, 900 + int(16 * (1 - ease((t - ci) / .35))), ease((t - ci) / .35)); x += c.shape[1] + 22
    else:                                                                # CTA
        k = t - T_CTA
        over(img, WM_L, (W - WM_L.shape[1]) // 2, 190, ease(k / .4))
        over(img, CTA, (W - CTA.shape[1]) // 2, 330 + int(30 * (1 - ease(k / .45))), ease(k / .45))
        x = (W - (sum(c.shape[1] for c in CHIPS) + 3 * 22)) // 2
        for i, c in enumerate(CHIPS):
            ci = .35 + i * .15; over(img, c, x, 560 + int(16 * (1 - ease((k - ci) / .3))), ease((k - ci) / .3)); x += c.shape[1] + 22
        bob = int(10 * math.sin(max(0, k - 1.0) * 2 * math.pi / 1.1))
        over(img, LINK, (W - LINK.shape[1]) // 2, 720 + bob, ease((k - .9) / .35))
        if TOTAL - t < .45: img = img * ease((TOTAL - t) / .45)
    if T_SPLIT <= t < T_CTA or t >= T_CTA: over(img, WM_S, W - WM_S.shape[1] - 60, 60, 1.0 if t < T_CTA else 0.0)
    return img

def main():
    json.dump(dict(segs=[dict(lesson=l, lang=g, src=[a, b], out=ot) for (l, g, a, b), ot in zip(SEGS, seg_t)], whooshes=[T_FREE, T_FLASH, T_SPLIT, T_CTA],
                   hits=[T_FLASH + i * .25 for i in range(4)], total=TOTAL, lessons={k: v for k, v in L.items()}), open(f"{P}/timeline.json", "w"), indent=1)
    enc = None if PREV else subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                                              "-c:v", "libx264", "-preset", "medium", "-crf", "17", "-pix_fmt", "yuv420p", OUT], stdin=subprocess.PIPE)
    tg = sorted(int(round(x * FPS)) for x in PREV) if PREV else None
    for j in range(NF):
        if tg is not None and j not in tg: continue
        t = j / FPS; out = (render(t) + DITHER).clip(0, 255).astype(np.uint8)
        if enc: enc.stdin.write(out.tobytes())
        else: Image.fromarray(out).save(f"{sys.argv[4]}/p{t:05.2f}.png")
    if enc: enc.stdin.close(); enc.wait()
    print("total", round(TOTAL, 2), "split at", [round(x, 2) for x in seg_t], "cta", round(T_CTA, 2))
main()
