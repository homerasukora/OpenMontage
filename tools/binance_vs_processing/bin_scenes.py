SUB = font("Black", 60)
H2 = font("ExtraBold", 50)

H2F = font("ExtraBold", 44)

# ---------- icons ----------
def icon_x(d, cx, cy, s, a, col=None):
    c = rgba(col or RED, a); r = 0.32 * s
    d.line([(cx - r, cy - r), (cx + r, cy + r)], fill=c, width=7); d.line([(cx + r, cy - r), (cx - r, cy + r)], fill=c, width=7)
def icon_check(d, cx, cy, s, a):
    d.line([(cx - 0.32 * s, cy), (cx - 0.08 * s, cy + 0.26 * s), (cx + 0.36 * s, cy - 0.28 * s)], fill=rgba(NEON, a), width=8, joint="curve")
def icon_refresh(d, cx, cy, s, a):
    r = 0.4 * s; d.arc((cx - r, cy - r, cx + r, cy + r), 30, 320, fill=rgba(NEON, a), width=6)
    d.polygon([(cx + r * 0.95, cy - 0.38 * s), (cx + r * 0.95, cy + 0.02 * s), (cx + r * 0.45, cy - 0.15 * s)], fill=rgba(NEON, a))
def icon_top(d, cx, cy, s, a):
    r = 0.45 * s; d.ellipse((cx - r, cy - r, cx + r, cy + r), outline=rgba(NEON, a), width=5)
    d.text((cx, cy + 2), "#1", font=font("Black", int(s * 0.42)), fill=rgba(NEON, a), anchor="mm")
def icon_wait(d, cx, cy, s, a, t=0.0):
    r = 0.42 * s; d.ellipse((cx - r, cy - r, cx + r, cy + r), outline=rgba(NEON, 0.35 * a), width=5)
    st = (t * 300) % 360; d.arc((cx - r, cy - r, cx + r, cy + r), st, st + 90, fill=rgba(NEON, a), width=6)
def icon_shield(d, cx, cy, s, a):
    w, h = 0.42 * s, 0.5 * s
    d.polygon([(cx, cy - h), (cx + w, cy - h * 0.62), (cx + w * 0.85, cy + h * 0.25), (cx, cy + h), (cx - w * 0.85, cy + h * 0.25), (cx - w, cy - h * 0.62)], outline=rgba(NEON, a), width=5)
    icon_check(d, cx, cy, s * 0.6, a)
def icon_bell(d, cx, cy, s, a):
    d.arc((cx - 0.32 * s, cy - 0.42 * s, cx + 0.32 * s, cy + 0.3 * s), 180, 360, fill=rgba(NEON, a), width=5)
    d.line([(cx - 0.32 * s, cy - 0.06 * s), (cx - 0.32 * s, cy + 0.22 * s), (cx - 0.44 * s, cy + 0.3 * s), (cx + 0.44 * s, cy + 0.3 * s), (cx + 0.32 * s, cy + 0.22 * s), (cx + 0.32 * s, cy - 0.06 * s)], fill=rgba(NEON, a), width=5)
    r = 0.08 * s; d.ellipse((cx - r, cy + 0.36 * s, cx + r, cy + 0.52 * s), fill=rgba(NEON, a))
def icon_store(d, cx, cy, s, a):
    d.line([(cx - 0.5 * s, cy - 0.1 * s), (cx - 0.38 * s, cy - 0.42 * s), (cx + 0.38 * s, cy - 0.42 * s), (cx + 0.5 * s, cy - 0.1 * s), (cx - 0.5 * s, cy - 0.1 * s)], fill=rgba(NEON, a), width=5)
    d.rectangle((cx - 0.42 * s, cy - 0.1 * s, cx + 0.42 * s, cy + 0.45 * s), outline=rgba(NEON, a), width=5)
def icon_phone(d, cx, cy, s, a):
    w, h = 0.6 * s, s
    d.rounded_rectangle((cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2), int(s * 0.12), outline=rgba(NEON, a), width=4)
    d.line([(cx - 0.1 * s, cy + h / 2 - 0.12 * s), (cx + 0.1 * s, cy + h / 2 - 0.12 * s)], fill=rgba(NEON, a), width=4)
def icon_bank(d, cx, cy, s, a):
    top, base = cy - 0.5 * s, cy + 0.5 * s
    d.polygon([(cx - 0.55 * s, top + 0.3 * s), (cx, top), (cx + 0.55 * s, top + 0.3 * s)], outline=rgba(NEON, a), width=5)
    for i in range(4):
        x = cx - 0.36 * s + i * 0.24 * s; d.line([(x, top + 0.42 * s), (x, base - 0.12 * s)], fill=rgba(NEON, a), width=5)
    d.line([(cx - 0.55 * s, base), (cx + 0.55 * s, base)], fill=rgba(NEON, a), width=6)
