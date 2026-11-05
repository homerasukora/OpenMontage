SUB = font("Black", 64)

# ---------- helpers (same look as the 16:9 version) ----------
def fit(d, txt, style, size, maxw):
    f = font(style, size)
    while d.textlength(txt, font=f) > maxw and size > 22: size -= 2; f = font(style, size)
    return f
def cover(im, cw, ch, z=1.0, fx=None, fy=None):
    pw, ph = im.size; s = max(cw / pw, ch / ph) * z; w_, h_ = cw / s, ch / s
    fx = pw / 2 if fx is None else fx; fy = ph / 2 if fy is None else fy
    x0 = clamp(fx - w_ / 2, 0, pw - w_); y0 = clamp(fy - h_ / 2, 0, ph - h_)
    return im.crop((int(x0), int(y0), int(x0 + w_), int(y0 + h_))).resize((cw, ch), Image.BICUBIC), (s, x0, y0)
def video_still(path, ts, cw, ch):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{ts:.3f}", "-i", path, "-frames:v", "1", "-vf",
                          f"scale={cw}:{ch}:force_original_aspect_ratio=increase,crop={cw}:{ch}", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True).stdout
    return Image.frombuffer("RGB", (cw, ch), raw).copy()
def paste_card(img, L, pic, x, y, a, r=28, width=4):
    if a <= 0: return
    m = Image.new("L", pic.size, 0); ImageDraw.Draw(m).rounded_rectangle((0, 0, pic.width - 1, pic.height - 1), r, fill=int(255 * a))
    img.paste(pic, (int(x), int(y)), m)
    L.n.rounded_rectangle((x - 3, y - 3, x + pic.width + 3, y + pic.height + 3), r + 2, outline=rgba(NEON, a), width=width)
def glass(L, box, a, r=34):
    if a <= 0: return
    L.f.rounded_rectangle(box, r, fill=(6, 16, 10, int(240 * a))); L.n.rounded_rectangle(box, r, outline=rgba(NEON, 0.9 * a), width=4)
def win(t, t0, t1, d=0.3): return min(appear(t, t0, d), 1 - ease((t - t1) / 0.25))
def decode(args, w, h):
    p = subprocess.run(["ffmpeg", "-v", "error"] + args + ["-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True).stdout
    n = len(p) // (w * h * 3); return np.frombuffer(p[: n * w * h * 3], np.uint8).reshape(n, h, w, 3)
def seg_of(t): return max(i for i, c in enumerate(CUTS) if c <= t + 1e-6)

# ---------- layout: graphics zone on top, people below ----------
TZ = (40, 200, 1040, 860)                 # graphics zone (inside Instagram safe area)
TCX = 540
VB_Y, VB_H = 900, 1020                     # video block
SRC_W = int(1080 * W / VB_H) if False else int(round(1080 * 1080 / VB_H))   # source crop width for 1080x1020
CROP_CX = {0: 860, 2: 920, 3: 930, 4: 930, 5: 760, 6: 760, 7: 740}
SUB_Y = 1560

def _top_bg():
    arr = np.zeros((VB_Y, W, 3), np.float32) + np.array((2, 8, 4), np.float32); yy, xx = np.mgrid[0:VB_Y, 0:W]
    arr += (np.exp(-(((xx - W / 2) / 620) ** 2 + ((yy - 520) / 420) ** 2)) * 0.5)[..., None] * np.array(NEON, np.float32)
    im = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8)); d = ImageDraw.Draw(im, "RGBA")
    for x in range(0, W + 1, 60): d.line([(x, 0), (x, VB_Y)], fill=(46, 232, 122, 14), width=1)
    for y in range(0, VB_Y + 1, 60): d.line([(0, y), (W, y)], fill=(46, 232, 122, 14), width=1)
    return im
TOP_BG = _top_bg()
def _full_bg():
    arr = np.asarray(BG).astype(np.float32); yy, xx = np.mgrid[0:H, 0:W]
    arr += (np.exp(-(((xx - W / 2) / 700) ** 2 + ((yy - H / 2) / 900) ** 2)) * 0.45)[..., None] * np.array(NEON, np.float32)
    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))
FS_BG = _full_bg()

