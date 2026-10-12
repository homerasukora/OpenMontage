"""KoiPay case reel: 'Ravi from Delhi'. Full-screen 9:16, photos + bike footage + neon overlays + TTS VO + music."""
import json, math, subprocess, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageEnhance

A = json.load(open(sys.argv[1]))          # assets/config json
OUT = sys.argv[2]
PREVIEW = [float(x) for x in sys.argv[3].split(",")] if len(sys.argv) > 3 else None

W, H, FPS = 1080, 1920, 25
NEON, NEON_DARK, WHITE, GREY = (46, 232, 122), (10, 88, 38), (250, 255, 251), (160, 178, 166)
F = "/usr/share/fonts/opentype/inter/"
def font(style, size): return ImageFont.truetype(F + f"InterDisplay-{style}.otf", size)
SUB = font("Black", 80); HUGE = font("Black", 150); BIG = font("Black", 104); TITLE = font("ExtraBold", 66)
PILL = font("Bold", 44); LABEL = font("SemiBold", 40); SMALL = font("SemiBold", 34)

VO = json.load(open(A["vo_json"])); LT = VO["lines"]; DUR = VO["dur"]
WORDS = json.load(open(A["words"]))       # [{w, s, e}] display words with times

def clamp(x, a=0.0, b=1.0): return max(a, min(b, x))
def ease(x): x = clamp(x); return 1 - (1 - x) ** 3
def appear(t, at, d=0.3): return ease((t - at) / d)
def rgba(c, a): return (*c, int(255 * clamp(a)))
def cue(word, n=0, line=None):
    hits = [w for w in WORDS if w["w"].lower().strip(".,?!").startswith(word.lower()) and (line is None or w["line"] == line)]
    return hits[n]["s"]

# ---------- drawing helpers (overlay layers are full-canvas RGBA) ----------
class Layers:
    def __init__(self):
        self.fill = Image.new("RGBA", (W, H), (0, 0, 0, 0)); self.neon = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        self.text = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        self.f, self.n, self.t = ImageDraw.Draw(self.fill), ImageDraw.Draw(self.neon), ImageDraw.Draw(self.text)

def card(L, box, a, r=36):
    L.f.rounded_rectangle(box, r, fill=(6, 16, 10, int(215 * a)))
    L.n.rounded_rectangle(box, r, outline=rgba(NEON, 0.9 * a), width=3)

def ctext(d, xy, s, fnt, col, a, anchor="mm"):
    if a > 0: d.text(xy, s, font=fnt, fill=rgba(col, a), anchor=anchor)

