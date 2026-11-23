"""Guru Nanak Jayanti greeting Reel (9:16): Wan selfie video + Ganesha Pay Noir overlays.
Logo on top, warm light garland, drifting gold sparkles, gold frame, captions, title card with line-art diyas,
'Peace · Kindness · Joy' tiles, CTA 'Share your wishes in the comments'. usage: gp_reel.py out.mp4 [--preview t1,t2 outdir]"""
import sys, math, subprocess, numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont, ImageFilter
D = "/tmp/claude-0/-home-user/7c5690c1-77ca-5715-b441-4cc8e349293a/scratchpad"; G = f"{D}/gurpurab"
OUT = sys.argv[1]; PREV = [float(x) for x in sys.argv[3].split(",")] if len(sys.argv) > 3 and sys.argv[2] == "--preview" else None
W, H, FPS, S = 1080, 1920, 30, 2
SRC_DUR = 14.0; HOLD = 2.4; TOTAL = SRC_DUR + HOLD; NF = int(TOTAL * FPS)
ONYX = (10, 11, 10); EMERALD = (15, 61, 46); GOLD = (207, 165, 74); CHAMP = (230, 214, 168); WARM = (255, 196, 110)
def fS(name, size, weight):
    f = ImageFont.truetype(f"{D}/fonts/{name}.ttf", size * S); f.set_variation_by_name(weight.encode()); return f