def icon_clock(d, cx, cy, s, a):
    r = 0.44 * s; d.ellipse((cx - r, cy - r, cx + r, cy + r), outline=rgba(NEON, a), width=5)
    d.line([(cx, cy), (cx, cy - 0.28 * s)], fill=rgba(NEON, a), width=5); d.line([(cx, cy), (cx + 0.2 * s, cy + 0.1 * s)], fill=rgba(NEON, a), width=5)
def icon_route(d, cx, cy, s, a):
    for dx, dy in ((-0.38, -0.3), (0.38, -0.3), (0, 0.36)):
        r = 0.12 * s; d.ellipse((cx + dx * s - r, cy + dy * s - r, cx + dx * s + r, cy + dy * s + r), fill=rgba(NEON, a))
        d.line([(cx, cy), (cx + dx * s, cy + dy * s)], fill=rgba(NEON, a), width=4)

def arrow_v(L, x, y0, y1, prog, a, t):
    if prog <= 0: return
    ye = y0 + (y1 - y0) * prog
    L.n.line([(x, y0), (x, ye)], fill=rgba(NEON, 0.5 * a), width=4)
    if prog >= 1:
        L.n.line([(x, y1), (x - 13, y1 - 15)], fill=rgba(NEON, a), width=5); L.n.line([(x, y1), (x + 13, y1 - 15)], fill=rgba(NEON, a), width=5)
        f = (t * 1.1) % 1.0; py = y0 + (y1 - y0) * f; L.n.ellipse((x - 6, py - 6, x + 6, py + 6), fill=rgba(NEON, a))

# ---------- media ----------
RX0, RY0, RX1, RY1 = 1255, 150, 1875, 900
RCX, RW, RH = (RX0 + RX1) // 2, RX1 - RX0, RY1 - RY0

def ptitle(L, y, txt, a, size=46):
    ctext(L.t, (RCX, y), txt, fit(L.t, txt, "ExtraBold", size, RW - 80), WHITE, a)
def glass(L, a, box=(RX0, RY0, RX1, RY1)):
    if a <= 0: return
    L.f.rounded_rectangle(box, 36, fill=(6, 16, 10, int(240 * a))); L.n.rounded_rectangle(box, 36, outline=rgba(NEON, 0.9 * a), width=4)

def paste_card(img, L, pic, x, y, a, r=26):
    if a <= 0: return
    m = Image.new("L", pic.size, 0); ImageDraw.Draw(m).rounded_rectangle((0, 0, pic.width - 1, pic.height - 1), r, fill=int(255 * a))
    img.paste(pic, (int(x), int(y)), m)
    L.n.rounded_rectangle((x - 3, y - 3, x + pic.width + 3, y + pic.height + 3), r + 2, outline=rgba(NEON, a), width=4)