def pill(L, cx, cy, s, a, filled=False, fnt=PILL, padx=36, h=80, icon=None):
    if a <= 0: return
    iw = h * 0.7 if icon else 0
    tw = L.t.textlength(s, font=fnt) + iw
    box = (cx - tw / 2 - padx, cy - h / 2, cx + tw / 2 + padx, cy + h / 2)
    L.f.rounded_rectangle(box, h // 2, fill=rgba(NEON_DARK, 0.95 * a) if filled else (6, 18, 10, int(210 * a)))
    L.n.rounded_rectangle(box, h // 2, outline=rgba(NEON, a), width=3)
    if icon: icon(L.n, box[0] + padx + iw * 0.4, cy, h * 0.55, a)
    ctext(L.t, (cx + iw / 2, cy + 1), s, fnt, WHITE, a)

def arrow_v(L, x, y0, y1, prog, a, t):
    if prog <= 0: return
    ye = y0 + (y1 - y0) * prog
    L.n.line([(x, y0), (x, ye)], fill=rgba(NEON, 0.5 * a), width=4)
    if prog >= 1:
        L.n.line([(x, y1), (x - 16, y1 - 18)], fill=rgba(NEON, a), width=5); L.n.line([(x, y1), (x + 16, y1 - 18)], fill=rgba(NEON, a), width=5)
        for k in range(2):
            f = (t * 1.1 + k / 2) % 1.0; py = y0 + (y1 - y0) * f
            L.n.ellipse((x - 7, py - 7, x + 7, py + 7), fill=rgba(NEON, a))

# icons
def icon_pin(d, cx, cy, s, a):
    r = 0.3 * s
    d.ellipse((cx - r, cy - 0.5 * s, cx + r, cy - 0.5 * s + 2 * r), outline=rgba(NEON, a), width=4)
    d.polygon([(cx - r * 0.8, cy - 0.05 * s), (cx + r * 0.8, cy - 0.05 * s), (cx, cy + 0.5 * s)], fill=rgba(NEON, a))
    d.ellipse((cx - r * 0.35, cy - 0.5 * s + r * 0.65, cx + r * 0.35, cy - 0.5 * s + r * 1.35), fill=rgba(NEON, a))
def icon_phone(d, cx, cy, s, a):
    w, h = 0.6 * s, s
    d.rounded_rectangle((cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2), int(s * 0.12), outline=rgba(NEON, a), width=4)
    d.line([(cx - 0.1 * s, cy + h / 2 - 0.12 * s), (cx + 0.1 * s, cy + h / 2 - 0.12 * s)], fill=rgba(NEON, a), width=4)
def icon_bank(d, cx, cy, s, a):
    top, base = cy - 0.5 * s, cy + 0.5 * s
    d.polygon([(cx - 0.55 * s, top + 0.3 * s), (cx, top), (cx + 0.55 * s, top + 0.3 * s)], outline=rgba(NEON, a), width=5)
    for i in range(4):
        x = cx - 0.36 * s + i * 0.24 * s; d.line([(x, top + 0.42 * s), (x, base - 0.12 * s)], fill=rgba(NEON, a), width=5)
    d.line([(cx - 0.55 * s, base), (cx + 0.55 * s, base)], fill=rgba(NEON, a), width=6)
def icon_store(d, cx, cy, s, a):
    d.line([(cx - 0.5 * s, cy - 0.1 * s), (cx - 0.38 * s, cy - 0.42 * s), (cx + 0.38 * s, cy - 0.42 * s), (cx + 0.5 * s, cy - 0.1 * s), (cx - 0.5 * s, cy - 0.1 * s)], fill=rgba(NEON, a), width=5)
    d.rectangle((cx - 0.42 * s, cy - 0.1 * s, cx + 0.42 * s, cy + 0.45 * s), outline=rgba(NEON, a), width=5)
    d.rectangle((cx - 0.12 * s, cy + 0.12 * s, cx + 0.12 * s, cy + 0.45 * s), outline=rgba(NEON, a), width=4)
def icon_coin(d, cx, cy, s, a):
    r = 0.45 * s
    d.ellipse((cx - r, cy - r, cx + r, cy + r), outline=rgba(NEON, a), width=5)
    f = font("Black", int(s * 0.62)); d.text((cx, cy + 2), "₹", font=f, fill=rgba(NEON, a), anchor="mm")
def icon_rickshaw(d, cx, cy, s, a):
    """Auto-rickshaw side view, line art."""
    c = rgba(NEON, a); w = 5
    d.line([(cx - 0.5 * s, cy + 0.15 * s), (cx - 0.5 * s, cy - 0.25 * s), (cx - 0.3 * s, cy - 0.45 * s),
            (cx + 0.2 * s, cy - 0.45 * s), (cx + 0.38 * s, cy - 0.1 * s), (cx + 0.55 * s, cy + 0.15 * s)], fill=c, width=w, joint="curve")
    d.line([(cx - 0.5 * s, cy + 0.15 * s), (cx + 0.55 * s, cy + 0.15 * s)], fill=c, width=w)
    d.line([(cx - 0.05 * s, cy - 0.45 * s), (cx - 0.05 * s, cy + 0.15 * s)], fill=c, width=4)
    for x in (cx - 0.3 * s, cx + 0.38 * s):
        r = 0.15 * s; d.ellipse((x - r, cy + 0.15 * s - r * 0.2, x + r, cy + 0.15 * s + r * 1.8), outline=c, width=w)
def icon_chat(d, cx, cy, s, a):
    d.rounded_rectangle((cx - 0.5 * s, cy - 0.38 * s, cx + 0.5 * s, cy + 0.22 * s), int(0.16 * s), outline=rgba(NEON, a), width=5)
    d.line([(cx - 0.2 * s, cy + 0.22 * s), (cx - 0.3 * s, cy + 0.45 * s), (cx + 0.02 * s, cy + 0.22 * s)], fill=rgba(NEON, a), width=5)
    for k in (-1, 0, 1):
        x = cx + k * 0.22 * s; d.ellipse((x - 6, cy - 0.08 * s - 6, x + 6, cy - 0.08 * s + 6), fill=rgba(NEON, a))

# ---------- backgrounds ----------
PHOTOS = {k: Image.open(v).convert("RGB") for k, v in A["photos"].items()}

def photo_frame(name, z, fx, fy, grade=None):
    im = PHOTOS[name]; pw, ph = im.size
    s = max(W / pw, H / ph) * z
    cw, ch = W / s, H / ph * ph / s
    x0 = clamp(fx - cw / 2, 0, pw - cw); y0 = clamp(fy - ch / 2, 0, ph - ch)
    fr = im.crop((int(x0), int(y0), int(x0 + cw), int(y0 + ch))).resize((W, H), Image.BICUBIC)
    if grade == "past":
        fr = ImageEnhance.Color(fr).enhance(0.25); fr = ImageEnhance.Brightness(fr).enhance(0.55)
    return fr, (s, x0, y0)

def neon_bg():
    bg = Image.new("RGB", (W, H), (2, 5, 3)); g = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(g)
    hz = 1250
    for i in range(-16, 17): d.line([(W / 2 + i * 40, hz), (W / 2 + i * 300, H + 60)], fill=(46, 232, 122, 30), width=1)
    y, step = hz, 8
    while y < H: d.line([(0, y), (W, y)], fill=(46, 232, 122, int(16 + 34 * (y - hz) / (H - hz))), width=1); step *= 1.3; y += step
    rng = np.random.default_rng(11)
    for _ in range(22):
        x = int(rng.uniform(20, W - 20)); top = int(rng.uniform(60, 1100)); bot = int(rng.uniform(top + 150, H))
        d.line([(x, top), (x, bot)], fill=(46, 232, 122, 55), width=2); d.ellipse((x - 4, top - 4, x + 4, top + 4), fill=(140, 255, 180, 200))
    gl = g.filter(ImageFilter.GaussianBlur(6)); bg.paste(gl, (0, 0), gl); bg.paste(g, (0, 0), g)
    arr = np.asarray(bg).astype(np.float32)
    yy, xx = np.mgrid[0:H, 0:W]; glow = np.exp(-(((xx - W / 2) / 700) ** 2 + ((yy - 700) / 700) ** 2)) * 0.10
    arr += glow[..., None] * np.array(NEON, np.float32)
    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))
