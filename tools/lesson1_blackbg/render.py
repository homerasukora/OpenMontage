"""Lesson 1 re-edit: speaker matted onto black, green spill -> gold, gold 'LESSON 1' title.
usage: render.py src.mov alpha.mkv out.mp4 [preview_frames_csv outdir]
"""
import sys, subprocess, numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

src, alpha, out = sys.argv[1:4]
PREVIEW = [int(x) for x in sys.argv[4].split(",")] if len(sys.argv) > 4 else None
W, H, FPS = 1918, 1080, 30
CUT_A, CUT_B = 1946, 1990          # drop frames [1946, 1990): "what KoiPay provides and"
PUNCH = 1.08                       # punch-in after the cut hides the jump
FONT = "/usr/share/fonts/opentype/inter/InterDisplay-SemiBold.otf"

# ---------- background: black with a faint warm glow behind the speaker ----------
yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
r = np.sqrt(((xx - W * .5) / (W * .55)) ** 2 + ((yy - H * .42) / (H * .75)) ** 2)
glow = np.clip(1 - r, 0, 1) ** 2.2
BG = (glow[..., None] * np.array([34, 24, 8], np.float32)).astype(np.float32)

# ---------- title overlay ----------
def gold_text_layer():
    S = 2
    f = ImageFont.truetype(FONT, 34 * S)
    txt = "LESSON 1"
    track = 7 * S
    widths = [f.getlength(c) for c in txt]
    tw = int(sum(widths) + track * (len(txt) - 1))
    asc, desc = f.getmetrics()
    line_w, gap = 70 * S, 22 * S
    cw, ch = tw + 2 * (line_w + gap) + 40 * S, asc + desc + 40 * S
    mask = Image.new("L", (cw, ch), 0); d = ImageDraw.Draw(mask)
    x = 20 * S + line_w + gap; y = 20 * S
    for c, w in zip(txt, widths):
        d.text((x, y), c, font=f, fill=255); x += w + track
    my = y + int(asc * 0.62)
    for x0 in (20 * S, 20 * S + line_w + gap + tw + gap):
        d.rectangle([x0, my - S, x0 + line_w, my + S], fill=255)
    # vertical metallic gold gradient
    g = np.linspace(0, 1, ch)[:, None, None]
    top, mid, bot = np.array([255, 226, 140]), np.array([233, 180, 60]), np.array([176, 118, 22])
    col = np.where(g < .5, top + (mid - top) * (g / .5), mid + (bot - mid) * ((g - .5) / .5))
    col = np.broadcast_to(col, (ch, cw, 3))
    m = np.asarray(mask, np.float32) / 255
    halo = np.asarray(mask.filter(ImageFilter.GaussianBlur(10 * S)), np.float32) / 255 * .45
    a = np.clip(m + halo * (1 - m), 0, 1)
    rgb = (col * m[..., None] + np.array([230, 170, 50]) * (halo * (1 - m))[..., None]) / np.maximum(a, 1e-4)[..., None]
    img = Image.fromarray(np.dstack([rgb.clip(0, 255), a * 255]).astype(np.uint8), "RGBA")
    return img.resize((cw // S, ch // S), Image.LANCZOS)

TITLE = gold_text_layer()
TW, TH = TITLE.size
TX, TY = W - TW - 50, 28
T_RGB = np.asarray(TITLE, np.float32)[..., :3]
T_A = np.asarray(TITLE, np.float32)[..., 3:] / 255

GOLD = np.array([1.0, .78, .32], np.float32)

def grade(fg):
    """Move green spill/rim light on the speaker into gold."""
    R, G, B = fg[..., 0], fg[..., 1], fg[..., 2]
    e = np.clip(G - np.maximum(R, B), 0, None)          # green excess
    out = fg.copy()
    out[..., 1] -= e
    out += e[..., None] * GOLD * 0.9
    return out

def compose(frame, a, k):
    fg = grade(frame.astype(np.float32))
    a = np.clip((a.astype(np.float32) / 255 - .04) / .92, 0, 1)[..., None]
    img = fg * a + BG * (1 - a)
    if k >= CUT_A:                                     # punch-in after the cut
        im = Image.fromarray(img.clip(0, 255).astype(np.uint8))
        cw, ch = W / PUNCH, H / PUNCH
        x0, y0 = (W - cw) / 2, (H - ch) * .25
        img = np.asarray(im.resize((W, H), Image.LANCZOS, box=(x0, y0, x0 + cw, y0 + ch)), np.float32)
    # title fades in over the first 0.6 s
    t = k / FPS
    o = np.clip((t - .2) / .6, 0, 1)
    reg = img[TY:TY + TH, TX:TX + TW]
    img[TY:TY + TH, TX:TX + TW] = reg * (1 - T_A * o) + T_RGB * T_A * o
    img *= np.clip((2050 - k) / 15, 0, 1)            # source goes black at frame 2050: fade out
    return img.clip(0, 255).astype(np.uint8)

dec = subprocess.Popen(["ffmpeg", "-v", "error", "-i", src, "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], stdout=subprocess.PIPE)
dea = subprocess.Popen(["ffmpeg", "-v", "error", "-i", alpha, "-f", "rawvideo", "-pix_fmt", "gray", "-"], stdout=subprocess.PIPE)
enc = None
if not PREVIEW:
    enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                            "-vf", "pad=1920:1080:1:0:black", "-c:v", "libx264", "-preset", "slow", "-crf", "17", "-pix_fmt", "yuv420p", out],
                           stdin=subprocess.PIPE)
n = k = 0
while True:
    b = dec.stdout.read(W * H * 3); ab = dea.stdout.read(W * H)
    if len(b) < W * H * 3 or len(ab) < W * H: break
    if CUT_A <= n < CUT_B: n += 1; continue
    if PREVIEW is None or n in PREVIEW:
        img = compose(np.frombuffer(b, np.uint8).reshape(H, W, 3), np.frombuffer(ab, np.uint8).reshape(H, W), n)
        if enc: enc.stdin.write(img.tobytes())
        else: Image.fromarray(img).save(f"{out}/f{n:04d}.png")
    n += 1; k += 1
    if PREVIEW and n > max(PREVIEW): break
if enc: enc.stdin.close(); enc.wait()
print("frames out:", k)
