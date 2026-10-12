"""KoiPay case reel: 'Sahil, 20 — first bike'. Full-screen 9:16, photos + bike footage + neon overlays + TTS VO + music."""
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

# bike footage
def bike_frame(src_t):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{src_t:.3f}", "-i", A["bike"], "-frames:v", "1",
                          "-vf", "scale=1440:1920:flags=lanczos,crop=1080:1920,unsharp=5:5:0.6", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
                         capture_output=True).stdout
    return Image.frombuffer("RGB", (W, H), raw)
BIKE_CUTS = A["bike_cuts"]      # [[src_start, out_start, out_dur], ...]

# ---------- timeline ----------
T_A1 = LT[1][0]; T_B = LT[2][0] - 0.2; T_C = LT[3][0] - 0.15; T_D = LT[5][0] - 0.15; T_E = LT[6][0] - 0.15
T_F = LT[7][0] - 0.15; T_G = LT[8][0]; T_H = LT[9][0] - 0.2

def background(t, L):
    if t < T_B:                                    # A: Sahil on the bike, punch-in on "made online"
        if t < T_A1: z, fx, fy = 1.0 + 0.06 * t / T_A1, 420, 560
        else: z, fx, fy = 1.28 + 0.04 * (t - T_A1), 390, 470
        fr, _ = photo_frame("bike", z, fx, fy); return fr, True
    if t < T_C:                                    # B: the past (desaturated)
        k = (t - T_B) / (T_C - T_B); fr, (s, x0, y0) = photo_frame("friend", 1.05 + 0.08 * k, 560, 700, grade="past")
        # neon ring on Sahil (red shirt), photo coords ~ (540, 600)
        cx, cy = (540 - x0) * s, (575 - y0) * s; a = appear(t, T_B + 0.2)
        r = 170 * (1.15 - 0.15 * a)
        L.n.ellipse((cx - r, cy - r * 1.15, cx + r, cy + r * 1.15), outline=rgba(NEON, a), width=5)
        pill(L, cx, cy - r * 1.15 - 50, "Sahil", a, filled=True, fnt=SMALL, h=62, padx=26)
        return fr, True
    if t < T_D: return NEON_BG.copy(), False       # C: what KoiPay is
    if t < T_E:                                    # D: started small, at the PC
        k = (t - T_D) / (T_E - T_D); fr, _ = photo_frame("pc", 1.02 + 0.10 * k, 600, 760); return fr, True
    if t < T_G: return NEON_BG.copy(), False       # E + F: growth chart, MONTH 5
    if t < T_H:                                    # G: bike montage on the drop
        for src, at, d in BIKE_CUTS:
            if at <= t < at + d:
                fr = bike_frame(src + (t - at) * 0.85)
                z = 1.0 + 0.05 * (t - at) / d
                if z > 1: fr = fr.crop((int(W * (1 - 1 / z) / 2), int(H * (1 - 1 / z) / 2), int(W - W * (1 - 1 / z) / 2), int(H - H * (1 - 1 / z) / 2))).resize((W, H), Image.BICUBIC)
                return fr, True
        return bike_frame(BIKE_CUTS[-1][0]), True
    k = (t - T_H) / (DUR - T_H); fr, _ = photo_frame("bike", 1.12 - 0.08 * k, 430, 640); return fr, True

