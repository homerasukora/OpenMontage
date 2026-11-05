"""KoiPay trader dashboard ad (9:16): screen-recording panels with neon framing, ElevenLabs VO, subtitles, case insert, Telegram CTA."""
import json, math, subprocess, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

A = json.load(open(sys.argv[1])); OUT = sys.argv[2]
PREVIEW = [float(x) for x in sys.argv[3].split(",")] if len(sys.argv) > 3 else None
D = A["dir"]
WORDS = json.load(open(f"{D}/words.json")); LT = json.load(open(f"{D}/vo.json"))["lines"]; DUR = A["dur"]; CUTS = A["cuts"]

W, H, FPS = 1080, 1920, 25
NEON, NEON_DARK, WHITE, GREY, RED = (46, 232, 122), (10, 88, 38), (250, 255, 251), (160, 178, 166), (255, 92, 92)
F = "/usr/share/fonts/opentype/inter/"
def font(style, size): return ImageFont.truetype(F + f"InterDisplay-{style}.otf", size)
SUB = font("Black", 70); HUGE = font("Black", 132); BIG = font("Black", 96); TITLE = font("ExtraBold", 62)
PILL = font("Bold", 44); LABEL = font("SemiBold", 40); SMALL = font("SemiBold", 34)

def clamp(x, a=0.0, b=1.0): return max(a, min(b, x))
def ease(x): x = clamp(x); return 1 - (1 - x) ** 3
def ease_io(x): x = clamp(x); return x * x * (3 - 2 * x)
def appear(t, at, d=0.3): return ease((t - at) / d)
def rgba(c, a): return (*c, int(255 * clamp(a)))
def cue(word, line, n=0):
    hits = [w for w in WORDS if w["line"] == line and w["w"].lower().strip(".,?!:").startswith(word.lower())]
    return hits[n]["s"]

class Layers:
    def __init__(self):
        self.fill = Image.new("RGBA", (W, H), (0, 0, 0, 0)); self.neon = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        self.text = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        self.f, self.n, self.t = ImageDraw.Draw(self.fill), ImageDraw.Draw(self.neon), ImageDraw.Draw(self.text)

def ctext(d, xy, s, fnt, col, a, anchor="mm"):
    if a > 0: d.text(xy, s, font=fnt, fill=rgba(col, a), anchor=anchor)

def pill(L, cx, cy, s, a, filled=False, fnt=PILL, padx=36, h=80, icon=None):
    if a <= 0: return
    iw = h * 0.7 if icon else 0
    tw = L.t.textlength(s, font=fnt) + iw
    box = (cx - tw / 2 - padx, cy - h / 2, cx + tw / 2 + padx, cy + h / 2)
    L.f.rounded_rectangle(box, h // 2, fill=rgba(NEON_DARK, 0.95 * a) if filled else (6, 18, 10, int(215 * a)))
    L.n.rounded_rectangle(box, h // 2, outline=rgba(NEON, a), width=3)
    if icon: icon(L.n, box[0] + padx + iw * 0.4, cy, h * 0.55, a)
    ctext(L.t, (cx + iw / 2, cy + 1), s, fnt, WHITE, a)

def icon_plane(d, cx, cy, s, a):
    r = 0.5 * s; d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=rgba(NEON, a))
    p = [(cx - 0.3 * s, cy - 0.02 * s), (cx + 0.28 * s, cy - 0.24 * s), (cx + 0.16 * s, cy + 0.26 * s), (cx + 0.0 * s, cy + 0.08 * s)]
    d.polygon(p, fill=(4, 14, 8, int(255 * a)))
def icon_chat(d, cx, cy, s, a):
    d.rounded_rectangle((cx - 0.5 * s, cy - 0.38 * s, cx + 0.5 * s, cy + 0.22 * s), int(0.16 * s), outline=rgba(NEON, a), width=5)
    d.line([(cx - 0.2 * s, cy + 0.22 * s), (cx - 0.3 * s, cy + 0.45 * s), (cx + 0.02 * s, cy + 0.22 * s)], fill=rgba(NEON, a), width=5)
def icon_shot(d, cx, cy, s, a):
    d.rounded_rectangle((cx - 0.3 * s, cy - 0.45 * s, cx + 0.3 * s, cy + 0.45 * s), int(0.1 * s), outline=rgba(NEON, a), width=5)
    d.rectangle((cx - 0.18 * s, cy - 0.25 * s, cx + 0.18 * s, cy + 0.15 * s), outline=rgba(NEON, a), width=3)
def icon_eye(d, cx, cy, s, a):
    d.ellipse((cx - 0.5 * s, cy - 0.28 * s, cx + 0.5 * s, cy + 0.28 * s), outline=rgba(NEON, a), width=5)
    r = 0.14 * s; d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=rgba(NEON, a))

