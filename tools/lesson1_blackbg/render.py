"""Lesson 1 re-edit: speaker matted onto black, green spill -> gold, gold 'LESSON 1' title, gold subtitles.
usage: render.py src.mov alpha.mkv words.json out.mp4 --cut A,B --end N --shots c1,c2,.. [--preview f1,f2 (out = dir)]
"""
import sys, json, re, argparse, subprocess, numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont, ImageFilter

ap = argparse.ArgumentParser()
ap.add_argument("src"); ap.add_argument("alpha"); ap.add_argument("words"); ap.add_argument("out")
ap.add_argument("--cut", required=True, help="drop source frames [A,B): the 'what KoiPay provides and' phrase")
ap.add_argument("--end", type=int, required=True, help="frame where the picture should be fully faded to black")
ap.add_argument("--shots", default="", help="source frames with hard cuts (glow tracker resets there)")
ap.add_argument("--preview", default="")
args = ap.parse_args()
src, alpha, words_path, out = args.src, args.alpha, args.words, args.out
PREVIEW = [int(x) for x in args.preview.split(",")] if args.preview else None
W, H, FPS = 1918, 1080, 30
CUT_A, CUT_B = map(int, args.cut.split(","))
END = args.end
SHOTS = set(int(x) for x in args.shots.split(",")) if args.shots else set()
PUNCH = 1.08                       # punch-in after the cut hides the jump
FONT = "/usr/share/fonts/opentype/inter/InterDisplay-SemiBold.otf"
SUB_FONT = "/usr/share/fonts/opentype/inter/InterDisplay-Bold.otf"

# ---------- background: black with a warm gold glow behind the speaker (follows the speaker) ----------
yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
GLOW_RGB = np.array([66, 48, 12], np.float32)       # v3: ~2x stronger and a touch more yellow than v1/v2 (34,24,8)
def make_bg(cx):
    r = np.sqrt(((xx - cx) / (W * .5)) ** 2 + ((yy - H * .40) / (H * .72)) ** 2)
    return (np.clip(1 - r, 0, 1) ** 2.0)[..., None] * GLOW_RGB
_bg_cache = {}
def bg_at(cx):
    key = int(round(cx / 8)) * 8
    if key not in _bg_cache: _bg_cache[key] = make_bg(key)
    return _bg_cache[key]
glow_x = [None]
DITHER = np.random.default_rng(1).uniform(-1, 1, (H, W, 1)).astype(np.float32)   # breaks up 8-bit banding in the glow

