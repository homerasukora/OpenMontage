"""9:16 version of the announcement trailer: plate card on top, presenter (plates removed via clean background) below.
10–12 s announcement trailer: trigger lines cut from the full video, flash cuts, end card 'Watch full on YouTube'."""
import sys, json, subprocess, numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont
SRC, LOGO_F, OUT_V = sys.argv[1], sys.argv[2], sys.argv[3]
PREVIEW = [float(x) for x in sys.argv[4].split(",")] if len(sys.argv) > 4 else None
SW, SH = 1920, 1080; W, H, FPS = 1080, 1920, 30
CLIPS = [(0.00, 4.50), (12.40, 14.75), (20.30, 23.30)]
CUTS = [0.0]
for a, b in CLIPS: CUTS.append(round(CUTS[-1] + b - a, 3))
END0 = CUTS[-1]; DUR = END0 + 2.6
NEON, WHITE, GREY = (46, 232, 122), (250, 255, 251), (170, 190, 178)
F = "/usr/share/fonts/opentype/inter/"
def font(st, sz): return ImageFont.truetype(F + f"InterDisplay-{st}.otf", sz)
def clamp(x, a=0.0, b=1.0): return max(a, min(b, x))
def ease(x): x = clamp(x); return 1 - (1 - x) ** 3
def rgba(c, a): return (*c, int(255 * clamp(a)))

def read_clip(a, b):
    p = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{a:.3f}", "-t", f"{b - a:.3f}", "-i", SRC, "-vf", f"fps={FPS},scale={SW}:{SH}", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True).stdout
    n = len(p) // (SW * SH * 3); return np.frombuffer(p[: n * SW * SH * 3], np.uint8).reshape(n, SH, SW, 3)
FR = [read_clip(a, b) for a, b in CLIPS]

def neon_bg():
    bg = Image.new("RGB", (W, H), (2, 6, 3)); g = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(g)
    for i in range(-16, 17): d.line([(W / 2 + i * 40, 1500), (W / 2 + i * 300, H + 60)], fill=(46, 232, 122, 30), width=1)
    y, st = 1500, 8
    while y < H: d.line([(0, y), (W, y)], fill=(46, 232, 122, int(16 + 30 * (y - 1500) / (H - 1500))), width=1); st *= 1.3; y += st
    gl = g.filter(ImageFilter.GaussianBlur(5)); bg.paste(gl, (0, 0), gl); bg.paste(g, (0, 0), g)
    arr = np.asarray(bg).astype(np.float32); yy, xx = np.mgrid[0:H, 0:W]
    arr += (np.exp(-(((xx - W / 2) / 700) ** 2 + ((yy - 900) / 700) ** 2)) * 0.42)[..., None] * np.array(NEON, np.float32)
    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))
BG = neon_bg()
LOGO = Image.open(LOGO_F).convert("RGB").resize((560, 560), Image.LANCZOS)
_m = Image.new("L", LOGO.size, 0); ImageDraw.Draw(_m).rounded_rectangle((4, 4, 555, 555), 95, fill=255); LOGO.putalpha(_m)