# ---------- backgrounds ----------
def neon_bg():
    bg = Image.new("RGB", (W, H), (2, 5, 3)); g = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(g)
    hz = 800
    for i in range(-16, 17): d.line([(W / 2 + i * 40, hz), (W / 2 + i * 300, H + 60)], fill=(46, 232, 122, 28), width=1)
    y, step = hz, 8
    while y < H: d.line([(0, y), (W, y)], fill=(46, 232, 122, int(14 + 30 * (y - hz) / (H - hz))), width=1); step *= 1.3; y += step
    rng = np.random.default_rng(5)
    for _ in range(34):
        x = int(rng.uniform(20, W - 20)); top = int(rng.uniform(60, 700)); bot = int(rng.uniform(top + 150, H))
        d.line([(x, top), (x, bot)], fill=(46, 232, 122, 50), width=2); d.ellipse((x - 4, top - 4, x + 4, top + 4), fill=(140, 255, 180, 190))
    gl = g.filter(ImageFilter.GaussianBlur(6)); bg.paste(gl, (0, 0), gl); bg.paste(g, (0, 0), g)
    arr = np.asarray(bg).astype(np.float32)
    yy, xx = np.mgrid[0:H, 0:W]; arr += (np.exp(-(((xx - W / 2) / 700) ** 2 + ((yy - 540) / 600) ** 2)) * 0.10)[..., None] * np.array(NEON, np.float32)
    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))
BG = neon_bg()
PHOTOS = {k: Image.open(v).convert("RGB") for k, v in A["photos"].items()}

# brand logo (original file, only scaled; rounded corners masked to drop the white JPEG background) + Telegram icon
LOGO_PX = 92
_lg = Image.open(A["logo"]).convert("RGB").resize((LOGO_PX * 4, LOGO_PX * 4), Image.LANCZOS)
_m = Image.new("L", _lg.size, 0); ImageDraw.Draw(_m).rounded_rectangle((6, 6, _lg.width - 7, _lg.height - 7), int(_lg.width * 0.17), fill=255)
_lg.putalpha(_m); LOGO = _lg.resize((LOGO_PX, LOGO_PX), Image.LANCZOS)
TG = Image.open(A["telegram"]).convert("RGBA").resize((170, 170), Image.LANCZOS)
BRAND = font("Bold", 46)
def draw_brand(img):
    img.alpha_composite(LOGO, (52, 58))
    d = ImageDraw.Draw(img); d.text((52 + LOGO_PX + 22, 58 + LOGO_PX // 2), "Koi Pay", font=BRAND, fill=(255, 255, 255, 255), anchor="lm",
                                  stroke_width=2, stroke_fill=(0, 0, 0, 120))

def photo_cover(name, z, fx, fy):
    im = PHOTOS[name]; pw, ph = im.size; s = max(W / pw, H / ph) * z; cw, ch = W / s, H / s
    x0 = clamp(fx - cw / 2, 0, pw - cw); y0 = clamp(fy - ch / 2, 0, ph - ch)
    return im.crop((int(x0), int(y0), int(x0 + cw), int(y0 + ch))).resize((W, H), Image.BICUBIC)

SUB = font("Black", 64)
# Instagram-safe teaser (9:16): no income figures, no deposit, no bot usernames. CTA: watch the full video on YouTube.
def fit(d, txt, style, size, maxw):
    f = font(style, size)
    while d.textlength(txt, font=f) > maxw and size > 22: size -= 2; f = font(style, size)
    return f
def cover(im, cw, ch, z=1.0, fx=None, fy=None):
    pw, ph = im.size; s = max(cw / pw, ch / ph) * z; w_, h_ = cw / s, ch / s
    fx = pw / 2 if fx is None else fx; fy = ph / 2 if fy is None else fy
    x0 = clamp(fx - w_ / 2, 0, pw - w_); y0 = clamp(fy - h_ / 2, 0, ph - h_)
    return im.crop((int(x0), int(y0), int(x0 + w_), int(y0 + h_))).resize((cw, ch), Image.BICUBIC), (s, x0, y0)
def video_still(path, ts, cw, ch):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{ts:.3f}", "-i", path, "-frames:v", "1", "-vf",
                          f"scale={cw}:{ch}:force_original_aspect_ratio=increase,crop={cw}:{ch}", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True).stdout
    return Image.frombuffer("RGB", (cw, ch), raw).copy()
