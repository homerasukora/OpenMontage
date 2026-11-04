"""KoiPay trader dashboard ad (9:16): screen-recording panels with neon framing, ElevenLabs VO, subtitles, case insert, Telegram CTA."""
import json, math, subprocess, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

A = json.load(open(sys.argv[1])); OUT = sys.argv[2]
PREVIEW = [float(x) for x in sys.argv[3].split(",")] if len(sys.argv) > 3 else None
D = A["dir"]
WORDS = json.load(open(f"{D}/words.json")); LT = json.load(open(f"{D}/vo.json"))["lines"]; DUR = A["dur"]; CUTS = A["cuts"]

W, H, FPS = 1920, 1080, 25
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

SUB = font("Black", 60)

# ---------- helpers ----------
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
def paste_top(L, pic, x, y, a, r=20):
    """Paste a picture above the glass layers (into the text layer)."""
    if a <= 0: return
    im = pic.convert("RGBA"); m = Image.new("L", im.size, 0); ImageDraw.Draw(m).rounded_rectangle((0, 0, im.width - 1, im.height - 1), r, fill=int(255 * a))
    im.putalpha(m); L.text.alpha_composite(im, (int(x), int(y)))
    L.n.rounded_rectangle((x - 3, y - 3, x + im.width + 3, y + im.height + 3), r + 2, outline=rgba(NEON, a), width=3)
def glass(L, box, a, r=34):
    if a <= 0: return
    L.f.rounded_rectangle(box, r, fill=(6, 16, 10, int(240 * a))); L.n.rounded_rectangle(box, r, outline=rgba(NEON, 0.9 * a), width=4)
def win(t, t0, t1, d=0.3): return min(appear(t, t0, d), 1 - ease((t - t1) / 0.25))
def decode(args, w, h):
    p = subprocess.run(["ffmpeg", "-v", "error"] + args + ["-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True).stdout
    n = len(p) // (w * h * 3); return np.frombuffer(p[: n * w * h * 3], np.uint8).reshape(n, h, w, 3)
def icon_check(d, cx, cy, s, a):
    d.line([(cx - 0.32 * s, cy), (cx - 0.08 * s, cy + 0.26 * s), (cx + 0.36 * s, cy - 0.28 * s)], fill=rgba(NEON, a), width=8, joint="curve")
def icon_coin(d, cx, cy, s, a):
    r = 0.45 * s; d.ellipse((cx - r, cy - r, cx + r, cy + r), outline=rgba(NEON, a), width=5)
    d.text((cx, cy + 2), "₹", font=font("Black", int(s * 0.62)), fill=rgba(NEON, a), anchor="mm")
def icon_list(d, cx, cy, s, a):
    for k in (-0.28, 0, 0.28):
        d.ellipse((cx - 0.42 * s - 5, cy + k * s - 5, cx - 0.42 * s + 5, cy + k * s + 5), fill=rgba(NEON, a))
        d.line([(cx - 0.25 * s, cy + k * s), (cx + 0.42 * s, cy + k * s)], fill=rgba(NEON, a), width=5)
def icon_clock(d, cx, cy, s, a):
    r = 0.44 * s; d.ellipse((cx - r, cy - r, cx + r, cy + r), outline=rgba(NEON, a), width=5)
    d.line([(cx, cy), (cx, cy - 0.28 * s)], fill=rgba(NEON, a), width=5); d.line([(cx, cy), (cx + 0.2 * s, cy + 0.1 * s)], fill=rgba(NEON, a), width=5)

def seg_of(t): return max(i for i, c in enumerate(CUTS) if c <= t + 1e-6)

# ---------- assets ----------
TGI = TG.resize((150, 150), Image.LANCZOS)
SC = {s["name"]: s for s in json.load(open(A["dash_scenes"]))["scenes"]}
def _dash(nm, crop, cw):
    x, y, w, h = crop; ch = int(cw * h / w); sc = SC[nm]
    fr = decode(["-ss", f"{sc['s']:.3f}", "-t", f"{min(4.0, sc['e'] - sc['s']):.3f}", "-i", A["dash_base"], "-vf", "fps=25"], 1920, 1080)
    out = []
    for f in fr:
        im = Image.fromarray(f)
        for b in sc["blur"]: im.paste(im.crop(tuple(b)).filter(ImageFilter.GaussianBlur(16)), tuple(b[:2]))
        out.append(np.asarray(im.crop((x, y, x + w, y + h)).resize((cw, ch), Image.LANCZOS)))
    return out
RPX0, RPY0, RPX1, RPY1 = 1270, 190, 1880, 880            # right-hand panel
RPW, RPCX = RPX1 - RPX0, (RPX0 + RPX1) // 2
DMAXW, DMAXH = 1320, 690
def _dash_fit(nm, crop, t_from=0.0, dur=3.0):
    x, y, w, h = crop; s_ = min(DMAXW / w, DMAXH / h); cw, ch = int(w * s_), int(h * s_); sc = SC[nm]
    fr = decode(["-ss", f"{sc['s'] + t_from:.3f}", "-t", f"{dur:.3f}", "-i", A["dash_base"], "-vf", "fps=25"], 1920, 1080)
    out = []
    for f in fr:
        im = Image.fromarray(f)
        for b in sc["blur"] + [[395, 0, 500, 66]]: im.paste(im.crop(tuple(b)).filter(ImageFilter.GaussianBlur(18)), tuple(b[:2]))   # SurfGate logo + personal data
        out.append(np.asarray(im.crop((x, y, x + w, y + h)).resize((cw, ch), Image.LANCZOS)))
    return out
DM = {"home": _dash_fit("home", (395, 515, 800, 330)), "requests": _dash_fit("payins", (395, 62, 1120, 420), 0.5),
      "history": _dash_fit("report", (395, 62, 1120, 560), 0.5), "commission": _dash_fit("report", (395, 700, 1120, 360), 1.5)}
def dm_img(key, ts): fr = DM[key]; return Image.fromarray(fr[int(clamp(ts * 25, 0, len(fr) - 1))])
def _fs_bg():
    arr = np.asarray(BG).astype(np.float32); yy, xx = np.mgrid[0:H, 0:W]
    arr += (np.exp(-(((xx - W / 2) / 900) ** 2 + ((yy - H / 2) / 520) ** 2)) * 0.45)[..., None] * np.array(NEON, np.float32)
    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))