def endcard(t):
    u = t - END0; img = BG.copy().convert("RGBA"); fl = Image.new("RGBA", (W, H), (0, 0, 0, 0)); nl = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    f, n = ImageDraw.Draw(fl), ImageDraw.Draw(nl)
    k = ease(u / 0.35); s = 1.25 - 0.25 * k
    lg = LOGO.resize((int(130 * s), int(130 * s)), Image.LANCZOS); lg.putalpha(lg.getchannel("A").point(lambda v: int(v * k)))
    img.alpha_composite(lg, (W // 2 - lg.width // 2, 520 - lg.height // 2))
    kq = ease((u - 0.15) / 0.3)
    for j, ln in enumerate(("Can your bank account", "be blocked?")):
        f.text((W / 2, 690 + 66 * j), ln, font=font("SemiBold", 52), fill=rgba(GREY, kq), anchor="mm")
    k2 = ease((u - 0.05) / 0.3); sz = int(150 * (1.18 - 0.18 * k2))
    f.text((W / 2, 930), "WATCH", font=font("Black", sz), fill=rgba(WHITE, k2), anchor="mm", stroke_width=4, stroke_fill=(0, 0, 0, int(140 * k2)))
    f.text((W / 2, 1080), "FULL", font=font("Black", sz), fill=rgba(WHITE, k2), anchor="mm", stroke_width=4, stroke_fill=(0, 0, 0, int(140 * k2)))
    k3 = ease((u - 0.3) / 0.3)
    txt = "on YouTube"; fnt = font("Black", 88); tw = f.textlength(txt, font=fnt); bw = tw + 170; x0 = W / 2 - bw / 2; y0 = 1200
    f.rounded_rectangle((x0, y0, x0 + bw, y0 + 132), 66, fill=rgba(NEON, k3)); n.rounded_rectangle((x0, y0, x0 + bw, y0 + 132), 66, outline=rgba(NEON, k3), width=8)
    cx, cy = x0 + 84, y0 + 66
    f.rounded_rectangle((cx - 40, cy - 28, cx + 40, cy + 28), 15, fill=(4, 20, 10, int(255 * k3)))
    f.polygon([(cx - 11, cy - 16), (cx - 11, cy + 16), (cx + 17, cy)], fill=rgba(NEON, k3))
    f.text((x0 + 150, cy + 2), txt, font=fnt, fill=(4, 20, 10, int(255 * k3)), anchor="lm")
    glow = nl.filter(ImageFilter.GaussianBlur(18))
    img = Image.alpha_composite(Image.alpha_composite(img, glow), fl)
    return img.convert("RGB")

CLEAN = Image.fromarray(FR[0][0])                       # first frame: no overlay plate yet
PLATE = (1130, 70, 1890, 700)                             # source area where the explainer plates appear
_pm = Image.new("L", (PLATE[2] - PLATE[0], PLATE[3] - PLATE[1]), 0)
ImageDraw.Draw(_pm).rectangle((14, 14, _pm.width - 15, _pm.height - 15), fill=255); PMASK = _pm.filter(ImageFilter.GaussianBlur(7))
PB_Y, PB_H = 720, 1200                                     # presenter block
TOP_H = PB_Y
def _top_bg():
    arr = np.zeros((TOP_H, W, 3), np.float32) + np.array((2, 8, 4), np.float32); yy, xx = np.mgrid[0:TOP_H, 0:W]
    arr += (np.exp(-(((xx - W / 2) / 620) ** 2 + ((yy - 360) / 330) ** 2)) * 0.55)[..., None] * np.array(NEON, np.float32)
    im = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8)); d = ImageDraw.Draw(im, "RGBA")
    for x in range(0, W + 1, 60): d.line([(x, 0), (x, TOP_H)], fill=(46, 232, 122, 16), width=1)
    for y in range(0, TOP_H + 1, 60): d.line([(0, y), (W, y)], fill=(46, 232, 122, 16), width=1)
    d.line([(0, TOP_H - 2), (W, TOP_H - 2)], fill=(46, 232, 122, 200), width=3)
    return im
TOP_BG = _top_bg()
WT = {"p2p": 3.12, "platform": 5.60, "matters": 6.08, "verified": 8.16, "merchants": 9.04}
def ap(t, at, d=0.3): return ease((t - at) / d)
def tx(d, xy, s_, fnt, col, a, anchor="mm"):
    if a > 0: d.text(xy, s_, font=fnt, fill=rgba(col, a), anchor=anchor)
def card(d, box, a, r=34, fill=(6, 18, 10), edge=NEON, w=4):
    if a > 0: d.rounded_rectangle(box, r, fill=(*fill, int(235 * a)), outline=rgba(edge, a), width=w)