NEON_BG = neon_bg()

# gradient for text legibility over photos
GRAD = np.ones((H, 1, 1), np.float32)
GRAD[:420, 0, 0] = np.linspace(0.45, 1, 420); GRAD[1150:, 0, 0] = np.linspace(1, 0.35, H - 1150)

# footage (cover-fit to 9:16)
def video_frame(path, src_t, zoom=1.0):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{src_t:.3f}", "-i", path, "-frames:v", "1",
                          "-vf", "scale=1080:1920:force_original_aspect_ratio=increase:flags=lanczos,crop=1080:1920",
                          "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True).stdout
    fr = Image.frombuffer("RGB", (W, H), raw)
    if zoom > 1:
        dx, dy = W * (1 - 1 / zoom) / 2, H * (1 - 1 / zoom) / 2
        fr = fr.crop((int(dx), int(dy), int(W - dx), int(H - dy))).resize((W, H), Image.BICUBIC)
    return fr

DASH = Image.open(A["dash"]).convert("RGB")

def phone(L, img, x, y, w, scroll, a):
    """Phone mockup with neon edge; screen shows `img` scrolled by `scroll` (0..1)."""
    if a <= 0: return
    sw = w - 28; scale = sw / DASH.width; sh = int(sw * 2.05)
    full = DASH.resize((sw, int(DASH.height * scale)), Image.BICUBIC)
    off = int((full.height - sh) * clamp(scroll)) if full.height > sh else 0
    scr = full.crop((0, off, sw, off + sh)) if full.height > sh else full
    h = scr.height + 28
    L.f.rounded_rectangle((x, y, x + w, y + h), 44, fill=(4, 8, 6, int(255 * a)))
    m = Image.new("L", scr.size, 0); ImageDraw.Draw(m).rounded_rectangle((0, 0, scr.width, scr.height), 32, fill=int(255 * a))
    L.fill.paste(scr, (x + 14, y + 14), m)
    L.n.rounded_rectangle((x, y, x + w, y + h), 44, outline=rgba(NEON, a), width=4)

def icon_sun(d, cx, cy, s, a):
    r = 0.22 * s; d.ellipse((cx - r, cy - r, cx + r, cy + r), outline=rgba(NEON, a), width=4)
    for k in range(8):
        an = k * math.pi / 4; d.line([(cx + math.cos(an) * 0.32 * s, cy + math.sin(an) * 0.32 * s), (cx + math.cos(an) * 0.46 * s, cy + math.sin(an) * 0.46 * s)], fill=rgba(NEON, a), width=4)