def paste_card(img, L, pic, x, y, a, r=28, width=4):
    if a <= 0: return
    m = Image.new("L", pic.size, 0); ImageDraw.Draw(m).rounded_rectangle((0, 0, pic.width - 1, pic.height - 1), r, fill=int(255 * a))
    img.paste(pic, (int(x), int(y)), m)
    L.n.rounded_rectangle((x - 3, y - 3, x + pic.width + 3, y + pic.height + 3), r + 2, outline=rgba(NEON, a), width=width)
def glass(L, box, a, r=34):
    if a <= 0: return
    L.f.rounded_rectangle(box, r, fill=(6, 16, 10, int(240 * a))); L.n.rounded_rectangle(box, r, outline=rgba(NEON, 0.9 * a), width=4)
def seg_of(t): return max(i for i, c in enumerate(CUTS) if c <= t + 1e-6)

TZ = (40, 200, 1040, 860); TCX = 540; VB_Y, VB_H = 900, 1020
SRC_W = int(round(1080 * 1080 / VB_H)); CROP_CX = [920, 920, 930]
SUB_Y = 1560
def _top_bg():
    arr = np.zeros((VB_Y, W, 3), np.float32) + np.array((2, 8, 4), np.float32); yy, xx = np.mgrid[0:VB_Y, 0:W]
    arr += (np.exp(-(((xx - W / 2) / 620) ** 2 + ((yy - 520) / 420) ** 2)) * 0.5)[..., None] * np.array(NEON, np.float32)
    im = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8)); d = ImageDraw.Draw(im, "RGBA")
    for x in range(0, W + 1, 60): d.line([(x, 0), (x, VB_Y)], fill=(46, 232, 122, 14), width=1)
    for y in range(0, VB_Y + 1, 60): d.line([(0, y), (W, y)], fill=(46, 232, 122, 14), width=1)
    return im
TOP_BG = _top_bg()
def _full_bg():
    arr = np.asarray(BG).astype(np.float32); yy, xx = np.mgrid[0:H, 0:W]
    arr += (np.exp(-(((xx - W / 2) / 700) ** 2 + ((yy - 820) / 800) ** 2)) * 0.45)[..., None] * np.array(NEON, np.float32)
    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))
FS_BG = _full_bg()
LOGO_BIG = Image.open(A["logo"]).convert("RGB").resize((560, 560), Image.LANCZOS)
_m = Image.new("L", LOGO_BIG.size, 0); ImageDraw.Draw(_m).rounded_rectangle((4, 4, 555, 555), 95, fill=255); LOGO_BIG.putalpha(_m)

def video_block(frame, i):
    x0 = clamp(CROP_CX[min(i, 2)] - SRC_W / 2, 0, 1920 - SRC_W)
    return frame.resize((W, VB_H), Image.BICUBIC, box=(x0, 0, x0 + SRC_W, 1080))