FS_BG = _fs_bg()
RAVI_G = (540, 690)

# ---------- split layout: video card left, story panel right ----------
VCARD = (40, 190, 1240, 865)                             # 1200x675
def split_amount(t):
    t0, t1 = cue("rickshaw", 1) - 0.45, CUTS[4] - 0.05
    return min(ease_io((t - t0) / 0.45), ease_io((t1 - t) / 0.4))

def story_panel(img, L, t):
    """Ravi's story beats (confirmed facts: Delhi rickshaw driver, $500 saved, first week ₹14,312, now full-time, ₹2,00,000+/month)."""
    ph_w, ph_h = RPW, 520
    beats = [(cue("rickshaw", 1) - 0.2, "rick"), (cue("$500", 1) - 0.25, "save"), (cue("started", 1) - 0.2, "koi"),
             (cue("step", 2) - 0.2, "week1"), (cue("later", 2) - 0.2, "fulltime"), (cue("now", 2) - 0.2, "income")]
    cur = [b for b in beats if t >= b[0]]
    if not cur: return
    t0, kind = cur[-1]; k = appear(t, t0, 0.3) * clamp(split_amount(t) * 1.6 - 0.6)
    if k <= 0: return
    y0 = RPY0
    if kind == "rick":
        pic = video_still(A["rk2"], 2.5 + (t - t0), ph_w, ph_h); paste_card(img, L, pic, RPX0, y0, k)
        pill(L, RPCX, RPY1 - 50, "Before: rickshaw driver · Delhi", k, filled=True, fnt=fit(L.t, "Before: rickshaw driver · Delhi", "Bold", 40, RPW - 80), h=80)
    elif kind == "save":
        pic, tr = cover(PHOTOS["group"], ph_w, ph_h, 1.25, 540, 760); paste_card(img, L, pic, RPX0, y0, k)
        s, x0, yy0 = tr; cx, cy = RPX0 + (RAVI_G[0] - x0) * s, y0 + (RAVI_G[1] - yy0) * s; r = 90
        L.n.ellipse((cx - r, cy - r * 1.2, cx + r, cy + r * 1.2), outline=rgba(NEON, k), width=5)
        pill(L, cx, cy - r * 1.2 - 40, "Ravi", k, filled=True, fnt=SMALL, h=58, padx=22)
        pill(L, RPCX, RPY1 - 50, "$500 saved from driving", k, filled=True, fnt=PILL, h=80)
    elif kind == "koi":
        glass(L, (RPX0, y0, RPX1, y0 + ph_h), k)
        lg = LOGO.resize((170, 170), Image.LANCZOS); lg.putalpha(lg.getchannel("A").point(lambda v: int(v * k))); L.text.alpha_composite(lg, (RPCX - 85, y0 + 70))
        ctext(L.t, (RPCX, y0 + 320), "$500", font("Black", 110), NEON, k); ctext(L.t, (RPCX, y0 + 430), "first deposit to start", LABEL, WHITE, k)
        pill(L, RPCX, RPY1 - 50, "Started with KoiPay", k, filled=True, fnt=PILL, h=80)
    elif kind == "week1":
        zk = ease((t - t0 - 0.3) / 0.8)
        pic, tr = cover(PHOTOS["selfie"], ph_w, ph_h, 1.0 + 1.5 * zk, 480 + 190 * zk, 640 + 20 * zk); paste_card(img, L, pic, RPX0, y0, k)
        s, x0, yy0 = tr; bx0, by0 = RPX0 + (585 - x0) * s, y0 + (652 - yy0) * s; bx1, by1 = RPX0 + (760 - x0) * s, y0 + (705 - yy0) * s
        if zk > 0.7: L.n.rounded_rectangle((bx0 - 12, by0 - 12, bx1 + 12, by1 + 12), 16, outline=rgba(NEON, k * appear(t, t0 + 1.0)), width=6)
        pill(L, RPCX, y0 + 60, "WEEK 1", k, filled=True, fnt=font("Black", 60), h=96, padx=40)
        pill(L, RPCX, RPY1 - 50, "Earned: ₹14,312", k, fnt=TITLE, h=90, padx=36)
    elif kind == "fulltime":
        glass(L, (RPX0, y0, RPX1, RPY1), k)
        ctext(L.t, (RPCX, y0 + 70), "Ravi's path", TITLE, WHITE, k)
        rows = [("Before", "Rickshaw driver", t0), ("Then", "Rickshaw + KoiPay", t0 + 0.35), ("Now", "KoiPay full-time ✓", cue("full-time", 2) - 0.2)]
        for j, (tag, lab, at) in enumerate(rows):
            kk = k * appear(t, at, 0.25); y = y0 + 190 + j * 165; on = j == 2
            box = (RPX0 + 40, y - 62, RPX1 - 40, y + 62)
            L.f.rounded_rectangle(box, 28, fill=rgba(NEON_DARK if (on and kk > 0.5) else (10, 26, 16), max(kk, 0.96 * k))); L.n.rounded_rectangle(box, 28, outline=rgba(NEON, kk), width=3)
            ctext(L.t, (RPX0 + 80, y), tag, SMALL, WHITE if on else NEON, kk, "lm")
            ctext(L.t, (RPX0 + 215, y), lab, fit(L.t, lab, "Bold", 42, RPX1 - 80 - (RPX0 + 215)), WHITE, kk, "lm")
    elif kind == "income":
        glass(L, (RPX0, y0, RPX1, RPY1), k)
        cy = (RPY0 + RPY1) / 2
        ctext(L.t, (RPCX, cy - 120), "Ravi now earns", LABEL, GREY, k)
        at = cue("₹2", 2); kk = k * appear(t, at - 0.2, 0.2)
        n = int(200000 * ease((t - at + 0.2) / 1.0)); txt = f"₹{n // 100000},{(n // 1000) % 100:02d},{n % 1000:03d}" if n >= 100000 else f"₹{n // 1000},{n % 1000:03d}" if n >= 1000 else f"₹{n}"
        if n >= 200000: txt += "+"
        ctext(L.t, (RPCX, cy), txt, fit(L.t, "₹2,00,000+", "Black", 104, RPW - 90), NEON, kk)
        ctext(L.t, (RPCX, cy + 110), "per month", TITLE, WHITE, k * appear(t, cue("month", 2) - 0.2))

