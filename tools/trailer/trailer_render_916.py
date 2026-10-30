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
CARD = (100, 40, 980, 680)                                 # top plate card
def compose(src, u, seg_len):
    can = Image.new("RGB", (W, H), (0, 0, 0))
    bg = src.resize((W, int(W * SH / SW)), Image.BILINEAR).filter(ImageFilter.GaussianBlur(30)); bg = Image.eval(bg, lambda v: int(v * 0.35))
    can.paste(bg.resize((W, PB_Y + 40)), (0, 0))
    # plate card (top)
    cw, ch = CARD[2] - CARD[0], CARD[3] - CARD[1]
    pc = src.crop((1150, 90, 1880, 90 + int(730 * ch / cw))).resize((cw, ch), Image.LANCZOS)
    m = Image.new("L", (cw, ch), 0); ImageDraw.Draw(m).rounded_rectangle((0, 0, cw - 1, ch - 1), 36, fill=255); can.paste(pc, CARD[:2], m)
    # presenter block: plates replaced by the clean background
    pr = src.copy(); pr.paste(CLEAN.crop(PLATE), PLATE[:2], PMASK)
    z = 1.0 + 0.05 * ease(u / seg_len) + 0.05 * max(0, 1 - u / 0.18)
    cw2 = 972 / z; ch2 = 1080 / z; cx, cy = 940, 540
    x0 = clamp(cx - cw2 / 2, 0, SW - cw2); y0 = clamp(cy - ch2 / 2, 0, SH - ch2)
    can.paste(pr.resize((W, PB_H), Image.BICUBIC, box=(x0, y0, x0 + cw2, y0 + ch2)), (0, PB_Y))
    ov = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(ov)
    d.rounded_rectangle((CARD[0] - 3, CARD[1] - 3, CARD[2] + 3, CARD[3] + 3), 38, outline=(*NEON, 255), width=5)
    gl = ov.filter(ImageFilter.GaussianBlur(10)); can = can.convert("RGBA"); can = Image.alpha_composite(Image.alpha_composite(can, gl), ov)
    lg = LOGO.resize((70, 70), Image.LANCZOS); can.alpha_composite(lg, (CARD[0] + 24, CARD[1] + 22))
    return can.convert("RGB")

def frame(t):
    if t >= END0: img = endcard(t)
    else:
        i = max(j for j in range(len(CLIPS)) if CUTS[j] <= t + 1e-6); u = t - CUTS[i]
        img = compose(Image.fromarray(FR[i][min(int(u * FPS), len(FR[i]) - 1)]), u, CUTS[i + 1] - CUTS[i])
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