def decode(args, w, h):
    p = subprocess.run(["ffmpeg", "-v", "error"] + args + ["-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True).stdout
    n = len(p) // (w * h * 3); return np.frombuffer(p[: n * w * h * 3], np.uint8).reshape(n, h, w, 3)

# Binance phone recording (status bar cropped), pre-scaled
PH_W, PH_H = 304, 636
PHONE = decode(["-i", A["binance_screen"], "-vf", f"fps=25,crop=1320:2758:0:110,scale={PH_W}:{PH_H}"], PH_W, PH_H)
def phone_img(ts): return Image.fromarray(PHONE[int(clamp(ts * 25, 0, len(PHONE) - 1))])

# Binance logo: original file, circular mask drops the white background
_bl = Image.open(A["binance_logo"]).convert("RGB"); _c = min(_bl.size) // 2
_bl = _bl.crop((_c - 372, _c - 372, _c + 372, _c + 372)).resize((600, 600), Image.LANCZOS)
_m = Image.new("L", (600, 600), 0); ImageDraw.Draw(_m).ellipse((4, 4, 595, 595), fill=255); _bl.putalpha(_m)
def blogo(size, a):
    g = _bl.resize((size, size), Image.LANCZOS); g.putalpha(g.getchannel("A").point(lambda v: int(v * clamp(a)))); return g

# KoiPay dashboard clips (personal data / third-party branding blurred, then cropped) — shown full-screen
SC = {s["name"]: s for s in json.load(open(A["dash_scenes"]))["scenes"]}
DCROP = {"home": (395, 515, 1120, 450), "forwarder": (640, 260, 640, 584), "payouts": (395, 100, 1120, 520)}
DMAXW, DMAXH = 1320, 720
DASH = {}
for nm, (x, y, w, h) in DCROP.items():
    sc = SC[nm]; s_ = min(DMAXW / w, DMAXH / h); cw, ch = int(w * s_), int(h * s_)
    fr = decode(["-ss", f"{sc['s']:.3f}", "-t", f"{sc['e'] - sc['s']:.3f}", "-i", A["dash_base"], "-vf", "fps=25"], 1920, 1080)
    out = []
    for f in fr:
        im = Image.fromarray(f)
        for b in sc["blur"]: im.paste(im.crop(tuple(b)).filter(ImageFilter.GaussianBlur(16)), tuple(b[:2]))
        out.append(np.asarray(im.crop((x, y, x + w, y + h)).resize((cw, ch), Image.LANCZOS)))
    DASH[nm] = out
def dash_img(nm, ts): fr = DASH[nm]; return Image.fromarray(fr[int(clamp(ts * 25, 0, len(fr) - 1))])

def seg_of(t): return max(i for i, c in enumerate(CUTS) if c <= t + 1e-6)
def seg_a(t, i, d=0.3):
    s0 = CUTS[i]; s1 = CUTS[i + 1] if i + 1 < len(CUTS) else DUR + 1
    return min(appear(t, s0 + 0.05, d), 1 - ease((t - (s1 - 0.12)) / 0.12))
def win(t, t0, t1, d=0.3): return min(appear(t, t0, d), 1 - ease((t - t1) / 0.2))

def fit(d, txt, style, size, maxw):
    f = font(style, size)
    while d.textlength(txt, font=f) > maxw and size > 22: size -= 2; f = font(style, size)
    return f
def row(L, y, txt, ic, k, base, h=100, col=WHITE, edge=NEON, fill=(10, 26, 16), fnt=LABEL, t=0.0):
    fnt = fit(L.t, txt, "ExtraBold" if fnt is not LABEL else "SemiBold", fnt.size, RX1 - 30 - 40 - (RX0 + 140))
    box = (RX0 + 30, y - h / 2, RX1 - 30, y + h / 2)
    L.f.rounded_rectangle(box, 26, fill=rgba(fill if k > 0.05 else (6, 16, 10), max(k, 0.96 * base))); L.n.rounded_rectangle(box, 26, outline=rgba(edge, k), width=3)
    if ic is icon_wait: ic(L.n, RX0 + 88, y, 54, k, t)
    elif ic: ic(L.n, RX0 + 88, y, 54, k)
    ctext(L.t, (RX0 + 140, y), txt, fnt, col, k, "lm")

# ---------- camera ----------
SIDE = (1.18, 1920 - 1920 / 1.18 / 2, 540); WIDE = (1.0, 960, 540); FACE = (1.42, 880, 470)
def cam_keys():
    k = []
    def at(t, st, d=0.55): k.append((t, st, d))
    c = CUTS
    at(0, (1.12, 960, 540), 0); at(0.05, WIDE, 0.8); at(cue("binance", 0) - 0.2, SIDE); at(cue("processing", 0) - 0.15, FACE, 0.45)
    at(c[1], SIDE, 0)
    at(c[3], WIDE, 0); at(cue("and", 3) + 0.4, SIDE)
    at(c[4], FACE, 0); at(cue("removes", 4) + 0.3, SIDE)
    at(c[5], WIDE, 0); at(cue("here's", 5) + 0.3, SIDE)
    at(c[6], SIDE, 0); at(c[7] - 0.01, WIDE, 0)
    at(c[8], FACE, 0); at(cue("volume", 8) - 0.35, SIDE)
    at(c[9], WIDE, 0); at(cue("telegram", 9) - 0.4, SIDE)
    at(c[10], FACE, 0); at(cue("discuss", 10) - 0.2, SIDE)
    at(c[11], WIDE, 0); at(c[11] + 0.1, FACE, 1.2)
    return sorted(k)
CAM = None
def cam(t):
    prev = CAM[0][1]; cur = CAM[0][1]
    for tk, st, d in CAM:
        if tk > t: break
        p = 1.0 if d == 0 else ease_io((t - tk) / d)
        cur = tuple(prev[j] + (st[j] - prev[j]) * p for j in range(3)); prev = cur if p >= 1 else cur
    return cur
def apply_cam(frame, st):
    z, cx, cy = st
    if abs(z - 1) < 1e-3: return frame
    w_, h_ = W / z, H / z; x0 = clamp(cx - w_ / 2, 0, W - w_); y0 = clamp(cy - h_ / 2, 0, H - h_)
    return frame.resize((W, H), Image.BICUBIC, box=(x0, y0, x0 + w_, y0 + h_))

# ---------- full-screen green scenes ----------
def _fs_bg():
    arr = np.asarray(BG).astype(np.float32); yy, xx = np.mgrid[0:H, 0:W]
    arr += (np.exp(-(((xx - W / 2) / 900) ** 2 + ((yy - H / 2) / 520) ** 2)) * 0.45)[..., None] * np.array(NEON, np.float32)
    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))