# ---------- side panel in the office ----------
OPX0, OPY0, OPX1, OPY1 = 1240, 150, 1870, 900
OPCX = (OPX0 + OPX1) // 2
def office_panel(img, L, t, i):
    if i == 5:
        a = min(appear(t, cue("why", 4) - 0.1, 0.3), 1.0)
        glass(L, (OPX0, OPY0, OPX1, OPY1), a)
        ctext(L.t, (OPCX, OPY0 + 80), "Why KoiPay?", TITLE, WHITE, a)
        rows = [("PayIn", "≈ 3%", "incoming payment", "↓", cue("3%", 4)), ("PayOut", "≈ 1%", "outgoing payment", "↑", cue("1%", 4))]
        for j, (tag, rate, sub, arr, at) in enumerate(rows):
            k = a * appear(t, at - 0.25, 0.3); y = OPY0 + 170 + j * 260
            box = (OPX0 + 40, y, OPX1 - 40, y + 225)
            L.f.rounded_rectangle(box, 30, fill=rgba((10, 26, 16) if k > 0.05 else (6, 16, 10), max(k, 0.96 * a))); L.n.rounded_rectangle(box, 30, outline=rgba(NEON, k), width=3)
            ctext(L.t, (OPCX, y + 48), f"{tag} {arr}", font("ExtraBold", 46), WHITE, k)
            ctext(L.t, (OPCX, y + 125), rate, font("Black", 100), NEON, k)
            ctext(L.t, (OPCX, y + 192), sub, font("SemiBold", 32), GREY, k)
        ctext(L.t, (OPCX, OPY1 - 60), "Base rates · terms confirmed at onboarding", fit(L.t, "Base rates · terms confirmed at onboarding", "SemiBold", 30, OPX1 - OPX0 - 70), GREY, a * appear(t, cue("payout", 4)))
    elif i == 6:
        ts = cue("support", 5)
        kA = 1 - appear(t, ts - 0.3, 0.25)
        glass(L, (OPX0, OPY0, OPX1, OPY1), 1.0)
        if kA > 0:
            ctext(L.t, (OPCX, OPY0 + 70), "One simple dashboard", fit(L.t, "One simple dashboard", "ExtraBold", 54, OPX1 - OPX0 - 70), WHITE, kA)
            yb = OPY0 + 200
            for j, (lab, ic, w_) in enumerate((("Requests", icon_list, "requests"), ("History", icon_clock, "history"), ("Commission", icon_coin, "commission"))):
                k = kA * appear(t, cue(w_, 5) - 0.15); y = yb + j * 100
                box = (OPX0 + 40, y - 40, OPX1 - 40, y + 40)
                L.f.rounded_rectangle(box, 24, fill=rgba((10, 26, 16) if k > 0.05 else (6, 16, 10), max(k, 0.96))); L.n.rounded_rectangle(box, 24, outline=rgba(NEON, k), width=3)
                ic(L.n, OPX0 + 95, y, 48, k); ctext(L.t, (OPX0 + 145, y), lab, font("Bold", 40), WHITE, k, "lm")
        kB = appear(t, ts - 0.15, 0.3)
        if kB > 0:
            g = TGI.copy(); g.putalpha(g.getchannel("A").point(lambda v: int(v * kB))); L.text.alpha_composite(g, (OPCX - 75, OPY0 + 90))
            ctext(L.t, (OPCX, OPY0 + 330), "Support in Telegram", fit(L.t, "Support in Telegram", "ExtraBold", 50, OPX1 - OPX0 - 70), WHITE, kB)
            k24 = kB * appear(t, cue("24/7", 5) - 0.3)
            ctext(L.t, (OPCX, OPY0 + 500), "24/7", font("Black", 150), NEON, k24)
            ctext(L.t, (OPCX, OPY0 + 620), "every day, any hour", font("SemiBold", 36), GREY, k24)

