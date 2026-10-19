"""KoiPay trader dashboard ad (9:16): screen-recording panels with neon framing, ElevenLabs VO, subtitles, case insert, Telegram CTA."""
import json, math, subprocess, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

A = json.load(open(sys.argv[1])); OUT = sys.argv[2]
PREVIEW = [float(x) for x in sys.argv[3].split(",")] if len(sys.argv) > 3 else None
D = A["dir"]
SC = json.load(open(f"{D}/scenes.json")); SCENES = SC["scenes"]; DUR = SC["end"]
WORDS = json.load(open(f"{D}/words.json")); LT = json.load(open(f"{D}/vo.json"))["lines"]

W, H, FPS = 1080, 1920, 25
NEON, NEON_DARK, WHITE, GREY, RED = (46, 232, 122), (10, 88, 38), (250, 255, 251), (160, 178, 166), (255, 92, 92)
F = "/usr/share/fonts/opentype/inter/"
def font(style, size): return ImageFont.truetype(F + f"InterDisplay-{style}.otf", size)
SUB = font("Black", 70); HUGE = font("Black", 132); BIG = font("Black", 96); TITLE = font("ExtraBold", 62)
PILL = font("Bold", 44); LABEL = font("SemiBold", 40); SMALL = font("SemiBold", 34)

def clamp(x, a=0.0, b=1.0): return max(a, min(b, x))
def ease(x): x = clamp(x); return 1 - (1 - x) ** 3
def ease_io(x): x = clamp(x); return x * x * (3 - 2 * x)
def appear(t, at, d=0.3): return ease((t - at) / d)
def rgba(c, a): return (*c, int(255 * clamp(a)))
def cue(word, line, n=0):
    hits = [w for w in WORDS if w["line"] == line and w["w"].lower().strip(".,?!:").startswith(word.lower())]
    return hits[n]["s"]

class Layers:
    def __init__(self):
        self.fill = Image.new("RGBA", (W, H), (0, 0, 0, 0)); self.neon = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        self.text = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        self.f, self.n, self.t = ImageDraw.Draw(self.fill), ImageDraw.Draw(self.neon), ImageDraw.Draw(self.text)

def ctext(d, xy, s, fnt, col, a, anchor="mm"):
    if a > 0: d.text(xy, s, font=fnt, fill=rgba(col, a), anchor=anchor)

def pill(L, cx, cy, s, a, filled=False, fnt=PILL, padx=36, h=80, icon=None):
    if a <= 0: return
    iw = h * 0.7 if icon else 0
    tw = L.t.textlength(s, font=fnt) + iw
    box = (cx - tw / 2 - padx, cy - h / 2, cx + tw / 2 + padx, cy + h / 2)
    L.f.rounded_rectangle(box, h // 2, fill=rgba(NEON_DARK, 0.95 * a) if filled else (6, 18, 10, int(215 * a)))
    L.n.rounded_rectangle(box, h // 2, outline=rgba(NEON, a), width=3)
    if icon: icon(L.n, box[0] + padx + iw * 0.4, cy, h * 0.55, a)
    ctext(L.t, (cx + iw / 2, cy + 1), s, fnt, WHITE, a)

def icon_plane(d, cx, cy, s, a):
    r = 0.5 * s; d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=rgba(NEON, a))
    p = [(cx - 0.3 * s, cy - 0.02 * s), (cx + 0.28 * s, cy - 0.24 * s), (cx + 0.16 * s, cy + 0.26 * s), (cx + 0.0 * s, cy + 0.08 * s)]
    d.polygon(p, fill=(4, 14, 8, int(255 * a)))
def icon_chat(d, cx, cy, s, a):
    d.rounded_rectangle((cx - 0.5 * s, cy - 0.38 * s, cx + 0.5 * s, cy + 0.22 * s), int(0.16 * s), outline=rgba(NEON, a), width=5)
    d.line([(cx - 0.2 * s, cy + 0.22 * s), (cx - 0.3 * s, cy + 0.45 * s), (cx + 0.02 * s, cy + 0.22 * s)], fill=rgba(NEON, a), width=5)
def icon_shot(d, cx, cy, s, a):
    d.rounded_rectangle((cx - 0.3 * s, cy - 0.45 * s, cx + 0.3 * s, cy + 0.45 * s), int(0.1 * s), outline=rgba(NEON, a), width=5)
    d.rectangle((cx - 0.18 * s, cy - 0.25 * s, cx + 0.18 * s, cy + 0.15 * s), outline=rgba(NEON, a), width=3)
def icon_eye(d, cx, cy, s, a):
    d.ellipse((cx - 0.5 * s, cy - 0.28 * s, cx + 0.5 * s, cy + 0.28 * s), outline=rgba(NEON, a), width=5)
    r = 0.14 * s; d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=rgba(NEON, a))

