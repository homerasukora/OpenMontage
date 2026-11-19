"""YouTube #1 «Who we are» — Ganesha Pay Noir montage.
Arnold (Wan 3.0 lip-sync clips, one per voice part) full frame / punch-in / left-shift with glass panels,
full-screen graphic scenes with Arnold in a circle, Devansh case, exchange table, live counter, Academy card, two-button CTA.
usage: yt_render.py out.mp4 [--preview t1,t2,... outdir]"""
import sys, json, re, math, subprocess, numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont, ImageFilter

D = "/tmp/claude-0/-home-user/7c5690c1-77ca-5715-b441-4cc8e349293a/scratchpad"
Y = f"{D}/yt"; P = f"{Y}/parts"; M = f"{Y}/mat"
OUT = sys.argv[1]
PREVIEW = [float(x) for x in sys.argv[3].split(",")] if len(sys.argv) > 3 and sys.argv[2] == "--preview" else None
W, H, FPS = 1920, 1080, 30

# ---------------- timeline: voice sections and their video clips ----------------
def dur(f): return float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", f]))
GAP = 0.12
# section: (name, audio file, [(clip file, offset inside the section audio, word json)])
SECS = [("s1", "s1", [("../hook/wan_hook", 0, "s1")]),
        ("s2", "s2", [("wan_s2", 0, "s2")]),
        ("s3", "s3", [("wan_s31", 0, "s31"), ("wan_s32", 9.62, "s32")]),
        ("s4", "s4", [("wan_s41", 0, "s41"), ("wan_s42", 10.56, "s42")]),
        ("s5", "s5", [("wan_s5", 0, "s5")]),
        ("s6a", "s6a", [("wan_s6a1", 0, "s6a1"), ("wan_s6a2", 7.2, "s6a2")]),
        ("s6b", "s6b", [("wan_s6b", 0, "s6b")]),
        ("s7", "s7", [("wan_s7", 0, "s7")]),
        ("s8", "s8", [("wan_s8", 0, "s8")]),
        ("s10", "s10", [("wan_s10", 0, "s10")])]
OFF, CLIPS, RAW = {}, [], []
t = 0.0
for name, af, clips in SECS:
    OFF[name] = t; d = dur(f"{P}/{af}.mp3")
    for k, (cf, o, wj) in enumerate(clips):
        mp = json.load(open(f"{P}/map_{wj}.json"))
        CLIPS.append(dict(f=f"{P}/{cf}.mp4", t0=t + o, sec=name, mt=[p[0] for p in mp], mv=[p[1] for p in mp], vd=dur(f"{P}/{cf}.mp4")))
        for w in json.load(open(f"{P}/{wj}.json")):
            RAW.append(dict(w=w["w"], s=round(t + o + w["s"], 3), e=round(t + o + w["e"], 3), sec=name))
    t += d + GAP
SPEECH_END = t - GAP
for i, c in enumerate(CLIPS): c["t1"] = CLIPS[i + 1]["t0"] if i + 1 < len(CLIPS) else 1e9
HOLD = 3.2
TOTAL = SPEECH_END + HOLD
NF = int(round(TOTAL * FPS))
SEC_END = {n: OFF[SECS[i + 1][0]] if i + 1 < len(SECS) else SPEECH_END for i, (n, _, _) in enumerate(SECS)}

def cue(sec, word, n=1):
    k = 0
    for w in RAW:
        if w["sec"] == sec and re.sub(r"[^\w$%₹]", "", w["w"].lower()).startswith(word.lower()):
            k += 1
            if k == n: return w["s"]
    raise KeyError((sec, word, n))

# ---------------- brand ----------------
ONYX = (10, 11, 10); EMERALD = (15, 61, 46); GOLD = (207, 165, 74); CHAMP = (230, 214, 168)
RED = (224, 71, 60)
def font(name, size, weight):
    f = ImageFont.truetype(f"{D}/fonts/{name}.ttf", size); f.set_variation_by_name(weight); return f
S = 2
def rgba(img): return np.asarray(img, np.float32)
def over(dst, src, x, y, alpha=1.0):
    if alpha <= 0: return
    h, w = src.shape[:2]
    x0, y0 = max(0, x), max(0, y); x1, y1 = min(W, x + w), min(H, y + h)
    if x1 <= x0 or y1 <= y0: return
    s = src[y0 - y:y1 - y, x0 - x:x1 - x]; a = s[..., 3:] / 255 * alpha
    dst[y0:y1, x0:x1] = dst[y0:y1, x0:x1] * (1 - a) + s[..., :3] * a