def work_art(L, t, k, t0, x0=290, y0=290, sc=1.6):
    if k <= 0: return
    u = t - t0; S_ = lambda v: v * sc; w_, h_ = S_(320), S_(250)
    L.f.rounded_rectangle((x0, y0, x0 + w_, y0 + h_), 34, fill=(6, 16, 10, int(225 * k))); L.n.rounded_rectangle((x0, y0, x0 + w_, y0 + h_), 34, outline=rgba(NEON, k), width=5)
    c = rgba(NEON, k); wc = rgba(WHITE, k); d = L.n; lw = 7
    d.line([(x0 + S_(30), y0 + S_(200)), (x0 + w_ - S_(30), y0 + S_(200))], fill=c, width=lw)
    mx0, my0, mx1, my1 = x0 + S_(150), y0 + S_(55), x0 + S_(290), y0 + S_(150)
    d.rounded_rectangle((mx0, my0, mx1, my1), 14, outline=c, width=lw); d.line([(mx0 + S_(70), my1), (mx0 + S_(70), y0 + S_(180))], fill=c, width=lw)
    d.line([(mx0 + S_(45), y0 + S_(182)), (mx0 + S_(95), y0 + S_(182))], fill=c, width=lw)
    for j in range(4):
        hgt = S_(14 + 14 * j) * ease((u - 0.2 - 0.15 * j) / 0.4); bx = mx0 + S_(22 + j * 26)
        if hgt > 0: L.t.rectangle((bx, my1 - S_(12) - hgt, bx + S_(14), my1 - S_(12)), fill=c)
    hx, hy = x0 + S_(85), y0 + S_(85)
    d.ellipse((hx - S_(22), hy - S_(22), hx + S_(22), hy + S_(22)), outline=wc, width=lw)
    d.arc((hx - S_(48), hy + S_(30), hx + S_(48), hy + S_(150)), 200, 340, fill=wc, width=lw)
    d.line([(hx + S_(30), hy + S_(60)), (hx + S_(75), hy + S_(100)), (mx0 + S_(10), y0 + S_(196))], fill=wc, width=lw)
    d.line([(mx0 - S_(40), y0 + S_(196)), (mx0 + S_(20), y0 + S_(196))], fill=c, width=lw + 2)
    for j in range(3):
        kk = k * appear(u, 0.6 + 0.45 * j, 0.2); cx, cy = mx1 + S_(4), my0 - S_(10) + S_(34) * j; r = S_(13)
        if kk > 0:
            L.f.ellipse((cx - r, cy - r, cx + r, cy + r), fill=rgba((10, 88, 38), kk)); L.n.ellipse((cx - r, cy - r, cx + r, cy + r), outline=rgba(NEON, kk), width=3)
            L.t.line([(cx - S_(6), cy), (cx - S_(2), cy + S_(5)), (cx + S_(7), cy - S_(6))], fill=rgba(WHITE, kk), width=4)

def top_zone(img, L, t, i):
    u = t - CUTS[i]
    if i == 0:                                       # hook: rickshaw footage
        k = appear(u, 0.0, 0.25)
        paste_card(img, L, video_still(A["rk2"], 2.0 + u, 1000, 520), 40, 220 + 20 * (1 - k), k)
        pill(L, TCX, 815, "He used to drive a rickshaw", appear(u, 0.4), filled=True, fnt=font("ExtraBold", 50), h=92, padx=40)
    elif i == 1:                                     # his path, no numbers
        glass(L, (40, 200, 1040, 860), 1.0)
        ctext(L.t, (TCX, 280), "Ravi's path", font("Black", 72), WHITE, appear(u, 0.0, 0.25))
        rows = [("Before", "Rickshaw driver", 0.1), ("Then", "Rickshaw + KoiPay", cue("grew", 1) - CUTS[1] - 0.2), ("Now", "KoiPay full-time ✓", cue("full-time", 1) - CUTS[1] - 0.2)]
        for j, (tag, lab, at) in enumerate(rows):
            kk = appear(u, at, 0.25); y = 420 + j * 150; on = j == 2
            box = (90, y - 60, 990, y + 60)
            L.f.rounded_rectangle(box, 28, fill=rgba(NEON_DARK if (on and kk > 0.5) else (10, 26, 16), max(kk, 0.96))); L.n.rounded_rectangle(box, 28, outline=rgba(NEON, kk), width=3)
            ctext(L.t, (135, y), tag, LABEL, WHITE if on else NEON, kk, "lm"); ctext(L.t, (320, y), lab, fit(L.t, lab, "Bold", 52, 640), WHITE, kk, "lm")
    else:                                            # steady daily work
        work_art(L, t, appear(u, 0.0, 0.3), CUTS[2] + 0.2)