def icon_moon(d, cx, cy, s, a):
    r = 0.4 * s; d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=rgba(NEON, a))
    d.ellipse((cx - r + 0.28 * s, cy - r - 0.1 * s, cx + r + 0.28 * s, cy + r - 0.1 * s), fill=(6, 18, 10, int(255 * a)))
def icon_up(d, cx, cy, s, a):
    pts = [(cx - 0.45 * s, cy + 0.3 * s), (cx - 0.1 * s, cy - 0.05 * s), (cx + 0.1 * s, cy + 0.12 * s), (cx + 0.45 * s, cy - 0.3 * s)]
    d.line(pts, fill=rgba(NEON, a), width=5, joint="curve")
    d.line([(cx + 0.45 * s, cy - 0.3 * s), (cx + 0.22 * s, cy - 0.3 * s)], fill=rgba(NEON, a), width=5); d.line([(cx + 0.45 * s, cy - 0.3 * s), (cx + 0.45 * s, cy - 0.08 * s)], fill=rgba(NEON, a), width=5)

# ---------- timeline ----------
T_FR = LT[2][0] - 0.15; T2 = LT[3][0] - 0.12; T3 = LT[4][0] - 0.05; T3b = cue("upi") - 0.25
T5 = LT[6][0] - 0.15; T6 = LT[7][0]; T7 = LT[8][0] - 0.15; T8 = LT[9][0] - 0.15
T_NR = LT[1][0] - 0.05

def map_pt(px, py, tr): s, x0, y0 = tr; return (px - x0) * s, (py - y0) * s
RAVI_G = (540, 690)                         # Ravi's face in the group photo (centre, red T-shirt)

def background(t, L):
    if t < T_FR:
        if t < T_NR: fr, _ = photo_frame("rick", 1.0 + 0.07 * t / T_NR, 540, 660)
        else: fr, _ = photo_frame("rick", 1.30 + 0.05 * (t - T_NR), 545, 560)       # punch-in on "but not from rides"
        return fr, True
    if t < T2:
        k = (t - T_FR) / (T2 - T_FR); fr, tr = photo_frame("group", 1.12 + 0.10 * k, 540, 820)
        cx, cy = map_pt(*RAVI_G, tr); a = appear(t, T_FR + 0.15)
        r = 120 * (1.2 - 0.2 * a) * tr[0] / 1.5
        L.n.ellipse((cx - r, cy - r * 1.2, cx + r, cy + r * 1.2), outline=rgba(NEON, a), width=6)
        pill(L, cx, cy - r * 1.2 - 60, "Ravi", appear(t, cue("ravi", line=2) - 0.1), filled=True, fnt=PILL, h=76, padx=30)
        return fr, True
    if t < T3: return video_frame(A["rk2"], 2.5 + (t - T2)), True
    if t < T3b: return video_frame(A["rk1"], 1.5 + (t - T3), 1.0 + 0.04 * (t - T3)), True
    if t < T5: return NEON_BG.copy(), False
    if t < T6:
        k = (t - T5) / (T6 - T5); fr, _ = photo_frame("rick", 1.25 + 0.08 * k, 545, 620); return fr, True
    if t < T7:
        # wide shot (face + computer), then smooth zoom into the earnings on "earned"
        te = cue("earned"); zk = ease((t - te + 0.1) / 0.8)
        z = 1.0 + 0.04 * clamp((t - T6) / 1.5) + 1.45 * zk
        fx, fy = 480 + (670 - 480) * zk, 700 + (650 - 700) * zk
        fr, tr = photo_frame("selfie", z, fx, fy)
        x0, y0 = map_pt(585, 652, tr); x1, y1 = map_pt(760, 705, tr)
        L.n.rounded_rectangle((x0 - 16, y0 - 16, x1 + 16, y1 + 16), 20, outline=rgba(NEON, appear(t, te + 0.7)), width=7)
        return fr, True
    if t < T8:
        return NEON_BG.copy(), False
    k = (t - T8) / (DUR - T8); fr, _ = photo_frame("selfie", 1.08 - 0.05 * k, 470, 700); return fr, True