# ---------- overlays ----------
def overlays(t, L):
    if t < T_B:
        hide = 1 - appear(t, T_A1 - 0.12, 0.12)
        pill(L, 540, 230, "SAHIL · 20", hide * appear(t, cue("sahil", line=0) - 0.1), filled=True, fnt=TITLE, h=104, padx=44)
        pill(L, 540, 350, "Bangalore", hide * appear(t, cue("bangalore") - 0.1), fnt=PILL, h=76, icon=icon_pin)
        k = appear(t, cue("dream") - 0.05) * (1 - appear(t, T_A1 - 0.1, 0.15))
        pill(L, 540, 1060, "Dream bike ✓", k, fnt=PILL, h=80)
        pill(L, 540, 240, "Made online", appear(t, cue("online") - 0.15) if t >= T_A1 else 0, filled=True, fnt=TITLE, h=104, padx=44, icon=icon_phone)
    elif t < T_C:
        a = 1 - appear(t, T_C - 0.15, 0.15)
        card(L, (130, 150, 950, 470), a * appear(t, T_B + 0.1))
        k1 = a * appear(t, cue("rickshaw") - 0.2)
        icon_rickshaw(L.n, 260, 255, 120, k1); ctext(L.t, (350, 255), "Rickshaw driver", TITLE, WHITE, k1, "lm")
        k2 = a * appear(t, cue("saved") - 0.15)
        ctext(L.t, (190, 375), "Saving for years", LABEL, GREY, k2, "lm")
        prog = ease((t - cue("saved")) / 1.6)
        L.n.rounded_rectangle((540, 360, 890, 392), 16, outline=rgba(NEON, 0.6 * k2), width=3)
        if prog > 0 and k2 > 0: L.f.rounded_rectangle((544, 364, 544 + 342 * prog, 388), 12, fill=rgba(NEON, k2))
    elif t < T_D:
        a = 1 - appear(t, T_D - 0.15, 0.15)
        t4 = LT[4][0]
        sh = ease((t - t4) / 0.4)                                   # title moves up when the flow starts
        y = 760 - 520 * sh; fnt = HUGE if sh < 0.5 else BIG
        ctext(L.t, (540, y), "KoiPay", fnt, WHITE, a * appear(t, cue("koipay") - 0.1, 0.2))
        pill(L, 540, y + (120 if sh < 0.5 else 95), "P2P processing platform", a * appear(t, cue("koipay") + 0.2) * (1 - sh), fnt=PILL, h=78)
        if t >= t4:
            nodes = [("Business", icon_store, cue("businesses") - 0.1), ("UPI payment", icon_phone, cue("process") - 0.1),
                     ("Trader's bank account", icon_bank, cue("bank") - 0.1)]
            ys = [400, 610, 820]
            for i, (lab, ic, at) in enumerate(nodes):
                k = a * appear(t, at, 0.25)
                box = (190, ys[i] - 70, 890, ys[i] + 70)
                L.f.rounded_rectangle(box, 30, fill=rgba((8, 22, 13), k)); L.n.rounded_rectangle(box, 30, outline=rgba(NEON, k), width=3)
                ic(L.n, 285, ys[i], 82, k); ctext(L.t, (360, ys[i]), lab, PILL, WHITE, k, "lm")
                if i: arrow_v(L, 540, ys[i - 1] + 72, ys[i] - 72, ease((t - at + 0.1) / 0.3), a, t)
            k = a * appear(t, cue("commission") - 0.1)
            if k > 0:
                arrow_v(L, 540, ys[2] + 72, 1000, ease((t - cue("commission") + 0.1) / 0.3), a, t)
                pill(L, 540, 1065, "+ commission", k, filled=True, fnt=TITLE, h=110, padx=48, icon=icon_coin)
    elif t < T_E:
        pill(L, 540, 230, "Test deposit", appear(t, cue("test") - 0.15), filled=True, fnt=TITLE, h=104, padx=44, icon=icon_coin)
        pill(L, 540, 355, "Still driving", appear(t, cue("driving") - 0.15), fnt=PILL, h=80, icon=icon_rickshaw)
    elif t < T_F:
        a = 1 - appear(t, T_F - 0.12, 0.12)
        card(L, (90, 250, 990, 1120), a * appear(t, T_E))
        ctext(L.t, (540, 335), "Sahil's earnings", TITLE, WHITE, a * appear(t, T_E + 0.1))
        base, top = 1000, 520; avg_y = 740
        xs = [230 + i * 155 for i in range(5)]
        hts = [0.18, 0.32, 0.52, 0.68, 0.86]
        t_pass, t_dep = cue("passed"), cue("grew")
        for i, x in enumerate(xs):
            g = ease((t - (T_E + 0.25 + 0.35 * i)) / 0.5)
            hh = (base - top) * hts[i] * g
            if i >= 3: hh *= 1 + 0.12 * ease((t - t_dep) / 0.5)
            on = (base - hh) < avg_y
            L.f.rounded_rectangle((x - 46, base - hh, x + 46, base), 14, fill=rgba(NEON if on else NEON_DARK, a * (0.95 if on else 0.8)))
            L.n.rounded_rectangle((x - 46, base - hh, x + 46, base), 14, outline=rgba(NEON, a * 0.8 * min(1, g * 3)), width=2)
            ctext(L.t, (x, base + 45), f"M{i + 1}", SMALL, GREY, a * appear(t, T_E + 0.2))
        ka = a * appear(t, t_pass - 0.6)
        for x in range(130, 960, 34): L.n.line([(x, avg_y), (x + 18, avg_y)], fill=rgba(WHITE, 0.75 * ka), width=3)
        ctext(L.t, (130, avg_y - 34), "India avg. salary", SMALL, WHITE, ka, "lm")
        pill(L, 770, 425, "Deposit ↑", a * appear(t, t_dep - 0.1), filled=True, fnt=PILL, h=78)
    elif t < T_G:
        k = appear(t, T_F, 0.2); n = min(5, 1 + int(clamp((t - T_F) / 0.7) * 4.999))
        ctext(L.t, (540, 640), "MONTH", TITLE, GREY, k)
        ctext(L.t, (540, 820), str(n), font("Black", 300), NEON, k)
    elif t < T_H:
        k = appear(t, T_G, 0.08) * (1 - appear(t, T_G + 0.9, 0.25))
        if k > 0: L.t.text((540, 330), "HE BOUGHT IT.", font=BIG, fill=rgba(WHITE, k), anchor="mm", stroke_width=7, stroke_fill=(0, 0, 0, int(200 * k)))
        f = 1 - clamp((t - T_G) / 0.25)                             # flash on the drop
        if f > 0: L.fill.alpha_composite(Image.new("RGBA", (W, H), rgba((210, 255, 225), 0.85 * f)))
        for x0, y0, sx, sy in ((60, 60, 1, 1), (W - 60, 60, -1, 1), (60, H - 60, 1, -1), (W - 60, H - 60, -1, -1)):   # neon corners
            L.n.line([(x0, y0), (x0 + 120 * sx, y0)], fill=rgba(NEON, 0.9), width=6); L.n.line([(x0, y0), (x0, y0 + 120 * sy)], fill=rgba(NEON, 0.9), width=6)
    else:
        k1 = appear(t, T_H + 0.1)
        card(L, (110, 860, 970, 1170), k1)
        icon_chat(L.n, 540, 935, 90, k1)
        ctext(L.t, (540, 1015), "Want Sahil's path?", LABEL, GREY, k1)
        pill(L, 540, 1100, "Message our manager", appear(t, cue("message") - 0.1), filled=True, fnt=TITLE, h=104, padx=44)
        pill(L, 540, 230, "Link in bio", appear(t, cue("link") - 0.1), filled=True, fnt=BIG, h=150, padx=60)

# ---------- subtitles ----------
GREEN = {"sahil", "bangalore", "dream", "bike", "online", "rickshaw", "years", "koipay", "upi", "commission", "bank",
         "small", "test", "deposit", "driving", "average", "salary", "five", "months", "manager", "bio", "20-year-old", "bought"}
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
    if not cur or T_G <= t < T_H: return img
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
