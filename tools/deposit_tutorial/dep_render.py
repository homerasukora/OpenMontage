"""Security deposit tutorial — Ganesha Pay Noir 16:9 edit of a screen recording.
Removes the third-party logo (flat fill of the header colour); the deposit QR + address stay visible (training example), frames the app in a branded
canvas with a key-point column, virtual-camera zooms on the clicks, gold-keyword subtitles.
usage: dep_render.py src.mp4 words.json out.mp4 [--preview t1,t2 outdir]"""
import sys, json, re, subprocess, numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont, ImageFilter

D = "/tmp/claude-0/-home-user/7c5690c1-77ca-5715-b441-4cc8e349293a/scratchpad"
SRC, WORDS_P, OUT = sys.argv[1:4]
PREVIEW = [float(x) for x in sys.argv[5].split(",")] if len(sys.argv) > 5 and sys.argv[4] == "--preview" else None
W, H, FPS = 1920, 1080, 30
DUR = 87.13; NF = int(DUR * FPS)
ONYX = (10, 11, 10); EMERALD = (15, 61, 46); GOLD = (207, 165, 74); CHAMP = (230, 214, 168); RED = (224, 71, 60)
S = 2
def font(name, size, weight):
    f = ImageFont.truetype(f"{D}/fonts/{name}.ttf", size); f.set_variation_by_name(weight); return f