def overlays(t, L):
    if t < T_FR:
        at = cue("₹14,000"); k = appear(t, at - 0.15, 0.2)
        n = int(14000 * ease((t - at + 0.15) / 0.9)); txt = (f"₹{n // 1000},{n % 1000:03d}" if n >= 1000 else f"₹{n}") + ("+" if n >= 14000 else "")
        if k > 0: L.t.text((540, 280), txt, font=HUGE, fill=rgba(NEON, k), anchor="mm", stroke_width=8, stroke_fill=(0, 0, 0, int(190 * k)))
        pill(L, 540, 420, "last week", appear(t, cue("last") - 0.1) * (1 - appear(t, T_NR - 0.1, 0.12)), fnt=PILL, h=78)
        kn = appear(t, cue("not") - 0.1, 0.15)
        if kn > 0:
            pill(L, 540, 420, "Not from rides", kn, filled=True, fnt=TITLE, h=104, padx=48)
    elif t < T2:
        pill(L, 540, 230, "Delhi", appear(t, cue("delhi") - 0.1), filled=True, fnt=TITLE, h=96, padx=40, icon=icon_pin)
    elif t < T3:
        pill(L, 540, 240, "Morning · rickshaw", appear(t, T2 + 0.1), filled=True, fnt=TITLE, h=104, padx=44, icon=icon_sun)
    elif t < T3b:
        pill(L, 540, 240, "Evening · KoiPay", appear(t, T3 + 0.05), filled=True, fnt=TITLE, h=104, padx=44, icon=icon_moon)
    elif t < T5:
        a = 1 - appear(t, T5 - 0.15, 0.15)
        phone(L, DASH, 55, 300, 470, (t - T3b) / (T5 - T3b), a * appear(t, T3b, 0.3))
        rows = [("UPI payments", icon_phone, cue("upi") - 0.05), ("Peak traffic", icon_up, cue("peaks") - 0.15),
                ("His bank account", icon_bank, cue("bank") - 0.15)]
        ys = [400, 600, 800]
        for i, (lab, ic, at) in enumerate(rows):
            k = a * appear(t, at, 0.25); xo = 30 * (1 - appear(t, at, 0.25))
            box = (560 + xo, ys[i] - 70, 1035 + xo, ys[i] + 70)
            L.f.rounded_rectangle(box, 28, fill=rgba((8, 22, 13), k)); L.n.rounded_rectangle(box, 28, outline=rgba(NEON, k), width=3)
            ic(L.n, 625 + xo, ys[i], 70, k); ctext(L.t, (680 + xo, ys[i]), lab, LABEL, WHITE, k, "lm")
        k = a * appear(t, cue("commission") - 0.1)
        pill(L, 797, 1000, "+ commission", k, filled=True, fnt=PILL, h=96, padx=30, icon=icon_coin)
    elif t < T6:
        pill(L, 540, 240, "Started with $500", appear(t, cue("$500") - 0.15), filled=True, fnt=TITLE, h=104, padx=44, icon=icon_coin)
        pill(L, 540, 360, "saved from driving", appear(t, cue("saved") - 0.1), fnt=PILL, h=78, icon=icon_rickshaw)
    elif t < T7:
        pill(L, 540, 240, "WEEK 1", appear(t, cue("first", line=7) - 0.1, 0.2), filled=True, fnt=BIG, h=140, padx=56)
        pill(L, 540, 385, "Earned: ₹14,312", appear(t, cue("earned") + 0.6), fnt=TITLE, h=100, padx=44)
    elif t < T8:
        a = 1 - appear(t, T8 - 0.12, 0.12)
        card(L, (110, 300, 970, 1120), a * appear(t, T7))
        ctext(L.t, (540, 390), "Ravi's plan", TITLE, WHITE, a * appear(t, T7 + 0.05))
        nodes = [("Now", "Rickshaw + Koi", T7 + 0.15), ("Next", "Grow the deposit", cue("grow") - 0.1), ("Goal", "Koi full-time", cue("full-time") - 0.15)]
        ys = [540, 740, 940]
        for i, (tag, lab, at) in enumerate(nodes):
            k = a * appear(t, at, 0.25); on = i == 2
            box = (180, ys[i] - 64, 900, ys[i] + 64)
            L.f.rounded_rectangle(box, 30, fill=rgba(NEON_DARK if on else (8, 22, 13), k)); L.n.rounded_rectangle(box, 30, outline=rgba(NEON, k), width=3)
            ctext(L.t, (230, ys[i]), tag, SMALL, NEON if not on else WHITE, k, "lm"); ctext(L.t, (370, ys[i]), lab, PILL, WHITE, k, "lm")
            if i: arrow_v(L, 540, ys[i - 1] + 66, ys[i] - 66, ease((t - at + 0.1) / 0.3), a, t)
    else:
        k1 = appear(t, T8 + 0.1)
        card(L, (110, 900, 970, 1170), k1)
        icon_chat(L.n, 540, 965, 80, k1)
        ctext(L.t, (540, 1035), "Combine your work with KoiPay", LABEL, GREY, k1)
        pill(L, 540, 1110, "Message our manager", appear(t, cue("message") - 0.1), filled=True, fnt=TITLE, h=100, padx=44)
        pill(L, 540, 240, "Link in bio", appear(t, cue("link") - 0.1), filled=True, fnt=BIG, h=150, padx=60)

