"""P2P Myth Check #1 — Ganesha Pay Noir montage (3 myths about P2P processing in India).
Quote cards with a MYTH stamp (thud + frame shake), red/green flag panels, Arnold full frame / punch-in / left-shift
or in a circle, live counter, Devansh case, two-button CTA.  usage: myth_render.py out.mp4 [--preview t1,t2,... outdir]"""
import sys, json, re, math, subprocess, numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont, ImageFilter

D = "/tmp/claude-0/-home-user/7c5690c1-77ca-5715-b441-4cc8e349293a/scratchpad"
Y = f"{D}/myth"; P = f"{Y}/parts"; M = f"{D}/yt/mat"
OUT = sys.argv[1]
PREVIEW = [float(x) for x in sys.argv[3].split(",")] if len(sys.argv) > 3 and sys.argv[2] == "--preview" else None
W, H, FPS = 1920, 1080, 30

# ---------------- timeline: voice sections and their video clips ----------------
def dur(f): return float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", f]))
GAP = 0.12
# section: (name, audio file, [(clip file, offset inside the section audio, word json)])
SECS = [("m1", "m1", [("wan_m1", 0, "m1")]),
        ("m2", "m2", [("wan_m2", 0, "m2")]),
        ("m3", "m3", [("wan_m31", 0, "m31"), ("wan_m32", 13.429, "m32"), ("wan_m33", 23.71, "m33")]),
        ("m4", "m4", [("wan_m41", 0, "m41"), ("wan_m42", 13.112, "m42")]),
        ("m5", "m5", [("wan_m51", 0, "m51"), ("wan_m52", 8.347, "m52")]),
        ("m6", "m6", [("wan_m61", 0, "m61"), ("wan_m62", 10.862, "m62")])]
GAPS = {"m3": 1.5, "m4": 1.5, "m5": 1.5}               # stamp beats after each myth
OFF, CLIPS, RAW = {}, [], []
t = 0.0
for name, af, clips in SECS:
    OFF[name] = t; d = dur(f"{P}/{af}.mp3")
    for k, (cf, o, wj) in enumerate(clips):
        mp = json.load(open(f"{P}/map_{wj}.json"))
        CLIPS.append(dict(f=f"{P}/{cf}.mp4", t0=t + o, sec=name, mt=[p[0] for p in mp], mv=[p[1] for p in mp], vd=dur(f"{P}/{cf}.mp4")))
        for w in json.load(open(f"{P}/{wj}.json")):
            RAW.append(dict(w=w["w"], s=round(t + o + w["s"], 3), e=round(t + o + w["e"], 3), sec=name))
    SPEECH_ENDS = globals().setdefault('SPEECH_ENDS', {}); SPEECH_ENDS[name] = t + d
    t += d + GAPS.get(name, GAP)
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
        if low[1:3] == ["lakh", "rupees"]: take(3, f"₹{low[0]} lakh"); continue
        if low[:2] == ["third", "party"]: take(2, "third-party"); continue
        if low[0] == "myth" and low[1] in ("one", "two", "three"): take(2, "Myth " + {"one": "1", "two": "2", "three": "3"}[low[1]] + tail(1)); continue
        if low[1:3] == ["per", "cent"] and low[0] in ("one", "three"): take(3, ("1%" if low[0] == "one" else "3%") + tail(2)); continue
        if low[1] == "percent" and low[0] in ("one", "three"): take(2, ("1%" if low[0] == "one" else "3%") + tail(1)); continue
        if low[:2] == ["ten", "thousand"]: take(2, "10,000" + tail(1)); continue
        if low[:2] == ["pay", "in"]: take(2, "PayIn" + tail(1)); continue
        if low[:2] == ["pay", "ins"]: take(2, "PayIns" + tail(1)); continue
        x = w[0]
        x = re.sub(r"^Devan\w*", "Devansh", x)
        x = re.sub(r"^payouts", "PayOuts", x); x = re.sub(r"^payout", "PayOut", x); x = re.sub(r"^pay-ins", "PayIns", x)
        x = re.sub(r"^telegram", "Telegram", x); x = re.sub(r"^academy", "Academy", x)
        x = {"five": "5", "twenty": "20", "gray,": "grey,", "gray": "grey"}.get(x, x)
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
                 r"crores|free|description|Devansh|processing|deposit|disputes|spread|shifts?|Ganesha|Pay|Myth|myths|scam|frozen|Telegram|verified|limits|real|percentages|green|flags|PayIns|PayOuts)$", re.I)
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