# ---------- full-screen dashboard montage ----------
PIP_C, PIP_R = (270, 765), 160
def dash_window(): return cue("dashboard", 5) - 0.45, cue("support", 5) - 0.35
def dash_fs(img, L, t, frame):
    t0, t1 = dash_window()
    d = 2 * PIP_R; src = frame.resize((d, d), Image.BICUBIC, box=(640 - 300, 420 - 300, 640 + 300, 420 + 300))
    m = Image.new("L", (d, d), 0); ImageDraw.Draw(m).ellipse((0, 0, d - 1, d - 1), fill=255); img.paste(src, (PIP_C[0] - PIP_R, PIP_C[1] - PIP_R), m)
    L.n.ellipse((PIP_C[0] - PIP_R - 4, PIP_C[1] - PIP_R - 4, PIP_C[0] + PIP_R + 4, PIP_C[1] + PIP_R + 4), outline=rgba(NEON, 1), width=6)
    beats = [(t0, "home", "Your dashboard"), (cue("requests", 5) - 0.15, "requests", "Requests"), (cue("history", 5) - 0.15, "history", "History"),
             (cue("commission", 5) - 0.15, "commission", "Commission per operation"), (cue("all", 5) - 0.15, "home", "All in one place")]
    cur = [b for b in beats if t >= b[0]]; bt, key, title = cur[-1]; u = t - bt
    k = appear(t, t0 + 0.25, 0.3); kc = appear(u, 0, 0.18) if bt > t0 else 1
    pic = dm_img(key, u + (0 if key != "home" or bt == t0 else 1.0)); z = 1.0 + 0.10 * ease_io(u / 1.6)                # push-in on every cut, anchored top-left so labels stay in frame
    pic = pic.resize((int(pic.width * z), int(pic.height * z)), Image.BICUBIC).crop((int(pic.width * (z - 1) * 0.15), int(pic.height * (z - 1) * 0.2), int(pic.width * (z - 1) * 0.15) + pic.width, int(pic.height * (z - 1) * 0.2) + pic.height))
    if bt == t0:                                                                                  # first beat grows in from the side panel size
        sc_ = 0.55 + 0.45 * ease_io((t - t0 - 0.1) / 0.6); pic = pic.resize((max(1, int(pic.width * sc_)), max(1, int(pic.height * sc_))), Image.BICUBIC)
    X = 1195; y = 560 - pic.height / 2 + 30
    paste_card(img, L, pic, X - pic.width / 2, y + 20 * (1 - k), k, r=24)
    pill(L, X, y - 55, title, k * kc, filled=True, fnt=font("ExtraBold", 46), h=84, padx=40)
    ys = 200
    for j, (bt_, key_, lab) in enumerate(beats[1:4]):
        kk = appear(t, bt_, 0.25)
        if kk <= 0: continue
        on = bt_ == bt
        L.f.rounded_rectangle((60, ys, 470, ys + 76), 24, fill=rgba(NEON_DARK if on else (6, 18, 10), 0.95 * kk)); L.n.rounded_rectangle((60, ys, 470, ys + 76), 24, outline=rgba(NEON, kk), width=3)
        ctext(L.t, (90, ys + 38), "✓ " + lab.split(" ")[0], font("Bold", 38), WHITE, kk, "lm"); ys += 92