# ---------- subtitles ----------
GREEN = {"ravi", "delhi", "rickshaw", "₹14,000", "rides", "week", "online", "mornings", "evenings", "upi", "koipay", "peaks", "bank", "commission", "$500", "driving", "first", "month", "deposit", "full-time", "manager", "bio", "week", "combine", "work", "koipay"}
chunks, cur = [], []
for w in WORDS:
    cur.append(w)
    if w["w"][-1] in ".,?!" or len(cur) == 3 or len(" ".join(x["w"] for x in cur)) >= 13: chunks.append(cur); cur = []
if cur: chunks.append(cur)
SUBS = []
for i, ch in enumerate(chunks):
    s = ch[0]["s"]; e = min(chunks[i + 1][0]["s"] if i + 1 < len(chunks) else DUR, ch[-1]["e"] + 0.4)
    SUBS.append((s, e, [(x["w"].rstrip(".,!"), x["w"].lower().strip(".,?!") in GREEN) for x in ch]))
SUB_Y = 1320

def draw_subs(t, img):
    cur = [s for s in SUBS if s[0] <= t < s[1]]
    if not cur: return img
    s, e, toks = cur[-1]; k = appear(t, s, 0.1); sc = 0.92 + 0.08 * k
    f = SUB if sc > 0.99 else font("Black", int(80 * sc))
    widths = [f.getlength(tx + (" " if i < len(toks) - 1 else "")) for i, (tx, g) in enumerate(toks)]
    x = (W - sum(widths)) / 2
    lay = Image.new("RGBA", (W, 260), (0, 0, 0, 0)); sh = Image.new("RGBA", (W, 260), (0, 0, 0, 0))
    d, sd = ImageDraw.Draw(lay), ImageDraw.Draw(sh)
    for (tx, g), wd in zip(toks, widths):
        sd.text((x, 134), tx, font=f, fill=(0, 0, 0, int(240 * k)), anchor="lm", stroke_width=6, stroke_fill=(0, 0, 0, int(240 * k)))
        d.text((x, 130), tx, font=f, fill=rgba(NEON if g else WHITE, k), anchor="lm", stroke_width=3, stroke_fill=(0, 0, 0, int(200 * k)))
        x += wd
    sh = sh.filter(ImageFilter.GaussianBlur(9))
    img.alpha_composite(sh, (0, SUB_Y - 130)); img.alpha_composite(lay, (0, SUB_Y - 130))
    return img

def compose(t):
    L = Layers()
    bg, is_photo = background(t, L)
    if is_photo:
        arr = (np.asarray(bg).astype(np.float32) * GRAD).astype(np.uint8); bg = Image.fromarray(arr)
    overlays(t, L)
    img = bg.convert("RGBA")
    img = Image.alpha_composite(img, L.fill)
    glow = L.neon.resize((W // 2, H // 2), Image.BILINEAR).filter(ImageFilter.GaussianBlur(9)).resize((W, H), Image.BILINEAR)
    img = Image.alpha_composite(Image.alpha_composite(img, glow), glow)
    img = Image.alpha_composite(img, L.neon); img = Image.alpha_composite(img, L.text)
    img = draw_subs(t, img)
    return img.convert("RGB")

if PREVIEW:
    for t in PREVIEW: compose(t).save(f"{OUT}/prev_{t:05.2f}.jpg", quality=88)
    sys.exit()

enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                        "-i", A["mix"], "-map", "0:v", "-map", "1:a", "-c:v", "libx264", "-preset", "slow", "-crf", "17", "-pix_fmt", "yuv420p",
                        "-movflags", "+faststart", "-c:a", "aac", "-b:a", "192k", "-shortest", OUT], stdin=subprocess.PIPE)
n = int(DUR * FPS)
for i in range(n):
    enc.stdin.write(compose(i / FPS).tobytes())
    if i % 100 == 0: print(i, flush=True)
enc.stdin.close(); enc.wait(); print("done", n)