FS_BG = _fs_bg()
PIP_C, PIP_R = (270, 765), 160
def pip(img, L, frame, a):
    if a <= 0: return
    d = 2 * PIP_R; src = frame.resize((d, d), Image.BICUBIC, box=(880 - 330, 470 - 330, 880 + 330, 470 + 330))
    m = Image.new("L", (d, d), 0); ImageDraw.Draw(m).ellipse((0, 0, d - 1, d - 1), fill=int(255 * a))
    img.paste(src, (PIP_C[0] - PIP_R, PIP_C[1] - PIP_R), m)
    L.n.ellipse((PIP_C[0] - PIP_R - 4, PIP_C[1] - PIP_R - 4, PIP_C[0] + PIP_R + 4, PIP_C[1] + PIP_R + 4), outline=rgba(NEON, a), width=6)
def wipe(t, t0, t1, d=0.45):
    """0..1 reveal amount of a full-screen scene living in [t0, t1]."""
    return min(ease_io((t - t0) / d), ease_io((t1 - t) / 0.35))

def card(L, box, k, edge=NEON, r=34):
    L.f.rounded_rectangle(box, r, fill=(6, 16, 10, int(240 * k))); L.n.rounded_rectangle(box, r, outline=rgba(edge, k), width=4)

def fs_math(img, L, t, t0):
    X = 1180
    pill(L, X, 175, "Binance P2P · spread math", appear(t, CUTS[2] + 0.35), filled=True, fnt=font("ExtraBold", 46), h=84, padx=40)
    k1 = appear(t, cue("1%", 2) - 0.15); k2 = appear(t, cue("₹1", 2) - 0.15)
    card(L, (560, 270, 1000, 520), k1); ctext(L.t, (780, 365), "1%", font("Black", 120), NEON, k1); ctext(L.t, (780, 465), "spread", LABEL, GREY, k1)
    ctext(L.t, (1070, 395), "×", font("Black", 90), WHITE, k2)
    card(L, (1140, 270, 1800, 520), k2); ctext(L.t, (1470, 365), "₹1,00,000", font("Black", 104), WHITE, k2); ctext(L.t, (1470, 465), "volume", LABEL, GREY, k2)
    k3 = appear(t, cue("₹1,000", 2) - 0.15, 0.25)
    ctext(L.t, (X, 640), "≈ ₹1,000", font("Black", 140), NEON, k3); ctext(L.t, (X, 735), "your margin", LABEL, GREY, k3)
    k4 = appear(t, cue("if", 2) - 0.1)
    if k4 > 0:
        txt = "Only if the rate doesn't move"; fnt = font("Bold", 42); tw = L.t.textlength(txt, font=fnt)
        box = (X - tw / 2 - 110, 800, X + tw / 2 + 40, 880); L.f.rounded_rectangle(box, 40, fill=(30, 10, 10, int(225 * k4))); L.n.rounded_rectangle(box, 40, outline=rgba(RED, k4), width=3)
        x0 = box[0] + 30; pts = [(x0 + j * 5, 840 + 14 * math.sin(j * 0.9 + t * 6) * math.exp(-0.02 * j)) for j in range(12)]
        L.n.line(pts, fill=rgba(RED, k4), width=4); ctext(L.t, (box[0] + 100, 840), txt, fnt, WHITE, k4, "lm")

def fs_rates(img, L, t, t0):
    X = 1180
    pill(L, X, 175, "KoiPay · base rates", appear(t, CUTS[7] + 0.35), filled=True, fnt=font("ExtraBold", 46), h=84, padx=40)
    cols = [("PayIn ↓", "≈ 3%", "≈ ₹3,000", 560, cue("3%", 7), cue("₹3,000", 7)), ("PayOut ↑", "≈ 1%", "≈ ₹1,000", 1200, cue("1%", 7), cue("₹1,000", 7))]
    for tag, rate, res, x0, ta, tb in cols:
        k = appear(t, ta - 0.2, 0.3); dy = int(24 * (1 - k)); cx = x0 + 300
        card(L, (x0, 250 + dy, x0 + 600, 800 + dy), k)
        pill(L, cx, 320 + dy, tag, k, filled=True, fnt=font("ExtraBold", 48), h=88, padx=36)
        ctext(L.t, (cx, 470 + dy), rate, font("Black", 140), NEON, k)
        kb = appear(t, tb - 0.25, 0.3)
        ctext(L.t, (cx, 610 + dy), "on ₹1,00,000", font("Bold", 48), WHITE, kb); ctext(L.t, (cx, 705 + dy), res, font("Black", 86), NEON, kb)
    ctext(L.t, (X, 870), "Your manager confirms your exact terms", font("SemiBold", 36), GREY, appear(t, cue("so", 7)))

