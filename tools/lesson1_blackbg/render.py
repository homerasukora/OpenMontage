"""Lesson 1 re-edit, Ganesha Pay Noir brand: speaker matted onto onyx with an emerald glow, rim light -> gold,
Noir wordmark top-right, 'LESSON 1' (Cormorant Garamond, gold) top-left, champagne Manrope subtitles.
usage: render.py src.mov alpha.mkv words.json out.mp4 --cut A,B --end N --shots c1,c2,.. [--preview f1,f2 (out = dir)]
"""
import sys, json, re, argparse, subprocess, numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont, ImageFilter

ap = argparse.ArgumentParser()
ap.add_argument("src"); ap.add_argument("alpha"); ap.add_argument("words"); ap.add_argument("out")
ap.add_argument("--cut", default="0,0", help="drop source frames [A,B) (e.g. a brand mention); 0,0 = no cut")
ap.add_argument("--label", default="LESSON 1")
ap.add_argument("--fps", type=float, default=30)
ap.add_argument("--subs", default="", help="ready subtitle list JSON [[start_s, end_s, text], ...] in SOURCE time (e.g. Hindi dub)")
ap.add_argument("--sub-font", default="Manrope:Bold", help="font file stem in --fonts and weight, e.g. NotoSansDeva:SemiBold")
ap.add_argument("--label-font", default="Cormorant:SemiBold", help="e.g. NotoSerifDeva:SemiBold for Devanagari")
ap.add_argument("--punch-from", type=int, default=0, help="static mode: punch-in from this frame (a cut made upstream)")
ap.add_argument("--maxframe", type=int, default=10**9, help="stop after this source frame (trim a dead tail)")
ap.add_argument("--static", action="store_true", help="no virtual camera (plain locked-off frame)")
ap.add_argument("--qa", default="", help="also write the final (camera-transformed) matte here, for leak QA")
ap.add_argument("--end", type=int, required=True, help="frame where the picture should be fully faded to black")
ap.add_argument("--shots", default="", help="source frames with hard cuts (glow tracker resets there)")
ap.add_argument("--preview", default="")
ap.add_argument("--fonts", required=True, help="dir with Cormorant.ttf and Manrope.ttf (Google Fonts variable fonts)")
ap.add_argument("--logo", required=True, help="Noir wordmark RGBA png (champagne + gold, cut from the brand book)")
args = ap.parse_args()
src, alpha, words_path, out = args.src, args.alpha, args.words, args.out
PREVIEW = [int(x) for x in args.preview.split(",")] if args.preview else None
W, H, FPS = 1918, 1080, args.fps
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

# ---------- temporal matte stabiliser ----------
_prev = {"a": None, "g": None}
def stabilise(a, frame, k):
    """Motion-adaptive temporal smoothing: where the picture is static, blend the matte with the previous
    (already smoothed) one so edges don't shimmer; where it moves, trust the current matte (no ghosting).
    Resets on every hard cut."""
    g = cv2.GaussianBlur(cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY).astype(np.float32), (0, 0), 2)
    if _prev["a"] is not None and k not in SHOTS and k != CUT_B:
        motion = np.abs(g - _prev["g"])
        w = np.clip(1 - motion / 10, 0, 1) * .6       # 0.6 = max weight of the previous matte
        a = a * (1 - w) + _prev["a"] * w
    _prev["a"], _prev["g"] = a, g
    return a