def ic_bank(d, cx, cy, s_, a):
    c = rgba(NEON, a); top = cy - 0.5 * s_
    d.polygon([(cx - 0.6 * s_, top + 0.32 * s_), (cx, top), (cx + 0.6 * s_, top + 0.32 * s_)], outline=c, width=6)
    for i in range(4): x = cx - 0.39 * s_ + i * 0.26 * s_; d.line([(x, top + 0.45 * s_), (x, cy + 0.36 * s_)], fill=c, width=7)
    d.line([(cx - 0.62 * s_, cy + 0.5 * s_), (cx + 0.62 * s_, cy + 0.5 * s_)], fill=c, width=8)
def ic_bell(d, cx, cy, s_, a):
    c = rgba(NEON, a); d.arc((cx - 0.32 * s_, cy - 0.45 * s_, cx + 0.32 * s_, cy + 0.3 * s_), 180, 360, fill=c, width=5)
    d.line([(cx - 0.32 * s_, cy - 0.08 * s_), (cx - 0.32 * s_, cy + 0.2 * s_), (cx - 0.45 * s_, cy + 0.3 * s_), (cx + 0.45 * s_, cy + 0.3 * s_), (cx + 0.32 * s_, cy + 0.2 * s_), (cx + 0.32 * s_, cy - 0.08 * s_)], fill=c, width=5)
    r = 0.08 * s_; d.ellipse((cx - r, cy + 0.36 * s_, cx + r, cy + 0.52 * s_), fill=c)
def ic_person(d, cx, cy, s_, a):
    c = rgba(NEON, a); r = 0.2 * s_; d.ellipse((cx - r, cy - 0.5 * s_, cx + r, cy - 0.1 * s_), outline=c, width=6)
    d.arc((cx - 0.42 * s_, cy + 0.02 * s_, cx + 0.42 * s_, cy + 0.82 * s_), 180, 360, fill=c, width=6)
def ic_chip(d, cx, cy, s_, a):
    c = rgba(NEON, a); r = 0.3 * s_; d.rounded_rectangle((cx - r, cy - r, cx + r, cy + r), 10, outline=c, width=6)
    for k in (-0.15, 0.0, 0.15):
        for sx, sy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            x0, y0 = cx + sx * r + (k * s_ if sx == 0 else 0), cy + sy * r + (k * s_ if sy == 0 else 0)
            d.line([(x0, y0), (x0 + sx * 0.14 * s_, y0 + sy * 0.14 * s_)], fill=c, width=5)
def ic_shield(d, cx, cy, s_, a):
    c = rgba(NEON, a); w_, h_ = 0.42 * s_, 0.5 * s_
    d.polygon([(cx, cy - h_), (cx + w_, cy - h_ * 0.62), (cx + w_ * 0.85, cy + h_ * 0.25), (cx, cy + h_), (cx - w_ * 0.85, cy + h_ * 0.25), (cx - w_, cy - h_ * 0.62)], outline=c, width=7)
    d.line([(cx - 0.18 * s_, cy), (cx - 0.04 * s_, cy + 0.15 * s_), (cx + 0.22 * s_, cy - 0.16 * s_)], fill=c, width=8, joint="curve")
def ic_store(d, cx, cy, s_, a):
    c = rgba(NEON, a)
    d.line([(cx - 0.5 * s_, cy - 0.1 * s_), (cx - 0.38 * s_, cy - 0.42 * s_), (cx + 0.38 * s_, cy - 0.42 * s_), (cx + 0.5 * s_, cy - 0.1 * s_), (cx - 0.5 * s_, cy - 0.1 * s_)], fill=c, width=5)
    d.rectangle((cx - 0.42 * s_, cy - 0.1 * s_, cx + 0.42 * s_, cy + 0.45 * s_), outline=c, width=5)