# ---------- end card ----------
T_END = None
def endcard(L, t, t0):
    k0 = appear(t, t0 + 0.2, 0.35)
    ctext(L.t, (960, 150), "Start now", font("Black", 92), WHITE, k0)
    cards = [("NEW TO P2P", "Free training", "@koiedubot", 200, t0 + 0.35), ("EXPERIENCED", "Start working", "@koipayp2p2bot", 1020, t0 + 0.6)]
    tg = TG.resize((150, 150), Image.LANCZOS)
    for tag, lab, user, x0, at in cards:
        k = appear(t, at, 0.35); dy = int(30 * (1 - k)); box = (x0, 235 + dy, x0 + 700, 785 + dy); cx = x0 + 350
        L.f.rounded_rectangle(box, 40, fill=(6, 16, 10, int(246 * k))); L.n.rounded_rectangle(box, 40, outline=rgba(NEON, k), width=5)
        fnt = font("Black", 44); tw = L.t.textlength(tag, font=fnt)
        L.f.rounded_rectangle((cx - tw / 2 - 34, 265 + dy, cx + tw / 2 + 34, 345 + dy), 40, fill=rgba(NEON, k))
        ctext(L.t, (cx, 306 + dy), tag, fnt, (4, 20, 10), k)
        g = tg.copy(); g.putalpha(g.getchannel("A").point(lambda v: int(v * k))); L.text.alpha_composite(g, (cx - 75, 380 + dy))
        ctext(L.t, (cx, 590 + dy), lab, TITLE, WHITE, k)
        pill(L, cx, 695 + dy, user, k, filled=True, fnt=font("Black", 54 if len(user) < 12 else 48), h=100, padx=40)
    k3 = appear(t, cue("under", 6) - 0.2)
    if k3 > 0:
        txt = "Links under this video ↓"; fnt = font("Black", 50); tw = L.t.textlength(txt, font=fnt)
        L.f.rounded_rectangle((960 - tw / 2 - 44, 825, 960 + tw / 2 + 44, 905), 40, fill=rgba(NEON, k3))
        ctext(L.t, (960, 866), txt, fnt, (4, 20, 10), k3)