# ---------- title + logo ----------
def flat_text(text, f, color, track=0, shadow_k=0.0, S=2):
    """Flat brand-colour text (no gradients/halos), optional soft dark shadow; rendered at S x and downsampled."""
    asc, desc = f.getmetrics(); pad = 30 * S
    if track:                                         # letter-spaced Latin label: draw glyph by glyph
        widths = [f.getlength(c, features=["lnum"]) for c in text]
        tw = int(sum(widths) + track * (len(text) - 1))
    else:                                             # whole-string shaping (required for Devanagari conjuncts/matras)
        tw = int(f.getlength(text, features=["lnum"]))
    mask = Image.new("L", (tw + 2 * pad, asc + desc + 2 * pad), 0); d = ImageDraw.Draw(mask)
    if track:
        x = pad
        for c, w in zip(text, widths):
            d.text((x, pad), c, font=f, fill=255, features=["lnum"]); x += w + track   # lining figures: "1", not old-style
    else:
        d.text((pad, pad), text, font=f, fill=255, features=["lnum"])
    m = np.asarray(mask, np.float32) / 255
    sh = np.zeros_like(m)
    if shadow_k:
        sh = np.roll(np.asarray(mask.filter(ImageFilter.GaussianBlur(9 * S)), np.float32) / 255, 3 * S, axis=0) * shadow_k
    a = np.clip(m + sh * (1 - m), 0, 1)
    rgb = np.array(color, np.float32) * (m / np.maximum(a, 1e-4))[..., None]
    img = Image.fromarray(np.dstack([rgb.clip(0, 255), a * 255]).astype(np.uint8), "RGBA")
    img = img.resize((img.width // S, img.height // S), Image.LANCZOS)
    return np.asarray(img, np.float32)[..., :3], np.asarray(img, np.float32)[..., 3:] / 255

_lf, _lw = args.label_font.split(":")
_deva = any("\u0900" <= ch <= "\u097f" for ch in args.label)
T_RGB, T_A = flat_text(args.label, font(_lf, (40 if _deva else 46) * 2, _lw.encode()), GOLD_HEX, track=0 if _deva else 7 * 2)
TH, TW = T_A.shape[:2]
TX, TY = 56 - 30, 50 - 30                             # text pad is 30 px

LOGO = Image.open(args.logo).convert("RGBA")
LOGO_W = 270                                          # >= 100 px minimum from the brand book
LOGO = LOGO.resize((LOGO_W, round(LOGO.height * LOGO_W / LOGO.width)), Image.LANCZOS)
L_RGB = np.asarray(LOGO, np.float32)[..., :3]; L_A = np.asarray(LOGO, np.float32)[..., 3:] / 255
LX, LY = W - LOGO_W - 60, 50

GOLD = np.array([1.0, .78, .32], np.float32)

# ---------- subtitles: 1-2 words per screen, bottom centre, champagne Manrope ----------
SMALL = {"a", "an", "the", "or", "as", "to", "of", "and", "with", "by", "on", "in", "it", "is", "you", "your", "we"}
def build_chunks(words):
    """Group words into 1-2 content words per screen; never end a screen on a function word."""
    cut0, cut1 = CUT_A / FPS, CUT_B / FPS
    ws = [dict(w, w="processed" if w["w"] == "Processed" else w["w"])
          for w in words if not (cut0 - .06 <= w["s"] < cut1)]
    # keep names together on one screen: "Ganesha Pay", "lesson 2"
    merged = []
    for w in ws:
        if merged and ((merged[-1]["w"] == "Ganesha" and re.match(r"Pay\b", w["w"]))
                       or (merged[-1]["w"].lower() == "lesson" and re.match(r"\d", w["w"]))):
            merged[-1] = dict(merged[-1], w=merged[-1]["w"] + " " + w["w"], e=w["e"])
        else: merged.append(w)
    ws = merged
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

SUBS = [tuple(x) for x in json.load(open(args.subs))] if args.subs else build_chunks(json.load(open(words_path)))
_sub_cache = {}
_sf, _sw = args.sub_font.split(":")
SUB_FONT = font(_sf, 56 * 2, _sw.encode())
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

# ---------- virtual camera: zooms + transitions on the finished composite (matte is never touched) ----------
ZOOM = {0: 1.0, 1: 1.12, 2: 1.24}

def face_track():
    """Head position per source frame from the matte (low-res pass)."""
    w4, h4 = 480, 270
    b = subprocess.run(["ffmpeg", "-v", "error", "-i", alpha, "-vf", f"scale={w4}:{h4}", "-f", "rawvideo", "-pix_fmt", "gray", "-"],
                       capture_output=True).stdout
    A = np.frombuffer(b, np.uint8).reshape(-1, h4, w4)
    out = []
    for a in A:
        rows = np.where(a.max(1) > 128)[0]
        if len(rows) == 0: out.append((W / 2, H * .35)); continue
        y0 = rows[0]; band = a[y0:y0 + 40] > 128
        xs = np.where(band.any(0))[0]
        cx = (xs.min() + xs.max()) / 2 if len(xs) else w4 / 2
        out.append((cx * W / w4, (y0 + .11 * h4) * H / h4))
    return np.array(out)

def plan_camera(nframes):
    """Segments (start_frame, level, transition) keyed to sentences and hard cuts."""
    ws = [w for w in json.load(open(words_path)) if not (CUT_A / FPS - .06 <= w["s"] < CUT_B / FPS)]
    starts, new = [], True
    for w in ws:
        if new: starts.append((w["s"], w["w"]))
        new = bool(re.search(r"[.?!]$", w["w"]))
    sent_end_q = {}
    cur = None
    for w in ws:
        if cur is None: cur = w["s"]
        if re.search(r"[.?!]$", w["w"]): sent_end_q[cur] = w["w"].endswith("?"); cur = None
    hard = sorted(set(SHOTS) | ({CUT_B} if CUT_B > CUT_A else set()))
    segs = [(0, 0, "hard")]
    level, cyc, last = 0, 0, 0
    PATTERN = [1, 0, 2, 0, 1, 2, 0]
    events = [(int(round((t - .10) * FPS)), "sent", sent_end_q.get(t, False)) for t, _ in starts[1:]]
    events += [(h, "cut", False) for h in hard]
    for f, kind, q in sorted(events):
        if f <= 0 or f >= nframes: continue
        if kind == "sent":
            if any(abs(f - h) < 25 for h in hard) or f - last < 72: continue
            nl = 2 if q else PATTERN[cyc % len(PATTERN)]
            if nl == level: nl = 0 if level else 1
            tr = "hard" if ZOOM[nl] > ZOOM[level] and cyc % 2 == 0 else "ease"
        else:
            nl = PATTERN[cyc % len(PATTERN)]
            if nl == level: nl = (level + 1) % 3
            tr = "cut"
        cyc += 1; level = nl; last = f
        segs.append((f, nl, tr))
    return segs

def box_for(level, anchor, prog):
    s = ZOOM[level] * (1 + .025 * prog)               # slow push-in inside every segment
    cw, ch = W / s, H / s
    x0 = np.clip(anchor[0] - cw / 2, 0, W - cw); y0 = np.clip(anchor[1] - .36 * ch, 0, H - ch)
    return np.array([x0, y0, cw])

def ease(x): x = np.clip(x, 0, 1); return x * x * (3 - 2 * x)

CAM = None
def setup_camera():
    global CAM
    track = face_track(); nf = len(track)
    segs = plan_camera(nf)
    bounds = [sg[0] for sg in segs[1:]] + [nf]
    plan = []
    for (f0, lvl, tr), f1 in zip(segs, bounds):
        anchor = np.median(track[f0:max(f1, f0 + 1)], 0)
        plan.append(dict(f0=f0, f1=f1, lvl=lvl, tr=tr, anchor=anchor))
    CAM = plan
    print("camera:", " ".join(f"{p['f0']}:{ZOOM[p['lvl']]:.2f}{p['tr'][0]}" for p in plan), flush=True)

def camera_box(k):
    for i, p in enumerate(CAM):
        if p["f0"] <= k < p["f1"]: break
    prog = (k - p["f0"]) / max(p["f1"] - p["f0"], 1)
    box = box_for(p["lvl"], p["anchor"], prog)
    t = k - p["f0"]
    if p["tr"] == "ease" and i > 0 and t < 15:        # smooth 0.5 s zoom between framings
        q = CAM[i - 1]; prev = box_for(q["lvl"], q["anchor"], 1.0)
        box = prev + (box - prev) * ease(t / 15)
    if p["tr"] == "cut" and t < 12:                   # cut "bump": incoming shot settles from +4 %
        e = 1 + .04 * (1 - ease(t / 12))
        c = box[:2] + box[2] * np.array([1, H / W]) / 2; cw = box[2] / e
        box = np.array([c[0] - cw / 2, c[1] - cw * H / W / 2, cw])
        box[0] = np.clip(box[0], 0, W - cw); box[1] = np.clip(box[1], 0, H - cw * H / W)
    return box

def apply_camera(img, k):
    x0, y0, cw = camera_box(k)
    if cw >= W - .5: return img
    s = W / cw
    M = np.array([[s, 0, -x0 * s], [0, s, -y0 * s]], np.float32)
    return cv2.warpAffine(img, M, (W, H), flags=cv2.INTER_LANCZOS4, borderMode=cv2.BORDER_REPLICATE)

def compose(frame, a, k):
    fg = grade(frame.astype(np.float32))
    a = stabilise(clean_alpha(a), frame, k)
    cols = a[H // 8: H // 2].sum(0)                   # speaker's horizontal centre (head/shoulders)
    cx = float((cols * np.arange(W)).sum() / cols.sum()) if cols.sum() > 1000 else W / 2
    glow_x[0] = cx if (glow_x[0] is None or k in SHOTS) else glow_x[0] * .9 + cx * .1
    if QA: QA_A[0] = a
    a = a[..., None]
    img = fg * a + bg_at(glow_x[0]) * (1 - a)
    if args.static:
        if (CUT_B > CUT_A and k >= CUT_A) or (args.punch_from and k >= args.punch_from):   # punch-in after the cut
            im = Image.fromarray(img.clip(0, 255).astype(np.uint8))
            cw, ch = W / PUNCH, H / PUNCH
            x0, y0 = (W - cw) / 2, (H - ch) * .25
            img = np.asarray(im.resize((W, H), Image.LANCZOS, box=(x0, y0, x0 + cw, y0 + ch)), np.float32)
    else:
        img = apply_camera(np.ascontiguousarray(img, np.float32), k)
        if QA: QA_A[0] = apply_camera(np.ascontiguousarray(QA_A[0], np.float32), k)
    if QA: QA.stdin.write((QA_A[0] * 255).clip(0, 255).astype(np.uint8).tobytes())
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
    img *= np.clip((END - k) / 15, 0, 1) * np.clip((k + 1) / 9, 0, 1)   # fade out at the end, quick fade-in at start             # fade to black at the end
    return (img + DITHER).clip(0, 255).astype(np.uint8)

if not args.static: setup_camera()
QA_A = [None]
QA = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "gray", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                       "-c:v", "ffv1", args.qa], stdin=subprocess.PIPE) if args.qa else None
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
    if n > args.maxframe: break
    if CUT_A <= n < CUT_B: n += 1; continue
    if PREVIEW is None or n in PREVIEW:
        img = compose(np.frombuffer(b, np.uint8).reshape(H, W, 3), np.frombuffer(ab, np.uint8).reshape(H, W), n)
        if enc: enc.stdin.write(img.tobytes())
        else: Image.fromarray(img).save(f"{out}/f{n:04d}.png")
    n += 1; k += 1
    if PREVIEW and n > max(PREVIEW): break
if enc: enc.stdin.close(); enc.wait()
if QA: QA.stdin.close(); QA.wait()
print("frames out:", k)
