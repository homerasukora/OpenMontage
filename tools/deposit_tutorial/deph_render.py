"""Security deposit tutorial (Hindi dub) — Ganesha Pay Noir 16:9 edit. Two third-party logos removed (header logo + white K).
Removes the third-party logo (flat fill of the header colour); the deposit QR + address stay visible (training example), frames the app in a branded
canvas with a key-point column, virtual-camera zooms on the clicks, gold-keyword subtitles.
usage: deph_render.py src.mov subs.json out.mp4 [--preview t1,t2 outdir]"""
import sys, json, re, subprocess, numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont, ImageFilter

D = "/tmp/claude-0/-home-user/7c5690c1-77ca-5715-b441-4cc8e349293a/scratchpad"
SRC, WORDS_P, OUT = sys.argv[1:4]
PREVIEW = [float(x) for x in sys.argv[5].split(",")] if len(sys.argv) > 5 and sys.argv[4] == "--preview" else None
W, H, FPS = 1920, 1080, 30
DUR = 89.2; NF = int(DUR * FPS)
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
SRC_R = (0, 0, 1920, 1080)                       # app fills the whole recording here (x1.5 of the English take)
WX, WY, WW, WH = 60, 118, 1400, 792
_mask = Image.new("L", (WW * S, WH * S), 0); ImageDraw.Draw(_mask).rounded_rectangle([0, 0, WW * S - 1, WH * S - 1], radius=20 * S, fill=255)
WMASK = np.asarray(_mask.resize((WW, WH), Image.LANCZOS), np.float32)[..., None] / 255
_fr = Image.new("RGBA", ((WW + 8) * S, (WH + 8) * S), (0, 0, 0, 0))
ImageDraw.Draw(_fr).rounded_rectangle([0, 0, _fr.width - 1, _fr.height - 1], radius=24 * S, outline=GOLD + (230,), width=2 * S)
FRAME = rgba(down(_fr))

# ---------------- clean-up of the recording ----------------
BOXES = [(50, 2, 170, 78), (1745, 98, 1845, 200)]          # header logo, white "K" mark
def clean(fr):
    f = fr.copy()
    for x0, y0, x1, y1 in BOXES:                           # backgrounds are flat but dim with modal overlays -> sample per frame
        ring = np.concatenate([f[y0:y1, x0 - 8:x0].reshape(-1, 3), f[y0:y1, x1:x1 + 8].reshape(-1, 3)])
        f[y0:y1, x0:x1] = np.median(ring, 0).astype(np.uint8)
    return f

# ---------------- virtual camera on the app ----------------
# (time, centre x, centre y, zoom) in recording pixels; zoom 1 = whole app area
KEYS = [(0, 960, 540, 1.0), (61.7, 960, 540, 1.0), (62.3, 1250, 363, 1.65), (64.6, 1250, 363, 1.65),
        (65.2, 835, 541, 1.85), (74.6, 835, 541, 1.85), (75.4, 835, 541, 1.08), (84.8, 835, 541, 1.08), (85.6, 960, 540, 1.0), (99, 960, 540, 1.0)]
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
    ft = font("NotoSerifDeva", 36 * S, b"SemiBold"); fi = font("NotoSansDeva", 26 * S, b"SemiBold"); fn = font("Manrope", 24 * S, b"Bold")
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
    dict(key="intro", title="सिक्योरिटी डिपॉज़िट", t_in=1.3, t_out=8.7, items=[("•", "ज़रूरत क्यों"), ("•", "सेट अप कैसे करें")], cues=[3.0, 5.8]),
    dict(key="why", title="डिपॉज़िट क्यों?", t_in=9.0, t_out=43.4,
         items=[("•", "आपसी गारंटी"), ("•", "हमारे फ़ंड्स आपके पास"), ("•", "दोनों के लिए सुरक्षा"), ("•", "आपका वर्किंग कैपिटल"), ("•", "आपकी पेमेंट लिमिट")],
         cues=[15.0, 18.3, 25.5, 34.5, 37.6]),
    dict(key="bigger", title="बड़ा डिपॉज़िट", t_in=43.6, t_out=55.4, items=[("•", "ज़्यादा फ़ंड्स एक्सेप्ट"), ("•", "ज़्यादा देर होल्ड")], cues=[49.5, 54.0]),
    dict(key="how", title="डिपॉज़िट कैसे करें", t_in=55.6, t_out=88.6,
         items=[("1", "Deposit USDT"), ("2", "2,000 USDT डालें"), ("3", "नेटवर्क चुनें"), ("4", "Proceed"), ("5", "QR पर USDT भेजें")],
         cues=[61.8, 69.5, 71.6, 76.2, 80.6]),
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
SUBS = [(a_, b_, t_.split()) for a_, b_, t_ in json.load(open(WORDS_P, encoding="utf-8"))]
KEY = re.compile(r"^(सिक्योरिटी|डिपॉज़िट|गारंटी|फ़ंड्स|बैंक|अकाउंट|वर्किंग|कैपिटल|ट्रैफ़िक|पेआउट्स|सेटलमेंट|USDT|QR|नेटवर्क|अमाउंट|2000|बटन|इथेरियम|एड्रेस|डिस्प्यूट)[,?]?$")
_sc = {}
def sub_layer(ws):
    k = " ".join(ws)
    if k not in _sc:
        f = font("NotoSansDeva", 50 * S, b"Bold"); sp = f.getlength(" "); wd = [f.getlength(w) for w in ws]
        tw = int(sum(wd) + sp * (len(ws) - 1)); pad = 30 * S; hh = 50 * S + 2 * pad + 40 * S
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
LAST = [None]
def compose(fr, t):
    if fr.mean() < 4 and LAST[0] is not None: fr = LAST[0]          # recording goes black at 87.2 s: hold the last frame
    else: LAST[0] = fr
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