def ic_search(d, cx, cy, s_, a):
    c = rgba(NEON, a); r = 0.28 * s_; d.ellipse((cx - r - 0.08 * s_, cy - r - 0.08 * s_, cx + r - 0.08 * s_, cy + r - 0.08 * s_), outline=c, width=6)
    d.line([(cx + 0.14 * s_, cy + 0.14 * s_), (cx + 0.42 * s_, cy + 0.42 * s_)], fill=c, width=8)
def ic_doc(d, cx, cy, s_, a):
    c = rgba(NEON, a); d.rounded_rectangle((cx - 0.32 * s_, cy - 0.42 * s_, cx + 0.32 * s_, cy + 0.42 * s_), 8, outline=c, width=5)
    for k in (-0.18, 0.0, 0.18): d.line([(cx - 0.18 * s_, cy + k * s_), (cx + 0.18 * s_, cy + k * s_)], fill=c, width=5)
def pill(d, cx, cy, s_, a, filled=False, fnt=None, h=84, padx=40, icon=None):
    if a <= 0: return
    fnt = fnt or font("Bold", 44); iw = h * 0.7 if icon else 0; tw = d.textlength(s_, font=fnt) + iw
    box = (cx - tw / 2 - padx, cy - h / 2, cx + tw / 2 + padx, cy + h / 2)
    d.rounded_rectangle(box, h // 2, fill=rgba((10, 88, 38) if filled else (6, 18, 10), 0.95 * a), outline=rgba(NEON, a), width=4)
    if icon: icon(d, box[0] + padx + iw * 0.35, cy, h * 0.5, a)
    tx(d, (cx + iw / 2, cy + 1), s_, fnt, WHITE, a)
def arrow(d, x0, x1, y, prog, a, t):
    if prog <= 0: return
    xe = x0 + (x1 - x0) * prog; d.line([(x0, y), (xe, y)], fill=rgba(NEON, a), width=5)
    if prog >= 1:
        d.line([(x1, y), (x1 - 16, y - 13)], fill=rgba(NEON, a), width=5); d.line([(x1, y), (x1 - 16, y + 13)], fill=rgba(NEON, a), width=5)
        f = (t * 1.3) % 1.0; px = x0 + (x1 - x0) * f; d.ellipse((px - 6, y - 6, px + 6, y + 6), fill=rgba(NEON, a))

def top_panel(t):
    """Our own explainer plates on a green background (replaces the source picture)."""
    img = TOP_BG.copy().convert("RGBA"); ov = Image.new("RGBA", (W, TOP_H), (0, 0, 0, 0)); d = ImageDraw.Draw(ov)
    i = max(j for j in range(len(CLIPS)) if CUTS[j] <= t + 1e-6); u0 = CUTS[i]
    k = ap(t, u0 + 0.05, 0.3)
    if i == 0:
        card(d, (110, 70, 970, 650), k)
        ic_bank(d, W / 2, 190, 120, k)
        kb = ap(t, 0.5, 0.35); dy = 20 * (1 - kb)
        card(d, (190, 300 + dy, 890, 420 + dy), kb, r=30, fill=(10, 60, 30)); ic_bell(d, 260, 360 + dy, 60, kb)
        tx(d, (570, 360 + dy), "Bank account review", font("ExtraBold", 50), WHITE, kb)
        pill(d, W / 2, 540, "P2P processing", ap(t, WT["p2p"] - 0.15), filled=True, fnt=font("ExtraBold", 50), h=96, padx=48)
    elif i == 1:
        card(d, (110, 70, 970, 650), k)
        tx(d, (W / 2, 160), "Choosing the platform", font("ExtraBold", 54), WHITE, k)
        ic_person(d, 330, 340, 130, k); arrow(d, 420, 640, 330, ease((t - u0 - 0.2) / 0.4), k, t); ic_chip(d, 750, 330, 150, ap(t, u0 + 0.35))
        tx(d, (750, 445), "Platform", font("Bold", 40), WHITE, ap(t, WT["platform"] - 0.2))
        pill(d, W / 2, 560, "Platform matters", ap(t, WT["matters"] - 0.2), filled=True, fnt=font("ExtraBold", 50), h=96, padx=48)
    else:
        card(d, (110, 70, 970, 650), k)
        ic_shield(d, W / 2, 185, 130, k)
        tx(d, (W / 2, 310), "Verified merchants", font("Black", 62), WHITE, ap(t, WT["verified"] - 0.2))
        steps = [(ic_store, "Merchant", 260), (ic_search, "Check", 540), (ic_doc, "Request", 820)]
        for j, (ic, lab, x) in enumerate(steps):
            kk = ap(t, WT["verified"] + 0.1 + 0.3 * j)
            if kk <= 0.01: continue
            d.ellipse((x - 62, 430 - 62, x + 62, 430 + 62), fill=(10, 40, 22, int(235 * kk)), outline=rgba(NEON, kk), width=4); ic(d, x, 430, 70, kk)
            tx(d, (x, 535), lab, font("Bold", 38), WHITE, kk)
            if j: arrow(d, x - 280 + 72, x - 72, 430, ease((t - WT["verified"] - 0.1 - 0.3 * j) / 0.25), kk, t)
    gl = ov.filter(ImageFilter.GaussianBlur(9)); img = Image.alpha_composite(Image.alpha_composite(img, gl), ov)
    lg = LOGO.resize((70, 70), Image.LANCZOS); img.alpha_composite(lg, (36, 30))
    return img.convert("RGB")

def compose(src, u, seg_len, t):
    can = Image.new("RGB", (W, H), (0, 0, 0))
    can.paste(top_panel(t), (0, 0))
    pr = src.copy(); pr.paste(CLEAN.crop(PLATE), PLATE[:2], PMASK)
    z = 1.0 + 0.05 * ease(u / seg_len) + 0.05 * max(0, 1 - u / 0.18)
    cw2 = 972 / z; ch2 = 1080 / z; cx, cy = 940, 540
    x0 = clamp(cx - cw2 / 2, 0, SW - cw2); y0 = clamp(cy - ch2 / 2, 0, SH - ch2)
    can.paste(pr.resize((W, PB_H), Image.BICUBIC, box=(x0, y0, x0 + cw2, y0 + ch2)), (0, PB_Y))
    d = ImageDraw.Draw(can); d.line([(0, PB_Y), (W, PB_Y)], fill=NEON, width=4)
    return can

def frame(t):
    if t >= END0: img = endcard(t)
    else:
        i = max(j for j in range(len(CLIPS)) if CUTS[j] <= t + 1e-6); u = t - CUTS[i]
        img = compose(Image.fromarray(FR[i][min(int(u * FPS), len(FR[i]) - 1)]), u, CUTS[i + 1] - CUTS[i], t)
        if i == 0 and u < 0.25: img = Image.blend(Image.new("RGB", (W, H)), img, ease(u / 0.25))
    for c in CUTS[1:]:
        d = t - c
        if -0.04 <= d < 0.16:
            a = (1 - max(0, d) / 0.16) * 0.75; img = Image.blend(img, Image.new("RGB", (W, H), (200, 255, 220)), a)
    if DUR - t < 0.5: img = Image.blend(Image.new("RGB", (W, H)), img, clamp((DUR - t) / 0.5))
    return img

if PREVIEW:
    for t in PREVIEW: frame(t).save(f"{OUT_V}_{t:05.2f}.jpg", quality=88)
    print(CUTS, DUR); sys.exit()
enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                        "-c:v", "libx264", "-preset", "slow", "-crf", "16", "-pix_fmt", "yuv420p", OUT_V], stdin=subprocess.PIPE)
for k in range(int(round(DUR * FPS))): enc.stdin.write(frame(k / FPS).tobytes())
enc.stdin.close(); enc.wait(); print(json.dumps({"cuts": CUTS, "dur": DUR, "clips": CLIPS}))
