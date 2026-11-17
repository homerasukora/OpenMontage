"""Binance P2P vs processing — Ganesha Pay Noir rebuild of the 2-min explainer.
Talking-head fragments (background kept) + right-side glass panels, full-screen graphic scenes with the speaker
in a circle, Binance marketplace screen in a phone, rate cards, dashboard mock, end card "Free P2P training".
usage: bn_render.py out.mp4 [--preview t1,t2,... outdir]"""
import sys, json, re, subprocess, numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont, ImageFilter

D = "/tmp/claude-0/-home-user/7c5690c1-77ca-5715-b441-4cc8e349293a/scratchpad"
BN = f"{D}/bn"
OUT = sys.argv[1]
PREVIEW = [float(x) for x in sys.argv[3].split(",")] if len(sys.argv) > 3 and sys.argv[2] == "--preview" else None
W, H, FPS = 1920, 1080, 25
PLAN = json.load(open(f"{BN}/plan.json"))
SPEECH_END = PLAN[-1]["o1"]
TOTAL = SPEECH_END + 2.6                       # hold on the end card
NF = int(round(TOTAL * FPS))

# ---------------- brand ----------------
ONYX = (10, 11, 10); EMERALD = (15, 61, 46); GOLD = (207, 165, 74); CHAMP = (230, 214, 168); IVORY = (244, 239, 228)
RED = (224, 71, 60); GREEN_OK = (31, 157, 107)
def font(name, size, weight):
    f = ImageFont.truetype(f"{D}/fonts/{name}.ttf", size); f.set_variation_by_name(weight); return f
F_TITLE = font("Cormorant", 44, b"SemiBold"); F_TITLE_BIG = font("Cormorant", 104, b"SemiBold")
F_ITEM = font("Manrope", 30, b"SemiBold"); F_SMALL = font("Manrope", 30, b"Medium"); F_PILL = font("Manrope", 34, b"Bold")
F_NUM = font("Manrope", 92, b"Bold"); F_NUM_M = font("Manrope", 58, b"Bold"); F_SUB = font("Manrope", 54, b"Bold")
S = 2                                           # supersampling for crisp vector shapes

def rgba(img): return np.asarray(img, np.float32)
def over(dst, src_rgba, x, y, alpha=1.0):
    """alpha-composite an RGBA float array onto dst (float RGB) at x,y."""
    if alpha <= 0: return
    h, w = src_rgba.shape[:2]
    x0, y0 = max(0, x), max(0, y); x1, y1 = min(W, x + w), min(H, y + h)
    if x1 <= x0 or y1 <= y0: return
    s = src_rgba[y0 - y:y1 - y, x0 - x:x1 - x]
    a = s[..., 3:] / 255 * alpha
    dst[y0:y1, x0:x1] = dst[y0:y1, x0:x1] * (1 - a) + s[..., :3] * a

