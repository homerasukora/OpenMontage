"""KoiPay 9:16 reel renderer: speaker on top, neon infographic panel below, subtitles on the seam."""
import json, math, subprocess, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

from edit2 import SEGS

BASE, WORDS, OUT = sys.argv[1], sys.argv[2], sys.argv[3]
PREVIEW = [float(x) for x in sys.argv[4].split(",")] if len(sys.argv) > 4 else None

W, H, FPS = 1080, 1920, 25
SEAM = 1080                      # speaker zone 0..SEAM, panel SEAM..H
PH = H - SEAM
NEON = (46, 232, 122)
NEON_DARK = (10, 88, 38)
WHITE = (250, 255, 251)
GREY = (150, 170, 158)

F = "/usr/share/fonts/opentype/inter/"
def font(style, size): return ImageFont.truetype(F + f"InterDisplay-{style}.otf", size)
SUB_FONT = font("Black", 84)
TITLE = font("ExtraBold", 64)
BIG = font("Black", 92)
LABEL = font("SemiBold", 38)
PILL = font("Bold", 40)
SMALL = font("SemiBold", 32)

# ---------- timeline ----------
words_by_clip = {int(k): v for k, v in json.load(open(WORDS)).items()}
FIX = {"Koipe": "KoiPay", "pay-in": "PayIn", "payout": "PayOut", "traders": "trader's"}
words, segs_out, t0 = [], [], 0.0
for c, a, b in SEGS:
    segs_out.append((t0, t0 + b - a, c))
    cw = words_by_clip[c]
    for i, w in enumerate(cw):
        if a - 0.12 <= w["s"] < b - 0.05:
            end = min(cw[i + 1]["s"] if i + 1 < len(cw) else b, b)
            text = w["w"]
            core = text.rstrip(".,?")
            if c == 0 and core == "traders": text = "trader's" + text[len(core):]
            elif core in FIX and core != "traders": text = FIX[core] + text[len(core):]
            words.append(dict(w=text, s=t0 + max(w["s"], a) - a, e=t0 + end - a, c=c))
    t0 += b - a
DUR = t0
# "Koi" + "Pay" -> "KoiPay"
for i in range(len(words) - 2, -1, -1):
    if words[i]["w"] == "Koi" and words[i + 1]["w"].startswith("Pay"):
        words[i]["w"] = "Koi" + words[i + 1]["w"]; words[i]["e"] = words[i + 1]["e"]; del words[i + 1]

def cue(clip, word, n=0):
    hits = [w for w in words if w["c"] == clip and w["w"].lower().strip(".,?").startswith(word.lower())]
    return hits[n]["s"]

def clip_span(clip):
    s = [x for x in segs_out if x[2] == clip]
    return s[0][0], s[-1][1]

# ---------- subtitles: 1–3 word chunks ----------
GREEN = {"bank", "blocked", "p2p", "unverified", "sources", "patterns", "normal", "activity", "platform",
         "matters", "koipay", "verified", "merchants", "checked", "traffic", "limits", "risk", "manager", "security", "security?", "processing"}
chunks, cur = [], []
for w in words:
    cur.append(w)
    txt = " ".join(x["w"] for x in cur)
    if w["w"][-1] in ".,?" or len(cur) == 3 or len(txt) >= 13:
        chunks.append(cur); cur = []
if cur: chunks.append(cur)
subs = []
for i, ch in enumerate(chunks):
    s = ch[0]["s"]
    e = chunks[i + 1][0]["s"] if i + 1 < len(chunks) else DUR
    e = min(e, ch[-1]["e"] + 0.35)
    toks = []
    for x in ch:
        t = x["w"].rstrip(".,")
        toks.append((t, t.lower().strip("?") in GREEN))
    # "KoiPay bot" -> keep both green
    subs.append((s, e, toks))

# ---------- easing / helpers ----------
def clamp(x, a=0.0, b=1.0): return max(a, min(b, x))
def ease(x): x = clamp(x); return 1 - (1 - x) ** 3
def appear(t, at, d=0.3): return ease((t - at) / d)
def rgba(c, a): return (*c, int(255 * clamp(a)))