# ---------- "steady daily work" illustration: neon line-art, person at a computer ----------
def work_art(L, t, k, t0):
    if k <= 0: return
    x0, y0, w_, h_ = 1570, 100, 320, 250; u = t - t0
    L.f.rounded_rectangle((x0, y0, x0 + w_, y0 + h_), 30, fill=(6, 16, 10, int(225 * k))); L.n.rounded_rectangle((x0, y0, x0 + w_, y0 + h_), 30, outline=rgba(NEON, k), width=4)
    c = rgba(NEON, k); wc = rgba(WHITE, k); d = L.n
    d.line([(x0 + 30, y0 + 200), (x0 + w_ - 30, y0 + 200)], fill=c, width=5)                       # desk
    mx0, my0, mx1, my1 = x0 + 150, y0 + 55, x0 + 290, y0 + 150                                   # monitor
    d.rounded_rectangle((mx0, my0, mx1, my1), 10, outline=c, width=5); d.line([(mx0 + 70, my1), (mx0 + 70, y0 + 180)], fill=c, width=5)
    d.line([(mx0 + 45, y0 + 182), (mx0 + 95, y0 + 182)], fill=c, width=5)
    for j in range(4):                                                                           # growing bars on screen
        hgt = (14 + 14 * j) * ease((u - 0.2 - 0.15 * j) / 0.4); bx = mx0 + 22 + j * 26
        if hgt > 0: L.t.rectangle((bx, my1 - 12 - hgt, bx + 14, my1 - 12), fill=c)
    hx, hy = x0 + 85, y0 + 85                                                                    # person
    d.ellipse((hx - 22, hy - 22, hx + 22, hy + 22), outline=wc, width=5)
    d.arc((hx - 48, hy + 30, hx + 48, hy + 150), 200, 340, fill=wc, width=5)
    d.line([(hx + 30, hy + 60), (hx + 75, hy + 100), (mx0 + 10, y0 + 196)], fill=wc, width=5)
    tap = 4 * math.sin(u * 18) if u > 0.3 else 0
    d.line([(mx0 - 40, y0 + 196 + tap * 0.2), (mx0 + 20, y0 + 196 + tap * 0.2)], fill=c, width=6)  # keyboard
    for j in range(3):                                                                           # confirmations popping
        kk = k * appear(u, 0.6 + 0.45 * j, 0.2); cx, cy = mx1 + 2, my0 - 10 + 34 * j
        if kk > 0:
            L.f.ellipse((cx - 13, cy - 13, cx + 13, cy + 13), fill=rgba((10, 88, 38), kk)); L.n.ellipse((cx - 13, cy - 13, cx + 13, cy + 13), outline=rgba(NEON, kk), width=3)
            L.t.line([(cx - 6, cy), (cx - 2, cy + 5), (cx + 7, cy - 6)], fill=rgba(WHITE, kk), width=3)