# walk-in: original vertical clip (720x1280), cropped to the video block
VERT = decode(["-i", A["walkin"], "-vf", f"fps=25,crop=720:680:0:190,scale={W}:{VB_H}"], W, VB_H)
def video_block(frame, t, i):
    if i == 1:
        u = t - CUTS[1]; return Image.fromarray(VERT[int(clamp(u * 25, 0, len(VERT) - 1))])
    cx = CROP_CX.get(i, 900); x0 = clamp(cx - SRC_W / 2, 0, 1920 - SRC_W)
    return frame.resize((W, VB_H), Image.BICUBIC, box=(x0, 0, x0 + SRC_W, 1080))

# ---------- assets ----------
SC = {s["name"]: s for s in json.load(open(A["dash_scenes"]))["scenes"]}
DMAXW, DMAXH = 1000, 520
def _dash_fit(nm, crop, t_from=0.0, dur=3.0):
    x, y, w, h = crop; s_ = min(DMAXW / w, DMAXH / h); cw, ch = int(w * s_), int(h * s_); sc = SC[nm]
    fr = decode(["-ss", f"{sc['s'] + t_from:.3f}", "-t", f"{dur:.3f}", "-i", A["dash_base"], "-vf", "fps=25"], 1920, 1080)
    out = []
    for f in fr:
        im = Image.fromarray(f)
        for b in sc["blur"] + [[395, 0, 500, 66]]: im.paste(im.crop(tuple(b)).filter(ImageFilter.GaussianBlur(18)), tuple(b[:2]))   # SurfGate logo + personal data
        out.append(np.asarray(im.crop((x, y, x + w, y + h)).resize((cw, ch), Image.LANCZOS)))
    return out
DM = {"home": _dash_fit("home", (395, 515, 800, 330)), "requests": _dash_fit("payins", (395, 62, 1120, 420), 0.5),
      "history": _dash_fit("report", (395, 62, 1120, 560), 0.5), "commission": _dash_fit("report", (395, 700, 1120, 360), 1.5)}
def dm_img(key, ts): fr = DM[key]; return Image.fromarray(fr[int(clamp(ts * 25, 0, len(fr) - 1))])
RAVI_G = (540, 690)

# ---------- top-zone scenes ----------
def name_card(L, t, k, title, sub):
    glass(L, (TZ[0] + 60, 330, TZ[2] - 60, 700), k)
    lg = LOGO.resize((120, 120), Image.LANCZOS); lg.putalpha(lg.getchannel("A").point(lambda v: int(v * k))); L.text.alpha_composite(lg, (TCX - 60, 370))
    ctext(L.t, (TCX, 560), title, font("Black", 92), WHITE, k); ctext(L.t, (TCX, 645), sub, TITLE, NEON, k)