def wrap(d, txt, fnt, maxw):
    out, cur = [], ""
    for w in txt.split():
        nxt = (cur + " " + w).strip()
        if d.textlength(nxt, font=fnt) <= maxw or not cur: cur = nxt
        else: out.append(cur); cur = w
    return out + [cur]
def callouts(L, items, t, k, x0=60, x1=490, y=190, ymax=575):
    for txt, at in items:
        kc = k * appear(t, at - 0.15, 0.25)
        if kc <= 0: continue
        fnt = font("Bold", 34); lines = wrap(L.t, txt, fnt, x1 - x0 - 56)
        h = 26 + 42 * len(lines)
        if y + h > ymax: break
        L.f.rounded_rectangle((x0, y, x1, y + h), 24, fill=(6, 18, 10, int(235 * kc))); L.n.rounded_rectangle((x0, y, x1, y + h), 24, outline=rgba(NEON, kc), width=3)
        for j, ln in enumerate(lines): ctext(L.t, (x0 + 28, y + 13 + 21 + 42 * j), ln, fnt, WHITE, kc, "lm")
        y += h + 14

def fs_dash(nm, title, calls):
    def f(img, L, t, t0):
        k = appear(t, t0 + 0.3, 0.3); pic = dash_img(nm, t - t0); X = 1195
        y = 552 - pic.height / 2 + 24 * (1 - k)
        paste_card(img, L, pic, X - pic.width / 2, y, k, r=24)
        pill(L, X, y - 58, title, k, filled=True, fnt=font("ExtraBold", 46), h=84, padx=40)
        callouts(L, calls, t, k)
    return f

def endcard(L, t, t0):
    k0 = appear(t, t0 + 0.2, 0.35)
    ctext(L.t, (960, 150), "Start with KoiPay", font("Black", 84), WHITE, k0)
    cards = [("NEW TO P2P", "Free training", "@koiedubot", 200, t0 + 0.35), ("EXPERIENCED", "Start working", "@koipayp2p2bot", 1020, t0 + 0.6)]
    tg = TG.resize((150, 150), Image.LANCZOS)
    for tag, lab, user, x0, at in cards:
        k = appear(t, at, 0.35); dy = int(30 * (1 - k)); box = (x0, 235 + dy, x0 + 700, 785 + dy); cx = x0 + 350
        L.f.rounded_rectangle(box, 40, fill=(6, 16, 10, int(246 * k))); L.n.rounded_rectangle(box, 40, outline=rgba(NEON, k), width=5)
        fnt = font("Black", 44); tw = L.t.textlength(tag, font=fnt)
        L.f.rounded_rectangle((cx - tw / 2 - 34, 265 + dy, cx + tw / 2 + 34, 345 + dy), 40, fill=rgba(NEON, k))
        ctext(L.t, (cx, 306 + dy), tag, fnt, (4, 20, 10), k)
        g = tg.copy(); g.putalpha(g.getchannel("A").point(lambda v: int(v * k))); L.text.alpha_composite(g, (cx - 75, 380 + dy))
        ctext(L.t, (cx, 590 + dy), lab, TITLE, WHITE, k)
        pill(L, cx, 695 + dy, user, k, filled=True, fnt=font("Black", 54 if len(user) < 12 else 48), h=100, padx=40)
    k3 = appear(t, cue("link", 11) - 0.2)
    if k3 > 0:
        txt = "Links in the description ↓"; fnt = font("Black", 50); tw = L.t.textlength(txt, font=fnt)
        L.f.rounded_rectangle((960 - tw / 2 - 44, 825, 960 + tw / 2 + 44, 905), 40, fill=rgba(NEON, k3))
        ctext(L.t, (960, 866), txt, fnt, (4, 20, 10), k3)