def rgba(img): return np.asarray(img, np.float32)
def down(img): return img.resize((img.width // S, img.height // S), Image.LANCZOS)
def ease(x): x = min(max(x, 0.0), 1.0); return x * x * (3 - 2 * x)
def over(dst, src, x, y, alpha=1.0):
    if alpha <= 0: return
    h, w = src.shape[:2]; x0, y0 = max(0, x), max(0, y); x1, y1 = min(W, x + w), min(H, y + h)
    if x1 <= x0 or y1 <= y0: return
    s = src[y0 - y:y1 - y, x0 - x:x1 - x]; a = s[..., 3:] / 255 * alpha
    dst[y0:y1, x0:x1] = dst[y0:y1, x0:x1] * (1 - a) + s[..., :3] * a

# ---------------- canvas ----------------
yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
r = np.sqrt(((xx - W * .42) / (W * .7)) ** 2 + ((yy - H * .48) / (H * .85)) ** 2)
BG = np.array(ONYX, np.float32) + (np.clip(1 - r, 0, 1) ** 1.8)[..., None] * (np.array(EMERALD, np.float32) * 1.4 - np.array(ONYX, np.float32))
DITHER = np.random.default_rng(5).uniform(-1, 1, (H, W, 1)).astype(np.float32)
_wm = Image.open(f"{D}/ganesha_wordmark_noir.png").convert("RGBA"); _wm = _wm.resize((250, round(_wm.height * 250 / _wm.width)), Image.LANCZOS)
LOGO = rgba(_wm)

# app window on the canvas
SRC_R = (319, 178, 1595, 900)                    # app area inside the recording (1276 x 722)
WX, WY, WW, WH = 60, 118, 1400, 792
_mask = Image.new("L", (WW * S, WH * S), 0); ImageDraw.Draw(_mask).rounded_rectangle([0, 0, WW * S - 1, WH * S - 1], radius=20 * S, fill=255)
WMASK = np.asarray(_mask.resize((WW, WH), Image.LANCZOS), np.float32)[..., None] / 255
_fr = Image.new("RGBA", ((WW + 8) * S, (WH + 8) * S), (0, 0, 0, 0))
ImageDraw.Draw(_fr).rounded_rectangle([0, 0, _fr.width - 1, _fr.height - 1], radius=24 * S, outline=GOLD + (230,), width=2 * S)
FRAME = rgba(down(_fr))

# ---------------- clean-up of the recording ----------------
def clean(fr):
    f = fr.copy()
    f[178:236, 344:442] = (25, 25, 25)                             # app header is flat #191919: logo removed without a trace
    return f

# ---------------- virtual camera on the app ----------------
# (time, centre x, centre y, zoom) in recording pixels; zoom 1 = whole app area
KEYS = [(0, 957, 539, 1.0), (62.7, 957, 539, 1.0), (63.3, 1150, 420, 1.65), (65.6, 1150, 420, 1.65),
        (66.2, 874, 540, 1.85), (75.2, 874, 540, 1.85), (75.9, 874, 540, 1.08), (82.6, 874, 540, 1.08), (83.4, 957, 539, 1.0), (99, 957, 539, 1.0)]
def cam(t):
    for (t0, x0, y0, z0), (t1, x1, y1, z1) in zip(KEYS, KEYS[1:]):
        if t0 <= t < t1:
            k = ease((t - t0) / (t1 - t0)) if (x0, y0, z0) != (x1, y1, z1) else 0
            return x0 + (x1 - x0) * k, y0 + (y1 - y0) * k, z0 + (z1 - z0) * k
    return KEYS[-1][1:]
def app_view(fr, t):
    cx, cy, z = cam(t); sx0, sy0, sx1, sy1 = SRC_R
    cw, ch = (sx1 - sx0) / z, (sy1 - sy0) / z
    x0 = float(np.clip(cx - cw / 2, sx0, sx1 - cw)); y0 = float(np.clip(cy - ch / 2, sy0, sy1 - ch))
    s = WW / cw
    M = np.array([[s, 0, -x0 * s], [0, s, -y0 * s]], np.float32)
    return cv2.warpAffine(fr, M, (WW, WH), flags=cv2.INTER_CUBIC if z > 1.01 else cv2.INTER_AREA, borderMode=cv2.BORDER_REPLICATE).astype(np.float32)

# ---------------- key-point column ----------------
PX, PW = 1500, 380
def panel(title, items, n):
    pad, row_h, gap, th = 24, 64, 10, 60
    hgt = pad + th + max(n, 0) * (row_h + gap) + pad - (gap if n else 6)
    im = Image.new("RGBA", (PW * S, hgt * S), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle([0, 0, PW * S - 1, hgt * S - 1], radius=24 * S, fill=ONYX + (225,), outline=GOLD + (230,), width=2 * S)
    ft = font("Cormorant", 42 * S, b"SemiBold"); fi = font("Manrope", 27 * S, b"SemiBold"); fn = font("Manrope", 24 * S, b"Bold")
    d.text((pad * S, (pad + 2) * S), title, font=ft, fill=CHAMP)
    y = pad + th
    for i, (mark, txt) in enumerate(items[:n]):
        d.rounded_rectangle([pad * S, y * S, (PW - pad) * S, (y + row_h) * S], radius=16 * S, fill=EMERALD + (160,), outline=GOLD + (90,), width=S)
        cx, cy = (pad + 30) * S, (y + row_h // 2) * S; rr = 16 * S
        if mark.isdigit():
            d.ellipse([cx - rr, cy - rr, cx + rr, cy + rr], outline=GOLD, width=3 * S); d.text((cx, cy), mark, font=fn, fill=GOLD, anchor="mm")
        else:
            d.ellipse([cx - 7 * S, cy - 7 * S, cx + 7 * S, cy + 7 * S], fill=GOLD)
        d.text(((pad + 60) * S, cy), txt, font=fi, fill=CHAMP, anchor="lm")
        y += row_h + gap
    return rgba(down(im))
PANELS = [
    dict(key="intro", title="Security deposit", t_in=1.3, t_out=8.9, items=[("•", "Why it’s needed"), ("•", "How to set it up")], cues=[3.8, 6.3]),
    dict(key="why", title="Why a deposit?", t_in=9.0, t_out=45.6,
         items=[("•", "Mutual guarantee"), ("•", "You hold our funds"), ("•", "Protects both sides"), ("•", "Your working capital"), ("•", "Your payment limit")],
         cues=[14.2, 17.8, 26.1, 35.9, 41.3]),
    dict(key="bigger", title="Bigger deposit", t_in=46.1, t_out=58.3, items=[("•", "Accept more funds"), ("•", "Hold funds longer"), ("•", "Before settlement")], cues=[51.5, 53.7, 55.3]),
    dict(key="how", title="How to deposit", t_in=58.7, t_out=86.4,
         items=[("1", "Deposit USDT"), ("2", "Enter 2,000 USDT"), ("3", "Network: TRC20"), ("4", "Proceed"), ("5", "Send USDT to QR")],
         cues=[63.3, 67.1, 71.3, 74.6, 76.6]),
]
_pc = {}
def draw_panels(img, t):
    for sp in PANELS:
        if not (sp["t_in"] <= t < sp["t_out"] + .35): continue
        a = ease((t - sp["t_in"]) / .35) * (1 - ease((t - sp["t_out"]) / .35))
        n = sum(1 for c in sp["cues"] if t >= c)
        for k in (n, n - 1):
            if k >= 0 and (sp["key"], k) not in _pc: _pc[(sp["key"], k)] = panel(sp["title"], sp["items"], k)
        dy = int(20 * (1 - ease((t - sp["t_in"]) / .35)))
        if n > 0 and t - sp["cues"][n - 1] < .25:
            f = ease((t - sp["cues"][n - 1]) / .25)
            over(img, _pc[(sp["key"], n - 1)], PX, WY + dy, a * (1 - f)); over(img, _pc[(sp["key"], n)], PX, WY + dy, a * f)
        else: over(img, _pc[(sp["key"], n)], PX, WY + dy, a)

# ---------------- subtitles ----------------
FIX = {("our", "phones"): ["our", "funds"], ("your", "phones"): ["your", "funds"], ("our", "phones."): ["our", "funds."]}
def load_words():
    ws = json.load(open(WORDS_P)); out = []
    i = 0
    while i < len(ws):
        w = dict(ws[i]); x = w["w"]
        nxt = ws[i + 1]["w"] if i + 1 < len(ws) else ""
        if (x, nxt) in FIX: a, b = FIX[(x, nxt)]; out += [dict(w, w=a), dict(ws[i + 1], w=b)]; i += 2; continue
        if x == "That's" and nxt == "a" and i + 3 < len(ws) and ws[i + 2]["w"] == "24":
            out += [dict(ws[i], w="TRC20,", e=ws[i + 2]["e"]), dict(ws[i + 3], w="for"), dict(ws[i + 3], w="example.", s=ws[i + 3]["s"] + .25)]; i += 4; continue
        if x == "code" and out and out[-1]["w"] == "your": w["w"] = "QR code"
        if x == "why" and out and out[-1]["w"] == "address": w["w"] = "where"
        if x == "what" and nxt in ("you", "we"): w["w"] = "that"
        if x == "Larger": w["w"] = "larger"
        if x == "since" and out and out[-1]["w"].endswith("."): w["w"] = "Since"
        out.append(w); i += 1
    return out
WORDS = load_words()
SMALL = {"a", "an", "the", "to", "of", "and", "with", "by", "on", "in", "it", "is", "you", "your", "for", "we", "our", "can", "this", "that"}
def chunks(ws):
    cl = lambda w: re.sub(r"[.,:;?]+$", "", w["w"]).lower(); out, cur = [], []
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
        res.append((s0, min(max(min(c[-1]["e"], c[-1]["s"] + .9), s0 + .35), nx), [re.sub(r"[.,:;]+$", "", x["w"]) for x in c]))
    return res
SUBS = chunks(WORDS)
KEY = re.compile(r"^(security|deposit|deposits|guarantee|funds|bank|accounts|working|capital|traffic|payouts?|settlement|USDT|TRC20|network|proceed|QR|code|address|amount|2000|button|system)$", re.I)
_sc = {}
def sub_layer(ws):
    k = " ".join(ws)
    if k not in _sc:
        f = font("Manrope", 50 * S, b"Bold"); sp = f.getlength(" "); wd = [f.getlength(w) for w in ws]
        tw = int(sum(wd) + sp * (len(ws) - 1)); pad = 30 * S; hh = 50 * S + 2 * pad + 20 * S
        m = Image.new("L", (tw + 2 * pad, hh), 0); col = Image.new("RGB", m.size, CHAMP); dm, dc = ImageDraw.Draw(m), ImageDraw.Draw(col); x = pad
        for w, d_ in zip(ws, wd):
            dm.text((x, pad), w, font=f, fill=255); dc.text((x, pad), w, font=f, fill=GOLD if KEY.match(w) else CHAMP); x += d_ + sp
        mm = np.asarray(m, np.float32) / 255
        sh = np.roll(np.asarray(m.filter(ImageFilter.GaussianBlur(9 * S)), np.float32) / 255, 3 * S, axis=0)
        a = np.clip(mm + sh * (1 - mm), 0, 1); rgb = np.asarray(col, np.float32) * (mm / np.maximum(a, 1e-4))[..., None]
        _sc[k] = rgba(down(Image.fromarray(np.dstack([rgb.clip(0, 255), a * 255]).astype(np.uint8), "RGBA")))
    return _sc[k]
def draw_subs(img, t):
    for s0, e0, ws in SUBS:
        if s0 <= t < e0:
            L = sub_layer(ws); h, w = L.shape[:2]
            over(img, L, WX + WW // 2 - w // 2, 996 - h // 2 - 6, min(1, (t - s0) / .1 + .35)); return

# ---------------- render ----------------
def compose(fr, t):
    img = BG.copy()
    view = app_view(clean(fr), t)
    reg = img[WY:WY + WH, WX:WX + WW]; img[WY:WY + WH, WX:WX + WW] = reg * (1 - WMASK) + view * WMASK
    over(img, FRAME, WX - 4, WY - 4)
    over(img, LOGO, 60, 40)
    draw_panels(img, t)
    draw_subs(img, t)
    img *= min(1, (t + 1 / FPS) / .4) * min(1, (DUR - t) / .5)          # fade in / out
    return (img + DITHER).clip(0, 255).astype(np.uint8)

dec = subprocess.Popen(["ffmpeg", "-v", "error", "-i", SRC, "-vf", f"fps={FPS}", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], stdout=subprocess.PIPE)
enc = None
if not PREVIEW:
    enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                            "-c:v", "libx264", "-preset", "medium", "-crf", "16", "-pix_fmt", "yuv420p", OUT], stdin=subprocess.PIPE)
targets = sorted(int(round(x * FPS)) for x in PREVIEW) if PREVIEW else None
j = 0
while True:
    b = dec.stdout.read(1920 * 1080 * 3)
    if len(b) < 1920 * 1080 * 3: break
    t = j / FPS
    if targets is None or j in targets:
        out = compose(np.frombuffer(b, np.uint8).reshape(1080, 1920, 3), t)
        if enc: enc.stdin.write(out.tobytes())
        else: Image.fromarray(out).save(f"{OUT}/f{t:06.2f}.png")
    j += 1
    if targets is not None and j > max(targets): break
if enc: enc.stdin.close(); enc.wait()
print("frames", j)
