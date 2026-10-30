"""10–12 s announcement trailer: trigger lines cut from the full video, flash cuts, end card 'Watch full on YouTube'."""
import sys, json, subprocess, numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont
SRC, LOGO_F, OUT_V = sys.argv[1], sys.argv[2], sys.argv[3]
PREVIEW = [float(x) for x in sys.argv[4].split(",")] if len(sys.argv) > 4 else None
W, H, FPS = 1920, 1080, 30
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
    p = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{a:.3f}", "-t", f"{b - a:.3f}", "-i", SRC, "-vf", f"fps={FPS},scale={W}:{H}", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True).stdout
    n = len(p) // (W * H * 3); return np.frombuffer(p[: n * W * H * 3], np.uint8).reshape(n, H, W, 3)
FR = [read_clip(a, b) for a, b in CLIPS]

def neon_bg():
    bg = Image.new("RGB", (W, H), (2, 6, 3)); g = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(g)
    for i in range(-16, 17): d.line([(W / 2 + i * 40, 780), (W / 2 + i * 300, H + 60)], fill=(46, 232, 122, 30), width=1)
    y, st = 780, 8
    while y < H: d.line([(0, y), (W, y)], fill=(46, 232, 122, int(16 + 30 * (y - 780) / (H - 780))), width=1); st *= 1.3; y += st
    gl = g.filter(ImageFilter.GaussianBlur(5)); bg.paste(gl, (0, 0), gl); bg.paste(g, (0, 0), g)
    arr = np.asarray(bg).astype(np.float32); yy, xx = np.mgrid[0:H, 0:W]
    arr += (np.exp(-(((xx - W / 2) / 850) ** 2 + ((yy - 500) / 480) ** 2)) * 0.42)[..., None] * np.array(NEON, np.float32)
    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))
BG = neon_bg()
LOGO = Image.open(LOGO_F).convert("RGB").resize((560, 560), Image.LANCZOS)
_m = Image.new("L", LOGO.size, 0); ImageDraw.Draw(_m).rounded_rectangle((4, 4, 555, 555), 95, fill=255); LOGO.putalpha(_m)

def endcard(t):
    u = t - END0; img = BG.copy().convert("RGBA"); fl = Image.new("RGBA", (W, H), (0, 0, 0, 0)); nl = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    f, n = ImageDraw.Draw(fl), ImageDraw.Draw(nl)
    k = ease(u / 0.35); s = 1.25 - 0.25 * k
    lg = LOGO.resize((int(130 * s), int(130 * s)), Image.LANCZOS); lg.putalpha(lg.getchannel("A").point(lambda v: int(v * k)))
    img.alpha_composite(lg, (W // 2 - lg.width // 2, 175 - lg.height // 2))
    f.text((W / 2, 330), "Can your bank account be blocked?", font=font("SemiBold", 46), fill=rgba(GREY, ease((u - 0.15) / 0.3)), anchor="mm")
    k2 = ease((u - 0.05) / 0.3); sz = int(150 * (1.18 - 0.18 * k2))
    f.text((W / 2, 490), "WATCH FULL", font=font("Black", sz), fill=rgba(WHITE, k2), anchor="mm", stroke_width=4, stroke_fill=(0, 0, 0, int(140 * k2)))
    k3 = ease((u - 0.3) / 0.3)
    txt = "on YouTube"; fnt = font("Black", 96); tw = f.textlength(txt, font=fnt); bw = tw + 180; x0 = W / 2 - bw / 2; y0 = 590
    f.rounded_rectangle((x0, y0, x0 + bw, y0 + 140), 70, fill=rgba(NEON, k3)); n.rounded_rectangle((x0, y0, x0 + bw, y0 + 140), 70, outline=rgba(NEON, k3), width=8)
    cx, cy = x0 + 90, y0 + 70                                                    # generic play button (not a third-party logo)
    f.rounded_rectangle((cx - 42, cy - 30, cx + 42, cy + 30), 16, fill=(4, 20, 10, int(255 * k3)))
    f.polygon([(cx - 12, cy - 17), (cx - 12, cy + 17), (cx + 18, cy)], fill=rgba(NEON, k3))
    f.text((x0 + 160, cy + 2), txt, font=fnt, fill=(4, 20, 10, int(255 * k3)), anchor="lm")
    glow = nl.filter(ImageFilter.GaussianBlur(18))
    img = Image.alpha_composite(Image.alpha_composite(img, glow), fl)
    return img.convert("RGB")

def frame(t):
    if t >= END0: img = endcard(t)
    else:
        i = max(j for j in range(len(CLIPS)) if CUTS[j] <= t + 1e-6); u = t - CUTS[i]
        arr = FR[i][min(int(u * FPS), len(FR[i]) - 1)]; im = Image.fromarray(arr)
        z = 1.0 + 0.06 * ease(u / (CUTS[i + 1] - CUTS[i])) + 0.05 * max(0, 1 - u / 0.18)       # slow push + punch on each cut
        w_, h_ = W / z, H / z; im = im.resize((W, H), Image.BICUBIC, box=((W - w_) / 2, (H - h_) / 2, (W + w_) / 2, (H + h_) / 2))
        img = im
        if i == 0 and u < 0.25: img = Image.blend(Image.new("RGB", (W, H)), img, ease(u / 0.25))
    for c in CUTS[1:]:                                                            # neon flash on every cut
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