# ---------------- Myth Check: quote cards + stamp ----------------
o = OFF; SE = SPEECH_ENDS
STAMPS = []                                   # (time, kind) — for the shake and the thud SFX

def wrap(txt, f, maxw):
    words, lines, cur = txt.split(), [], ""
    for w in words:
        nxt = (cur + " " + w).strip()
        if f.getlength(nxt) > maxw and cur: lines.append(cur); cur = w
        else: cur = nxt
    return lines + [cur]

def quote_card(label, txt, w, h, size=64):
    im = Image.new("RGBA", (w * S, h * S), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle([0, 0, w * S - 1, h * S - 1], radius=30 * S, fill=ONYX + (232,), outline=GOLD + (235,), width=2 * S)
    fq = fS("Cormorant", 220, "SemiBold"); d.text((34 * S, -40 * S), "“", font=fq, fill=GOLD + (200,))
    if label:
        fl = fS("Manrope", 26, "Bold"); d.text((w * S // 2, 52 * S), label, font=fl, fill=GOLD, anchor="mm")
    f = fS("CormorantItalic", size, "SemiBold Italic")
    lines = wrap(txt, f, (w - 150) * S); lh = size * 1.18 * S
    y0 = h * S / 2 - lh * len(lines) / 2 + lh / 2 + (18 * S if label else 0)
    for k, ln in enumerate(lines): d.text((w * S // 2, y0 + k * lh), ln, font=f, fill=CHAMP, anchor="mm", features=["lnum"])
    return rgba(down(im))

def _stamp(text, px=118):
    f = fS("Manrope", px, "ExtraBold"); tw = f.getlength(text); pad = 46 * S
    w, h = int(tw + 2 * pad), int(px * S * 1.0 + 2 * pad * .8)
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle([4 * S, 4 * S, w - 4 * S, h - 4 * S], radius=18 * S, outline=RED + (240,), width=9 * S)
    d.rounded_rectangle([20 * S, 20 * S, w - 20 * S, h - 20 * S], radius=10 * S, outline=RED + (200,), width=3 * S)
    d.text((w // 2, h // 2 + 4 * S), text, font=f, fill=RED + (245,), anchor="mm")
    # a little ink texture so it reads as a stamp, not a button
    a = np.asarray(im, np.float32); rng = np.random.default_rng(7)
    a[..., 3] *= np.clip(.78 + .3 * rng.random(a.shape[:2]), 0, 1)
    im = Image.fromarray(a.astype(np.uint8), "RGBA").rotate(9, resample=Image.BICUBIC, expand=True)
    return rgba(down(im))
STAMP_MYTH = _stamp("MYTH"); STAMP_Q = _stamp("MYTH?", 96)

def draw_stamp(img, st, cx, cy, t, t0, scale=1.0, sound=True):
    if t < t0: return
    k = t - t0; sc = scale * (1 + .75 * (1 - ease(k / .13))); a = min(1, k / .05)
    lay = st if abs(sc - 1) < .003 else cv2.resize(st, (max(2, int(st.shape[1] * sc)), max(2, int(st.shape[0] * sc))), interpolation=cv2.INTER_AREA)
    over(img, lay, cx - lay.shape[1] // 2, cy - lay.shape[0] // 2, a)

QC = {}
def qcard(key, *a, **kw):
    if key not in QC: QC[key] = quote_card(*a, **kw)
    return QC[key]

HOOK_CARDS = [("“₹2 lakh a month?” Impossible.", "₹2 lakh a month? Impossible.", cue("m1", "2"), cue("m1", "impossible") + .55),
              ("Your bank account will get frozen.", "Your bank account will get frozen.", cue("m1", "your"), cue("m1", "frozen") + .5),
              ("It's a scam.", "It's a scam.", cue("m1", "and"), cue("m1", "scam") + .45)]
MYTHS = {"m3": ("MYTH 1", "P2P processing is a scam."), "m4": ("MYTH 2", "Your bank account will get frozen."),
         "m5": ("MYTH 3", "You can't make real money with P2P.")}
TITLE_END = {"m3": cue("m3", "heres") - .12, "m4": cue("m4", "freezes") - .12, "m5": cue("m5", "on") - .12}
for k in MYTHS: STAMPS.append((SE[k] + .25, "myth"))
for _, _, _, ts in HOOK_CARDS: STAMPS.append((ts, "q"))
H_CAM = cue("m1", "thats") - .1                      # hook: cards full screen, then Arnold
CTA_RECAP_END = cue("m6", "thats") - .12
END_FS = cue("m6", "if", 2) - .12
M3_GREEN = cue("m3", "a", 3) - .1                     # "A real platform shows green flags"
M4_FS = cue("m4", "in", 1) - .12                      # "In Ganesha Pay, payments come only…"
M5_CAM = cue("m5", "its", 1) - .12                   # "It's real work"

def mode_at(t):
    if any(SE[k] <= t < SE[k] + GAPS[k] for k in GAPS): return True, None
    if t < H_CAM: return True, None
    if t < o["m2"]: return False, "full"
    if t < o["m3"]: return False, "punch"
    if t < TITLE_END["m3"]: return True, None
    if t < M3_GREEN: return False, "left"
    if t < TITLE_END["m4"]: return True, None
    if t < M4_FS: return False, "left"
    if t < M5_CAM: return True, None
    if t < o["m6"]: return False, "punch"
    if t < CTA_RECAP_END: return True, None
    if t < END_FS: return False, "left"
    return True, None

# ---------------- end card ----------------
_lb = Image.open(f"{D}/ganesha_wordmark_noir.png").convert("RGBA"); _lb = _lb.resize((440, round(_lb.height * 440 / _lb.width)), Image.LANCZOS)
def btn(label, text, ic):
    return card([("Manrope", 30, "Bold", label, GOLD, .30), ("Manrope", 52, "Bold", text, CHAMP, .64)], 820, 190, icons=[(ic, 64, 44, 63)])
END_B1 = btn("NEW TO P2P", "Free Academy course", "cap")
END_B2 = btn("ALREADY TRADING P2P", "Message a manager", "plane")
END_LINK = pill("Links in the description", ic="down", fill=GOLD + (255,), border=GOLD, fg=ONYX, size=44, h=100, padx=46)
END_LOGO = rgba(_lb)
END_CACHE = {}
def end_group(b1, b2):
    gw = 860; gh = END_LOGO.shape[0] + 40 + 190 + 28 + 190 + 44 + 100
    g = np.zeros((gh, gw, 4), np.float32)
    def put(layer, x, y, a=1.0):
        h, w = layer.shape[:2]; reg = g[y:y + h, x:x + w]; la = layer[..., 3:] / 255 * a
        reg[..., :3] = reg[..., :3] * (1 - la) + layer[..., :3] * la; reg[..., 3:] = reg[..., 3:] * (1 - la) + 255 * la
    put(END_LOGO, (gw - END_LOGO.shape[1]) // 2, 0); y = END_LOGO.shape[0] + 40
    put(END_B1, 20, y, b1); y += 218; put(END_B2, 20, y, b2); y += 234
    put(END_LINK, (gw - END_LINK.shape[1]) // 2, y)
    return g

COUNTER = None
def frame_counter():
    global COUNTER
    if COUNTER is None: COUNTER = Reader(f"{M}/counter.mp4", PH_W, PH_H, t0=1.0, crop="1320:2070:0:230")
    return COUNTER.next()
def rupee_fmt(v):
    s = str(int(v)); head, tail = s[:-3], s[-3:]; parts = []
    while len(head) > 2: parts.insert(0, head[-2:]); head = head[:-2]
    if head: parts.insert(0, head)
    return "₹" + ",".join(parts + [tail]) if parts else "₹" + s
_cnt = {}
def counter_img(v):
    k = rupee_fmt(v)
    if k not in _cnt: _cnt[k] = text_img(k, "Manrope", 150, "Bold", GOLD)
    return _cnt[k]
DISCL = text_img("Depends on volume. Not guaranteed.", "Manrope", 28, "Medium", (200, 190, 160))
DEV_SMALL = framed(Image.open(f"{M}/dev1_clean.png"), 360, 480)

def myth_title(img, t, sec, t_in, t_out, stamp_t=None):
    lab, txt = MYTHS[sec]
    c = qcard(sec, lab, txt, 1300, 400, 76)
    a = ease((t - t_in) / .35) * (1 - ease((t - t_out) / .3)) if t_out else ease((t - t_in) / .35)
    sc = .94 + .06 * ease((t - t_in) / .35)
    lay = c if sc > .999 else cv2.resize(c, (int(c.shape[1] * sc), int(c.shape[0] * sc)), interpolation=cv2.INTER_AREA)
    over(img, lay, (W - lay.shape[1]) // 2, 300 + (c.shape[0] - lay.shape[0]) // 2, a)
    if stamp_t is not None: draw_stamp(img, STAMP_MYTH, 1420, 640, t, stamp_t)

def scene_fs(img, t, frame):
    if t < H_CAM:                                                          # hook: three quote cards, MYTH? stamps
        for k, (key, txt, tin, ts) in enumerate(HOOK_CARDS):
            if t < tin - .01: continue
            c = qcard("h" + str(k), None, txt, 540, 360, 54); a = ease((t - tin) / .3)
            x = 110 + k * 580; y = 300 + int(40 * (1 - ease((t - tin) / .35)))
            over(img, c, x, y, a); draw_stamp(img, STAMP_Q, x + 360, y + 290, t, ts, scale=.72)
        draw_pill(img, t, "h_t", "P2P MYTH CHECK", W // 2, 150, .1, H_CAM, center=True, size=44, h=100)
    elif o["m3"] <= t < TITLE_END["m3"] or o["m4"] <= t < TITLE_END["m4"] or o["m5"] <= t < TITLE_END["m5"]:
        sec = "m3" if t < o["m4"] else "m4" if t < o["m5"] else "m5"
        myth_title(img, t, sec, o[sec] - .05, TITLE_END[sec])
    elif any(SE[s] <= t < SE[s] + GAPS[s] for s in ("m3", "m4", "m5")):  # stamp beat
        sec = next(s for s in ("m3", "m4", "m5") if SE[s] <= t < SE[s] + GAPS[s])
        myth_title(img, t, sec, SE[sec], None, stamp_t=SE[sec] + .25)
    elif M3_GREEN <= t < SE["m3"]:                                          # green flags
        dv0, dv1 = cue("m3", "real", 3) - .1, cue("m3", "and", 3) - .1    # "Real agents … like Devansh"
        if dv0 <= t < dv1:
            q = ease((t - dv0) / .3) * (1 - ease((t - dv1 + .3) / .3))
            draw_circle(img, frame, 300, 560, a=1 - q); fade_in(img, DEV_SMALL, 120, 300, t, dv0, dv1 - .3)
            draw_pill(img, t, "dev_n", "Devansh · Mumbai", 300, 800, dv0 + .2, dv1 - .3, center=True, size=28, h=60)
        else: draw_circle(img, frame, 300, 560)
        rows = [("ok", "Every merchant passes KYB", cue("m3", "every")), ("ok", "Fixed rates: 3% + 1%", cue("m3", "rates")),
                ("ok", "Live volume on the website", cue("m3", "our")), ("ok", "A real manager on Telegram", cue("m3", "manager")),
                ("ok", "Real agent results", cue("m3", "agents")), ("cap", "Free Academy before you start", cue("m3", "learn"))]
        draw_panel(img, t, dict(key="green", title="Green flags", sub="Ganesha Pay", t_in=M3_GREEN + .05, t_out=SE["m3"] - .05, width=1140,
                                items=[(a, b) for a, b, _ in rows], cues=[c for _, _, c in rows]), x=640, y=110)
    elif M4_FS <= t < SE["m4"]:                                            # verified merchants, 0.05%
        draw_circle(img, frame, 300, 560); e = SE["m4"] - .05
        draw_pill(img, t, "m4_t", "In Ganesha Pay: verified merchants only", 1210, 120, M4_FS + .05, e, center=True, ic="ok", size=38, h=88)
        draw_card(img, t, "m4_c", [("Manrope", 32, "SemiBold", "Cyber complaints", CHAMP, .17), ("Manrope", 120, "Bold", "~5", GOLD, .45),
                                   ("Manrope", 32, "SemiBold", "in every 10,000 transactions", CHAMP, .72), ("Manrope", 28, "Medium", "≈ 0.05%", (200, 190, 160), .88)],
                  660, 250, 640, 440, cue("m4", "cyber"), e)
        draw_pill(img, t, "m4_l", "You work within your limits", 1360, 330, cue("m4", "limits"), e, ic="dot", size=32, h=76)
        draw_pill(img, t, "m4_m", "Disputes: your manager", 1360, 440, cue("m4", "manager"), e, ic="ok", size=32, h=76)
    elif TITLE_END["m5"] <= t < M5_CAM:                                     # up to ₹4 lakh
        draw_circle(img, frame, 300, 560); e = M5_CAM - .05; c0 = TITLE_END["m5"] + .05
        draw_pill(img, t, "m5_t", "Average Ganesha Pay agent", 1210, 140, c0, e, center=True, size=38, h=88)
        p = ease((t - cue("m5", "4")) / 1.2) if t >= cue("m5", "4") else 0
        if t >= c0:
            v = 400000 * (1 - (1 - p) ** 3); ci = counter_img(v)
            lab = text_img("up to", "Manrope", 40, "SemiBold", CHAMP); over(img, lab, 1210 - lab.shape[1] // 2, 260, ease((t - c0) / .3))
            over(img, ci, 1210 - ci.shape[1] // 2, 320, ease((t - c0) / .3))
            ml = text_img("a month", "Manrope", 40, "SemiBold", CHAMP); over(img, ml, 1210 - ml.shape[1] // 2, 540, ease((t - c0) / .3))
            over(img, DISCL, 1210 - DISCL.shape[1] // 2, 610, ease((t - c0 - .6) / .4))
        draw_pill(img, t, "m5_more", "More? Depends on your bank accounts", 1210, 720, cue("m5", "and"), e, center=True, ic="arrow", size=36, h=86)
    elif o["m6"] <= t < CTA_RECAP_END:                                      # recap: all three stamped
        for k, (key, txt, tin, ts) in enumerate(HOOK_CARDS):
            c = qcard("h" + str(k), None, txt, 540, 360, 54); x = 110 + k * 580
            over(img, c, x, 300, ease((t - o["m6"]) / .3))
            draw_stamp(img, STAMP_MYTH, x + 360, 590, t, o["m6"] + .15 + k * .22, scale=.72)
    if t >= END_FS:                                                         # CTA end card
        a = ease((t - END_FS) / .4); k = ease((t - SPEECH_END) / .6)
        if t < SPEECH_END + .3: draw_circle(img, frame, 300, 560, a=a * (1 - ease((t - SPEECH_END) / .3)))
        b1 = 1.0; b2 = ease((t - cue("m6", "message")) / .35)
        key = round(b2, 2); g = END_CACHE.get(key)
        if g is None: g = END_CACHE.setdefault(key, end_group(b1, b2))
        sc = .9 + .1 * k; cx = W // 2 + int(180 * (1 - k))
        if sc < .999: g = cv2.resize(g, (int(g.shape[1] * sc), int(g.shape[0] * sc)), interpolation=cv2.INTER_AREA)
        over(img, g, cx - g.shape[1] // 2, (H - g.shape[0]) // 2 - 50, a)

def cam_overlays(img, t):
    if H_CAM <= t < o["m2"]:
        draw_card(img, t, "ep", [("Manrope", 28, "Bold", "EPISODE 1", GOLD, .28), ("Cormorant", 66, "SemiBold", "P2P Myth Check", CHAMP, .66)],
                  1330, 590, 520, 160, H_CAM + .1, o["m2"] - .1, fill=ONYX + (230,))
    if o["m2"] <= t < o["m3"]:
        draw_card(img, t, "lt", [("Cormorant", 64, "SemiBold", "Arnold", GOLD, .38), ("Manrope", 30, "SemiBold", "Manager · Ganesha Pay", CHAMP, .74)],
                  80, 700, 480, 150, o["m2"] + .2, cue("m2", "every") + 1.0, fill=ONYX + (225,))
        c = cue("m2", "these")
        for k, txt in enumerate(["1  “It’s a scam”", "2  “Bank freeze”", "3  “No real money”"]):
            draw_pill(img, t, f"ch{k}", txt, 1500, 590 + k * 88, c + k * .35, o["m3"] - .15, size=30, h=70)
    if TITLE_END["m3"] <= t < M3_GREEN:                                     # red flags
        rows = [("x", "A stranger’s DM on Telegram", cue("m3", "stranger")), ("x", "Huge percentages", cue("m3", "huge")),
                ("x", "Deposit… then silence", cue("m3", "disappears"))]
        draw_panel(img, t, dict(key="red", title="Red flags", t_in=TITLE_END["m3"] + .05, t_out=M3_GREEN - .05, width=720,
                                items=[(a, b) for a, b, _ in rows], cues=[c for _, _, c in rows]))
    if TITLE_END["m4"] <= t < M4_FS:                                        # what triggers freezes
        rows = [("x", "Grey, third-party money", cue("m4", "gr")), ("x", "Anonymous buyers on exchanges", cue("m4", "exchanges"))]
        draw_panel(img, t, dict(key="frz", title="What triggers freezes", t_in=TITLE_END["m4"] + .05, t_out=M4_FS - .05, width=720,
                                items=[(a, b) for a, b, _ in rows], cues=[c for _, _, c in rows]))
    if M5_CAM <= t < o["m6"]:
        for k, (txt, w) in enumerate([("Shifts", "shifts"), ("Confirmations", "confirm"), ("Limits", "limits")]):
            draw_pill(img, t, f"wk{k}", txt, 1560, 590 + k * 88, cue("m5", w), SE["m5"] - .05, ic="ok", size=30, h=70)
    if CTA_RECAP_END <= t < END_FS:
        rows = [("ok", "Free course", cue("m6", "free")), ("ok", "How the work really happens", cue("m6", "really")), ("ok", "Step by step", cue("m6", "step"))]
        draw_panel(img, t, dict(key="acad", title="Ganesha Pay Academy", title_icon="cap", t_in=cue("m6", "built") - .1, t_out=END_FS - .05, width=720,
                                items=[(a, b) for a, b, _ in rows], cues=[c for _, _, c in rows]))

# ---------------- render ----------------
def shake(t):
    for ts, kind in STAMPS:
        k = t - ts - .1
        if 0 <= k < .22:
            amp = (12 if kind == "myth" else 6) * (1 - k / .22)
            return int(amp * math.sin(k * 90)), int(amp * .6 * math.cos(k * 70))
    return 0, 0

def frame_at(t, frame):
    fs, cm = mode_at(t)
    if fs:
        img = FS_BG.copy(); scene_fs(img, t, frame)
    else:
        img = cam_view(frame, cm) * (1 - GRAD)
        cam_overlays(img, t)
    dx, dy = shake(t)
    if dx or dy: img = np.roll(np.roll(img, dx, axis=1), dy, axis=0)
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
    json.dump(dict(stamps=STAMPS, offsets=OFF, total=TOTAL, gaps=GAPS), open(f"{Y}/timeline.json", "w"))

if __name__ == "__main__":
    print("sections", {k: round(v, 2) for k, v in OFF.items()}, "speech end", round(SPEECH_END, 2), "total", round(TOTAL, 2))
    main()