# ---------- side overlays on the presenter ----------
def overlays(img, L, t, i):
    a = seg_a(t, i)
    if i == 0:
        tb, tp = cue("binance", 0), cue("processing", 0)
        A_ = win(t, tb - 0.1, tp - 0.3)
        glass(L, A_)
        L.text.alpha_composite(blogo(150, A_), (RCX - 75, RY0 + 40)); ptitle(L, RY0 + 245, "Binance P2P routine", A_)
        items = [("Update your ad price", icon_refresh, cue("update", 0)), ("Fight for the top spot", icon_top, cue("fight", 0)), ("Wait for a match…", icon_wait, cue("wait", 0))]
        for j, (lab, ic, at) in enumerate(items): row(L, RY0 + 380 + j * 130, lab, ic, A_ * appear(t, at - 0.15), A_, t=t)
    elif i == 1:
        tm = cue("merchant", 1); ts = cue("sell", 1)
        k = a * appear(t, CUTS[1] + 0.3)
        src = (t - CUTS[1]) * 0.9 if t < ts - 0.2 else 10.6 + (t - ts + 0.2)
        ph = phone_img(src); x, y = RCX - PH_W / 2, 205 + 20 * (1 - k)
        if k > 0: bz = Image.new("RGBA", (PH_W + 28, PH_H + 28), (0, 0, 0, 0)); ImageDraw.Draw(bz).rounded_rectangle((0, 0, PH_W + 27, PH_H + 27), 44, fill=(10, 12, 14, int(255 * k))); img.paste(bz, (int(x - 14), int(y - 14)), bz)
        paste_card(img, L, ph, x, y, k, r=32)
        L.text.alpha_composite(blogo(76, k), (int(x + PH_W - 40), int(y - 26)))
        pill(L, RCX, 128, "Marketplace", a * appear(t, tm - 0.1), filled=True, fnt=PILL, h=78)
        tag = "Buy ads" if t < ts - 0.2 else "Sell ads"
        pill(L, RCX, 780, tag, a * appear(t, cue("buy", 1) - 0.1), fnt=PILL, h=78)
        pill(L, RCX, 900, "Your margin = spread", a * appear(t, cue("spread", 1) - 0.15), filled=True, fnt=PILL, h=84)
    elif i == 3:
        A_ = a * appear(t, cue("and", 3) + 0.45)
        glass(L, A_); ptitle(L, RY0 + 75, "On P2P, risks are yours", A_)
        items = [("Price wars", "price"), ("Slow days", "slow"), ("“Paid” without paying", "buyers"), ("Appeals", "appeals")]
        for j, (lab, w) in enumerate(items): row(L, RY0 + 185 + j * 112, lab, icon_x, A_ * appear(t, cue(w, 3) - 0.15), A_, h=92)
        kf = A_ * appear(t, cue("frozen", 3) - 0.3)
        y = RY0 + 185 + 4 * 112 + 22
        row(L, y, "Bank account frozen", icon_x, kf, A_, h=104, edge=RED, fill=(48, 12, 12), fnt=font("ExtraBold", 40))
    elif i == 4:
        tm = cue("merchants", 4); A_ = a * appear(t, cue("removes", 4) + 0.3)
        glass(L, A_)
        kA = A_ * (1 - appear(t, tm - 0.35, 0.25))
        if kA > 0:
            ptitle(L, RY0 + 75, "Processing removes", kA)
            for j, lab in enumerate(("Marketplace layer", "Ads & price updates", "Hunting for buyers")):
                kk = kA * appear(t, cue("removes", 4) + 0.35 + 0.35 * j); y = RY0 + 230 + j * 150
                row(L, y, lab, icon_x, kk, A_, h=110, col=GREY)
                if kk > 0.5: L.t.line([(RX0 + 140, y + 2), (RX0 + 140 + (L.t.textlength(lab, font=fit(L.t, lab, "SemiBold", 40, RX1 - 30 - 40 - (RX0 + 140)))) * ease((kk - 0.5) * 2), y + 2)], fill=rgba(RED, kk), width=5)
        kB = A_ * appear(t, tm - 0.2, 0.25)
        if kB > 0:
            ptitle(L, RY0 + 75, "How requests reach you", kB)
            nodes = [("Merchant request", icon_store, tm), ("KoiPay routing", icon_route, cue("routes", 4)), ("You, the trader", icon_phone, cue("traders", 4))]
            ys = [RY0 + 220, RY0 + 420, RY0 + 620]
            for j, (lab, ic, at) in enumerate(nodes):
                k = kB * appear(t, at - 0.15, 0.25); row(L, ys[j], lab, ic, k, A_, h=110)
                if j == 1 and k > 0: L.text.alpha_composite(LOGO_S(k), (RX1 - 110, ys[j] - 33))
                if j: arrow_v(L, RCX, ys[j - 1] + 58, ys[j] - 58, ease((t - at + 0.15) / 0.3), kB, t)
    elif i == 5:
        tf = cue("sms", 5); A_ = a * appear(t, cue("here's", 5) + 0.3)
        kA = A_ * (1 - appear(t, tf - 0.3, 0.25))
        if kA > 0:
            glass(L, kA)
            ctext(L.t, (RCX, RY0 + 75), "KoiPay PayIn ↓", font("Black", 58), NEON, kA)
            nodes = [("Client pays via UPI", icon_phone, cue("upi", 5)), ("Your business account", icon_bank, cue("business", 5))]
            ys = [RY0 + 250, RY0 + 470]
            for j, (lab, ic, at) in enumerate(nodes):
                k = kA * appear(t, at - 0.2, 0.25); row(L, ys[j], lab, ic, k, kA, h=120)
                if j: arrow_v(L, RCX, ys[j - 1] + 62, ys[j] - 62, ease((t - at + 0.2) / 0.3), kA, t)
    elif i == 6:
        tp = cue("payout", 6)
        kA = a * (1 - appear(t, tp - 0.3, 0.25))
        if kA > 0:
            glass(L, kA); ptitle(L, RY0 + 75, "After you confirm", kA)
            items = [("Anti-Fraud check", icon_shield, cue("anti-fraud", 6)), ("Merchant callback", icon_bell, cue("callback", 6)), ("Commission in dashboard", icon_check, cue("commission", 6))]
            for j, (lab, ic, at) in enumerate(items):
                k = kA * appear(t, at - 0.15); y = RY0 + 230 + j * 190; row(L, y, lab, ic, k, kA, h=120)
                if j: arrow_v(L, RCX, y - 190 + 62, y - 62, ease((t - at + 0.15) / 0.3), kA, t)
    elif i == 8:
        A_ = a * appear(t, cue("volume", 8) - 0.1)
        glass(L, A_)
        ctext(L.t, (RCX, RY0 + 70), "You earn per", LABEL, GREY, A_); ptitle(L, RY0 + 130, "completed operation", A_)
        k = A_ * appear(t, cue("volume", 8)); y = RY0 + 250
        row(L, y, "Volume not guaranteed", icon_x, k, A_, h=100, edge=RED, fill=(40, 12, 12))
        ctext(L.t, (RCX, RY0 + 360), "It depends on", LABEL, GREY, A_ * appear(t, cue("depends", 8) - 0.1))
        row(L, RY0 + 440, "KoiPay routing", icon_route, A_ * appear(t, cue("routing", 8) - 0.15), A_, h=90)
        row(L, RY0 + 545, "Your limits", icon_bank, A_ * appear(t, cue("limits", 8) - 0.15), A_, h=90)
        pill(L, RCX, RY0 + 665, "Manager confirms your rates", A_ * appear(t, cue("manager", 8) - 0.1), filled=True, fnt=font("Bold", 36), h=76, padx=28)
    elif i == 9:
        tt = cue("telegram", 9)
        kB = a * appear(t, tt - 0.1, 0.3)
        if kB > 0:
            glass(L, kB)
            tg = TG.copy(); tg.putalpha(tg.getchannel("A").point(lambda v: int(v * kB))); L.text.alpha_composite(tg, (RCX - 85, RY0 + 50))
            ptitle(L, RY0 + 280, "Telegram bot", kB)
            row(L, RY0 + 410, "New request alerts", icon_bell, kB * appear(t, cue("alerts", 9) - 0.1), kB, h=104)
            k24 = kB * appear(t, cue("24/7", 9) - 0.3)
            ctext(L.t, (RCX, RY0 + 575), "24/7", font("Black", 120), NEON, k24); ctext(L.t, (RCX, RY0 + 670), "support", TITLE, WHITE, k24)
    elif i == 10:
        A_ = a * appear(t, cue("discuss", 10) - 0.05)
        glass(L, A_)
        ptitle(L, RY0 + 80, "Before you start", A_)
        items = [("Business bank accounts", icon_bank, "bank"), ("Working funds", icon_coin, "working"), ("Your hours", icon_clock, "hours")]
        for j, (lab, ic, w) in enumerate(items): row(L, RY0 + 220 + j * 135, lab, ic, A_ * appear(t, cue(w, 10) - 0.15), A_, h=110)
        pill(L, RCX, RY1 - 140, "With your manager", A_ * appear(t, cue("manager", 10) - 0.15), filled=True, fnt=PILL, h=80)
        ctext(L.t, (RCX, RY1 - 55), "Active work · not passive income", font("SemiBold", 32), GREY, A_ * appear(t, cue("manager", 10) + 0.2))