def endcard(L, img, t, t0):
    u = t - t0; k = ease(u / 0.35); s = 1.2 - 0.2 * k
    lg = LOGO_BIG.resize((int(170 * s), int(170 * s)), Image.LANCZOS); lg.putalpha(lg.getchannel("A").point(lambda v: int(v * k))); L.text.alpha_composite(lg, (TCX - lg.width // 2, 420 - lg.height // 2))
    kq = ease((u - 0.15) / 0.3)
    for j, ln in enumerate(("From rickshaw driver", "to full-time on KoiPay")):
        ctext(L.t, (TCX, 600 + 66 * j), ln, font("SemiBold", 52), GREY, kq)
    k2 = ease((u - 0.05) / 0.3); sz = int(170 * (1.18 - 0.18 * k2))
    ctext(L.t, (TCX, 850), "WATCH", font("Black", sz), WHITE, k2); ctext(L.t, (TCX, 1010), "FULL", font("Black", sz), WHITE, k2)
    k3 = ease((u - 0.3) / 0.3)
    txt = "on YouTube"; fnt = font("Black", 90); tw = L.t.textlength(txt, font=fnt); bw = tw + 170; x0 = TCX - bw / 2; y0 = 1140
    L.f.rounded_rectangle((x0, y0, x0 + bw, y0 + 134), 67, fill=rgba(NEON, k3)); L.n.rounded_rectangle((x0, y0, x0 + bw, y0 + 134), 67, outline=rgba(NEON, k3), width=8)
    cx, cy = x0 + 84, y0 + 67
    L.f.rounded_rectangle((cx - 40, cy - 28, cx + 40, cy + 28), 15, fill=(4, 20, 10, int(255 * k3)))
    L.f.polygon([(cx - 11, cy - 16), (cx - 11, cy + 16), (cx + 17, cy)], fill=rgba(NEON, k3))
    ctext(L.t, (x0 + 150, cy + 2), txt, fnt, (4, 20, 10), k3, "lm")
    ka = appear(u, 0.6, 0.3)                                                    # arrow toward the link sticker area
    if ka > 0:
        yy = 1350 + 12 * math.sin(u * 5)
        L.n.line([(TCX, yy), (TCX, yy + 70)], fill=rgba(NEON, ka), width=8)
        L.n.line([(TCX - 28, yy + 42), (TCX, yy + 74), (TCX + 28, yy + 42)], fill=rgba(NEON, ka), width=8, joint="curve")

# ---------- subtitles ----------
GREEN = {"arnold", "koipay", "guest", "traders", "ravi", "rickshaw", "$500", "step", "volume", "full-time", "₹2", "lakh", "month", "respect", "steady", "daily", "rates", "3%", "1%", "payin", "payout", "dashboard", "requests", "history", "commission", "support", "24/7", "telegram", "ready", "start", "today", "links"}
chunks, cur = [], []
for w in WORDS:
    cur.append(w)
    if w["w"][-1] in ".,?!:" or len(cur) == 3 or len(" ".join(x["w"] for x in cur)) >= 14: chunks.append(cur); cur = []
if cur: chunks.append(cur)
SUBS = []
for i, ch in enumerate(chunks):
    s = ch[0]["s"]; e = min(chunks[i + 1][0]["s"] if i + 1 < len(chunks) else DUR, ch[-1]["e"] + 0.4)
    SUBS.append((s, e, [(x["w"].rstrip(".,!:"), x["w"].lower().strip(".,?!:") in GREEN) for x in ch]))
SUB_Y = 1560

def draw_subs(t, img):
    cur = [s for s in SUBS if s[0] <= t < s[1]]
    if not cur: return
    s, e, toks = cur[-1]; k = appear(t, s, 0.1)
    widths = [SUB.getlength(tx + (" " if i < len(toks) - 1 else "")) for i, (tx, g) in enumerate(toks)]
    x = (W - sum(widths)) / 2
    lay = Image.new("RGBA", (W, 240), (0, 0, 0, 0)); sh = Image.new("RGBA", (W, 240), (0, 0, 0, 0))
    d, sd = ImageDraw.Draw(lay), ImageDraw.Draw(sh)
    for (tx, g), wd in zip(toks, widths):
        sd.text((x, 124), tx, font=SUB, fill=(0, 0, 0, int(240 * k)), anchor="lm", stroke_width=6, stroke_fill=(0, 0, 0, int(240 * k)))
        d.text((x, 120), tx, font=SUB, fill=rgba(NEON if g else WHITE, k), anchor="lm", stroke_width=3, stroke_fill=(0, 0, 0, int(200 * k)))
        x += wd
    sh = sh.filter(ImageFilter.GaussianBlur(9))
    img.alpha_composite(sh, (0, SUB_Y - 120)); img.alpha_composite(lay, (0, SUB_Y - 120))


def finish(img, L):
    out = img.convert("RGBA"); out = Image.alpha_composite(out, L.fill)
    glow = L.neon.resize((W // 2, H // 2), Image.BILINEAR).filter(ImageFilter.GaussianBlur(9)).resize((W, H), Image.BILINEAR)
    out = Image.alpha_composite(Image.alpha_composite(out, glow), glow); out = Image.alpha_composite(out, L.neon); return Image.alpha_composite(out, L.text)

def compose(t, frame):
    END0 = CUTS[3]; L = Layers()
    if t >= END0:
        img = FS_BG.copy(); endcard(L, img, t, END0); out = finish(img, L); draw_brand(out)
    else:
        i = seg_of(t); u = t - CUTS[i]
        img = Image.new("RGB", (W, H)); img.paste(TOP_BG, (0, 0))
        vb = video_block(frame, i); z = 1.0 + 0.05 * clamp(u / 4) + 0.05 * max(0, 1 - u / 0.18)
        if z > 1.001: w_, h_ = W / z, VB_H / z; vb = vb.resize((W, VB_H), Image.BICUBIC, box=((W - w_) / 2, (VB_H - h_) / 2, (W + w_) / 2, (VB_H + h_) / 2))
        img.paste(vb, (0, VB_Y)); top_zone(img, L, t, i)
        L.n.line([(0, VB_Y), (W, VB_Y)], fill=rgba(NEON, 1), width=4)
        out = finish(img, L); draw_brand(out); draw_subs(t, out)
        if t < 0.2: out = Image.blend(Image.new("RGBA", (W, H), (0, 0, 0, 255)), out, clamp(t / 0.2))
    for c in CUTS[1:4]:
        d = t - c
        if -0.04 <= d < 0.16: out = Image.blend(out.convert("RGB"), Image.new("RGB", (W, H), (200, 255, 220)), (1 - max(0, d) / 0.16) * 0.7).convert("RGBA")
    if DUR - t < 0.4: out = Image.blend(Image.new("RGBA", (W, H), (0, 0, 0, 255)), out, clamp((DUR - t) / 0.4))
    return out.convert("RGB")

def read_frame(t):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{t:.3f}", "-i", A["base"], "-frames:v", "1", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True).stdout
    return Image.frombuffer("RGB", (1920, 1080), raw).copy()

if PREVIEW:
    for t in PREVIEW: compose(t, read_frame(t)).save(f"{OUT}/prev_{t:05.2f}.jpg", quality=88)
    sys.exit()
dec = subprocess.Popen(["ffmpeg", "-v", "error", "-i", A["base"], "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], stdout=subprocess.PIPE)
enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                        "-i", A["mix"], "-map", "0:v", "-map", "1:a", "-c:v", "libx264", "-preset", "slow", "-crf", "17", "-pix_fmt", "yuv420p",
                        "-movflags", "+faststart", "-c:a", "aac", "-b:a", "192k", "-shortest", OUT], stdin=subprocess.PIPE)
n = int(DUR * FPS)
for k in range(n):
    buf = dec.stdout.read(1920 * 1080 * 3)
    fr = Image.frombuffer("RGB", (1920, 1080), buf).copy() if len(buf) == 1920 * 1080 * 3 else Image.new("RGB", (1920, 1080))
    enc.stdin.write(compose(k / FPS, fr).tobytes())
enc.stdin.close(); enc.wait(); print("done", n)