def clean_alpha(a):
    """Keep only the speaker (and what touches him, e.g. the mic); drop haze and stray islands."""
    a = np.clip((a.astype(np.float32) / 255 - .08) / .88, 0, 1)
    small = cv2.resize(a, (W // 4, H // 4), interpolation=cv2.INTER_AREA)
    n, lab, st, _ = cv2.connectedComponentsWithStats((small > .35).astype(np.uint8), 8)
    if n <= 1: return a * 0
    areas = st[1:, cv2.CC_STAT_AREA]; big = areas.max()
    keep = np.isin(lab, 1 + np.where(areas >= .03 * big)[0]).astype(np.uint8)
    keep = cv2.dilate(keep, np.ones((5, 5), np.uint8))
    keep = cv2.GaussianBlur(cv2.resize(keep.astype(np.float32), (W, H), interpolation=cv2.INTER_LINEAR), (0, 0), 3)
    return a * np.clip(keep * 1.5, 0, 1)

# ---------- title overlay ----------
def gold_text_layer():
    S = 2
    f = ImageFont.truetype(FONT, 34 * S)
    txt = "LESSON 1"
    track = 7 * S
    widths = [f.getlength(c) for c in txt]
    tw = int(sum(widths) + track * (len(txt) - 1))
    asc, desc = f.getmetrics()
    line_w, gap = 0, 0                 # no side rules, just the label
    cw, ch = tw + 2 * (line_w + gap) + 40 * S, asc + desc + 40 * S
    mask = Image.new("L", (cw, ch), 0); d = ImageDraw.Draw(mask)
    x = 20 * S + line_w + gap; y = 20 * S
    for c, w in zip(txt, widths):
        d.text((x, y), c, font=f, fill=255); x += w + track
    return gold_fill(mask, S, halo_rgb=(230, 170, 50), halo_k=.45)

def gold_fill(mask, S, halo_rgb, halo_k, shadow_k=0.0):
    """Vertical metallic gold gradient inside `mask` (+ optional warm halo / dark shadow), downsampled by S."""
    cw, ch = mask.size
    g = np.linspace(0, 1, ch)[:, None, None]
    top, mid, bot = np.array([255, 226, 140]), np.array([240, 188, 58]), np.array([190, 128, 24])
    col = np.where(g < .5, top + (mid - top) * (g / .5), mid + (bot - mid) * ((g - .5) / .5))
    col = np.broadcast_to(col, (ch, cw, 3))
    m = np.asarray(mask, np.float32) / 255
    halo = np.asarray(mask.filter(ImageFilter.GaussianBlur(10 * S)), np.float32) / 255 * halo_k
    rgb_h, a_h = np.array(halo_rgb, np.float32), halo
    if shadow_k:                                      # dark drop shadow for readability over the shirt
        sh = np.asarray(mask.filter(ImageFilter.GaussianBlur(9 * S)), np.float32) / 255
        sh = np.roll(sh, 3 * S, axis=0) * shadow_k
        a_h = np.clip(sh + halo * (1 - sh), 0, 1)
        rgb_h = (np.array(halo_rgb, np.float32) * (halo * (1 - sh))[..., None]) / np.maximum(a_h, 1e-4)[..., None]
    a = np.clip(m + a_h * (1 - m), 0, 1)
    rgb = (col * m[..., None] + rgb_h * (a_h * (1 - m))[..., None]) / np.maximum(a, 1e-4)[..., None]
    img = Image.fromarray(np.dstack([rgb.clip(0, 255), a * 255]).astype(np.uint8), "RGBA")
    return img.resize((cw // S, ch // S), Image.LANCZOS)

TITLE = gold_text_layer()
TW, TH = TITLE.size
TX, TY = W - TW - 50, 28
T_RGB = np.asarray(TITLE, np.float32)[..., :3]
T_A = np.asarray(TITLE, np.float32)[..., 3:] / 255

GOLD = np.array([1.0, .78, .32], np.float32)

# ---------- subtitles: 1-2 words per screen, bottom centre, gold ----------
SMALL = {"a", "an", "the", "to", "of", "and", "with", "by", "on", "in", "it", "is", "you", "your", "we"}
def build_chunks(words):
    """Group words into 1-2 content words per screen; never end a screen on a function word."""
    cut0, cut1 = CUT_A / FPS, CUT_B / FPS
    ws = [dict(w, w="processed" if w["w"] == "Processed" else w["w"])
          for w in words if not (cut0 - .06 <= w["s"] < cut1)]
    clean = lambda w: re.sub(r"[.,:;?]+$", "", w["w"]).lower()
    chunks, cur = [], []
    for i, w in enumerate(ws):
        cur.append(w)
        nxt = ws[i + 1] if i + 1 < len(ws) else None
        hard = (nxt is None or re.search(r"[.,:;?]$", w["w"]) or nxt["s"] - w["e"] > .25
                or w["s"] < cut0 <= nxt["s"])
        content = sum(clean(c) not in SMALL for c in cur)
        soft = content >= 2 or len(cur) >= 4 or (nxt and sum(len(c["w"]) + 1 for c in cur) + len(nxt["w"]) > 22)
        if hard:
            chunks.append(cur); cur = []
        elif soft:
            carry = []
            while len(cur) > 1 and clean(cur[-1]) in SMALL:
                carry.insert(0, cur.pop())
            chunks.append(cur); cur = carry
    out = []
    for i, c in enumerate(chunks):
        s0 = c[0]["s"]
        nx = chunks[i + 1][0]["s"] if i + 1 < len(chunks) else 1e9
        e0 = min(max(min(c[-1]["e"], c[-1]["s"] + .9), s0 + .35), nx)
        out.append((s0, e0, " ".join(re.sub(r"[.,:;]+$", "", x["w"]) for x in c)))
    return out

SUBS = build_chunks(json.load(open(words_path)))
_sub_cache = {}
def sub_layer(text):
    if text not in _sub_cache:
        S = 2
        f = ImageFont.truetype(SUB_FONT, 60 * S)
        x0, y0, x1, y1 = f.getbbox(text)
        pad = 30 * S
        mask = Image.new("L", (x1 - x0 + 2 * pad, 60 * S + 2 * pad + 20 * S), 0)
        ImageDraw.Draw(mask).text((pad - x0, pad), text, font=f, fill=255)
        img = gold_fill(mask, S, halo_rgb=(0, 0, 0), halo_k=0.0, shadow_k=1.0)
        _sub_cache[text] = (np.asarray(img, np.float32)[..., :3], np.asarray(img, np.float32)[..., 3:] / 255)
    return _sub_cache[text]
SUB_Y = 1000                                          # below the hands, on black (guide: ~900; moved down for readability)

def overlay(img, rgb, a, x, y, o):
    h, w = a.shape[:2]
    reg = img[y:y + h, x:x + w]
    img[y:y + h, x:x + w] = reg * (1 - a * o) + rgb * a * o

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
    a = clean_alpha(a)
    cols = a[H // 8: H // 2].sum(0)                   # speaker's horizontal centre (head/shoulders)
    cx = float((cols * np.arange(W)).sum() / cols.sum()) if cols.sum() > 1000 else W / 2
    glow_x[0] = cx if (glow_x[0] is None or k in SHOTS) else glow_x[0] * .9 + cx * .1
    a = a[..., None]
    img = fg * a + bg_at(glow_x[0]) * (1 - a)
    if k >= CUT_A:                                     # punch-in after the cut
        im = Image.fromarray(img.clip(0, 255).astype(np.uint8))
        cw, ch = W / PUNCH, H / PUNCH
        x0, y0 = (W - cw) / 2, (H - ch) * .25
        img = np.asarray(im.resize((W, H), Image.LANCZOS, box=(x0, y0, x0 + cw, y0 + ch)), np.float32)
    # title fades in over the first 0.6 s
    t = k / FPS
    o = np.clip((t - .2) / .6, 0, 1)
    overlay(img, T_RGB, T_A, TX, TY, o)
    for s0, e0, text in SUBS:
        if s0 <= t < e0:
            rgb, a_s = sub_layer(text)
            h, w = a_s.shape[:2]
            o = min(1, (t - s0) / .12 + 1 / 3)      # quick fade-in
            overlay(img, rgb, a_s, (W - w) // 2, SUB_Y - h // 2 - 10, o)
            break
    img *= np.clip((END - k) / 15, 0, 1)             # fade to black at the end
    return (img + DITHER).clip(0, 255).astype(np.uint8)

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