# ---------- full-frame overlays ----------
def overlays(img, L, t, i):
    if i == 0:
        k = win(t, 0.6, 4.3)
        pill(L, 470, 870, "Arnold · KoiPay manager", k, filled=True, fnt=TITLE, h=96, padx=44)
    elif i == 1:
        cx0, cy0, cw, ch = 690, 60, 540, 960
        L.n.rounded_rectangle((cx0 - 3, cy0 - 3, cx0 + cw + 3, cy0 + ch + 3), 8, outline=rgba(NEON, 1), width=5)
        u = t - CUTS[1]
        ka = appear(u, 0.15, 0.35)
        pic, _ = cover(PHOTOS["rick"], 460, 600, 1.05 + 0.04 * u, 520, 640); paste_card(img, L, pic, 130, 260 + 20 * (1 - ka), ka)
        pill(L, 360, 200, "Remember Ravi?", ka, filled=True, fnt=font("ExtraBold", 48), h=88, padx=36)
        pill(L, 360, 930, "Rickshaw driver · Delhi", appear(u, 0.6), fnt=PILL, h=78)
        kb = appear(u, 1.3, 0.35)
        pic, _ = cover(PHOTOS["selfie"], 460, 600, 1.08, 520, 700); paste_card(img, L, pic, 1330, 260 + 20 * (1 - kb), kb)
        pill(L, 1560, 200, "First video: week 1", kb, filled=True, fnt=font("ExtraBold", 44), h=88, padx=32)
        pill(L, 1560, 930, "Earned ₹14,312", appear(u, 1.8), fnt=PILL, h=78)
    elif i in (2, 3):
        if t < cue("rickshaw", 1) - 0.45:
            k = win(t, cue("ravi", 1) - 0.1, cue("rickshaw", 1) - 0.6)
            pill(L, 1450, 870, "Ravi · KoiPay trader", k, filled=True, fnt=TITLE, h=96, padx=44)
    elif i == 4:
        work_art(L, t, win(t, cue("results", 3) - 0.2, CUTS[5] - 0.3), cue("results", 3) - 0.2)
    elif i in (5, 6):
        office_panel(img, L, t, i)
    elif i == 7:
        k = win(t, cue("start", 6) - 0.2, cue("all", 6) - 0.4)
        pill(L, 1450, 870, "Start today", k, filled=True, fnt=TITLE, h=96, padx=44)

# ---------- subtitles ----------
GREEN = {"arnold", "koipay", "guest", "traders", "ravi", "rickshaw", "$500", "step", "volume", "full-time", "₹2", "lakh", "month", "respect", "steady", "daily", "rates", "3%", "1%", "payin", "payout", "dashboard", "requests", "history", "commission", "support", "24/7", "telegram", "ready", "start", "today", "links"}
chunks, cur = [], []
for w in WORDS:
    cur.append(w)
    if w["w"][-1] in ".,?!:" or len(cur) == 3 or len(" ".join(x["w"] for x in cur)) >= 15: chunks.append(cur); cur = []
if cur: chunks.append(cur)
SUBS = []
for i, ch in enumerate(chunks):
    s = ch[0]["s"]; e = min(chunks[i + 1][0]["s"] if i + 1 < len(chunks) else DUR, ch[-1]["e"] + 0.4)
    SUBS.append((s, e, [(x["w"].rstrip(".,!:"), x["w"].lower().strip(".,?!:") in GREEN) for x in ch]))
