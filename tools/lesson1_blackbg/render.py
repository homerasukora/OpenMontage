"""Lesson 1 re-edit, Ganesha Pay Noir brand: speaker matted onto onyx with an emerald glow, rim light -> gold,
Noir wordmark top-right, 'LESSON 1' (Cormorant Garamond, gold) top-left, champagne Manrope subtitles.
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
ap.add_argument("--fonts", required=True, help="dir with Cormorant.ttf and Manrope.ttf (Google Fonts variable fonts)")
ap.add_argument("--logo", required=True, help="Noir wordmark RGBA png (champagne + gold, cut from the brand book)")
args = ap.parse_args()
src, alpha, words_path, out = args.src, args.alpha, args.words, args.out
PREVIEW = [int(x) for x in args.preview.split(",")] if args.preview else None
W, H, FPS = 1918, 1080, 30
CUT_A, CUT_B = map(int, args.cut.split(","))
END = args.end
SHOTS = set(int(x) for x in args.shots.split(",")) if args.shots else set()
PUNCH = 1.08                       # punch-in after the cut hides the jump
# Brand book (Ganesha Pay, Noir, 11.2026): onyx bg, emerald = second surface, gold only for lines/accents,
# champagne = light text on dark (no pure white), Cormorant Garamond = headings, Manrope = text.
ONYX = np.array([10, 11, 10], np.float32)
EMERALD = np.array([15, 61, 46], np.float32)
GOLD_HEX = (207, 165, 74)
CHAMPAGNE = (230, 214, 168)
def font(name, size, weight):
    f = ImageFont.truetype(f"{args.fonts}/{name}.ttf", size); f.set_variation_by_name(weight); return f

# ---------- background: onyx with an emerald glow behind the speaker (follows the speaker) ----------
yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
GLOW_PEAK = EMERALD * 1.25                           # same strength/shape as the v3 gold glow, brand emerald instead
def make_bg(cx):
    r = np.sqrt(((xx - cx) / (W * .5)) ** 2 + ((yy - H * .40) / (H * .72)) ** 2)
    g = (np.clip(1 - r, 0, 1) ** 2.0)[..., None]
    return ONYX + g * (GLOW_PEAK - ONYX)
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

# ---------- title + logo ----------
def flat_text(text, f, color, track=0, shadow_k=0.0, S=2):
    """Flat brand-colour text (no gradients/halos), optional soft dark shadow; rendered at S x and downsampled."""
    widths = [f.getlength(c, features=["lnum"]) for c in text]
    tw = int(sum(widths) + track * (len(text) - 1))
    asc, desc = f.getmetrics(); pad = 30 * S
    mask = Image.new("L", (tw + 2 * pad, asc + desc + 2 * pad), 0); d = ImageDraw.Draw(mask)
    x = pad
    for c, w in zip(text, widths):
        d.text((x, pad), c, font=f, fill=255, features=["lnum"]); x += w + track   # lining figures: "1", not old-style
    m = np.asarray(mask, np.float32) / 255
    sh = np.zeros_like(m)
    if shadow_k:
        sh = np.roll(np.asarray(mask.filter(ImageFilter.GaussianBlur(9 * S)), np.float32) / 255, 3 * S, axis=0) * shadow_k
    a = np.clip(m + sh * (1 - m), 0, 1)
    rgb = np.array(color, np.float32) * (m / np.maximum(a, 1e-4))[..., None]
    img = Image.fromarray(np.dstack([rgb.clip(0, 255), a * 255]).astype(np.uint8), "RGBA")
    img = img.resize((img.width // S, img.height // S), Image.LANCZOS)
    return np.asarray(img, np.float32)[..., :3], np.asarray(img, np.float32)[..., 3:] / 255

T_RGB, T_A = flat_text("LESSON 1", font("Cormorant", 46 * 2, b"SemiBold"), GOLD_HEX, track=7 * 2)
TH, TW = T_A.shape[:2]
TX, TY = 56 - 30, 50 - 30                             # text pad is 30 px

LOGO = Image.open(args.logo).convert("RGBA")
LOGO_W = 270                                          # >= 100 px minimum from the brand book
LOGO = LOGO.resize((LOGO_W, round(LOGO.height * LOGO_W / LOGO.width)), Image.LANCZOS)
L_RGB = np.asarray(LOGO, np.float32)[..., :3]; L_A = np.asarray(LOGO, np.float32)[..., 3:] / 255
LX, LY = W - LOGO_W - 60, 50

GOLD = np.array([1.0, .78, .32], np.float32)

# ---------- subtitles: 1-2 words per screen, bottom centre, champagne Manrope ----------
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
SUB_FONT = font("Manrope", 56 * 2, b"Bold")
def sub_layer(text):
    if text not in _sub_cache:
        _sub_cache[text] = flat_text(text, SUB_FONT, CHAMPAGNE, shadow_k=1.0)
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
    overlay(img, L_RGB, L_A, LX, LY, o)
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
                            "-vf", "pad=1920:1080:1:0:0x0A0B0A", "-c:v", "libx264", "-preset", "slow", "-crf", "17", "-pix_fmt", "yuv420p", out],
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