def story(img, L, t):
    """Ravi's confirmed story beats: Delhi rickshaw driver, $500 saved, week 1 ₹14,312, full-time now, ₹2,00,000+/month."""
    beats = [(cue("rickshaw", 1) - 0.2, "rick"), (cue("$500", 1) - 0.25, "save"), (cue("started", 1) - 0.2, "koi"),
             (cue("step", 2) - 0.2, "week1"), (cue("later", 2) - 0.2, "fulltime"), (cue("now", 2) - 0.2, "income")]
    cur = [b for b in beats if t >= b[0]]
    if not cur: return False
    t0, kind = cur[-1]; k = appear(t, t0, 0.3) * (1 - ease((t - (CUTS[4] - 0.25)) / 0.25))
    pw, ph = TZ[2] - TZ[0], 560; x0, y0 = TZ[0], TZ[1]
    if kind == "rick":
        paste_card(img, L, video_still(A["rk2"], 2.5 + (t - t0), pw, ph), x0, y0, k)
        pill(L, TCX, 820, "Before: rickshaw driver · Delhi", k, filled=True, fnt=PILL, h=80)
    elif kind == "save":
        pic, tr = cover(PHOTOS["group"], pw, ph, 1.15, 540, 700); paste_card(img, L, pic, x0, y0, k)
        s, gx0, gy0 = tr; cx, cy = x0 + (RAVI_G[0] - gx0) * s, y0 + (RAVI_G[1] - gy0) * s; r = 95
        L.n.ellipse((cx - r, cy - r * 1.2, cx + r, cy + r * 1.2), outline=rgba(NEON, k), width=5)
        pill(L, cx, cy - r * 1.2 - 40, "Ravi", k, filled=True, fnt=SMALL, h=58, padx=22)
        pill(L, TCX, 820, "$500 saved from driving", k, filled=True, fnt=PILL, h=80)
    elif kind == "koi":
        glass(L, (x0, y0, x0 + pw, y0 + ph), k)
        lg = LOGO.resize((150, 150), Image.LANCZOS); lg.putalpha(lg.getchannel("A").point(lambda v: int(v * k))); L.text.alpha_composite(lg, (TCX - 75, y0 + 60))
        ctext(L.t, (TCX, y0 + 320), "$500", font("Black", 130), NEON, k); ctext(L.t, (TCX, y0 + 440), "first deposit to start", TITLE, WHITE, k)
        pill(L, TCX, 820, "Started with KoiPay", k, filled=True, fnt=PILL, h=80)
    elif kind == "week1":
        zk = ease((t - t0 - 0.3) / 0.8)
        pic, tr = cover(PHOTOS["selfie"], pw, ph, 1.0 + 1.5 * zk, 480 + 190 * zk, 640 + 20 * zk); paste_card(img, L, pic, x0, y0, k)
        s, sx0, sy0 = tr; bx0, by0 = x0 + (585 - sx0) * s, y0 + (652 - sy0) * s; bx1, by1 = x0 + (760 - sx0) * s, y0 + (705 - sy0) * s
        if zk > 0.7: L.n.rounded_rectangle((bx0 - 12, by0 - 12, bx1 + 12, by1 + 12), 16, outline=rgba(NEON, k * appear(t, t0 + 1.0)), width=6)
        pill(L, TCX, y0 + 60, "WEEK 1", k, filled=True, fnt=font("Black", 60), h=96, padx=40)
        pill(L, TCX, 820, "Earned: ₹14,312", k, fnt=TITLE, h=90, padx=36)
    elif kind == "fulltime":
        glass(L, (x0, y0, x0 + pw, 860), k)
        ctext(L.t, (TCX, y0 + 70), "Ravi's path", TITLE, WHITE, k)
        rows = [("Before", "Rickshaw driver", t0), ("Then", "Rickshaw + KoiPay", t0 + 0.35), ("Now", "KoiPay full-time ✓", cue("full-time", 2) - 0.2)]
        for j, (tag, lab, at) in enumerate(rows):
            kk = k * appear(t, at, 0.25); y = y0 + 200 + j * 160; on = j == 2
            box = (x0 + 50, y - 62, x0 + pw - 50, y + 62)
            L.f.rounded_rectangle(box, 28, fill=rgba(NEON_DARK if (on and kk > 0.5) else (10, 26, 16), max(kk, 0.96 * k))); L.n.rounded_rectangle(box, 28, outline=rgba(NEON, kk), width=3)
            ctext(L.t, (x0 + 95, y), tag, LABEL, WHITE if on else NEON, kk, "lm")
            ctext(L.t, (x0 + 280, y), lab, fit(L.t, lab, "Bold", 50, pw - 330), WHITE, kk, "lm")
    elif kind == "income":
        glass(L, (x0, y0, x0 + pw, 860), k)
        cy = (y0 + 860) / 2
        ctext(L.t, (TCX, cy - 150), "Ravi now earns", TITLE, GREY, k)
        at = cue("₹2", 2); kk = k * appear(t, at - 0.2, 0.2)
        n = int(200000 * ease((t - at + 0.2) / 1.0)); txt = f"₹{n // 100000},{(n // 1000) % 100:02d},{n % 1000:03d}" if n >= 100000 else f"₹{n // 1000},{n % 1000:03d}" if n >= 1000 else f"₹{n}"
        if n >= 200000: txt += "+"
        ctext(L.t, (TCX, cy), txt, fit(L.t, "₹2,00,000+", "Black", 150, pw - 100), NEON, kk)
        ctext(L.t, (TCX, cy + 140), "per month", font("ExtraBold", 66), WHITE, k * appear(t, cue("month", 2) - 0.2))
    return True