def icon_coin(d, cx, cy, s, a):
    r = 0.45 * s; d.ellipse((cx - r, cy - r, cx + r, cy + r), outline=rgba(NEON, a), width=5)
    d.text((cx, cy + 2), "₹", font=font("Black", int(s * 0.62)), fill=rgba(NEON, a), anchor="mm")
def LOGO_S(k):
    g = LOGO.resize((66, 66), Image.LANCZOS); g.putalpha(g.getchannel("A").point(lambda v: int(v * k))); return g

#@@SUBS@@
# ---------- compose ----------
FSW = None
def fs_windows():
    w = [(CUTS[2], CUTS[3], fs_math),
         (cue("sms", 5) - 0.25, CUTS[6], fs_dash("forwarder", "SMS Forwarder", [("Reads the bank SMS", cue("reads", 5)), ("✓ Confirms PayIn automatically", cue("automatically", 5))])),
         (cue("payout", 6) - 0.25, CUTS[7], fs_dash("payouts", "PayOuts", [("You send an approved payment", cue("approved", 6))])),
         (CUTS[7], CUTS[8], fs_rates),
         (CUTS[9] + 0.25, cue("telegram", 9) - 0.3, fs_dash("home", "Trader Room", [("Incoming requests", cue("incoming", 9)), ("Statuses", cue("statuses", 9)), ("Limits", cue("limits", 9)), ("History", cue("history", 9)), ("Commission", cue("commission", 9))])),
         (cue("apply", 11) - 0.35, DUR + 5, None)]
    return w