def down(img): return img.resize((img.width // S, img.height // S), Image.LANCZOS)

# ---------------- icons ----------------
BLOGO = None
def binance_logo(px):
    global BLOGO
    if BLOGO is None:
        im = Image.open(f"{BN}/src/binance_logo.webp").convert("RGB"); a = np.asarray(im).astype(np.float32)
        h, w = a.shape[:2]; yy, xx = np.mgrid[0:h, 0:w]
        cx, cy, r = w / 2, h / 2 + 0.0, w * .289            # the yellow disc
        m = np.clip((r - np.sqrt((xx - cx) ** 2 + (yy - cy) ** 2)) / 2 + .5, 0, 1)
        BLOGO = Image.fromarray(np.dstack([a, m * 255]).astype(np.uint8), "RGBA").crop((int(cx - r - 2), int(cy - r - 2), int(cx + r + 2), int(cy + r + 2)))
    return BLOGO.resize((px, px), Image.LANCZOS)

def icon(kind, px):
    im = Image.new("RGBA", (px * S, px * S), (0, 0, 0, 0)); d = ImageDraw.Draw(im); p = px * S; lw = max(3, p // 11)
    if kind == "ok":
        d.ellipse([lw, lw, p - lw, p - lw], outline=GOLD, width=lw)
        d.line([(p * .3, p * .52), (p * .45, p * .67), (p * .72, p * .36)], fill=GOLD, width=lw, joint="curve")
    elif kind == "x":
        d.ellipse([lw, lw, p - lw, p - lw], outline=RED, width=lw)
        d.line([(p * .34, p * .34), (p * .66, p * .66)], fill=RED, width=lw); d.line([(p * .66, p * .34), (p * .34, p * .66)], fill=RED, width=lw)
    elif kind == "dot":
        d.ellipse([p * .3, p * .3, p * .7, p * .7], fill=GOLD)
    elif kind == "arrow":
        d.line([(p * .2, p * .5), (p * .78, p * .5)], fill=GOLD, width=lw); d.line([(p * .55, p * .27), (p * .8, p * .5), (p * .55, p * .73)], fill=GOLD, width=lw, joint="curve")
    elif kind == "down":
        d.line([(p * .5, p * .18), (p * .5, p * .8)], fill=GOLD, width=lw); d.line([(p * .27, p * .56), (p * .5, p * .8), (p * .73, p * .56)], fill=GOLD, width=lw, joint="curve")
    elif kind == "up":
        d.line([(p * .5, p * .82), (p * .5, p * .2)], fill=GOLD, width=lw); d.line([(p * .27, p * .44), (p * .5, p * .2), (p * .73, p * .44)], fill=GOLD, width=lw, joint="curve")
    elif kind == "plane":                                  # paper plane (Telegram-style, brand-neutral)
        d.polygon([(p * .12, p * .48), (p * .88, p * .18), (p * .66, p * .86), (p * .46, p * .62)], outline=GOLD, width=lw)
        d.line([(p * .46, p * .62), (p * .88, p * .18)], fill=GOLD, width=lw)
    elif kind == "binance":
        return binance_logo(px)
    return down(im)

# ---------------- glass panel ----------------
def text_w(f, t): return f.getlength(t)
def panel(title, items, n, width=720, title_icon=None, struck=False):
    """Right-side glass card: title + rows; first n rows visible. items: [(icon, text)]."""
    pad, row_h, gap = 34, 88, 14
    th = 76
    hgt = pad + th + 10 + max(n, 0) * (row_h + gap) + pad - (gap if n else 10)   # card grows with the rows
    im = Image.new("RGBA", (width * S, hgt * S), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle([0, 0, width * S - 1, hgt * S - 1], radius=28 * S, fill=ONYX + (214,), outline=GOLD + (230,), width=2 * S)
    x = pad
    if title_icon:
        ic = icon(title_icon, 54); im.alpha_composite(ic.resize((54 * S, 54 * S)), (pad * S, (pad + 8) * S)); x += 70
    ft = ImageFont.truetype(F_TITLE.path, 54 * S); ft.set_variation_by_name(b"SemiBold")
    d.text((x * S, (pad + 4) * S), title, font=ft, fill=CHAMP)
    fi = ImageFont.truetype(F_ITEM.path, 37 * S); fi.set_variation_by_name(b"SemiBold")
    y = pad + th + 10
    for i, (ic, t) in enumerate(items):
        if i < n:
            d.rounded_rectangle([pad * S, y * S, (width - pad) * S, (y + row_h) * S], radius=18 * S, fill=EMERALD + (150,), outline=GOLD + (90,), width=S)
            icimg = icon(ic, 46); im.alpha_composite(icimg.resize((46 * S, 46 * S)), ((pad + 20) * S, (y + 21) * S))
            d.text(((pad + 84) * S, (y + 44) * S), t, font=fi, fill=CHAMP, anchor='lm')
            if struck and ic == "x":
                tw = fi.getlength(t)
                d.line([((pad + 84) * S, (y + 46) * S), ((pad + 84) * S + tw, (y + 46) * S)], fill=RED + (230,), width=3 * S)
        y += row_h + gap
    return rgba(down(im))

PANEL_CACHE = {}
def panel_state(key, title, items, n, **kw):
    k = (key, n)
    if k not in PANEL_CACHE: PANEL_CACHE[k] = panel(title, items, n, **kw)
    return PANEL_CACHE[k]

def ease(x): x = min(max(x, 0.0), 1.0); return x * x * (3 - 2 * x)

def draw_panel(img, t, spec, x=None, y=130):
    if x is None: x = W - spec.get("width", 720) - 60
    """spec: dict(key,title,items,cues,t_in,t_out,...). Rows appear at their cue with a short fade."""
    t_in, t_out = spec["t_in"], spec["t_out"]
    if not (t_in - .01 <= t < t_out + .3): return
    a = ease((t - t_in) / .3) * (1 - ease((t - t_out) / .3))
    n = sum(1 for c in spec["cues"] if t >= c)
    kw = {k: v for k, v in spec.items() if k in ("width", "title_icon", "struck")}
    cur = panel_state(spec["key"], spec["title"], spec["items"], n, **kw)
    dx = int(40 * (1 - ease((t - t_in) / .35)))
    if n > 0 and t - spec["cues"][n - 1] < .25:              # newest row fading in
        prev = panel_state(spec["key"], spec["title"], spec["items"], n - 1, **kw)
        f = ease((t - spec["cues"][n - 1]) / .25)
        over(img, prev, x + dx, y, a * (1 - f)); over(img, cur, x + dx, y, a * f)
    else:
        over(img, cur, x + dx, y, a)

# ---------------- pills, cards ----------------
def pill(text, ic=None, fill=ONYX + (220,), border=GOLD, fg=CHAMP, f=None, padx=30, h=76):
    f = f or F_PILL
    fs = ImageFont.truetype(f.path, f.size * S); fs.set_variation_by_name(f.get_variation_axes() and b"Bold" or b"Bold")
    tw = int(fs.getlength(text) / S); icw = 52 if ic else 0
    w = tw + 2 * padx + icw
    im = Image.new("RGBA", (w * S, h * S), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle([0, 0, w * S - 1, h * S - 1], radius=h * S // 2, fill=fill, outline=border + (240,), width=2 * S)
    if ic: im.alpha_composite(icon(ic, 40).resize((40 * S, 40 * S)), (padx * S, (h - 40) // 2 * S))
    d.text(((padx + icw) * S, (h // 2) * S), text, font=fs, fill=fg, anchor="lm")
    return rgba(down(im))

PILL_CACHE = {}
def draw_pill(img, t, key, text, x, y, t_in, t_out, ic=None, center=False, **kw):
    if not (t_in - .01 <= t < t_out + .3): return
    if key not in PILL_CACHE: PILL_CACHE[key] = pill(text, ic, **kw)
    p = PILL_CACHE[key]; a = ease((t - t_in) / .3) * (1 - ease((t - t_out) / .3))
    if center: x = x - p.shape[1] // 2
    over(img, p, x, y + int(16 * (1 - ease((t - t_in) / .3))), a)

def card(lines, w, h, border=GOLD, fill=EMERALD + (235,)):
    """lines: [(font, text, color, y_center_frac)]"""
    im = Image.new("RGBA", (w * S, h * S), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle([0, 0, w * S - 1, h * S - 1], radius=26 * S, fill=fill, outline=border + (240,), width=2 * S)
    for f, t, col, fy in lines:
        fs = ImageFont.truetype(f.path, f.size * S)
        try: fs.set_variation_by_name(b"Bold")
        except Exception: pass
        d.text((w * S // 2, int(h * S * fy)), t, font=fs, fill=col, anchor="mm")
    return rgba(down(im))

CARD_CACHE = {}
def draw_card(img, t, key, lines, x, y, w, h, t_in, t_out, **kw):
    if not (t_in - .01 <= t < t_out + .3): return
    if key not in CARD_CACHE: CARD_CACHE[key] = card(lines, w, h, **kw)
    a = ease((t - t_in) / .35) * (1 - ease((t - t_out) / .3))
    sc = .92 + .08 * ease((t - t_in) / .35)
    c = CARD_CACHE[key]
    if sc < .999:
        c = cv2.resize(c, (int(w * sc), int(h * sc)), interpolation=cv2.INTER_AREA); x += (w - c.shape[1]) // 2; y += (h - c.shape[0]) // 2
    over(img, c, x, y, a)

# ---------------- full-screen background ----------------
yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
r = np.sqrt(((xx - W * .55) / (W * .62)) ** 2 + ((yy - H * .45) / (H * .8)) ** 2)
GLOW = np.clip(1 - r, 0, 1) ** 1.8
FS_BG = (np.array(ONYX, np.float32) + GLOW[..., None] * (np.array(EMERALD, np.float32) * 1.5 - np.array(ONYX, np.float32)))
# faint gold hairlines (brand: gold = lines only)
_lines = Image.new("L", (W, H), 0); _d = ImageDraw.Draw(_lines)
for i in range(9):
    yv = 160 + i * 100; _d.line([(0, yv), (W, yv)], fill=10)
FS_BG = FS_BG + np.asarray(_lines, np.float32)[..., None] / 255 * np.array(GOLD, np.float32) * .5
DITHER = np.random.default_rng(3).uniform(-1, 1, (H, W, 1)).astype(np.float32)

# ---------------- logo ----------------
_wm = Image.open(f"{D}/ganesha_wordmark_noir.png").convert("RGBA")
_wm = _wm.resize((250, round(_wm.height * 250 / _wm.width)), Image.LANCZOS)
LOGO = rgba(_wm)
_pl = Image.new("RGBA", ((250 + 48) * S, (_wm.height + 36) * S), (0, 0, 0, 0))
ImageDraw.Draw(_pl).rounded_rectangle([0, 0, _pl.width - 1, _pl.height - 1], radius=20 * S, fill=ONYX + (205,))
LOGO_PLATE = rgba(down(_pl))
def draw_logo(img, fullscreen):
    if not fullscreen: over(img, LOGO_PLATE, 40, 36)
    over(img, LOGO, 64, 54)

# bottom gradient for subtitles on camera shots
GRAD = np.clip((yy[..., None] - H * .68) / (H * .32), 0, 1) ** 1.4 * .62

# ---------------- subtitles ----------------
words = json.load(open(f"{BN}/voice_words.json"))
def merge(ws):
    out, i = [], 0
    def take(n, txt):
        nonlocal i
        out.append(dict(w=txt, s=ws[i]["s"], e=ws[i + n - 1]["e"])); i += n
    while i < len(ws):
        w = [x["w"] for x in ws[i:i + 4]] + [""] * 4
        low = [x.lower().strip(".,?") for x in w]
        if low[:3] == ["p", "to", "p"]: take(3, "P2P?"); continue
        if low[:3] == ["twenty", "four", "seven"]: take(3, "24/7."); continue
        if low[1:3] == ["per", "cent"] and low[0] in ("one", "three"):
            take(3, ("1%" if low[0] == "one" else "3%") + ("," if w[2].endswith(",") else "")); continue
        if low[:2] == ["one", "lakh"]:
            if low[2] == "rupees": take(3, "₹1 lakh"); continue
            take(2, "₹1 lakh"); continue
        if low[1:2] == ["thousand"] and low[0] in ("one", "three"):
            v = "₹1,000" if low[0] == "one" else "₹3,000"
            if low[2] == "rupees": take(3, v + ("." if w[2].endswith(".") else "")); continue
            take(2, v + ("." if w[1].endswith(".") else "")); continue
        x = w[0]
        x = {"telegram": "Telegram", "forwarder": "Forwarder"}.get(x, x)
        x = re.sub(r"^[Pp]ay-ins", "PayIns", x); x = re.sub(r"^[Pp]ay-in", "PayIn", x)
        x = re.sub(r"^[Pp]ayouts", "PayOuts", x); x = re.sub(r"^[Pp]ayout", "PayOut", x)
        take(1, x)
    return out
WORDS = merge(words)
SMALL = {"a", "an", "the", "to", "of", "and", "with", "by", "on", "in", "it", "is", "you", "your", "for", "who", "can", "are", "them", "into", "through"}
def chunks(ws):
    cl = lambda w: re.sub(r"[.,:;?]+$", "", w["w"]).lower()
    out, cur = [], []
    for i, w in enumerate(ws):
        cur.append(w); nxt = ws[i + 1] if i + 1 < len(ws) else None
        hard = nxt is None or re.search(r"[.,:;?]$", w["w"]) or nxt["s"] - w["e"] > .25
        content = sum(cl(c) not in SMALL for c in cur)
        soft = content >= 2 or len(cur) >= 4 or (nxt and sum(len(c["w"]) + 1 for c in cur) + len(nxt["w"]) > 24)
        if hard: out.append(cur); cur = []
        elif soft:
            carry = []
            while len(cur) > 1 and cl(cur[-1]) in SMALL: carry.insert(0, cur.pop())
            out.append(cur); cur = carry
    res = []
    for i, c in enumerate(out):
        s0 = c[0]["s"]; nx = out[i + 1][0]["s"] if i + 1 < len(out) else 1e9
        e0 = min(max(min(c[-1]["e"], c[-1]["s"] + .9), s0 + .35), nx)
        res.append((s0, e0, [re.sub(r"[.,:;]+$", "", x["w"]) for x in c]))
    return res
SUBS = chunks(WORDS)
KEY = re.compile(r"^(USDT|Binance|P2P\??|merchants?|marketplace|spread|₹.*|\d+%|processing|platform|PayIns?|PayOuts?|UPI|SMS|Forwarder|"
                 r"Anti-fraud|callback|commission|dashboard|guaranteed|routing|limits|manager|Telegram|24/7|description|onboarding|risks|frozen|"
                 r"Appeals|wars|rates|requests|traders?)$", re.I)
_sub_cache = {}
def sub_layer(ws):
    key = " ".join(ws)
    if key not in _sub_cache:
        f = ImageFont.truetype(F_SUB.path, 54 * S); f.set_variation_by_name(b"Bold")
        sp = f.getlength(" "); widths = [f.getlength(w) for w in ws]; tw = int(sum(widths) + sp * (len(ws) - 1))
        pad = 30 * S; hh = 54 * S + 2 * pad + 20 * S
        m = Image.new("L", (tw + 2 * pad, hh), 0); col = Image.new("RGB", m.size, CHAMP)
        dm = ImageDraw.Draw(m); dc = ImageDraw.Draw(col); x = pad
        for w, wd in zip(ws, widths):
            dm.text((x, pad), w, font=f, fill=255); dc.text((x, pad), w, font=f, fill=GOLD if KEY.match(w) else CHAMP); x += wd + sp
        mm = np.asarray(m, np.float32) / 255
        sh = np.roll(np.asarray(m.filter(ImageFilter.GaussianBlur(9 * S)), np.float32) / 255, 3 * S, axis=0)
        a = np.clip(mm + sh * (1 - mm), 0, 1)
        rgb = np.asarray(col, np.float32) * (mm / np.maximum(a, 1e-4))[..., None]
        im = Image.fromarray(np.dstack([rgb.clip(0, 255), a * 255]).astype(np.uint8), "RGBA")
        _sub_cache[key] = rgba(down(im))
    return _sub_cache[key]
def draw_subs(img, t):
    for s0, e0, ws in SUBS:
        if s0 <= t < e0:
            L = sub_layer(ws); h, w = L.shape[:2]
            over(img, L, (W - w) // 2, 1000 - h // 2 - 8, min(1, (t - s0) / .1 + .35)); return

# ---------------- video sources ----------------
class Reader:
    """Sequential reader for one EDL part, frames at 25 fps."""
    def __init__(self, src, t0, t1, w, h):
        self.w, self.h = w, h
        self.p = subprocess.Popen(["ffmpeg", "-v", "error", "-ss", f"{t0:.3f}", "-to", f"{t1:.3f}", "-i", src, "-vf", f"fps={FPS},scale={w}:{h}:flags=lanczos",
                                   "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], stdout=subprocess.PIPE)
        self.last = np.zeros((h, w, 3), np.uint8)
    def next(self):
        b = self.p.stdout.read(self.w * self.h * 3)
        if len(b) == self.w * self.h * 3: self.last = np.frombuffer(b, np.uint8).reshape(self.h, self.w, 3)
        return self.last

HEAD = {k: json.load(open(f"{BN}/head_{k}.json")) for k in "BEHJL"}
CIRCLE_D = 400
_cm = Image.new("L", (CIRCLE_D * S, CIRCLE_D * S), 0); ImageDraw.Draw(_cm).ellipse([0, 0, CIRCLE_D * S - 1, CIRCLE_D * S - 1], fill=255)
CMASK = np.asarray(_cm.resize((CIRCLE_D, CIRCLE_D), Image.LANCZOS), np.float32)[..., None] / 255
_ring = Image.new("RGBA", ((CIRCLE_D + 16) * S, (CIRCLE_D + 16) * S), (0, 0, 0, 0))
ImageDraw.Draw(_ring).ellipse([2 * S, 2 * S, (CIRCLE_D + 14) * S, (CIRCLE_D + 14) * S], outline=GOLD, width=4 * S)
RING = rgba(down(_ring))
def draw_circle(img, frame, head, cx, cy, a=1.0, zoom=.44):
    fh, fw = frame.shape[:2]; side = int(fh * zoom)
    hx, hy = head[0] * fw, head[1] * fh + side * .12
    x0 = int(np.clip(hx - side / 2, 0, fw - side)); y0 = int(np.clip(hy - side / 2, 0, fh - side))
    crop = cv2.resize(np.ascontiguousarray(frame[y0:y0 + side, x0:x0 + side]), (CIRCLE_D, CIRCLE_D), interpolation=cv2.INTER_LANCZOS4).astype(np.float32)
    if fh < 600:                                                   # low-res reference footage: gentle sharpen
        bl = cv2.GaussianBlur(crop, (0, 0), 1.6); crop = np.clip(crop * 1.45 - bl * .45, 0, 255)
    x, y = cx - CIRCLE_D // 2, cy - CIRCLE_D // 2
    reg = img[y:y + CIRCLE_D, x:x + CIRCLE_D]; m = CMASK * a
    img[y:y + CIRCLE_D, x:x + CIRCLE_D] = reg * (1 - m) + crop * m
    over(img, RING, x - 8, y - 8, a)

# phone with Binance marketplace screen recording
PH_W, PH_H = 362, 760
_pf = Image.new("RGBA", ((PH_W + 24) * S, (PH_H + 24) * S), (0, 0, 0, 0))
ImageDraw.Draw(_pf).rounded_rectangle([0, 0, _pf.width - 1, _pf.height - 1], radius=58 * S, fill=ONYX + (255,), outline=GOLD, width=3 * S)
PHONE = rgba(down(_pf))
_sm = Image.new("L", (PH_W * S, PH_H * S), 0); ImageDraw.Draw(_sm).rounded_rectangle([0, 0, PH_W * S - 1, PH_H * S - 1], radius=46 * S, fill=255)
SMASK = np.asarray(_sm.resize((PH_W, PH_H), Image.LANCZOS), np.float32)[..., None] / 255

# ---------------- scene timeline (output seconds; cues = spoken words) ----------------
seg = {p["id"]: p for p in PLAN}
segs_by = {}
for p in PLAN: segs_by.setdefault(p["id"], []).append(p)
def span(i): return segs_by[i][0]["o0"], segs_by[i][-1]["o1"]
A0, A1 = span("A"); B0, B1 = span("B"); C0, C1 = span("C"); D0, D1 = span("D"); E0, E1 = span("E"); F0, F1 = span("F")
G0, G1 = span("G"); H0, H1 = span("H"); I0, I1 = span("I"); J0, J1 = span("J"); K0, K1 = span("K"); L0, L1 = span("L")
J_SPLIT = 100.45                      # dashboard (full-screen) -> Telegram bot (camera)
END_CARD = 113.90                     # "The link is in the description"

PANELS = [
    dict(key="routine", title="Binance P2P routine", title_icon="binance", t_in=3.44, t_out=9.15,
         items=[("dot", "Update your ad price"), ("dot", "Fight for the top spot"), ("dot", "Wait for a match")], cues=[4.88, 6.24, 7.68]),
    dict(key="risks", title="On P2P, risks are yours", t_in=29.14, t_out=D1 - .15,
         items=[("x", "Price wars"), ("x", "Slow days"), ("x", "“Paid” without paying"), ("x", "Appeals"), ("x", "Frozen bank account")],
         cues=[30.82, 32.10, 33.22, 35.62, 38.54]),
    dict(key="payin", title="PayIn", title_icon="down", t_in=49.90, t_out=56.30,
         items=[("dot", "Client pays via UPI"), ("dot", "Into your business account")], cues=[51.50, 54.70]),
    dict(key="sms", title="SMS Forwarder", t_in=56.46, t_out=F1 - .15,
         items=[("dot", "Reads the bank SMS"), ("ok", "Confirms the payment")], cues=[58.22, 61.04]),
    dict(key="after", title="After you confirm", t_in=63.20, t_out=69.50,
         items=[("ok", "Anti-fraud check"), ("ok", "Merchant callback"), ("ok", "Commission in dashboard")], cues=[63.28, 65.44, 67.28]),
    dict(key="payout", title="PayOut", title_icon="up", t_in=69.68, t_out=G1 - .15,
         items=[("dot", "Request approved"), ("arrow", "You send the payment")], cues=[71.52, 72.24]),
    dict(key="earn", title="You earn per operation", t_in=84.62, t_out=I1 - .15, width=760,
         items=[("x", "Volume isn’t guaranteed"), ("dot", "Depends on routing"), ("dot", "And on your limits"), ("ok", "Manager confirms rates")],
         cues=[87.26, 89.58, 90.38, 91.50]),
    dict(key="tg", title="Telegram bot", title_icon="plane", t_in=100.56, t_out=J1 - .15,
         items=[("dot", "New request alerts"), ("ok", "Support 24/7")], cues=[101.76, 103.60]),
    dict(key="before", title="Before you start", t_in=105.68, t_out=K1 - .1,
         items=[("dot", "Business bank accounts"), ("dot", "Working funds"), ("dot", "Your hours"), ("ok", "Agree with your manager")],
         cues=[107.36, 109.12, 109.92, 111.12]),
]

def fullscreen_at(t):
    return (B0 <= t < E1 and not (D0 <= t < D1)) or (H0 <= t < H1) or (J0 <= t < J_SPLIT) or t >= END_CARD

def scene_fs(img, t, frames):
    """Full-screen graphic scenes."""
    if B0 <= t < B1:                                              # marketplace
        draw_circle(img, frames["ref"], HEAD["B"][min(len(HEAD["B"]) - 1, int((t - B0) * FPS))], 330, 600)
        draw_pill(img, t, "mkt_t", "Binance P2P · Marketplace", 960, 70, B0 + .05, B1 - .2, ic="binance", center=True)
        # phone
        px, py = 780, 180
        over(img, PHONE, px - 12, py - 12)
        scr = cv2.resize(frames["screen"], (PH_W, PH_H), interpolation=cv2.INTER_AREA).astype(np.float32)
        reg = img[py:py + PH_H, px:px + PH_W]; img[py:py + PH_H, px:px + PH_W] = reg * (1 - SMASK) + scr * SMASK
        for k, (txt, ic, c) in enumerate([("You’re a merchant", "dot", 12.56), ("You hold USDT", "dot", 15.04), ("Buy & sell ads", "dot", 17.04), ("You earn the spread", "ok", 18.72)]):
            draw_pill(img, t, f"mkt{k}", txt, 1250, 280 + k * 120, c, B1 - .2, ic=ic)
    elif C0 <= t < C1:                                            # spread math
        draw_pill(img, t, "sm_t", "Binance P2P · spread math", 960, 90, C0 + .05, C1 - .2, ic="binance", center=True)
        draw_card(img, t, "sm1", [(F_NUM, "1%", GOLD, .45), (F_SMALL, "spread", CHAMP, .8)], 330, 300, 340, 260, 21.62, C1 - .2)
        if t >= 23.0: draw_pill(img, t, "sm_x", "×", 760, 400, 23.0, C1 - .2, center=True, padx=22)
        draw_card(img, t, "sm2", [(F_NUM_M, "₹1,00,000", CHAMP, .45), (F_SMALL, "volume", CHAMP, .8)], 830, 300, 520, 260, 23.14, C1 - .2)
        if t >= 25.0: draw_pill(img, t, "sm_eq", "≈", 1430, 400, 25.0, C1 - .2, center=True, padx=22)
        draw_card(img, t, "sm3", [(F_NUM_M, "₹1,000", GOLD, .45), (F_SMALL, "your margin", CHAMP, .8)], 1500, 300, 330, 260, 25.14, C1 - .2)
        draw_pill(img, t, "sm_w", "Only if the rate doesn’t move against you", 960, 650, 27.14, C1 - .2, ic="x", center=True)
    elif E0 <= t < E1:                                            # processing removes / how requests reach you
        draw_circle(img, frames["ref"], HEAD["E"][min(len(HEAD["E"]) - 1, int((t - E0) * FPS))], 300, 560)
        rm = dict(key="removes", title="Processing removes", t_in=40.06, t_out=E1 - .2, struck=True, width=640,
                  items=[("x", "Marketplace layer"), ("x", "Ads & price updates"), ("x", "Hunting for buyers")], cues=[41.50, 42.94, 44.06])
        draw_panel(img, t, rm, x=530, y=240)
        fl = dict(key="flow", title="How requests reach you", t_in=45.30, t_out=E1 - .2, width=690,
                  items=[("dot", "Merchant request"), ("arrow", "Ganesha Pay routing"), ("ok", "You, the trader")], cues=[45.42, 48.14, 49.10])
        draw_panel(img, t, fl, x=1190, y=240)
    elif H0 <= t < H1:                                            # base rates
        draw_circle(img, frames["cam"], HEAD["H"][min(len(HEAD["H"]) - 1, int((t - H0) * FPS))], 300, 560)
        draw_pill(img, t, "r_t", "Ganesha Pay · base rates", 1170, 90, H0 + .05, H1 - .2, center=True)
        draw_card(img, t, "r1", [(F_PILL, "PayIn ↓", CHAMP, .16), (F_NUM, "≈ 3%", GOLD, .42)], 640, 200, 480, 430, 74.24, H1 - .2)
        draw_card(img, t, "r2", [(F_PILL, "PayOut ↑", CHAMP, .16), (F_NUM, "≈ 1%", GOLD, .42)], 1220, 200, 480, 430, 75.92, H1 - .2)
        draw_card(img, t, "r1b", [(F_SMALL, "on ₹1,00,000", CHAMP, .3), (F_NUM_M, "≈ ₹3,000", GOLD, .68)], 660, 470, 440, 140, 80.24, H1 - .2, fill=ONYX + (235,))
        draw_card(img, t, "r2b", [(F_SMALL, "on ₹1,00,000", CHAMP, .3), (F_NUM_M, "≈ ₹1,000", GOLD, .68)], 1240, 470, 440, 140, 82.94, H1 - .2, fill=ONYX + (235,))
        draw_pill(img, t, "r_n", "Your manager confirms your exact terms", 1170, 690, 77.76, H1 - .2, ic="ok", center=True, f=F_SMALL, h=54)
    elif J0 <= t < J_SPLIT:                                       # dashboard
        draw_circle(img, frames["cam"], HEAD["J"][min(len(HEAD["J"]) - 1, int((t - J0) * FPS))], 300, 560)
        rows = [("Incoming requests", 95.66), ("Statuses", 96.94), ("Limits", 97.98), ("History", 98.70), ("Commission", 99.50)]
        dash = dict(key="dash", title="Your dashboard", t_in=94.45, t_out=J_SPLIT - .15, width=820,
                    items=[("ok" if n == "Commission" else "dot", n) for n, _ in rows], cues=[c for _, c in rows])
        draw_panel(img, t, dash, x=720, y=120)
    if t >= END_CARD:                                             # end card
        a = ease((t - END_CARD) / .4)
        if t < SPEECH_END + .3:
            draw_circle(img, frames["cam"], HEAD["L"][min(len(HEAD["L"]) - 1, int((t - segs_by["L"][1]["o0"]) * FPS))], 300, 560,
                        a=a * (1 - ease((t - SPEECH_END) / .3)))
        over(img, LOGO_BIG, (W - LOGO_BIG.shape[1]) // 2 + 150, 200, a)
        over(img, END_TITLE, (W - END_TITLE.shape[1]) // 2 + 150, 360, a)
        over(img, END_BTN, (W - END_BTN.shape[1]) // 2 + 150, 560, ease((t - END_CARD - .4) / .4))
        bob = int(14 * np.sin((t - END_CARD) * 2 * np.pi / 1.1))
        over(img, END_ARROW, (W - END_ARROW.shape[1]) // 2 + 150, 700 + bob, ease((t - END_CARD - .7) / .4))

# end-card assets
_lb = Image.open(f"{D}/ganesha_wordmark_noir.png").convert("RGBA"); _lb = _lb.resize((420, round(_lb.height * 420 / _lb.width)), Image.LANCZOS)
LOGO_BIG = rgba(_lb)
def _end_title():
    f = ImageFont.truetype(F_TITLE_BIG.path, 104 * S); f.set_variation_by_name(b"SemiBold")
    a_txt, b_txt = "Free ", "P2P training"
    wa, wb = f.getlength(a_txt), f.getlength(b_txt)
    im = Image.new("RGBA", (int(wa + wb) + 40 * S, 150 * S), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.text((20 * S, 10 * S), a_txt, font=f, fill=CHAMP); d.text((20 * S + wa, 10 * S), b_txt, font=f, fill=GOLD)
    return rgba(down(im))
END_TITLE = _end_title()
END_BTN = pill("Link below — in the description", fill=GOLD + (255,), border=GOLD, fg=ONYX, h=84, padx=44, f=font("Manrope", 36, b"Bold"))
END_ARROW = rgba(icon("down", 70))

# ---------------- render loop ----------------
def frame_at(t, frames, cam_ok):
    fs = fullscreen_at(t)
    if fs:
        img = FS_BG.copy()
        scene_fs(img, t, frames)
    else:
        img = frames["cam"].astype(np.float32).copy()
        img = img * (1 - GRAD)                                   # darken the bottom for subtitles (background kept)
        for sp in PANELS: draw_panel(img, t, sp)
        if A0 <= t < A1 and t >= 9.2:
            draw_pill(img, t, "diff", "Processing works differently", 1240, 150, 9.20, A1 - .1, ic="arrow")
    draw_logo(img, fs)
    if t < SPEECH_END + .05: draw_subs(img, t)
    return img

def main():
    enc = None
    if not PREVIEW:
        enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                                "-c:v", "libx264", "-preset", "medium", "-crf", "17", "-pix_fmt", "yuv420p", OUT], stdin=subprocess.PIPE)
    # one reader per EDL part, opened lazily in order
    parts = PLAN; pi = 0; cam = None; ref = None
    screen = Reader(f"{BN}/src/4ea4e461-ScreenRecording_10-28-2026_15-57-29_1.mp4", 0, 14.4, 660, 1434)
    prev_img = None; prev_fs = None; fade_from = None; fade_t0 = -1
    targets = sorted(int(round(x * FPS)) for x in PREVIEW) if PREVIEW else None
    for j in range(NF):
        t = j / FPS
        while pi < len(parts) and t >= parts[pi]["o1"] and pi < len(parts) - 1: pi += 1
        p = parts[pi]
        if getattr(main, "_open", None) != pi:
            main._open = pi
            if p["kind"] == "ref":
                ref = Reader(f"{BN}/src/{p['src']}.mp4", p["s0"], p["s1"], 848, 476)
            else:
                cam = Reader(f"{BN}/src/{p['src']}.mp4", p["s0"], p["s1"], W, H)
        frames = {"cam": cam.next() if (cam is not None and p["kind"] == "cam") else (cam.last if cam is not None else np.zeros((H, W, 3), np.uint8)),
                  "ref": ref.next() if (ref is not None and p["kind"] == "ref") else (ref.last if ref is not None else np.zeros((476, 848, 3), np.uint8)),
                  "screen": screen.next() if B0 <= t < B1 else screen.last}
        if targets is not None and j not in targets:
            if j > max(targets): break
            continue
        img = frame_at(t, frames, True)
        fs = fullscreen_at(t)
        if prev_fs is not None and fs != prev_fs and targets is None: fade_from, fade_t0 = prev_img, t      # 0.24 s crossfade between camera and graphics
        if fade_from is not None and t - fade_t0 < .24:
            k = ease((t - fade_t0) / .24); img = fade_from * (1 - k) + img * k
        prev_img, prev_fs = img, fs
        out = (img + DITHER).clip(0, 255).astype(np.uint8)
        if enc: enc.stdin.write(out.tobytes())
        else: Image.fromarray(out).save(f"{OUT}/f{t:07.2f}.png")
        if j % 250 == 0: print(j, NF, flush=True)
    if enc: enc.stdin.close(); enc.wait()
main()