# ---------- backgrounds ----------
def neon_bg():
    bg = Image.new("RGB", (W, H), (2, 5, 3)); g = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(g)
    hz = 1400
    for i in range(-16, 17): d.line([(W / 2 + i * 40, hz), (W / 2 + i * 300, H + 60)], fill=(46, 232, 122, 28), width=1)
    y, step = hz, 8
    while y < H: d.line([(0, y), (W, y)], fill=(46, 232, 122, int(14 + 30 * (y - hz) / (H - hz))), width=1); step *= 1.3; y += step
    rng = np.random.default_rng(5)
    for _ in range(22):
        x = int(rng.uniform(20, W - 20)); top = int(rng.uniform(60, 1200)); bot = int(rng.uniform(top + 150, H))
        d.line([(x, top), (x, bot)], fill=(46, 232, 122, 50), width=2); d.ellipse((x - 4, top - 4, x + 4, top + 4), fill=(140, 255, 180, 190))
    gl = g.filter(ImageFilter.GaussianBlur(6)); bg.paste(gl, (0, 0), gl); bg.paste(g, (0, 0), g)
    arr = np.asarray(bg).astype(np.float32)
    yy, xx = np.mgrid[0:H, 0:W]; arr += (np.exp(-(((xx - W / 2) / 700) ** 2 + ((yy - 860) / 800) ** 2)) * 0.10)[..., None] * np.array(NEON, np.float32)
    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))
BG = neon_bg()
PHOTOS = {k: Image.open(v).convert("RGB") for k, v in A["photos"].items()}