def work_art(L, t, k, t0, x0=290, y0=240, sc=1.6):
    """Neon line-art: a person working at a computer, bars growing, confirmations popping."""
    if k <= 0: return
    u = t - t0; S_ = lambda v: v * sc
    w_, h_ = S_(320), S_(250)
    L.f.rounded_rectangle((x0, y0, x0 + w_, y0 + h_), 34, fill=(6, 16, 10, int(225 * k))); L.n.rounded_rectangle((x0, y0, x0 + w_, y0 + h_), 34, outline=rgba(NEON, k), width=5)
    c = rgba(NEON, k); wc = rgba(WHITE, k); d = L.n; lw = 7
    d.line([(x0 + S_(30), y0 + S_(200)), (x0 + w_ - S_(30), y0 + S_(200))], fill=c, width=lw)
    mx0, my0, mx1, my1 = x0 + S_(150), y0 + S_(55), x0 + S_(290), y0 + S_(150)
    d.rounded_rectangle((mx0, my0, mx1, my1), 14, outline=c, width=lw); d.line([(mx0 + S_(70), my1), (mx0 + S_(70), y0 + S_(180))], fill=c, width=lw)
    d.line([(mx0 + S_(45), y0 + S_(182)), (mx0 + S_(95), y0 + S_(182))], fill=c, width=lw)
    for j in range(4):
        hgt = S_(14 + 14 * j) * ease((u - 0.2 - 0.15 * j) / 0.4); bx = mx0 + S_(22 + j * 26)
        if hgt > 0: L.t.rectangle((bx, my1 - S_(12) - hgt, bx + S_(14), my1 - S_(12)), fill=c)
    hx, hy = x0 + S_(85), y0 + S_(85)
    d.ellipse((hx - S_(22), hy - S_(22), hx + S_(22), hy + S_(22)), outline=wc, width=lw)
    d.arc((hx - S_(48), hy + S_(30), hx + S_(48), hy + S_(150)), 200, 340, fill=wc, width=lw)
    d.line([(hx + S_(30), hy + S_(60)), (hx + S_(75), hy + S_(100)), (mx0 + S_(10), y0 + S_(196))], fill=wc, width=lw)
    d.line([(mx0 - S_(40), y0 + S_(196)), (mx0 + S_(20), y0 + S_(196))], fill=c, width=lw + 2)
    for j in range(3):
        kk = k * appear(u, 0.6 + 0.45 * j, 0.2); cx, cy = mx1 + S_(4), my0 - S_(10) + S_(34) * j; r = S_(13)
        if kk > 0:
            L.f.ellipse((cx - r, cy - r, cx + r, cy + r), fill=rgba((10, 88, 38), kk)); L.n.ellipse((cx - r, cy - r, cx + r, cy + r), outline=rgba(NEON, kk), width=3)
            L.t.line([(cx - S_(6), cy), (cx - S_(2), cy + S_(5)), (cx + S_(7), cy - S_(6))], fill=rgba(WHITE, kk), width=4)

def rates(L, t):
    a = appear(t, cue("why", 4) - 0.1, 0.3)
    ctext(L.t, (TCX, 260), "Why KoiPay?", font("Black", 76), WHITE, a)
    rows = [("PayIn ↓", "≈ 3%", "incoming payment", 50, cue("3%", 4)), ("PayOut ↑", "≈ 1%", "outgoing payment", 550, cue("1%", 4))]
    for tag, rate, sub, x, at in rows:
        k = appear(t, at - 0.25, 0.3); box = (x, 340, x + 480, 760)
        L.f.rounded_rectangle(box, 34, fill=(6, 16, 10, int(240 * k))); L.n.rounded_rectangle(box, 34, outline=rgba(NEON, k), width=4)
        ctext(L.t, (x + 240, 420), tag, font("ExtraBold", 54), WHITE, k)
        ctext(L.t, (x + 240, 560), rate, font("Black", 130), NEON, k)
        ctext(L.t, (x + 240, 690), sub, font("SemiBold", 36), GREY, k)
    ctext(L.t, (TCX, 820), "Base rates · terms confirmed at onboarding", font("SemiBold", 34), GREY, appear(t, cue("payout", 4)))