def down(img): return img.resize((img.width // S, img.height // S), Image.LANCZOS)
def ease(x): x = min(max(x, 0.0), 1.0); return x * x * (3 - 2 * x)
def fS(name, size, weight="Bold"):
    return font(name, size * S, weight.encode())

# ---------------- icons ----------------
BLOGO = None
def binance_logo(px):
    global BLOGO
    if BLOGO is None:
        im = Image.open(f"{D}/bn/src/binance_logo.webp").convert("RGB"); a = np.asarray(im).astype(np.float32)
        h, w = a.shape[:2]; yy, xx = np.mgrid[0:h, 0:w]; cx, cy, r = w / 2, h / 2, w * .289
        m = np.clip((r - np.sqrt((xx - cx) ** 2 + (yy - cy) ** 2)) / 2 + .5, 0, 1)
        BLOGO = Image.fromarray(np.dstack([a, m * 255]).astype(np.uint8), "RGBA").crop((int(cx - r - 2), int(cy - r - 2), int(cx + r + 2), int(cy + r + 2)))
    return BLOGO.resize((px, px), Image.LANCZOS)
def icon(kind, px, GOLD=GOLD):
    if kind == "binance": return binance_logo(px)
    im = Image.new("RGBA", (px * S, px * S), (0, 0, 0, 0)); d = ImageDraw.Draw(im); p = px * S; lw = max(3, p // 11)
    if kind == "ok":
        d.ellipse([lw, lw, p - lw, p - lw], outline=GOLD, width=lw)
        d.line([(p * .3, p * .52), (p * .45, p * .67), (p * .72, p * .36)], fill=GOLD, width=lw, joint="curve")
    elif kind == "x":
        d.ellipse([lw, lw, p - lw, p - lw], outline=RED, width=lw)
        d.line([(p * .34, p * .34), (p * .66, p * .66)], fill=RED, width=lw); d.line([(p * .66, p * .34), (p * .34, p * .66)], fill=RED, width=lw)
    elif kind == "dot": d.ellipse([p * .3, p * .3, p * .7, p * .7], fill=GOLD)
    elif kind == "arrow":
        d.line([(p * .2, p * .5), (p * .78, p * .5)], fill=GOLD, width=lw); d.line([(p * .55, p * .27), (p * .8, p * .5), (p * .55, p * .73)], fill=GOLD, width=lw, joint="curve")
    elif kind == "down":
        d.line([(p * .5, p * .18), (p * .5, p * .8)], fill=GOLD, width=lw); d.line([(p * .27, p * .56), (p * .5, p * .8), (p * .73, p * .56)], fill=GOLD, width=lw, joint="curve")
    elif kind == "up":
        d.line([(p * .5, p * .82), (p * .5, p * .2)], fill=GOLD, width=lw); d.line([(p * .27, p * .44), (p * .5, p * .2), (p * .73, p * .44)], fill=GOLD, width=lw, joint="curve")
    elif kind == "plane":
        d.polygon([(p * .12, p * .48), (p * .88, p * .18), (p * .66, p * .86), (p * .46, p * .62)], outline=GOLD, width=lw)
        d.line([(p * .46, p * .62), (p * .88, p * .18)], fill=GOLD, width=lw)
    elif kind == "cap":                                       # graduation cap (Academy)
        d.polygon([(p * .08, p * .40), (p * .5, p * .2), (p * .92, p * .40), (p * .5, p * .6)], outline=GOLD, width=lw)
        d.line([(p * .26, p * .5), (p * .26, p * .72)], fill=GOLD, width=lw); d.line([(p * .74, p * .5), (p * .74, p * .72)], fill=GOLD, width=lw)
        d.arc([p * .26, p * .56, p * .74, p * .86], 0, 180, fill=GOLD, width=lw)
    return down(im)

# ---------------- glass panel ----------------
def panel(title, items, n, width=720, title_icon=None, struck=False, sub=None):
    pad, row_h, gap, th = 34, 88, 14, 76 + (40 if sub else 0)
    hgt = pad + th + 10 + max(n, 0) * (row_h + gap) + pad - (gap if n else 10)
    im = Image.new("RGBA", (width * S, hgt * S), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle([0, 0, width * S - 1, hgt * S - 1], radius=28 * S, fill=ONYX + (214,), outline=GOLD + (230,), width=2 * S)
    x = pad
    if title_icon:
        im.alpha_composite(icon(title_icon, 54).resize((54 * S, 54 * S)), (pad * S, (pad + 8) * S)); x += 70
    d.text((x * S, (pad + 4) * S), title, font=fS("Cormorant", 54, "SemiBold"), fill=CHAMP)
    if sub: d.text((pad * S, (pad + 74) * S), sub, font=fS("Manrope", 28, "Medium"), fill=GOLD)
    fi = fS("Manrope", 37, "SemiBold")
    y = pad + th + 10
    for i, (ic, t) in enumerate(items):
        if i < n:
            d.rounded_rectangle([pad * S, y * S, (width - pad) * S, (y + row_h) * S], radius=18 * S, fill=EMERALD + (150,), outline=GOLD + (90,), width=S)
            im.alpha_composite(icon(ic, 46).resize((46 * S, 46 * S)), ((pad + 20) * S, (y + 21) * S))
            d.text(((pad + 84) * S, (y + 44) * S), t, font=fi, fill=CHAMP, anchor="lm")
            if struck and ic == "x":
                tw = fi.getlength(t); d.line([((pad + 84) * S, (y + 46) * S), ((pad + 84) * S + tw, (y + 46) * S)], fill=RED + (230,), width=3 * S)
        y += row_h + gap
    return rgba(down(im))
PANEL_CACHE = {}
def draw_panel(img, t, spec, x=None, y=150):
    width = spec.get("width", 720)
    if x is None: x = W - width - 60
    t_in, t_out = spec["t_in"], spec["t_out"]
    if not (t_in - .01 <= t < t_out + .3): return
    a = ease((t - t_in) / .3) * (1 - ease((t - t_out) / .3))
    n = sum(1 for c in spec["cues"] if t >= c)
    kw = {k: v for k, v in spec.items() if k in ("width", "title_icon", "struck", "sub")}
    def st(n):
        k = (spec["key"], n)
        if k not in PANEL_CACHE: PANEL_CACHE[k] = panel(spec["title"], spec["items"], n, **kw)
        return PANEL_CACHE[k]
    dx = int(40 * (1 - ease((t - t_in) / .35)))
    if n > 0 and t - spec["cues"][n - 1] < .25:
        f = ease((t - spec["cues"][n - 1]) / .25)
        over(img, st(n - 1), x + dx, y, a * (1 - f)); over(img, st(n), x + dx, y, a * f)
    else: over(img, st(n), x + dx, y, a)

# ---------------- pills, cards ----------------
def pill(text, ic=None, fill=ONYX + (220,), border=GOLD, fg=CHAMP, size=34, padx=30, h=76, weight="Bold"):
    fs = fS("Manrope", size, weight)
    tw = int(fs.getlength(text) / S); icw = int(h * .68) if ic else 0
    w = tw + 2 * padx + icw
    im = Image.new("RGBA", (w * S, h * S), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle([0, 0, w * S - 1, h * S - 1], radius=h * S // 2, fill=fill, outline=border + (240,), width=2 * S)
    if ic:
        q = int(h * .53); im.alpha_composite(icon(ic, q, GOLD=fg if fill[:3] == GOLD else GOLD).resize((q * S, q * S)), (padx * S, (h - q) // 2 * S))
    d.text(((padx + icw) * S, (h // 2) * S), text, font=fs, fill=fg, anchor="lm")
    return rgba(down(im))
PILL_CACHE = {}
def draw_pill(img, t, key, text, x, y, t_in, t_out, ic=None, center=False, **kw):
    if not (t_in - .01 <= t < t_out + .3): return
    if key not in PILL_CACHE: PILL_CACHE[key] = pill(text, ic, **kw)
    p = PILL_CACHE[key]; a = ease((t - t_in) / .3) * (1 - ease((t - t_out) / .3))
    if center: x = x - p.shape[1] // 2
    over(img, p, x, y + int(16 * (1 - ease((t - t_in) / .3))), a)

def card(lines, w, h, border=GOLD, fill=EMERALD + (235,), icons=()):
    """lines: [(font_name, size, weight, text, color, y_frac)]; icons: [(kind, px, x, y)]"""
    im = Image.new("RGBA", (w * S, h * S), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle([0, 0, w * S - 1, h * S - 1], radius=26 * S, fill=fill, outline=border + (240,), width=2 * S)
    for fn, sz, wt, txt, col, fy in lines:
        d.text((w * S // 2, int(h * S * fy)), txt, font=fS(fn, sz, wt), fill=col, anchor="mm", features=["lnum"] if fn == "Cormorant" else None)
    for kind, px, ix, iy in icons: im.alpha_composite(icon(kind, px).resize((px * S, px * S)), (ix * S, iy * S))
    return rgba(down(im))
CARD_CACHE = {}
def draw_card(img, t, key, lines, x, y, w, h, t_in, t_out, **kw):
    if not (t_in - .01 <= t < t_out + .3): return
    if key not in CARD_CACHE: CARD_CACHE[key] = card(lines, w, h, **kw)
    a = ease((t - t_in) / .35) * (1 - ease((t - t_out) / .3)); sc = .92 + .08 * ease((t - t_in) / .35)
    c = CARD_CACHE[key]
    if sc < .999:
        c = cv2.resize(c, (int(w * sc), int(h * sc)), interpolation=cv2.INTER_AREA); x += (w - c.shape[1]) // 2; y += (h - c.shape[0]) // 2
    over(img, c, x, y, a)

def text_img(txt, fn, size, weight, col, shadow=True):
    f = fS(fn, size, weight); tw = int(f.getlength(txt)); pad = 24 * S
    m = Image.new("L", (tw + 2 * pad, int(size * 1.5 * S) + 2 * pad), 0)
    ImageDraw.Draw(m).text((pad, pad), txt, font=f, fill=255, features=["lnum"] if fn == "Cormorant" else None)
    mm = np.asarray(m, np.float32) / 255
    sh = np.asarray(m.filter(ImageFilter.GaussianBlur(10 * S)), np.float32) / 255 * (.8 if shadow else 0)
    a = np.clip(mm + sh * (1 - mm), 0, 1)
    rgb = np.array(col, np.float32)[None, None] * (mm / np.maximum(a, 1e-4))[..., None]
    return rgba(down(Image.fromarray(np.dstack([rgb.clip(0, 255), a * 255]).astype(np.uint8), "RGBA")))

# ---------------- background, logo ----------------
yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
r = np.sqrt(((xx - W * .55) / (W * .62)) ** 2 + ((yy - H * .45) / (H * .8)) ** 2)
GLOW = np.clip(1 - r, 0, 1) ** 1.8
FS_BG = (np.array(ONYX, np.float32) + GLOW[..., None] * (np.array(EMERALD, np.float32) * 1.5 - np.array(ONYX, np.float32)))
_lines = Image.new("L", (W, H), 0); _d = ImageDraw.Draw(_lines)
for i in range(9): _d.line([(0, 160 + i * 100), (W, 160 + i * 100)], fill=10)
FS_BG = FS_BG + np.asarray(_lines, np.float32)[..., None] / 255 * np.array(GOLD, np.float32) * .5
DITHER = np.random.default_rng(3).uniform(-1, 1, (H, W, 1)).astype(np.float32)
_wm = Image.open(f"{D}/ganesha_wordmark_noir.png").convert("RGBA")
_wm = _wm.resize((250, round(_wm.height * 250 / _wm.width)), Image.LANCZOS)
LOGO = rgba(_wm)
_pl = Image.new("RGBA", ((250 + 48) * S, (_wm.height + 36) * S), (0, 0, 0, 0))
ImageDraw.Draw(_pl).rounded_rectangle([0, 0, _pl.width - 1, _pl.height - 1], radius=20 * S, fill=ONYX + (205,))
LOGO_PLATE = rgba(down(_pl))
def draw_logo(img, fullscreen):
    if not fullscreen: over(img, LOGO_PLATE, 40, 36)
    over(img, LOGO, 64, 54)
GRAD = np.clip((yy[..., None] - H * .68) / (H * .32), 0, 1) ** 1.4 * .62

# ---------------- subtitles ----------------
def merge(ws):
    out, i = [], 0
    def take(n, txt):
        nonlocal i
        out.append(dict(w=txt, s=ws[i]["s"], e=ws[i + n - 1]["e"])); i += n
    while i < len(ws):
        w = [x["w"] for x in ws[i:i + 4]] + [""] * 4
        low = [re.sub(r"[.,?]+$", "", x.lower()) for x in w]
        tail = lambda k: re.search(r"[.,?]*$", w[k]).group(0)
        if low[:3] == ["3", "lakh", "12,000"]: take(4, "₹3,12,075"); continue
        if low[1:3] == ["per", "cent"] and low[0] in ("one", "three"): take(3, ("1%" if low[0] == "one" else "3%") + tail(2)); continue
        if low[1] == "percent" and low[0] in ("one", "three"): take(2, ("1%" if low[0] == "one" else "3%") + tail(1)); continue
        if low[:2] == ["ten", "thousand"]: take(2, "10,000" + tail(1)); continue
        if low[:2] == ["pay", "in"]: take(2, "PayIn" + tail(1)); continue
        if low[:2] == ["pay", "ins"]: take(2, "PayIns" + tail(1)); continue
        x = w[0]
        x = re.sub(r"^Devan\w*", "Devansh", x)
        x = re.sub(r"^payouts", "PayOuts", x); x = re.sub(r"^payout", "PayOut", x)
        x = {"five": "5", "twenty": "20"}.get(x, x)
        take(1, x)
    return out
WORDS = merge(RAW)
SMALL = {"a", "an", "the", "to", "of", "and", "with", "by", "on", "in", "it", "is", "you", "your", "for", "who", "can", "are", "his", "as", "from", "at"}
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
KEY = re.compile(r"^(₹.*|\$.*|\d+%|\d[\d,]*|P2P\??|PayIns?|PayOuts?|UPI|KYB|commission|dashboard|manager|Binance|Bybit|Academy|merchants?|"
                 r"crores|free|description|Devansh|processing|deposit|disputes|spread|shift|Ganesha|Pay)$", re.I)
_sub_cache = {}
def sub_layer(ws):
    key = " ".join(ws)
    if key not in _sub_cache:
        f = fS("Manrope", 54, "Bold")
        sp = f.getlength(" "); widths = [f.getlength(w) for w in ws]; tw = int(sum(widths) + sp * (len(ws) - 1))
        pad = 30 * S; hh = 54 * S + 2 * pad + 20 * S
        m = Image.new("L", (tw + 2 * pad, hh), 0); col = Image.new("RGB", m.size, CHAMP)
        dm = ImageDraw.Draw(m); dc = ImageDraw.Draw(col); x = pad
        for w, wd in zip(ws, widths):
            dm.text((x, pad), w, font=f, fill=255); dc.text((x, pad), w, font=f, fill=GOLD if KEY.match(w.rstrip("?")) else CHAMP); x += wd + sp
        mm = np.asarray(m, np.float32) / 255
        sh = np.roll(np.asarray(m.filter(ImageFilter.GaussianBlur(9 * S)), np.float32) / 255, 3 * S, axis=0)
        a = np.clip(mm + sh * (1 - mm), 0, 1)
        rgb = np.asarray(col, np.float32) * (mm / np.maximum(a, 1e-4))[..., None]
        _sub_cache[key] = rgba(down(Image.fromarray(np.dstack([rgb.clip(0, 255), a * 255]).astype(np.uint8), "RGBA")))
    return _sub_cache[key]
def draw_subs(img, t):
    for s0, e0, ws in SUBS:
        if s0 <= t < e0:
            L = sub_layer(ws); h, w = L.shape[:2]
            over(img, L, (W - w) // 2, 1000 - h // 2 - 8, min(1, (t - s0) / .1 + .35)); return

# ---------------- video ----------------
class Reader:
    def __init__(self, src, w, h, t0=0.0, crop=None):
        self.w, self.h = w, h
        vf = (f"crop={crop}," if crop else "") + f"fps={FPS},scale={w}:{h}:flags=lanczos"
        self.p = subprocess.Popen(["ffmpeg", "-v", "error", "-ss", f"{t0:.3f}", "-i", src, "-vf", vf, "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], stdout=subprocess.PIPE)
        self.last = np.zeros((h, w, 3), np.uint8)
    def next(self):
        b = self.p.stdout.read(self.w * self.h * 3)
        if len(b) == self.w * self.h * 3: self.last = np.frombuffer(b, np.uint8).reshape(self.h, self.w, 3)
        return self.last

def clip_time(c, tl):
    """clean-TTS local time -> clip time (Wan stretched its own audio a few %, lips follow that)."""
    mt, mv = c["mt"], c["mv"]
    if tl <= mt[0]: v = mv[0] - (mt[0] - tl)
    elif tl >= mt[-1]: v = mv[-1] + (tl - mt[-1])
    else: v = float(np.interp(tl, mt, mv))
    return min(max(v, 0.0), c["vd"] - 1.5 / FPS)

class SeqReader(Reader):
    """monotone fractional-frame access with blending of the two neighbouring frames."""
    def __init__(self, src):
        super().__init__(src, W, H); self.i = -1; self.a = self.b = None
    def get(self, fi):
        need = int(math.floor(fi)) + 1
        while self.i < need:
            nf = self.next().astype(np.float32)
            self.a = nf if self.b is None else self.b; self.b = nf; self.i += 1
        fr = fi - (self.i - 1)
        if fr <= 0.02 or self.a is None: return self.a if self.a is not None else self.b
        if fr >= .98: return self.b
        return self.a * (1 - fr) + self.b * fr

def cam_view(frame, mode):
    """full: as shot · punch: 1.15x on the face · left: 1.25x shifted so Arnold sits left of centre (room for a panel)."""
    if mode == "full": return frame.astype(np.float32)
    if mode == "punch": x0, y0, cw = 150, 40, 1670
    else: x0, y0, cw = 384, 60, 1536
    ch = int(cw * 9 / 16)
    return cv2.resize(np.ascontiguousarray(frame[y0:y0 + ch, x0:x0 + cw]), (W, H), interpolation=cv2.INTER_LANCZOS4).astype(np.float32)

CIRCLE_D = 400
_cm = Image.new("L", (CIRCLE_D * S, CIRCLE_D * S), 0); ImageDraw.Draw(_cm).ellipse([0, 0, CIRCLE_D * S - 1, CIRCLE_D * S - 1], fill=255)
CMASK = np.asarray(_cm.resize((CIRCLE_D, CIRCLE_D), Image.LANCZOS), np.float32)[..., None] / 255
_ring = Image.new("RGBA", ((CIRCLE_D + 16) * S, (CIRCLE_D + 16) * S), (0, 0, 0, 0))
ImageDraw.Draw(_ring).ellipse([2 * S, 2 * S, (CIRCLE_D + 14) * S, (CIRCLE_D + 14) * S], outline=GOLD, width=4 * S)
RING = rgba(down(_ring))
def draw_circle(img, frame, cx, cy, a=1.0):
    side = 680; x0, y0 = 985 - side // 2, 30            # Arnold's head sits at ~(985, 300) in every clip
    crop = cv2.resize(np.ascontiguousarray(frame[y0:y0 + side, x0:x0 + side]), (CIRCLE_D, CIRCLE_D), interpolation=cv2.INTER_AREA).astype(np.float32)
    x, y = cx - CIRCLE_D // 2, cy - CIRCLE_D // 2
    reg = img[y:y + CIRCLE_D, x:x + CIRCLE_D]; m = CMASK * a
    img[y:y + CIRCLE_D, x:x + CIRCLE_D] = reg * (1 - m) + crop * m
    over(img, RING, x - 8, y - 8, a)

def framed(im, w, h, radius=30, border=3):
    """photo/screen into a rounded gold-framed card (RGBA float)."""
    im = im.convert("RGB").resize((w, h), Image.LANCZOS)
    m = Image.new("L", (w * S, h * S), 0); ImageDraw.Draw(m).rounded_rectangle([0, 0, w * S - 1, h * S - 1], radius=radius * S, fill=255)
    m = m.resize((w, h), Image.LANCZOS)
    out = Image.new("RGBA", (w, h)); out.paste(im, (0, 0)); out.putalpha(m)
    fr = Image.new("RGBA", (w * S, h * S), (0, 0, 0, 0))
    ImageDraw.Draw(fr).rounded_rectangle([0, 0, w * S - 1, h * S - 1], radius=radius * S, outline=GOLD + (255,), width=border * S)
    out.alpha_composite(down(fr)); return rgba(out)
def fade_in(img, layer, x, y, t, t_in, t_out, slide=30):
    if not (t_in - .01 <= t < t_out + .3): return
    a = ease((t - t_in) / .4) * (1 - ease((t - t_out) / .3))
    over(img, layer, x, y + int(slide * (1 - ease((t - t_in) / .4))), a)

# photos
_d1 = Image.open(f"{M}/dev1_clean.png")                      # domain + "Payin Blocked" banner blurred
DEV1 = framed(_d1.crop((0, 0, 1086, 1448)), 600, 800)
_d2 = Image.open(f"{M}/dev2.png").crop((530, 170, 1010, 1210))   # Devansh only (right person)
DEV2 = framed(_d2, 400, 867)

# phone with the live counter recording
PH_W, PH_H = 500, 784                                        # site header + live card, 1320x2070 -> 500x784
_pf = Image.new("RGBA", ((PH_W + 24) * S, (PH_H + 24) * S), (0, 0, 0, 0))
ImageDraw.Draw(_pf).rounded_rectangle([0, 0, _pf.width - 1, _pf.height - 1], radius=40 * S, fill=ONYX + (255,), outline=GOLD, width=3 * S)
PHONE = rgba(down(_pf))
_sm = Image.new("L", (PH_W * S, PH_H * S), 0); ImageDraw.Draw(_sm).rounded_rectangle([0, 0, PH_W * S - 1, PH_H * S - 1], radius=30 * S, fill=255)
SMASK = np.asarray(_sm.resize((PH_W, PH_H), Image.LANCZOS), np.float32)[..., None] / 255

# ---------------- scene plan ----------------
o = OFF
# hook
H_FS_END = cue("s1", "processing") - .1
# who we are / one round / devansh / table / counter / academy / cta
S4_FS = cue("s4", "then") - .15
S6_FS = cue("s6a", "on", 2) - .15
S6_CAM = cue("s6b", "cyber") - .15
S7_FS = cue("s7", "open") - .15
S8_FS = cue("s8", "start") - .15
END_FS = cue("s10", "already") - .15

def mode_at(t):
    """returns (fullscreen?, camera mode)"""
    if t < H_FS_END: return True, None
    if t < o["s2"]: return False, "full"
    if t < o["s3"]: return False, "punch"
    if t < o["s4"]: return True, None
    if t < S4_FS: return False, "left"
    if t < o["s5"]: return True, None
    if t < o["s6a"]: return True, None
    if t < S6_FS: return False, "full"
    if t < S6_CAM: return True, None
    if t < o["s7"]: return False, "left"
    if t < S7_FS: return False, "punch"
    if t < o["s8"]: return True, None
    if t < o["s10"]: return True, None
    if t < END_FS: return False, "punch"
    return True, None

PANELS = [
    dict(key="round", title="One round", title_icon="arrow", t_in=o["s4"] + .1, t_out=S4_FS - .05,
         items=[("dot", "Customer pays via UPI"), ("dot", "Money lands in your account"), ("ok", "You confirm in the dashboard"), ("down", "That’s a PayIn · 3%")],
         cues=[cue("s4", "customer"), cue("s4", "lands"), cue("s4", "confirm"), cue("s4", "3")]),
]

# exchange vs Ganesha Pay table
TB_X, TB_Y, TB_W = 560, 150, 1300
COLS = [(0, 250), (250, 480), (730, 570)]
ROWS = ["Counterparty", "Order flow", "Commission", "Disputes"]
CELLS = [(0, 1, "x", "Anonymous buyers", cue("s6a", "anonymous")), (0, 2, "ok", "KYB-checked merchants", cue("s6a", "kyb")),
         (1, 1, "x", "You hunt for orders", cue("s6a", "hunt")), (1, 2, "ok", "Assigned every shift", cue("s6a", "assigned")),
         (2, 1, "x", "Floating spread", cue("s6b", "floating")), (2, 2, "ok", "Fixed 3% + 1%", cue("s6b", "fixed")),
         (3, 1, "x", "Days of appeals", cue("s6b", "days")), (3, 2, "ok", "Manager handles them", cue("s6b", "manager"))]
ROW_H, HEAD_H = 130, 120
def table(n):
    hgt = HEAD_H + len(ROWS) * ROW_H + 20
    im = Image.new("RGBA", (TB_W * S, hgt * S), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle([0, 0, TB_W * S - 1, hgt * S - 1], radius=28 * S, fill=ONYX + (214,), outline=GOLD + (230,), width=2 * S)
    d.rounded_rectangle([COLS[2][0] * S + 10 * S, 10 * S, (TB_W - 10) * S, (hgt - 10) * S], radius=22 * S, fill=EMERALD + (170,))
    fh = fS("Manrope", 36, "Bold")
    im.alpha_composite(icon("binance", 46).resize((46 * S, 46 * S)), ((COLS[1][0] + 30) * S, 37 * S))
    d.text(((COLS[1][0] + 90) * S, 60 * S), "Exchange P2P", font=fh, fill=CHAMP, anchor="lm")
    d.text(((COLS[2][0] + 40) * S, 60 * S), "Ganesha Pay", font=fS("Cormorant", 50, "SemiBold"), fill=GOLD, anchor="lm")
    d.line([(30 * S, HEAD_H * S), ((TB_W - 30) * S, HEAD_H * S)], fill=GOLD + (140,), width=S)
    fl = fS("Manrope", 30, "Medium"); fc = fS("Manrope", 34, "SemiBold")
    shown = sorted(CELLS, key=lambda c: c[4])[:n]
    rows_on = {c[0] for c in shown}
    for ri, name in enumerate(ROWS):
        yc = HEAD_H + ri * ROW_H + ROW_H // 2
        if ri in rows_on: d.text((40 * S, yc * S), name, font=fl, fill=GOLD, anchor="lm")
        if ri > 0: d.line([(30 * S, (yc - ROW_H // 2) * S), ((TB_W - 30) * S, (yc - ROW_H // 2) * S)], fill=GOLD + (50,), width=S)
    for ri, ci, ic, txt, _ in shown:
        yc = HEAD_H + ri * ROW_H + ROW_H // 2; x = COLS[ci][0] + 36
        im.alpha_composite(icon(ic, 44).resize((44 * S, 44 * S)), (x * S, (yc - 22) * S))
        d.text(((x + 62) * S, yc * S), txt, font=fc, fill=CHAMP if ci == 2 else (190, 180, 150), anchor="lm")
    return rgba(down(im))
TABLE_CACHE = {}
def draw_table(img, t, t_in, t_out):
    if not (t_in - .01 <= t < t_out + .3): return
    a = ease((t - t_in) / .35) * (1 - ease((t - t_out) / .3))
    cues = sorted(c[4] for c in CELLS); n = sum(1 for c in cues if t >= c)
    def st(n):
        if n not in TABLE_CACHE: TABLE_CACHE[n] = table(n)
        return TABLE_CACHE[n]
    if n > 0 and t - cues[n - 1] < .25:
        f = ease((t - cues[n - 1]) / .25); over(img, st(n - 1), TB_X, TB_Y, a * (1 - f)); over(img, st(n), TB_X, TB_Y, a * f)
    else: over(img, st(n), TB_X, TB_Y, a)

# counter (hook)
CNT_T0, CNT_T1 = .15, 2.6
def rupee_fmt(v):
    s = str(int(v));
    if len(s) <= 3: return "₹" + s
    head, tail = s[:-3], s[-3:]
    parts = []
    while len(head) > 2: parts.insert(0, head[-2:]); head = head[:-2]
    if head: parts.insert(0, head)
    return "₹" + ",".join(parts + [tail])
_cnt_cache = {}
def counter_img(v):
    k = rupee_fmt(v)
    if k not in _cnt_cache: _cnt_cache[k] = text_img(k, "Manrope", 150, "Bold", GOLD)
    return _cnt_cache[k]
HK_LBL = text_img("commission · last 30 days", "Manrope", 40, "SemiBold", CHAMP)
HK_DIS = text_img("Individual result. Depends on volume.", "Manrope", 28, "Medium", (200, 190, 160))

# end card
_lb = Image.open(f"{D}/ganesha_wordmark_noir.png").convert("RGBA"); _lb = _lb.resize((440, round(_lb.height * 440 / _lb.width)), Image.LANCZOS)
def btn(label, text, ic):
    w, h = 820, 190
    return card([("Manrope", 30, "Bold", label, GOLD, .30), ("Manrope", 52, "Bold", text, CHAMP, .64)], w, h, icons=[(ic, 64, 44, 63)])
END_B1 = btn("ALREADY TRADING P2P", "Message a manager", "plane")
END_B2 = btn("NEW TO P2P", "Free Academy course", "cap")
END_LINK = pill("Links in the description", ic="down", fill=GOLD + (255,), border=GOLD, fg=ONYX, size=44, h=100, padx=46)
END_LOGO = rgba(_lb)

def end_group(show_b1, show_b2, t):
    gw = 820; parts_h = END_LOGO.shape[0] + 40 + 190 + 28 + 190 + 44 + 100
    g = np.zeros((parts_h, gw + 40, 4), np.float32)
    def put(layer, x, y, a=1.0):
        h, w = layer.shape[:2]; reg = g[y:y + h, x:x + w]
        la = layer[..., 3:] / 255 * a
        reg[..., :3] = reg[..., :3] * (1 - la) + layer[..., :3] * la
        reg[..., 3:] = reg[..., 3:] * (1 - la) + 255 * la
    put(END_LOGO, (gw + 40 - END_LOGO.shape[1]) // 2, 0)
    y = END_LOGO.shape[0] + 40
    put(END_B1, 20, y, show_b1); y += 190 + 28
    put(END_B2, 20, y, show_b2); y += 190 + 44
    put(END_LINK, (gw + 40 - END_LINK.shape[1]) // 2, y)
    return g

def scene_fs(img, t, frame):
    if t < H_FS_END:                                                     # hook: counter + Devansh dashboard photo
        p = ease((t - CNT_T0) / (CNT_T1 - CNT_T0)); v = 312075 * (1 - (1 - p) ** 3)
        c = counter_img(v); over(img, c, 600 - c.shape[1] // 2, 290, ease(t / .3))
        fade_in(img, HK_LBL, 600 - HK_LBL.shape[1] // 2, 520, t, .5, H_FS_END)
        draw_pill(img, t, "hk_dev", "Devansh · Mumbai", 600, 640, cue("s1", "devan") - .05, H_FS_END, center=True, ic="ok")
        fade_in(img, HK_DIS, 600 - HK_DIS.shape[1] // 2, 760, t, 1.2, H_FS_END, slide=0)
        fade_in(img, DEV1, 1200, 140, t, .25, H_FS_END)
    elif o["s3"] <= t < o["s4"]:                                          # who we are: merchant -> UPI -> you -> commission
        draw_circle(img, frame, 300, 560)
        draw_pill(img, t, "s3_t", "Ganesha Pay · P2P processing in India", 1200, 120, o["s3"] + .05, o["s4"] - .2, center=True, size=38, h=84)
        draw_pill(img, t, "s3_clean", "Clean merchant traffic", 1200, 230, cue("s3", "clean"), o["s4"] - .2, center=True, ic="ok", size=30, h=64, weight="SemiBold")
        bx, by, bw, bh, gapx = 600, 360, 360, 220, 60
        nodes = [("Verified", "merchant", "KYB-checked", cue("s3", "verified")), ("UPI", "payments", "accept & send", cue("s3", "upi")),
                 ("You", "agent", "own bank accounts", cue("s3", "agents"))]
        for k, (a1, a2, a3, c) in enumerate(nodes):
            draw_card(img, t, f"s3n{k}", [("Cormorant", 64, "SemiBold", a1, GOLD, .30), ("Manrope", 34, "Bold", a2, CHAMP, .58), ("Manrope", 26, "Medium", a3, (200, 190, 160), .80)],
                      bx + k * (bw + gapx), by, bw, bh, c, o["s4"] - .2)
            if k:
                ar = icon("arrow", 52); fade_in(img, rgba(ar), bx + k * (bw + gapx) - gapx + 4, by + bh // 2 - 26, t, c, o["s4"] - .2, slide=0)
        draw_card(img, t, "s3fix", [("Manrope", 38, "SemiBold", "Fixed commission on every operation", CHAMP, .5)], 600, 640, 1200, 110,
                  cue("s3", "fixed"), o["s4"] - .2, fill=ONYX + (230,), icons=[("ok", 50, 40, 30)])
    elif o["s4"] <= t < o["s5"]:                                          # rates
        draw_circle(img, frame, 300, 560)
        draw_pill(img, t, "s4_t", "Fixed commission", 1200, 110, S4_FS + .05, o["s5"] - .2, center=True, size=38, h=84)
        draw_card(img, t, "r1", [("Manrope", 36, "Bold", "PayIn", CHAMP, .2), ("Manrope", 130, "Bold", "3%", GOLD, .55), ("Manrope", 28, "Medium", "money in · you confirm", (200, 190, 160), .85)],
                  620, 240, 520, 380, S4_FS + .05, o["s5"] - .2, icons=[("down", 44, 40, 40)])
        draw_card(img, t, "r2", [("Manrope", 36, "Bold", "PayOut", CHAMP, .2), ("Manrope", 130, "Bold", "1%", GOLD, .55), ("Manrope", 28, "Medium", "approved withdrawal · you send", (200, 190, 160), .85)],
                  1260, 240, 520, 380, cue("s4", "payout"), o["s5"] - .2, icons=[("up", 44, 40, 40)])
        draw_pill(img, t, "s4_usd", "Commission paid daily in USD", 1200, 680, cue("s4", "commission"), o["s5"] - .2, center=True, ic="ok", size=40, h=92)
    elif o["s5"] <= t < o["s6a"]:                                         # Devansh: Bybit -> Ganesha Pay
        e = o["s6a"] - .2
        fade_in(img, DEV2, 150, 110, t, o["s5"] + .05, e)
        draw_pill(img, t, "s5_name", "Devansh · Mumbai", 350, 900, o["s5"] + .3, e, center=True, size=30, h=64)
        draw_pill(img, t, "s5_t", "From Bybit P2P  →  Ganesha Pay", 1200, 130, cue("s5", "bybit"), e, center=True, size=42, h=96)
        draw_pill(img, t, "s5_dep", "$2,000 working deposit", 1200, 260, cue("s5", "$2"), e, center=True, ic="dot", size=34, h=76)
        draw_panel(img, t, dict(key="bef", title="Before", sub="Bybit P2P", t_in=cue("s5", "but"), t_out=e, struck=True, width=500,
                                items=[("x", "Adjusting offers"), ("x", "Waiting for matches")], cues=[cue("s5", "adjusting"), cue("s5", "waiting")]), x=640, y=380)
        draw_panel(img, t, dict(key="now", title="Now", sub="Ganesha Pay", t_in=cue("s5", "now"), t_out=e, width=650,
                                items=[("ok", "Requests in his dashboard")], cues=[cue("s5", "requests")]), x=1180, y=380)
    elif S6_FS <= t < S6_CAM:                                             # exchange vs Ganesha Pay
        draw_circle(img, frame, 280, 560)
        draw_table(img, t, S6_FS + .05, S6_CAM - .05)
    elif S7_FS <= t < o["s8"]:                                            # live counter
        draw_circle(img, frame, 300, 560)
        e = o["s8"] - .2
        a = ease((t - S7_FS) / .4) * (1 - ease((t - e) / .3)); px, py = 680, 140
        if a > 0:
            lay = img.copy(); over(lay, PHONE, px - 12, py - 12)
            scr = cv2.resize(frame_counter(t), (PH_W, PH_H), interpolation=cv2.INTER_AREA).astype(np.float32)
            reg = lay[py:py + PH_H, px:px + PH_W]; lay[py:py + PH_H, px:px + PH_W] = reg * (1 - SMASK) + scr * SMASK
            img[:] = img * (1 - a) + lay * a
        draw_pill(img, t, "s7_a", "Live counter on our website", 1260, 300, cue("s7", "counter"), e, ic="dot", size=34, h=80)
        draw_pill(img, t, "s7_b", "Already in crores today", 1260, 420, cue("s7", "crores"), e, ic="ok", size=34, h=80)
        draw_pill(img, t, "s7_c", "Grow: add accounts & shifts", 1260, 540, cue("s7", "grow"), e, ic="arrow", size=34, h=80)
    elif o["s8"] <= t < o["s10"]:                                         # Academy (clip s8 has a re-arranged set: circle only)
        draw_circle(img, frame, 300, 560)
        e = o["s10"] - .2
        draw_pill(img, t, "s8_q", "New to P2P?", 1210, 110, o["s8"] + .05, S8_FS, center=True, ic="cap", size=44, h=100)
        draw_pill(img, t, "s8_t", "Ganesha Pay Academy", 1210, 110, S8_FS + .05, e, center=True, ic="cap", size=44, h=100)
        x = 640
        for k, (txt, c) in enumerate([("No experience needed", cue("s8", "experience")), ("Free", cue("s8", "free")), ("~20 min a day", cue("s8", "twenty"))]):
            draw_pill(img, t, f"s8_c{k}", txt, x, 250, c, e, ic="ok", size=32, h=72); x += PILL_CACHE.get(f"s8_c{k}", pill(txt, "ok", size=32, h=72)).shape[1] + 24
        draw_panel(img, t, dict(key="acad", title="You’ll learn", t_in=cue("s8", "youll") - .05, t_out=e, width=1140,
                                items=[("down", "PayIns and PayOuts"), ("ok", "How to keep your accounts safe"), ("cap", "Certificate: Payment Processing Manager")],
                                cues=[cue("s8", "pay", 2), cue("s8", "keep"), cue("s8", "certified")]), x=640, y=360)
    if t >= END_FS:                                                        # CTA end card
        a = ease((t - END_FS) / .4); k = ease((t - SPEECH_END) / .6)
        if t < SPEECH_END + .3: draw_circle(img, frame, 300, 560, a=a * (1 - ease((t - SPEECH_END) / .3)))
        b1 = ease((t - cue("s10", "already")) / .35); b2 = ease((t - cue("s10", "new")) / .35)
        key = (round(b1, 2), round(b2, 2))
        g = END_CACHE.get(key)
        if g is None: g = END_CACHE.setdefault(key, end_group(b1, b2, t))
        sc = .9 + .1 * k; cx = W // 2 + int(180 * (1 - k))
        if sc < .999: g = cv2.resize(g, (int(g.shape[1] * sc), int(g.shape[0] * sc)), interpolation=cv2.INTER_AREA)
        over(img, g, cx - g.shape[1] // 2, (H - g.shape[0]) // 2 - 50, a)
END_CACHE = {}

COUNTER = None
def frame_counter(t):
    global COUNTER
    if COUNTER is None:
        COUNTER = Reader(f"{M}/counter.mp4", PH_W, PH_H, t0=1.0, crop="1320:2070:0:230")
    return COUNTER.next()

def cam_overlays(img, t):
    if H_FS_END <= t < o["s2"]:                                              # hook on camera
        draw_pill(img, t, "hk_n1", "Not trading", 1470, 590, cue("s1", "not", 1), o["s2"] - .2, ic="x", size=32, h=72)
        draw_pill(img, t, "hk_n2", "Not guessing prices", 1470, 680, cue("s1", "not", 2), o["s2"] - .2, ic="x", size=32, h=72)
    if o["s2"] <= t < o["s3"]:                                               # intro
        draw_card(img, t, "lt", [("Cormorant", 64, "SemiBold", "Arnold", GOLD, .38), ("Manrope", 30, "SemiBold", "Manager · Ganesha Pay", CHAMP, .74)],
                  80, 700, 480, 150, o["s2"] + .2, cue("s2", "in") - .1 + 1.2, fill=ONYX + (225,))
        for k, (txt, c) in enumerate([("01  Who we are", cue("s2", "who")), ("02  How it works", cue("s2", "how", 1)), ("03  How to start", cue("s2", "how", 2))]):
            draw_pill(img, t, f"ch{k}", txt, 1560, 600 + k * 88, c, o["s3"] - .2, size=30, h=70)
    for sp in PANELS: draw_panel(img, t, sp)
    if S6_CAM <= t < o["s7"]:                                                # complaints stat
        draw_card(img, t, "cyb", [("Manrope", 32, "SemiBold", "Cyber complaints", CHAMP, .16), ("Manrope", 112, "Bold", "~5", GOLD, .42),
                                  ("Manrope", 32, "SemiBold", "in every 10,000 transactions", CHAMP, .68), ("Manrope", 28, "Medium", "≈ 0.05%", (200, 190, 160), .86)],
                  1180, 190, 640, 420, cue("s6b", "cyber"), o["s7"] - .15, fill=ONYX + (240,))
    if o["s7"] <= t < S7_FS:
        draw_pill(img, t, "s7_v", "Real volume", 1570, 610, cue("s7", "volume"), S7_FS, ic="ok", size=32, h=74)

# ---------------- render ----------------
def frame_at(t, frame):
    fs, cm = mode_at(t)
    if fs:
        img = FS_BG.copy(); scene_fs(img, t, frame)
    else:
        img = cam_view(frame, cm) * (1 - GRAD)
        cam_overlays(img, t)
    draw_logo(img, fs)
    if t < SPEECH_END + .05: draw_subs(img, t)
    return img, (fs, cm)

def main():
    enc = None
    if not PREVIEW:
        enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                                "-c:v", "libx264", "-preset", "medium", "-crf", "17", "-pix_fmt", "yuv420p", OUT], stdin=subprocess.PIPE)
    targets = sorted(int(round(x * FPS)) for x in PREVIEW) if PREVIEW else None
    ci, rd = -1, None; prev_img = prev_sig = fade_from = None; fade_t0 = -1
    for j in range(NF):
        t = j / FPS
        k = max(i for i, c in enumerate(CLIPS) if c["t0"] <= t + 1e-6)
        if targets is not None:
            if j not in targets:
                if j > max(targets): break
                continue
            c = CLIPS[k]; rr = Reader(c["f"], W, H, t0=clip_time(c, t - c["t0"])); frame = rr.next(); rr.p.kill()
        else:
            if k != ci: ci = k; rd = SeqReader(CLIPS[k]["f"])
            frame = rd.get(clip_time(CLIPS[k], t - CLIPS[k]["t0"]) * FPS)
        img, sig = frame_at(t, frame)
        if targets is None:
            if prev_sig is not None and sig != prev_sig: fade_from, fade_t0 = prev_img, t
            if fade_from is not None and t - fade_t0 < .24:
                q = ease((t - fade_t0) / .24); img = fade_from * (1 - q) + img * q
            prev_img, prev_sig = img, sig
        out = (img + DITHER).clip(0, 255).astype(np.uint8)
        if enc: enc.stdin.write(out.tobytes())
        else: Image.fromarray(out).save(f"{sys.argv[4] if len(sys.argv) > 4 else OUT}/f{t:07.2f}.png")
        if j % 300 == 0: print(j, NF, flush=True)
    if enc: enc.stdin.close(); enc.wait()

if __name__ == "__main__":
    print("sections", {k: round(v, 2) for k, v in OFF.items()}, "speech end", round(SPEECH_END, 2), "total", round(TOTAL, 2))
    main()