def rgba(im): return np.asarray(im, np.float32)
def down(im): return im.resize((im.width // S, im.height // S), Image.LANCZOS)
def ease(x): x = min(max(x, 0.0), 1.0); return x * x * (3 - 2 * x)
def over(dst, src, x, y, a=1.0):
    h, w = src.shape[:2]; x0, y0 = max(0, x), max(0, y); x1, y1 = min(W, x + w), min(H, y + h)
    if x1 <= x0 or y1 <= y0 or a <= 0: return
    s = src[y0 - y:y1 - y, x0 - x:x1 - x]; al = s[..., 3:] / 255 * a
    dst[y0:y1, x0:x1] = dst[y0:y1, x0:x1] * (1 - al) + s[..., :3] * al
def add(dst, src, x, y, a=1.0):              # additive light (glows)
    h, w = src.shape[:2]; x0, y0 = max(0, x), max(0, y); x1, y1 = min(W, x + w), min(H, y + h)
    if x1 <= x0 or y1 <= y0 or a <= 0: return
    dst[y0:y1, x0:x1] += src[y0 - y:y1 - y, x0 - x:x1 - x] * a

# ---------- static layers ----------
yy = np.arange(H, dtype=np.float32)[:, None, None]
BOTTOM = np.clip((yy - H * .50) / (H * .5), 0, 1) ** 1.2 * .78            # darken lower half for captions/cards
TOP = np.clip((H * .26 - yy) / (H * .26), 0, 1) ** 1.3 * .62              # darken top for the logo
_fr = Image.new("RGBA", (W * S, H * S), (0, 0, 0, 0))
ImageDraw.Draw(_fr).rounded_rectangle([26 * S, 26 * S, (W - 26) * S, (H - 26) * S], radius=46 * S, outline=GOLD + (150,), width=3 * S)
FRAME = rgba(down(_fr))
_wm = Image.open(f"{D}/ganesha_wordmark_noir.png").convert("RGBA"); _wm = _wm.resize((380, round(_wm.height * 380 / _wm.width)), Image.LANCZOS)
LOGO = rgba(_wm)
_pl = Image.new("RGBA", ((380 + 64) * S, (_wm.height + 44) * S), (0, 0, 0, 0))
ImageDraw.Draw(_pl).rounded_rectangle([0, 0, _pl.width - 1, _pl.height - 1], radius=26 * S, fill=ONYX + (205,), outline=GOLD + (170,), width=2 * S)
LOGO_PL = rgba(down(_pl)); LOGO_Y = 150

def glow(r, col, core=.9):
    n = int(r * 6); yy_, xx_ = np.mgrid[0:n, 0:n].astype(np.float32); d = np.sqrt((xx_ - n / 2) ** 2 + (yy_ - n / 2) ** 2)
    g = np.exp(-(d / r) ** 2) * core + np.exp(-(d / (r * 2.6)) ** 2) * .35
    return g[..., None] * np.array(col, np.float32)[None, None]
BULB = glow(8, WARM, 1.3); SPARK = glow(4, (255, 214, 140), 1.1); BOKEH = glow(18, GOLD, .25)

# light garland: a sagging string of warm bulbs under the logo
GX = np.linspace(70, W - 70, 19); GY = 330 + 70 * np.sin(np.linspace(0, math.pi, 19))
_gl = Image.new("RGBA", (W * S, H * S), (0, 0, 0, 0)); dg = ImageDraw.Draw(_gl)
dg.line([(x * S, y * S) for x, y in zip(np.linspace(40, W - 40, 60), 330 + 70 * np.sin(np.linspace(-.05, math.pi + .05, 60)))], fill=GOLD + (190,), width=3 * S)
WIRE = rgba(down(_gl))
rng = np.random.default_rng(11)
NP = 46
PX = rng.uniform(40, W - 40, NP); PY0 = rng.uniform(0, H, NP); PV = rng.uniform(25, 70, NP); PPH = rng.uniform(0, 6.28, NP); PK = rng.integers(0, 3, NP)

def diya(px):                                   # line-art oil lamp with a flame (brand gold)
    im = Image.new("RGBA", (px * S, px * S), (0, 0, 0, 0)); d = ImageDraw.Draw(im); p = px * S; lw = max(3, p // 16)
    d.arc([p * .12, p * .32, p * .88, p * .92], 0, 180, fill=GOLD, width=lw)
    d.line([(p * .12, p * .62), (p * .88, p * .62)], fill=GOLD, width=lw)
    d.polygon([(p * .5, p * .10), (p * .60, p * .38), (p * .5, p * .52), (p * .40, p * .38)], fill=WARM + (255,))
    return rgba(down(im))
DIYA = diya(86)
def card(h, w=920):
    im = Image.new("RGBA", (w * S, h * S), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle([0, 0, w * S - 1, h * S - 1], radius=34 * S, fill=ONYX + (215,), outline=GOLD + (230,), width=3 * S)
    return im, d
def title_card():
    im, d = card(290)
    d.text((460 * S, 58 * S), "HAPPY GURPURAB", font=fS("Manrope", 32, "ExtraBold"), fill=GOLD, anchor="mm")
    d.text((460 * S, 142 * S), "Happy Guru Nanak", font=fS("CormorantItalic", 78, "SemiBold Italic"), fill=CHAMP, anchor="mm")
    d.text((460 * S, 226 * S), "Jayanti", font=fS("CormorantItalic", 78, "SemiBold Italic"), fill=GOLD, anchor="mm")
    L = rgba(down(im)); dy = DIYA
    for x in (34, 920 - 34 - dy.shape[1]):
        L[140:140 + dy.shape[0], x:x + dy.shape[1]] = L[140:140 + dy.shape[0], x:x + dy.shape[1]] * (1 - dy[..., 3:] / 255) + dy * (dy[..., 3:] / 255)
    return L
def from_card():
    im, d = card(200)
    d.text((460 * S, 62 * S), "WARM WISHES FROM", font=fS("Manrope", 32, "ExtraBold"), fill=GOLD, anchor="mm")
    wm = Image.open(f"{D}/ganesha_wordmark_noir.png").convert("RGBA"); wm = wm.resize((520 * S, round(wm.height * 520 * S / wm.width)), Image.LANCZOS)
    im.alpha_composite(wm, ((920 * S - wm.width) // 2, 98 * S)); return rgba(down(im))
def tiles(n):
    im, d = card(230)
    d.text((460 * S, 52 * S), "WISHING YOU", font=fS("Manrope", 32, "ExtraBold"), fill=GOLD, anchor="mm")
    for k, wd in enumerate(["Peace", "Kindness", "Joy"][:n]):
        cx = [170, 460, 750][k]
        d.rounded_rectangle([(cx - 130) * S, 92 * S, (cx + 130) * S, 200 * S], radius=22 * S, fill=EMERALD + (200,), outline=GOLD + (200,), width=2 * S)
        d.text((cx * S, 146 * S), wd, font=fS("Cormorant", 62, "SemiBold"), fill=GOLD, anchor="mm")
    return rgba(down(im))
def cta_card():
    im, d = card(270)
    cx, cy, r = 120, 135, 52                                        # speech-bubble icon
    d.rounded_rectangle([(cx - r) * S, (cy - r + 6) * S, (cx + r) * S, (cy + r - 14) * S], radius=22 * S, outline=GOLD, width=5 * S)
    d.polygon([((cx - 18) * S, (cy + r - 16) * S), ((cx - 30) * S, (cy + r + 14) * S), ((cx + 4) * S, (cy + r - 16) * S)], fill=GOLD)
    for k in (-1, 0, 1): d.ellipse([(cx + k * 22 - 6) * S, (cy - 10) * S, (cx + k * 22 + 6) * S, (cy + 2) * S], fill=GOLD)
    d.text((560 * S, 98 * S), "Share your wishes", font=fS("Manrope", 60, "ExtraBold"), fill=CHAMP, anchor="mm")
    d.text((560 * S, 178 * S), "in the comments", font=fS("Cormorant", 70, "SemiBold"), fill=GOLD, anchor="mm")
    return rgba(down(im))
def arrow(px=84):
    im = Image.new("RGBA", (px * S, px * S), (0, 0, 0, 0)); d = ImageDraw.Draw(im); p = px * S; lw = p // 10
    d.line([(p * .5, p * .12), (p * .5, p * .82)], fill=GOLD, width=lw); d.line([(p * .24, p * .56), (p * .5, p * .84), (p * .76, p * .56)], fill=GOLD, width=lw, joint="curve")
    return rgba(down(im))
TITLE, FROM, CTA, ARROW = title_card(), from_card(), cta_card(), arrow()
TILES = [tiles(n) for n in range(4)]
CARD_Y = 1290                                    # card band (bottom edge ≤ ~1540)

# ---------- captions ----------
CAPS = [(0.00, .92, [("Hi, friends!", 0)]), (.96, 2.74, [("Happy", 0), ("Guru Nanak Jayanti", 1)]), (2.80, 3.98, [("Happy", 0), ("Gurpurab", 1)]),
        (4.00, 5.66, [("to everyone celebrating", 0)]), (5.76, 7.70, [("From all of us at", 0), ("Ganesha Pay", 1)]),
        (7.76, 9.40, [("we wish you and your families", 0)]), (9.44, 11.86, [("peace,", 1), ("kindness", 1), ("and", 0), ("joy", 1)]),
        (11.92, 13.80, [("Share your wishes in the", 0), ("comments", 1)])]
_cc = {}
def caption(parts):
    key = tuple(parts)
    if key not in _cc:
        f = fS("Manrope", 62, "ExtraBold"); sp = f.getlength(" ")
        txt = [p for p, _ in parts]; widths = [f.getlength(t) for t in txt]; tw = int(sum(widths) + sp * (len(txt) - 1)); pad = 30 * S
        m = Image.new("L", (tw + 2 * pad, 62 * S + 2 * pad + 24 * S), 0); col = Image.new("RGB", m.size, CHAMP)
        dm, dc = ImageDraw.Draw(m), ImageDraw.Draw(col); x = pad
        for (t, g), wd in zip(parts, widths):
            dm.text((x, pad), t, font=f, fill=255); dc.text((x, pad), t, font=f, fill=GOLD if g else CHAMP); x += wd + sp
        mm = np.asarray(m, np.float32) / 255; sh = np.roll(np.asarray(m.filter(ImageFilter.GaussianBlur(10 * S)), np.float32) / 255, 3 * S, axis=0)
        a = np.clip(mm + sh * (1 - mm) * .9, 0, 1); rgb = np.asarray(col, np.float32) * (mm / np.maximum(a, 1e-4))[..., None]
        L = rgba(down(Image.fromarray(np.dstack([rgb.clip(0, 255), a * 255]).astype(np.uint8), "RGBA")))
        if L.shape[1] > 920: L = cv2.resize(L, (920, int(L.shape[0] * 920 / L.shape[1])), interpolation=cv2.INTER_AREA)
        _cc[key] = L
    return _cc[key]

def frame_at(t, base):
    img = base.astype(np.float32)
    img = img * (1 - BOTTOM) + np.array(ONYX, np.float32) * BOTTOM
    img = img * (1 - TOP) + np.array(ONYX, np.float32) * TOP
    if t > SRC_DUR: img = img * (1 - .25 * ease((t - SRC_DUR) / .6))            # gentle dim on the hold
    light = np.zeros_like(img)
    # sparkles drifting up (fainter over the face area)
    for i in range(NP):
        y = (PY0[i] - PV[i] * t) % H; x = PX[i] + 14 * math.sin(t * .8 + PPH[i])
        tw = .55 + .45 * math.sin(t * 3.1 + PPH[i] * 2)
        face = 280 < x < 800 and 380 < y < 1050
        a = tw * (.25 if face else .75)
        if PK[i] == 2: add(light, BOKEH, int(x - BOKEH.shape[1] / 2), int(y - BOKEH.shape[0] / 2), a * .8)
        else: add(light, SPARK, int(x - SPARK.shape[1] / 2), int(y - SPARK.shape[0] / 2), a)
    # garland
    over(img, WIRE, 0, 0, ease(t / .6))
    for k, (x, y) in enumerate(zip(GX, GY)):
        tw = .6 + .4 * math.sin(t * 2.4 + k * 1.3)
        add(light, BULB, int(x - BULB.shape[1] / 2), int(y + 8 - BULB.shape[0] / 2), tw * ease((t - k * .03) / .5))
    img = img + light * .9
    over(img, FRAME, 0, 0)
    over(img, LOGO_PL, (W - LOGO_PL.shape[1]) // 2, LOGO_Y - 22); over(img, LOGO, (W - LOGO.shape[1]) // 2, LOGO_Y)
    # cards
    def show(L, t0, t1, dy=0):
        if t0 - .01 <= t < t1 + .3:
            a = ease((t - t0) / .35) * (1 - ease((t - t1) / .3))
            over(img, L, (W - L.shape[1]) // 2, CARD_Y + dy + int(26 * (1 - ease((t - t0) / .35))), a)
    show(TITLE, .95, 5.6)
    show(FROM, 5.75, 7.6)
    if 7.7 <= t < 11.9 + .3:
        n = sum(1 for c in (9.44, 10.16, 11.12) if t >= c)
        show(TILES[n], 7.75, 11.85)
    show(CTA, 11.9, 99)
    if t >= 12.4:
        bob = int(14 * math.sin((t - 12.4) * 2 * math.pi / 1.1))
        over(img, ARROW, (W - ARROW.shape[1]) // 2, CARD_Y + CTA.shape[0] + 18 + bob, ease((t - 12.4) / .4))
    # captions
    for s0, e0, parts in CAPS:
        if s0 <= t < e0:
            L = caption(parts); over(img, L, (W - L.shape[1]) // 2, 1175 - L.shape[0] // 2, min(1, (t - s0) / .1 + .35)); break
    return img

def main():
    dec = subprocess.Popen(["ffmpeg", "-v", "error", "-i", f"{G}/wan.mp4", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], stdout=subprocess.PIPE)
    enc = None if PREV else subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                                              "-c:v", "libx264", "-preset", "medium", "-crf", "17", "-pix_fmt", "yuv420p", OUT], stdin=subprocess.PIPE)
    last = None; tg = sorted(int(round(x * FPS)) for x in PREV) if PREV else None
    dither = np.random.default_rng(2).uniform(-1, 1, (H, W, 1)).astype(np.float32)
    for j in range(NF):
        t = j / FPS
        if t < SRC_DUR:
            b = dec.stdout.read(W * H * 3)
            if len(b) == W * H * 3: last = np.frombuffer(b, np.uint8).reshape(H, W, 3)
        if tg is not None and j not in tg:
            if j > max(tg): break
            continue
        out = (frame_at(t, last) + dither).clip(0, 255).astype(np.uint8)
        if enc: enc.stdin.write(out.tobytes())
        else: Image.fromarray(out).save(f"{sys.argv[4]}/g{t:05.2f}.png")
    if enc: enc.stdin.close(); enc.wait()
main()