def dash_window(): return cue("dashboard", 5) - 0.3, cue("support", 5) - 0.3
def dashboard(img, L, t):
    t0, t1 = dash_window(); kw = min(appear(t, t0, 0.3), 1 - ease((t - t1) / 0.25))
    beats = [(t0, "home", "Your dashboard"), (cue("requests", 5) - 0.15, "requests", "Requests"), (cue("history", 5) - 0.15, "history", "History"),
             (cue("commission", 5) - 0.15, "commission", "Commission per operation"), (cue("all", 5) - 0.15, "home", "All in one place")]
    bt, key, title = [b for b in beats if t >= b[0]][-1]; u = t - bt
    pic = dm_img(key, u + (0 if key != "home" or bt == t0 else 1.0)); z = 1.0 + 0.10 * ease_io(u / 1.6)
    pic = pic.resize((int(pic.width * z), int(pic.height * z)), Image.BICUBIC).crop((int(pic.width * (z - 1) * 0.15), int(pic.height * (z - 1) * 0.2), int(pic.width * (z - 1) * 0.15) + pic.width, int(pic.height * (z - 1) * 0.2) + pic.height))
    if bt == t0:
        sc_ = 0.6 + 0.4 * ease_io((t - t0) / 0.6); pic = pic.resize((max(1, int(pic.width * sc_)), max(1, int(pic.height * sc_))), Image.BICUBIC)
    y = 560 - pic.height / 2 + 20
    paste_card(img, L, pic, TCX - pic.width / 2, y, kw, r=22)
    pill(L, TCX, y - 60, title, kw, filled=True, fnt=fit(L.t, title, "ExtraBold", 48, 900), h=86, padx=40)

def support(L, t):
    k = appear(t, cue("support", 5) - 0.15, 0.3)
    g = TG.resize((160, 160), Image.LANCZOS); g.putalpha(g.getchannel("A").point(lambda v: int(v * k))); L.text.alpha_composite(g, (TCX - 80, 230))
    ctext(L.t, (TCX, 450), "Support in Telegram", font("ExtraBold", 62), WHITE, k)
    k24 = k * appear(t, cue("24/7", 5) - 0.3)
    ctext(L.t, (TCX, 620), "24/7", font("Black", 190), NEON, k24); ctext(L.t, (TCX, 770), "every day, any hour", font("SemiBold", 40), GREY, k24)

def recall(img, L, t):
    u = t - CUTS[1]
    ctext(L.t, (TCX, 245), "Remember Ravi?", font("Black", 72), WHITE, appear(u, 0.1, 0.3))
    ka = appear(u, 0.25, 0.35); pic, _ = cover(PHOTOS["rick"], 450, 470, 1.05 + 0.04 * u, 520, 640); paste_card(img, L, pic, 60, 310 + 20 * (1 - ka), ka)
    pill(L, 285, 830, "Rickshaw · Delhi", appear(u, 0.6), fnt=PILL, h=76)
    kb = appear(u, 1.2, 0.35); pic, _ = cover(PHOTOS["selfie"], 450, 470, 1.08, 520, 700); paste_card(img, L, pic, 570, 310 + 20 * (1 - kb), kb)
    pill(L, 795, 830, "Week 1: ₹14,312", appear(u, 1.7), fnt=PILL, h=76)

def top_zone(img, L, t, i):
    if i == 0: name_card(L, t, appear(t, 0.5, 0.4), "Arnold", "KoiPay manager")
    elif i == 1: recall(img, L, t)
    elif i in (2, 3):
        if not story(img, L, t): name_card(L, t, appear(t, cue("ravi", 1) - 0.2, 0.3), "Ravi", "KoiPay trader")
    elif i == 4: work_art(L, t, appear(t, CUTS[4] + 0.1, 0.35), CUTS[4] + 0.3)
    elif i == 5: rates(L, t)
    elif i == 6:
        t0, t1 = dash_window()
        if t < t0: rates(L, t)                       # keep the rates card until the dashboard comes in
        elif t < t1: dashboard(img, L, t)
        else: support(L, t)
    elif i == 7: pill(L, TCX, 530, "Start today", appear(t, cue("start", 6) - 0.2), filled=True, fnt=font("Black", 80), h=140, padx=60)