def compose(t, frame):
    L = Layers(); i = seg_of(t)
    win_ = next((w for w in FSW if w[0] <= t < w[1]), None)
    if win_:
        t0, t1, fn = win_
        cont_in = any(abs(w[1] - t0) < 1e-3 for w in FSW); cont_out = any(abs(w[0] - t1) < 1e-3 for w in FSW)
        p = min(1.0 if cont_in else ease_io((t - t0) / 0.45), 1.0 if cont_out else ease_io((t1 - t) / 0.35))
        base = apply_cam(frame, cam(t))
        fs = FS_BG.copy(); L2 = Layers()
        if fn: pip(fs, L2, frame, 1.0 if cont_in else appear(t, t0 + 0.3, 0.3)); fn(fs, L2, t, t0)
        else: endcard(L2, t, t0)
        fs = fs.convert("RGBA"); fs = Image.alpha_composite(fs, L2.fill)
        glow = L2.neon.resize((W // 2, H // 2), Image.BILINEAR).filter(ImageFilter.GaussianBlur(9)).resize((W, H), Image.BILINEAR)
        fs = Image.alpha_composite(Image.alpha_composite(fs, glow), glow); fs = Image.alpha_composite(fs, L2.neon); fs = Image.alpha_composite(fs, L2.text)
        out = base.convert("RGBA")
        if p > 0:
            xe = int(W * (1 - p)); out.paste(fs.crop((xe, 0, W, H)), (xe, 0))
            if p < 1: ImageDraw.Draw(out).rectangle((xe - 6, 0, xe + 6, H), fill=rgba(NEON, 0.9))
    else:
        img = apply_cam(frame, cam(t))
        overlays(img, L, t, i)
        out = img.convert("RGBA")
        out = Image.alpha_composite(out, L.fill)
        glow = L.neon.resize((W // 2, H // 2), Image.BILINEAR).filter(ImageFilter.GaussianBlur(9)).resize((W, H), Image.BILINEAR)
        out = Image.alpha_composite(Image.alpha_composite(out, glow), glow)
        out = Image.alpha_composite(out, L.neon); out = Image.alpha_composite(out, L.text)
    draw_brand(out); draw_subs(t, out)
    return out.convert("RGB")
CAM = cam_keys(); FSW = fs_windows()

def read_frame(t):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{t:.3f}", "-i", A["base"], "-frames:v", "1", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True).stdout
    return Image.frombuffer("RGB", (1920, 1080), raw).copy()

if PREVIEW:
    for t in PREVIEW: compose(t, read_frame(t)).save(f"{OUT}/prev_{t:06.2f}.jpg", quality=88)
    sys.exit()

dec = subprocess.Popen(["ffmpeg", "-v", "error", "-i", A["base"], "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], stdout=subprocess.PIPE)
enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                        "-i", A["mix"], "-map", "0:v", "-map", "1:a", "-c:v", "libx264", "-preset", "slow", "-crf", "17", "-pix_fmt", "yuv420p",
                        "-movflags", "+faststart", "-c:a", "aac", "-b:a", "192k", "-shortest", OUT], stdin=subprocess.PIPE)
n = int(DUR * FPS)
for k in range(n):
    buf = dec.stdout.read(1920 * 1080 * 3)
    fr = Image.frombuffer("RGB", (1920, 1080), buf).copy() if len(buf) == 1920 * 1080 * 3 else Image.new("RGB", (1920, 1080))
    enc.stdin.write(compose(k / FPS, fr).tobytes())
    if k % 250 == 0: print(k, flush=True)
enc.stdin.close(); enc.wait(); print("done", n)