# brand logo (original file, only scaled; rounded corners masked to drop the white JPEG background) + Telegram icon
LOGO_PX = 92
_lg = Image.open(A["logo"]).convert("RGB").resize((LOGO_PX * 4, LOGO_PX * 4), Image.LANCZOS)
_m = Image.new("L", _lg.size, 0); ImageDraw.Draw(_m).rounded_rectangle((6, 6, _lg.width - 7, _lg.height - 7), int(_lg.width * 0.17), fill=255)
_lg.putalpha(_m); LOGO = _lg.resize((LOGO_PX, LOGO_PX), Image.LANCZOS)
TG = Image.open(A["telegram"]).convert("RGBA").resize((170, 170), Image.LANCZOS)
BRAND = font("Bold", 46)
def draw_brand(img):
    img.alpha_composite(LOGO, (52, 58))
    d = ImageDraw.Draw(img); d.text((52 + LOGO_PX + 22, 58 + LOGO_PX // 2), "Koi Pay", font=BRAND, fill=(255, 255, 255, 255), anchor="lm",
                                  stroke_width=2, stroke_fill=(0, 0, 0, 120))

def photo_cover(name, z, fx, fy):
    im = PHOTOS[name]; pw, ph = im.size; s = max(W / pw, H / ph) * z; cw, ch = W / s, H / s
    x0 = clamp(fx - cw / 2, 0, pw - cw); y0 = clamp(fy - ch / 2, 0, ph - ch)
    return im.crop((int(x0), int(y0), int(x0 + cw), int(y0 + ch))).resize((W, H), Image.BICUBIC)

# ---------- screen panel ----------
PANEL_W, PANEL_MAXH, PANEL_CY = 1000, 1020, 880
def panel(L, base_img, frame, sc, t, a):
    if a <= 0: return
    k = ease_io((t - sc["s"]) / max(0.1, sc["e"] - sc["s"]))
    c0, c1 = sc["crops"]; x, y, w, h = [c0[i] + (c1[i] - c0[i]) * k for i in range(4)]
    asp = h / w; pw = PANEL_W if PANEL_W * asp <= PANEL_MAXH else PANEL_MAXH / asp; ph = pw * asp
    img = frame
    for b in sc["blur"]:
        img.paste(img.crop(b).filter(ImageFilter.GaussianBlur(16)), tuple(b[:2]))
    pw, ph = int(pw), int(ph)
    crop = img.crop((int(x), int(y), int(x + w), int(y + h))).resize((pw, ph), Image.LANCZOS)
    px, py = (W - pw) // 2, int(PANEL_CY - ph / 2 + 30 * (1 - a))
    m = Image.new("L", (pw, ph), 0); ImageDraw.Draw(m).rounded_rectangle((0, 0, pw - 1, ph - 1), 28, fill=int(255 * a))
    base_img.paste(crop, (px, py), m)
    L.n.rounded_rectangle((px - 3, py - 3, px + pw + 3, py + ph + 3), 30, outline=rgba(NEON, a), width=4)
    return (px, py, pw, ph)

# ---------- scenes without footage ----------
def scene_hook(img, L, t, sc):
    ctext(L.t, (540, 360), "Done P2P", HUGE, WHITE, appear(t, 0.15, 0.25))
    ctext(L.t, (540, 500), "on Binance?", BIG, NEON, appear(t, cue("binance", 0) - 0.1, 0.25))
    items = [("Chats", icon_chat, cue("chats", 0)), ("Screenshots", icon_shot, cue("screenshots", 0)), ("Manual checks", icon_eye, cue("checking", 0))]
    for i, (lab, ic, at) in enumerate(items):
        k = appear(t, at - 0.1, 0.25); y = 760 + i * 170
        box = (190, y - 62, 890, y + 62)
        L.f.rounded_rectangle(box, 30, fill=rgba((20, 10, 10), 0.85 * k)); L.n.rounded_rectangle(box, 30, outline=rgba(RED, 0.8 * k), width=3)
        ic(L.n, 270, y, 70, k); ctext(L.t, (340, y), lab, PILL, WHITE, k, "lm")
        x = appear(t, at + 0.35, 0.2)
        if x > 0:
            L.t.line([(800, y - 22), (844, y + 22)], fill=rgba(RED, x), width=7); L.t.line([(844, y - 22), (800, y + 22)], fill=rgba(RED, x), width=7)

def scene_sahil(img, L, t, sc):
    mid = cue("then", 3) - 0.1
    if t < mid: img.paste(photo_cover("sahil_pc", 1.05 + 0.1 * (t - sc["s"]) / (mid - sc["s"]), 600, 760))
    else: img.paste(photo_cover("sahil_bike", 1.0 + 0.06 * (t - mid) / (sc["e"] - mid), 430, 620))
    arr = np.asarray(img).astype(np.float32); g = np.ones((H, 1, 1), np.float32)
    g[:420, 0, 0] = np.linspace(0.45, 1, 420); g[1150:, 0, 0] = np.linspace(1, 0.4, H - 1150)
    img.paste(Image.fromarray((arr * g).astype(np.uint8)))
    pill(L, 540, 230, "Sahil · Bangalore", appear(t, sc["s"] + 0.1), filled=True, fnt=TITLE, h=100, padx=44)
    pill(L, 540, 350, "5 months → first bike", appear(t, cue("bought", 3) - 0.1), fnt=PILL, h=80)

BIG_LOGO = None
def scene_brand(img, L, t, sc):
    global BIG_LOGO
    if BIG_LOGO is None:
        lg = Image.open(A["logo"]).convert("RGB").resize((1040, 1040), Image.LANCZOS)
        m = Image.new("L", lg.size, 0); ImageDraw.Draw(m).rounded_rectangle((16, 16, 1023, 1023), 180, fill=255)
        lg.putalpha(m); BIG_LOGO = lg.resize((260, 260), Image.LANCZOS)
    k = appear(t, sc["s"], 0.35); sz = int(260 * (0.85 + 0.15 * k))
    lg = BIG_LOGO.resize((sz, sz), Image.LANCZOS); lg.putalpha(lg.getchannel("A").point(lambda v: int(v * k)))
    L.text.alpha_composite(lg, (540 - sz // 2, 520 - sz // 2))
    ctext(L.t, (540, 760), "KoiPay", HUGE, WHITE, appear(t, sc["s"] + 0.15))
    pill(L, 540, 905, "P2P processing platform", appear(t, cue("p2p", 1) - 0.1), filled=True, fnt=TITLE, h=100, padx=44)
    pill(L, 540, 1030, "Everything in one place", appear(t, cue("everything", 1) - 0.1), fnt=PILL, h=84)

def scene_cta(img, L, t, sc):
    s = sc["s"]
    ctext(L.t, (540, 420), "Experienced in P2P?", TITLE, WHITE, appear(t, s + 0.05))
    ctext(L.t, (540, 520), "Get a workspace built for it.", LABEL, GREY, appear(t, cue("get", 12) - 0.1))
    k = appear(t, cue("message", 12) - 0.1)
    if k > 0:
        L.f.rounded_rectangle((110, 640, 970, 1160), 40, fill=rgba((6, 16, 10), 0.92 * k)); L.n.rounded_rectangle((110, 640, 970, 1160), 40, outline=rgba(NEON, k), width=4)
        tg = TG.copy(); tg.putalpha(tg.getchannel("A").point(lambda v: int(v * k)))
        L.text.alpha_composite(tg, (540 - 85, 760 - 85))
        ctext(L.t, (540, 890), "Message our manager on Telegram", LABEL, WHITE, k)
    k2 = appear(t, cue("@koirequestbot", 12) - 0.2, 0.3)
    if k2 > 0:
        pulse = 1 + 0.03 * math.sin((t - s) * 4)
        pill(L, 540, 1040, "@koirequestbot", k2, filled=True, fnt=font("Black", int(78 * pulse)), h=int(124 * pulse), padx=48)
    k3 = appear(t, cue("@koirequestbot", 12) + 0.5, 0.3)
    if k3 > 0:   # bright green "link below" plate
        txt = "Start via the link below ↓"; fnt = font("Black", 52); tw = L.t.textlength(txt, font=fnt)
        box = (540 - tw / 2 - 48, 1250 - 50, 540 + tw / 2 + 48, 1250 + 50)
        L.f.rounded_rectangle(box, 50, fill=rgba(NEON, k3)); L.n.rounded_rectangle(box, 50, outline=rgba(NEON, k3), width=4)
        ctext(L.t, (540, 1251), txt, fnt, (4, 20, 10), k3)

# ---------- subtitles ----------
GREEN = {"binance", "koipay", "platform", "one", "place", "earnings", "sahil", "bike", "limits", "forwarder", "sms", "payins", "review", "receipt", "payouts",
         "overdue", "proof", "crypto", "usdt", "report", "earning", "utr", "export", "score", "improve", "team", "employees", "earnings", "p2p", "@koirequestbot", "telegram"}
chunks, cur = [], []
for w in WORDS:
    cur.append(w)
    if w["w"][-1] in ".,?!:" or len(cur) == 3 or len(" ".join(x["w"] for x in cur)) >= 15: chunks.append(cur); cur = []
if cur: chunks.append(cur)
SUBS = []
for i, ch in enumerate(chunks):
    s = ch[0]["s"]; e = min(chunks[i + 1][0]["s"] if i + 1 < len(chunks) else DUR, ch[-1]["e"] + 0.4)
    SUBS.append((s, e, [(x["w"].rstrip(".,!:"), x["w"].lower().strip(".,?!:") in GREEN) for x in ch]))
SUB_Y = 1530

def draw_subs(t, img):
    cur = [s for s in SUBS if s[0] <= t < s[1]]
    if not cur: return
    s, e, toks = cur[-1]; k = appear(t, s, 0.1)
    widths = [SUB.getlength(tx + (" " if i < len(toks) - 1 else "")) for i, (tx, g) in enumerate(toks)]
    x = (W - sum(widths)) / 2
    lay = Image.new("RGBA", (W, 240), (0, 0, 0, 0)); sh = Image.new("RGBA", (W, 240), (0, 0, 0, 0))
    d, sd = ImageDraw.Draw(lay), ImageDraw.Draw(sh)
    for (tx, g), wd in zip(toks, widths):
        sd.text((x, 124), tx, font=SUB, fill=(0, 0, 0, int(240 * k)), anchor="lm", stroke_width=6, stroke_fill=(0, 0, 0, int(240 * k)))
        d.text((x, 120), tx, font=SUB, fill=rgba(NEON if g else WHITE, k), anchor="lm", stroke_width=3, stroke_fill=(0, 0, 0, int(200 * k)))
        x += wd
    sh = sh.filter(ImageFilter.GaussianBlur(9))
    img.alpha_composite(sh, (0, SUB_Y - 120)); img.alpha_composite(lay, (0, SUB_Y - 120))

# ---------- compose ----------
def compose(t, frame):
    L = Layers(); img = BG.copy()
    sc = next(s for s in SCENES if s["s"] <= t < s["e"] or s is SCENES[-1])
    a_in = appear(t, sc["s"], 0.25)
    if sc["name"] == "hook": scene_hook(img, L, t, sc)
    elif sc["name"] == "sahil": scene_sahil(img, L, t, sc)
    elif sc["name"] == "cta": scene_cta(img, L, t, sc)
    elif sc["name"] == "brand": scene_brand(img, L, t, sc)
    else:
        same_head = [p for p in SCENES if p["e"] == sc["s"] and p.get("head") == sc.get("head")]
        a = 1.0 if same_head else a_in
        panel(L, img, frame, sc, t, max(a, 0.001))
        pill(L, 540, 222, sc["head"], 1.0 if same_head else appear(t, sc["s"] + 0.05), filled=True, fnt=TITLE, h=100, padx=46)
        if "callout" in sc:
            lab, at = sc["callout"]
            pill(L, 540, 332, lab, appear(t, at - 0.1), fnt=SMALL, h=64, padx=30)
    out = img.convert("RGBA")
    out = Image.alpha_composite(out, L.fill)
    glow = L.neon.resize((W // 2, H // 2), Image.BILINEAR).filter(ImageFilter.GaussianBlur(9)).resize((W, H), Image.BILINEAR)
    out = Image.alpha_composite(Image.alpha_composite(out, glow), glow)
    out = Image.alpha_composite(out, L.neon); out = Image.alpha_composite(out, L.text)
    draw_brand(out)
    draw_subs(t, out)
    return out.convert("RGB")

def read_frame(t):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{t:.3f}", "-i", A["base"], "-frames:v", "1", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True).stdout
    return Image.frombuffer("RGB", (1920, 1080), raw).copy()

if PREVIEW:
    for t in PREVIEW: compose(t, read_frame(t)).save(f"{OUT}/prev_{t:05.2f}.jpg", quality=88)
    sys.exit()

dec = subprocess.Popen(["ffmpeg", "-v", "error", "-i", A["base"], "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], stdout=subprocess.PIPE)
enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                        "-i", A["mix"], "-map", "0:v", "-map", "1:a", "-c:v", "libx264", "-preset", "slow", "-crf", "17", "-pix_fmt", "yuv420p",
                        "-movflags", "+faststart", "-c:a", "aac", "-b:a", "192k", "-shortest", OUT], stdin=subprocess.PIPE)
n = int(DUR * FPS)
for i in range(n):
    buf = dec.stdout.read(1920 * 1080 * 3)
    fr = Image.frombuffer("RGB", (1920, 1080), buf).copy() if len(buf) == 1920 * 1080 * 3 else Image.new("RGB", (1920, 1080))
    enc.stdin.write(compose(i / FPS, fr).tobytes())
    if i % 200 == 0: print(i, flush=True)
enc.stdin.close(); enc.wait(); print("done", n)