class Layers:
    def __init__(self):
        self.fill = Image.new("RGBA", (W, PH), (0, 0, 0, 0))
        self.neon = Image.new("RGBA", (W, PH), (0, 0, 0, 0))
        self.text = Image.new("RGBA", (W, PH), (0, 0, 0, 0))
        self.f, self.n, self.t = ImageDraw.Draw(self.fill), ImageDraw.Draw(self.neon), ImageDraw.Draw(self.text)

def card(L, box, a, r=34):
    L.f.rounded_rectangle(box, r, fill=(8, 18, 11, int(225 * a)))
    L.n.rounded_rectangle(box, r, outline=rgba(NEON, 0.9 * a), width=3)

def ctext(d, xy, s, fnt, col, a, anchor="mm"):
    d.text(xy, s, font=fnt, fill=rgba(col, a), anchor=anchor)

def pill(L, cx, cy, s, a, filled=False, fnt=PILL, padx=34, h=70, check=False):
    tw = L.t.textlength(s, font=fnt) + (46 if check else 0)
    box = (cx - tw / 2 - padx, cy - h / 2, cx + tw / 2 + padx, cy + h / 2)
    if filled: L.f.rounded_rectangle(box, h // 2, fill=rgba(NEON_DARK, 0.95 * a))
    else: L.f.rounded_rectangle(box, h // 2, fill=(6, 20, 10, int(200 * a)))
    L.n.rounded_rectangle(box, h // 2, outline=rgba(NEON, a), width=3)
    x = cx + (23 if check else 0)
    if check:
        cx0 = box[0] + padx + 14
        L.n.line([(cx0 - 12, cy), (cx0 - 3, cy + 10), (cx0 + 14, cy - 11)], fill=rgba(NEON, a), width=5, joint="curve")
    ctext(L.t, (x, cy + 1), s, fnt, WHITE, a)
    return box

def arrow(L, p0, p1, prog, a, t, dots=True):
    if prog <= 0: return
    x0, y0 = p0; x1, y1 = p1
    xe, ye = x0 + (x1 - x0) * prog, y0 + (y1 - y0) * prog
    L.n.line([(x0, y0), (xe, ye)], fill=rgba(NEON, 0.55 * a), width=4)
    if prog >= 1:
        ang = math.atan2(y1 - y0, x1 - x0)
        for s in (-1, 1):
            L.n.line([(x1, y1), (x1 - 20 * math.cos(ang + s * 0.5), y1 - 20 * math.sin(ang + s * 0.5))], fill=rgba(NEON, a), width=5)
        if dots:
            for k in range(3):
                f = ((t * 0.9 + k / 3) % 1.0)
                px, py = x0 + (x1 - x0) * f, y0 + (y1 - y0) * f
                L.n.ellipse((px - 7, py - 7, px + 7, py + 7), fill=rgba(NEON, a))

# ---------- icons (line art, drawn on neon layer) ----------
def icon_phone(d, cx, cy, s, a, ok=0.0):
    w, h = 0.62 * s, s
    d.rounded_rectangle((cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2), int(s * 0.12), outline=rgba(NEON, a), width=5)
    d.line([(cx - 0.12 * s, cy - h / 2 + 0.09 * s), (cx + 0.12 * s, cy - h / 2 + 0.09 * s)], fill=rgba(NEON, a), width=4)
    r = 0.17 * s
    d.ellipse((cx - r, cy - r, cx + r, cy + r), outline=rgba(NEON, a), width=4)
    if ok > 0:
        d.line([(cx - r * 0.5, cy), (cx - r * 0.1, cy + r * 0.4), (cx + r * 0.55, cy - r * 0.4)], fill=rgba(NEON, a * ok), width=5)

def icon_bank(d, cx, cy, s, a):
    top, base = cy - 0.5 * s, cy + 0.5 * s
    d.polygon([(cx - 0.55 * s, top + 0.3 * s), (cx, top), (cx + 0.55 * s, top + 0.3 * s)], outline=rgba(NEON, a), width=5)
    for i in range(4):
        x = cx - 0.36 * s + i * 0.24 * s
        d.line([(x, top + 0.42 * s), (x, base - 0.12 * s)], fill=rgba(NEON, a), width=5)
    d.line([(cx - 0.55 * s, base), (cx + 0.55 * s, base)], fill=rgba(NEON, a), width=6)
    d.line([(cx - 0.48 * s, base - 0.08 * s), (cx + 0.48 * s, base - 0.08 * s)], fill=rgba(NEON, a), width=4)

def icon_people(d, cx, cy, s, a):
    for dx, sc in ((-0.3, 0.8), (0.3, 0.8), (0, 1.0)):
        x, r = cx + dx * s, 0.16 * s * sc
        y = cy - 0.2 * s + (0 if sc == 1 else 0.06 * s)
        d.ellipse((x - r, y - r, x + r, y + r), outline=rgba(NEON, a), width=4)
        d.arc((x - 2.1 * r, y + 1.3 * r, x + 2.1 * r, y + 5.5 * r), 180, 360, fill=rgba(NEON, a), width=4)

def icon_inbox(d, cx, cy, s, a):
    d.rounded_rectangle((cx - 0.5 * s, cy - 0.38 * s, cx + 0.5 * s, cy + 0.38 * s), int(0.1 * s), outline=rgba(NEON, a), width=5)
    for k in range(3):
        y = cy - 0.18 * s + k * 0.18 * s
        d.line([(cx - 0.3 * s, y), (cx + (0.3 - 0.15 * k) * s, y)], fill=rgba(NEON, a), width=4)

def icon_bars(d, cx, cy, s, a):
    for i, hh in enumerate((0.35, 0.6, 0.9)):
        x = cx - 0.3 * s + i * 0.3 * s
        d.line([(x, cy + 0.4 * s), (x, cy + 0.4 * s - hh * s * 0.8)], fill=rgba(NEON, a), width=8)

def icon_clock(d, cx, cy, s, a):
    r = 0.42 * s
    d.ellipse((cx - r, cy - r, cx + r, cy + r), outline=rgba(NEON, a), width=5)
    d.line([(cx, cy), (cx, cy - 0.25 * s), ], fill=rgba(NEON, a), width=5)
    d.line([(cx, cy), (cx + 0.18 * s, cy + 0.1 * s)], fill=rgba(NEON, a), width=5)

def icon_pct(d, cx, cy, s, a):
    r = 0.12 * s
    d.line([(cx + 0.35 * s, cy - 0.38 * s), (cx - 0.35 * s, cy + 0.38 * s)], fill=rgba(NEON, a), width=5)
    for x, y in ((cx - 0.25 * s, cy - 0.25 * s), (cx + 0.25 * s, cy + 0.25 * s)):
        d.ellipse((x - r, y - r, x + r, y + r), outline=rgba(NEON, a), width=5)

def icon_plane(d, cx, cy, s, a):
    r = 0.5 * s
    d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=rgba(NEON, a))
    p = [(cx - 0.3 * s, cy - 0.02 * s), (cx + 0.28 * s, cy - 0.24 * s), (cx + 0.16 * s, cy + 0.26 * s), (cx + 0.0 * s, cy + 0.08 * s)]
    d.polygon(p, fill=(4, 14, 8, int(255 * a)))
    d.line([(cx + 0.28 * s, cy - 0.24 * s), (cx + 0.0 * s, cy + 0.08 * s), (cx - 0.04 * s, cy + 0.22 * s)], fill=rgba(NEON, a), width=4)

# ---------- icons (video 2) ----------
def icon_shield(d, cx, cy, s, a, ok=1.0):
    p = [(cx, cy - 0.5 * s), (cx + 0.42 * s, cy - 0.34 * s), (cx + 0.38 * s, cy + 0.12 * s), (cx, cy + 0.5 * s),
         (cx - 0.38 * s, cy + 0.12 * s), (cx - 0.42 * s, cy - 0.34 * s)]
    d.line(p + [p[0]], fill=rgba(NEON, a), width=6, joint="curve")
    if ok > 0:
        d.line([(cx - 0.17 * s, cy), (cx - 0.04 * s, cy + 0.14 * s), (cx + 0.2 * s, cy - 0.14 * s)], fill=rgba(NEON, a * ok), width=6)

def icon_warn(d, cx, cy, s, a):
    p = [(cx, cy - 0.45 * s), (cx + 0.5 * s, cy + 0.4 * s), (cx - 0.5 * s, cy + 0.4 * s)]
    d.line(p + [p[0]], fill=rgba(NEON, a), width=5, joint="curve")
    d.line([(cx, cy - 0.15 * s), (cx, cy + 0.12 * s)], fill=rgba(NEON, a), width=6)
    d.ellipse((cx - 5, cy + 0.24 * s - 5, cx + 5, cy + 0.24 * s + 5), fill=rgba(NEON, a))

def icon_store(d, cx, cy, s, a):
    d.line([(cx - 0.5 * s, cy - 0.1 * s), (cx - 0.38 * s, cy - 0.42 * s), (cx + 0.38 * s, cy - 0.42 * s), (cx + 0.5 * s, cy - 0.1 * s), (cx - 0.5 * s, cy - 0.1 * s)], fill=rgba(NEON, a), width=5)
    d.rectangle((cx - 0.42 * s, cy - 0.1 * s, cx + 0.42 * s, cy + 0.45 * s), outline=rgba(NEON, a), width=5)
    d.rectangle((cx - 0.12 * s, cy + 0.12 * s, cx + 0.12 * s, cy + 0.45 * s), outline=rgba(NEON, a), width=4)

def icon_chat(d, cx, cy, s, a):
    d.rounded_rectangle((cx - 0.5 * s, cy - 0.38 * s, cx + 0.5 * s, cy + 0.22 * s), int(0.16 * s), outline=rgba(NEON, a), width=5)
    d.line([(cx - 0.2 * s, cy + 0.22 * s), (cx - 0.3 * s, cy + 0.45 * s), (cx + 0.02 * s, cy + 0.22 * s)], fill=rgba(NEON, a), width=5)
    for k in (-1, 0, 1):
        x = cx + k * 0.22 * s
        d.ellipse((x - 7, cy - 0.08 * s - 7, x + 7, cy - 0.08 * s + 7), fill=rgba(NEON, a))

def check_mark(L, x, y, k):
    L.n.ellipse((x - 30, y - 30, x + 30, y + 30), outline=rgba(NEON, k), width=5)
    L.n.line([(x - 14, y), (x - 3, y + 12), (x + 16, y - 12)], fill=rgba(NEON, k), width=6)

# ---------- scenes (video 2) ----------
CX, CARD = W // 2, (95, 60, 985, 625)

def scene_hook(L, t, a):
    card(L, CARD, a)
    k = a * appear(t, cue(0, "can") - 0.1)
    icon_bank(L.n, CX, 200, 150, k)
    kk = a * appear(t, cue(0, "blocked") - 0.1, 0.2)
    if kk > 0:   # alert badge on the bank
        L.f.ellipse((CX + 55, 100, CX + 125, 170), fill=rgba((4, 14, 8), kk))
        icon_warn(L.n, CX + 90, 137, 52, kk)
    ctext(L.t, (CX, 365), "Bank account", TITLE, WHITE, a * appear(t, cue(0, "bank")))
    ctext(L.t, (CX, 445), "blocked?", BIG, NEON, kk)
    k3 = a * appear(t, cue(0, "p2p") - 0.1)
    if k3 > 0: pill(L, CX, 545, "while working with P2P processing", k3, fnt=SMALL, h=58)

def scene_reviews(L, t, a):
    card(L, CARD, a)
    ctext(L.t, (CX, 135), "When do banks review accounts?", LABEL, GREY, a * appear(t, cue(1, "reviews") - 0.1))
    rows = [("Unverified payment", "sources", cue(1, "unverified") - 0.15),
            ("Patterns that don't match", "normal activity", cue(1, "transaction") - 0.15)]
    for i, (l1, l2, at) in enumerate(rows):
        k = a * appear(t, at, 0.25); y = 265 + i * 170 - 20 * (1 - appear(t, at, 0.25))
        box = (150, y - 68, 930, y + 68)
        L.f.rounded_rectangle(box, 26, fill=rgba((12, 30, 18), k))
        L.n.rounded_rectangle(box, 26, outline=rgba(NEON, 0.6 * k), width=3)
        icon_warn(L.n, 225, y, 70, k)
        ctext(L.t, (290, y - 22), l1, PILL, WHITE, k, "lm")
        ctext(L.t, (290, y + 26), l2, PILL, NEON, k, "lm")

def scene_platform(L, t, a):
    card(L, CARD, a)
    k = a * appear(t, cue(2, "that") - 0.1)
    ctext(L.t, (CX, 225), "Choosing the", TITLE, WHITE, k)
    ctext(L.t, (CX, 320), "platform", BIG, NEON, a * appear(t, cue(2, "platform") - 0.1))
    k2 = a * appear(t, cue(2, "matters") - 0.1)
    if k2 > 0: pill(L, CX, 460, "matters", k2, filled=True, fnt=TITLE, h=96, padx=48)

def scene_verified(L, t, a):
    card(L, CARD, a)
    ctext(L.t, (CX, 125), "KoiPay", TITLE, WHITE, a * appear(t, cue(3, "koipay") - 0.1))
    k = a * appear(t, cue(3, "verified") - 0.1)
    if k > 0: pill(L, CX, 205, "Verified gaming merchants only", k, filled=True)
    xs = (220, CX, 860); y = 370
    k1 = a * appear(t, cue(3, "every") - 0.1)
    icon_store(L.n, xs[0], y, 100, k1); ctext(L.t, (xs[0], y + 85), "Merchant", SMALL, WHITE, k1)
    arrow(L, (xs[0] + 75, y), (xs[1] - 75, y), ease((t - cue(3, "checked") + 0.1) / 0.5), a, t)
    k2 = a * appear(t, cue(3, "checked") + 0.3)
    icon_shield(L.n, xs[1], y, 110, k2, appear(t, cue(3, "checked") + 0.5, 0.2))
    ctext(L.t, (xs[1], y + 85), "Checked", SMALL, NEON, k2)
    arrow(L, (xs[1] + 75, y), (xs[2] - 75, y), ease((t - cue(3, "sent")) / 0.5), a, t)
    k3 = a * appear(t, cue(3, "traders") - 0.1)
    icon_people(L.n, xs[2], y, 110, k3); ctext(L.t, (xs[2], y + 85), "Traders", SMALL, WHITE, k3)
    k4 = a * appear(t, cue(3, "payment"))
    ctext(L.t, (CX, 545), "before any payment request is sent", SMALL, GREY, k4)

def scene_checklist(L, t, a):
    card(L, CARD, a)
    rows = [("Verified traffic", "verified"), ("Clear limits", "clear"), ("Proper operating steps", "proper")]
    for i, (name, wd) in enumerate(rows):
        y = 140 + i * 115
        at = cue(6, wd) - 0.1
        k = a * appear(t, at, 0.25)
        on = appear(t, at + 0.15, 0.2)
        box = (150, y - 48, 930, y + 48)
        L.f.rounded_rectangle(box, 24, fill=rgba(NEON_DARK if on > 0.5 else (12, 30, 18), k * 0.9))
        L.n.rounded_rectangle(box, 24, outline=rgba(NEON, k), width=3)
        ctext(L.t, (200, y), name, PILL, WHITE, k, "lm")
        if on > 0: check_mark(L, 870, y, k * on)
    k = a * appear(t, cue(6, "reduce") - 0.1)
    if k > 0:
        L.n.line([(200, 470), (880, 470)], fill=rgba(NEON, 0.35 * k), width=2)
        pill(L, CX, 540, "Helps reduce avoidable risk", k, filled=True, h=82)

def scene_cta(L, t, a):
    card(L, CARD, a)
    icon_chat(L.n, CX, 155, 120, a * appear(t, cue(7, "manager") - 0.4))
    ctext(L.t, (CX, 290), "Questions about", TITLE, WHITE, a * appear(t, cue(7, "questions") - 0.2))
    ctext(L.t, (CX, 365), "your security?", TITLE, NEON, a * appear(t, cue(7, "questions")))
    k = a * appear(t, cue(7, "manager"))
    if k > 0: pill(L, CX, 470, "Ask our manager", k, filled=True, fnt=TITLE, h=100, padx=44)
    k3 = a * appear(t, cue(7, "manager") + 0.6)
    if k3 > 0: pill(L, CX, 568, "Link in bio", k3, fnt=SMALL, h=54)

SCENES = []
for clip, fn in [(0, scene_hook), (1, scene_reviews), (2, scene_platform), (3, scene_verified), (6, scene_checklist), (7, scene_cta)]:
    s, e = clip_span(clip)
    SCENES.append((s, e, fn))

# ---------- static panel background ----------
def make_bg():
    bg = Image.new("RGB", (W, PH), (2, 5, 3))
    g = Image.new("RGBA", (W, PH), (0, 0, 0, 0)); d = ImageDraw.Draw(g)
    hz = 600                                 # horizon for floor grid
    for i in range(-14, 15):
        d.line([(CX + i * 40, hz), (CX + i * 260, PH + 40)], fill=(46, 232, 122, 34), width=1)
    y, step = hz, 8
    while y < PH:
        d.line([(0, y), (W, y)], fill=(46, 232, 122, int(18 + 30 * (y - hz) / (PH - hz))), width=1)
        step *= 1.32; y += step
    rng = np.random.default_rng(7)
    for _ in range(18):
        x = int(rng.uniform(20, W - 20)); top = int(rng.uniform(40, 560)); bot = int(rng.uniform(top + 120, PH))
        d.line([(x, top), (x, bot)], fill=(46, 232, 122, 60), width=2)
        d.ellipse((x - 4, top - 4, x + 4, top + 4), fill=(140, 255, 180, 200))
    glow = g.filter(ImageFilter.GaussianBlur(6))
    bg.paste(glow, (0, 0), glow); bg.paste(g, (0, 0), g)
    # green haze under the seam
    haze = np.zeros((PH, W), np.float32)
    yy = np.arange(PH)[:, None]; haze += np.exp(-yy / 160.0) * 0.35
    arr = np.asarray(bg).astype(np.float32) + haze[..., None] * np.array(NEON, np.float32)[None, None]
    return np.clip(arr, 0, 255).astype(np.uint8)
BG = make_bg()

# speaker: crop centre/zoom per segment (alternate punch-in on jump cuts)
SEG_ZOOM = []
prev_clip = None; z = 1.0
for c, a, b in SEGS:
    z = (1.12 if z == 1.0 else 1.0) if c == prev_clip else 1.0
    SEG_ZOOM.append(z); prev_clip = c
SEG_ZOOM[-1] = 1.12  # CTA end in close-up

def speaker(frame, t):
    i = max(k for k, s in enumerate(segs_out) if s[0] <= t + 1e-6)
    z = SEG_ZOOM[i]
    w, h = W / z, SEAM / z
    cx = 912  # speaker centred per clip (logo not needed in frame)
    cy = SEAM / 2 - (SEAM / 2 - 470) * (z - 1) / 0.12
    box = (int(cx - w / 2), int(cy - h / 2), int(cx - w / 2) + int(w), int(cy - h / 2) + int(h))
    img = Image.fromarray(frame).crop(box)
    if z != 1.0: img = img.resize((W, SEAM), Image.LANCZOS)
    return np.asarray(img)

# seam fade on speaker bottom
FADE = np.ones((SEAM, 1, 1), np.float32)
FADE[-110:, 0, 0] = np.linspace(1, 0.35, 110)

def subtitle_layer(t):
    lay = Image.new("RGBA", (W, 260), (0, 0, 0, 0))
    cur = [s for s in subs if s[0] <= t < s[1]]
    if not cur: return None
    s, e, toks = cur[-1]
    k = appear(t, s, 0.12)
    sp = lay.width
    parts, total = [], 0
    for i, (tx, g) in enumerate(toks):
        wdt = SUB_FONT.getlength(tx + (" " if i < len(toks) - 1 else ""))
        parts.append((tx, g, total)); total += wdt
    x0 = (W - total) / 2; y = 130 + 10 * (1 - k)
    sh = Image.new("RGBA", lay.size, (0, 0, 0, 0)); sd = ImageDraw.Draw(sh)
    d = ImageDraw.Draw(lay)
    for tx, g, off in parts:
        sd.text((x0 + off, y + 4), tx, font=SUB_FONT, fill=(0, 0, 0, int(230 * k)), anchor="lm")
    sh = sh.filter(ImageFilter.GaussianBlur(10))
    for tx, g, off in parts:
        d.text((x0 + off, y), tx, font=SUB_FONT, fill=rgba(NEON if g else WHITE, k), anchor="lm")
    out = Image.alpha_composite(sh, Image.alpha_composite(sh, lay))
    return out

def render_panel(t):
    L = Layers()
    for s, e, fn in SCENES:
        if s - 0.01 <= t < e + 0.01:
            a = min(appear(t, s, 0.3), 1 - ease((t - (e - 0.18)) / 0.18)) if e < DUR - 0.05 else appear(t, s, 0.3)
            fn(L, t, a)
    panel = Image.fromarray(BG).convert("RGBA")
    panel = Image.alpha_composite(panel, L.fill)
    small = L.neon.resize((W // 2, PH // 2), Image.BILINEAR).filter(ImageFilter.GaussianBlur(9)).resize((W, PH), Image.BILINEAR)
    panel = Image.alpha_composite(panel, small); panel = Image.alpha_composite(panel, small)
    panel = Image.alpha_composite(panel, L.neon)
    panel = Image.alpha_composite(panel, L.text)
    return np.asarray(panel.convert("RGB"))

SEAM_GLOW = None
def compose(frame, t):
    global SEAM_GLOW
    canvas = np.zeros((H, W, 3), np.uint8)
    sp = speaker(frame, t).astype(np.float32) * FADE
    canvas[:SEAM] = sp.astype(np.uint8)
    canvas[SEAM:] = render_panel(t)
    img = Image.fromarray(canvas).convert("RGBA")
    if SEAM_GLOW is None:
        g = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(g)
        d.line([(0, SEAM), (W, SEAM)], fill=(*NEON, 255), width=4)
        SEAM_GLOW = Image.alpha_composite(g.filter(ImageFilter.GaussianBlur(10)), g)
    img = Image.alpha_composite(img, SEAM_GLOW)
    sub = subtitle_layer(t)
    if sub is not None: img.alpha_composite(sub, (0, SEAM - 130))
    return img.convert("RGB")

if PREVIEW:
    for t in PREVIEW:
        fr = subprocess.run(["ffmpeg", "-v", "error", "-ss", str(t), "-i", BASE, "-frames:v", "1", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True).stdout
        compose(np.frombuffer(fr, np.uint8).reshape(1080, 1920, 3), t).save(f"{OUT}/prev_{t:05.2f}.jpg", quality=90)
    sys.exit()

dec = subprocess.Popen(["ffmpeg", "-v", "error", "-i", BASE, "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], stdout=subprocess.PIPE)
enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                        "-i", BASE, "-map", "0:v", "-map", "1:a", "-c:v", "libx264", "-preset", "slow", "-crf", "16", "-pix_fmt", "yuv420p",
                        "-profile:v", "high", "-movflags", "+faststart", "-c:a", "aac", "-b:a", "192k", "-shortest", OUT], stdin=subprocess.PIPE)
n = 0
while True:
    buf = dec.stdout.read(1920 * 1080 * 3)
    if len(buf) < 1920 * 1080 * 3: break
    enc.stdin.write(compose(np.frombuffer(buf, np.uint8).reshape(1080, 1920, 3), n / FPS).tobytes())
    n += 1
    if n % 100 == 0: print(n, flush=True)
enc.stdin.close(); enc.wait()
print("frames", n, "dur", DUR)