# ---------- end card (vertical) ----------
def endcard(L, t, t0):
    k0 = appear(t, t0 + 0.2, 0.35)
    ctext(L.t, (TCX, 330), "Start now", font("Black", 110), WHITE, k0)
    cards = [("NEW TO P2P", "Free training", "@koiedubot", 430, t0 + 0.35), ("EXPERIENCED", "Start working", "@koipayp2p2bot", 950, t0 + 0.6)]
    tg = TG.resize((120, 120), Image.LANCZOS)
    for tag, lab, user, y0, at in cards:
        k = appear(t, at, 0.35); dx = int(30 * (1 - k)); box = (120 + dx, y0, 960 + dx, y0 + 470); cx = 540 + dx
        L.f.rounded_rectangle(box, 40, fill=(6, 16, 10, int(246 * k))); L.n.rounded_rectangle(box, 40, outline=rgba(NEON, k), width=5)
        fnt = font("Black", 46); tw = L.t.textlength(tag, font=fnt)
        L.f.rounded_rectangle((cx - tw / 2 - 34, y0 + 35, cx + tw / 2 + 34, y0 + 115), 40, fill=rgba(NEON, k)); ctext(L.t, (cx, y0 + 76), tag, fnt, (4, 20, 10), k)
        g = tg.copy(); g.putalpha(g.getchannel("A").point(lambda v: int(v * k))); L.text.alpha_composite(g, (cx - 60, y0 + 140))
        ctext(L.t, (cx, y0 + 315), lab, font("ExtraBold", 62), WHITE, k)
        pill(L, cx, y0 + 405, user, k, filled=True, fnt=font("Black", 56 if len(user) < 12 else 50), h=100, padx=40)
    k3 = appear(t, cue("under", 6) - 0.2)
    if k3 > 0:
        txt = "Links under this video ↓"; fnt = font("Black", 54); tw = L.t.textlength(txt, font=fnt)
        L.f.rounded_rectangle((TCX - tw / 2 - 44, 1490, TCX + tw / 2 + 44, 1576), 43, fill=rgba(NEON, k3)); ctext(L.t, (TCX, 1534), txt, fnt, (4, 20, 10), k3)

#@@SUBS@@
# ---------- compose ----------
def finish(img, L):
    out = img.convert("RGBA"); out = Image.alpha_composite(out, L.fill)
    glow = L.neon.resize((W // 2, H // 2), Image.BILINEAR).filter(ImageFilter.GaussianBlur(9)).resize((W, H), Image.BILINEAR)
    out = Image.alpha_composite(Image.alpha_composite(out, glow), glow); out = Image.alpha_composite(out, L.neon); return Image.alpha_composite(out, L.text)

def compose(t, frame):
    T_END = cue("all", 6) - 0.35
    L = Layers(); i = seg_of(t)
    img = Image.new("RGB", (W, H)); img.paste(TOP_BG, (0, 0)); img.paste(video_block(frame, t, i), (0, VB_Y))
    top_zone(img, L, t, i)
    L.n.line([(0, VB_Y), (W, VB_Y)], fill=rgba(NEON, 1), width=4)
    out = finish(img, L)
    if t >= T_END:
        p = ease_io((t - T_END) / 0.45)
        fs = FS_BG.copy(); L2 = Layers(); endcard(L2, t, T_END); fs = finish(fs, L2)
        ye = int(H * (1 - p)); out.paste(fs.crop((0, ye, W, H)), (0, ye))
        if p < 1: ImageDraw.Draw(out).rectangle((0, ye - 6, W, ye + 6), fill=rgba(NEON, 0.9))
    for c in (CUTS[1], CUTS[2], CUTS[5]):
        d = t - c
        if -0.04 <= d < 0.16: out = Image.blend(out.convert("RGB"), Image.new("RGB", (W, H), (200, 255, 220)), (1 - max(0, d) / 0.16) * 0.7).convert("RGBA")
    draw_brand(out)
    if t < T_END + 0.3: draw_subs(t, out)
    if DUR - t < 0.6: out = Image.blend(Image.new("RGBA", (W, H), (0, 0, 0, 255)), out, clamp((DUR - t) / 0.6))
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
for k in range(n):
    buf = dec.stdout.read(1920 * 1080 * 3)
    fr = Image.frombuffer("RGB", (1920, 1080), buf).copy() if len(buf) == 1920 * 1080 * 3 else Image.new("RGB", (1920, 1080))
    enc.stdin.write(compose(k / FPS, fr).tobytes())
    if k % 250 == 0: print(k, flush=True)
enc.stdin.close(); enc.wait(); print("done", n)