SUB_Y = 985

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


# ---------- compose ----------
def finish(img, L):
    out = img.convert("RGBA"); out = Image.alpha_composite(out, L.fill)
    glow = L.neon.resize((W // 2, H // 2), Image.BILINEAR).filter(ImageFilter.GaussianBlur(9)).resize((W, H), Image.BILINEAR)
    out = Image.alpha_composite(Image.alpha_composite(out, glow), glow); out = Image.alpha_composite(out, L.neon); return Image.alpha_composite(out, L.text)

def punch(frame, z, cx=960, cy=470):
    if z <= 1.001: return frame
    w_, h_ = W / z, H / z; x0 = clamp(cx - w_ / 2, 0, W - w_); y0 = clamp(cy - h_ / 2, 0, H - h_)
    return frame.resize((W, H), Image.BICUBIC, box=(x0, y0, x0 + w_, y0 + h_))

def compose(t, frame):
    global T_END
    T_END = cue("all", 6) - 0.35
    L = Layers(); i = seg_of(t)
    if i == 4: frame = punch(frame, 1.0 + 0.06 * ease((t - CUTS[4]) / 0.5), 900, 430)
    sp = split_amount(t) if i in (2, 3) else 0.0
    if t >= T_END:
        p = ease_io((t - T_END) / 0.45)
        fs = FS_BG.copy(); L2 = Layers(); endcard(L2, t, T_END); fs = finish(fs, L2)
        out = frame.convert("RGBA")
        xe = int(W * (1 - p)); out.paste(fs.crop((xe, 0, W, H)), (xe, 0))
        if p < 1: ImageDraw.Draw(out).rectangle((xe - 6, 0, xe + 6, H), fill=rgba(NEON, 0.9))
    elif dash_window()[0] <= t < dash_window()[1]:
        t0, t1 = dash_window(); p = min(ease_io((t - t0) / 0.45), ease_io((t1 - t) / 0.35))
        fs = FS_BG.copy(); L2 = Layers(); dash_fs(fs, L2, t, frame); fs = finish(fs, L2)
        out = frame.convert("RGBA"); xe = int(W * (1 - p)); out.paste(fs.crop((xe, 0, W, H)), (xe, 0))
        if p < 1: ImageDraw.Draw(out).rectangle((xe - 6, 0, xe + 6, H), fill=rgba(NEON, 0.9))
    elif sp > 0:
        img = FS_BG.copy()
        x0, y0 = VCARD[0] * sp, VCARD[1] * sp; x1, y1 = W + (VCARD[2] - W) * sp, H + (VCARD[3] - H) * sp
        v = frame.resize((int(x1 - x0), int(y1 - y0)), Image.BICUBIC)
        m = Image.new("L", v.size, 0); ImageDraw.Draw(m).rounded_rectangle((0, 0, v.width - 1, v.height - 1), int(28 * sp), fill=255)
        img.paste(v, (int(x0), int(y0)), m)
        L.n.rounded_rectangle((x0 - 3, y0 - 3, x1 + 3, y1 + 3), 30, outline=rgba(NEON, sp), width=4)
        story_panel(img, L, t)
        out = finish(img, L)
    else:
        img = frame.copy(); overlays(img, L, t, i); out = finish(img, L)
    for c in (CUTS[1], CUTS[2], CUTS[5]):                                   # neon flash on scene changes
        d = t - c
        if -0.04 <= d < 0.16: out = Image.blend(out.convert("RGB"), Image.new("RGB", (W, H), (200, 255, 220)), (1 - max(0, d) / 0.16) * 0.7).convert("RGBA")
    draw_brand(out); draw_subs(t, out)
    if DUR - t < 0.6: out = Image.blend(Image.new("RGBA", (W, H), (0, 0, 0, 255)), out, clamp((DUR - t) / 0.6))
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
    if k % 250 == 0: print(k, flush=True)
enc.stdin.close(); enc.wait(); print("done", n)
