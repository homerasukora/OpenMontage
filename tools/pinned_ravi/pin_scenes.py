SUB = font("Black", 60)

# ---------- helpers ----------
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
def paste_top(L, pic, x, y, a, r=20):
    """Paste a picture above the glass layers (into the text layer)."""
    if a <= 0: return
    im = pic.convert("RGBA"); m = Image.new("L", im.size, 0); ImageDraw.Draw(m).rounded_rectangle((0, 0, im.width - 1, im.height - 1), r, fill=int(255 * a))
    im.putalpha(m); L.text.alpha_composite(im, (int(x), int(y)))
    L.n.rounded_rectangle((x - 3, y - 3, x + im.width + 3, y + im.height + 3), r + 2, outline=rgba(NEON, a), width=3)
def glass(L, box, a, r=34):
    if a <= 0: return
    L.f.rounded_rectangle(box, r, fill=(6, 16, 10, int(240 * a))); L.n.rounded_rectangle(box, r, outline=rgba(NEON, 0.9 * a), width=4)
def win(t, t0, t1, d=0.3): return min(appear(t, t0, d), 1 - ease((t - t1) / 0.25))
def decode(args, w, h):
    p = subprocess.run(["ffmpeg", "-v", "error"] + args + ["-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True).stdout
    n = len(p) // (w * h * 3); return np.frombuffer(p[: n * w * h * 3], np.uint8).reshape(n, h, w, 3)
def icon_check(d, cx, cy, s, a):
    d.line([(cx - 0.32 * s, cy), (cx - 0.08 * s, cy + 0.26 * s), (cx + 0.36 * s, cy - 0.28 * s)], fill=rgba(NEON, a), width=8, joint="curve")
def icon_coin(d, cx, cy, s, a):
    r = 0.45 * s; d.ellipse((cx - r, cy - r, cx + r, cy + r), outline=rgba(NEON, a), width=5)
    d.text((cx, cy + 2), "₹", font=font("Black", int(s * 0.62)), fill=rgba(NEON, a), anchor="mm")
def icon_list(d, cx, cy, s, a):
    for k in (-0.28, 0, 0.28):
        d.ellipse((cx - 0.42 * s - 5, cy + k * s - 5, cx - 0.42 * s + 5, cy + k * s + 5), fill=rgba(NEON, a))
        d.line([(cx - 0.25 * s, cy + k * s), (cx + 0.42 * s, cy + k * s)], fill=rgba(NEON, a), width=5)
def icon_clock(d, cx, cy, s, a):
    r = 0.44 * s; d.ellipse((cx - r, cy - r, cx + r, cy + r), outline=rgba(NEON, a), width=5)
    d.line([(cx, cy), (cx, cy - 0.28 * s)], fill=rgba(NEON, a), width=5); d.line([(cx, cy), (cx + 0.2 * s, cy + 0.1 * s)], fill=rgba(NEON, a), width=5)

def seg_of(t): return max(i for i, c in enumerate(CUTS) if c <= t + 1e-6)

# ---------- assets ----------
TGI = TG.resize((150, 150), Image.LANCZOS)
SC = {s["name"]: s for s in json.load(open(A["dash_scenes"]))["scenes"]}
def _dash(nm, crop, cw):
    x, y, w, h = crop; ch = int(cw * h / w); sc = SC[nm]
    fr = decode(["-ss", f"{sc['s']:.3f}", "-t", f"{min(4.0, sc['e'] - sc['s']):.3f}", "-i", A["dash_base"], "-vf", "fps=25"], 1920, 1080)
    out = []
    for f in fr:
        im = Image.fromarray(f)
        for b in sc["blur"]: im.paste(im.crop(tuple(b)).filter(ImageFilter.GaussianBlur(16)), tuple(b[:2]))
        out.append(np.asarray(im.crop((x, y, x + w, y + h)).resize((cw, ch), Image.LANCZOS)))
    return out
RPX0, RPY0, RPX1, RPY1 = 1270, 190, 1880, 880            # right-hand panel
RPW, RPCX = RPX1 - RPX0, (RPX0 + RPX1) // 2
DASH_HOME = _dash("home", (395, 515, 1120, 450), RPW - 60)
def dash_home(ts): return Image.fromarray(DASH_HOME[int(clamp(ts * 25, 0, len(DASH_HOME) - 1))])
def _fs_bg():
    arr = np.asarray(BG).astype(np.float32); yy, xx = np.mgrid[0:H, 0:W]
    arr += (np.exp(-(((xx - W / 2) / 900) ** 2 + ((yy - H / 2) / 520) ** 2)) * 0.45)[..., None] * np.array(NEON, np.float32)
    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))
FS_BG = _fs_bg()
RAVI_G = (540, 690)

# ---------- split layout: video card left, story panel right ----------
VCARD = (40, 190, 1240, 865)                             # 1200x675
def split_amount(t):
    t0, t1 = cue("rickshaw", 1) - 0.45, CUTS[4] - 0.05
    return min(ease_io((t - t0) / 0.45), ease_io((t1 - t) / 0.4))

def story_panel(img, L, t):
    """Ravi's story beats (confirmed facts: Delhi rickshaw driver, $500 saved, first week ₹14,312, now full-time, ₹2,00,000+/month)."""
    ph_w, ph_h = RPW, 520
    beats = [(cue("rickshaw", 1) - 0.2, "rick"), (cue("$500", 1) - 0.25, "save"), (cue("started", 1) - 0.2, "koi"),
             (cue("step", 2) - 0.2, "week1"), (cue("later", 2) - 0.2, "fulltime"), (cue("now", 2) - 0.2, "income")]
    cur = [b for b in beats if t >= b[0]]
    if not cur: return
    t0, kind = cur[-1]; k = appear(t, t0, 0.3) * clamp(split_amount(t) * 1.6 - 0.6)
    if k <= 0: return
    y0 = RPY0
    if kind == "rick":
        pic = video_still(A["rk2"], 2.5 + (t - t0), ph_w, ph_h); paste_card(img, L, pic, RPX0, y0, k)
        pill(L, RPCX, RPY1 - 50, "Before: rickshaw driver · Delhi", k, filled=True, fnt=fit(L.t, "Before: rickshaw driver · Delhi", "Bold", 40, RPW - 80), h=80)
    elif kind == "save":
        pic, tr = cover(PHOTOS["group"], ph_w, ph_h, 1.25, 540, 760); paste_card(img, L, pic, RPX0, y0, k)
        s, x0, yy0 = tr; cx, cy = RPX0 + (RAVI_G[0] - x0) * s, y0 + (RAVI_G[1] - yy0) * s; r = 90
        L.n.ellipse((cx - r, cy - r * 1.2, cx + r, cy + r * 1.2), outline=rgba(NEON, k), width=5)
        pill(L, cx, cy - r * 1.2 - 40, "Ravi", k, filled=True, fnt=SMALL, h=58, padx=22)
        pill(L, RPCX, RPY1 - 50, "$500 saved from driving", k, filled=True, fnt=PILL, h=80)
    elif kind == "koi":
        glass(L, (RPX0, y0, RPX1, y0 + ph_h), k)
        lg = LOGO.resize((170, 170), Image.LANCZOS); lg.putalpha(lg.getchannel("A").point(lambda v: int(v * k))); L.text.alpha_composite(lg, (RPCX - 85, y0 + 70))
        ctext(L.t, (RPCX, y0 + 320), "$500", font("Black", 110), NEON, k); ctext(L.t, (RPCX, y0 + 430), "first deposit to start", LABEL, WHITE, k)
        pill(L, RPCX, RPY1 - 50, "Started with KoiPay", k, filled=True, fnt=PILL, h=80)
    elif kind == "week1":
        zk = ease((t - t0 - 0.3) / 0.8)
        pic, tr = cover(PHOTOS["selfie"], ph_w, ph_h, 1.0 + 1.5 * zk, 480 + 190 * zk, 640 + 20 * zk); paste_card(img, L, pic, RPX0, y0, k)
        s, x0, yy0 = tr; bx0, by0 = RPX0 + (585 - x0) * s, y0 + (652 - yy0) * s; bx1, by1 = RPX0 + (760 - x0) * s, y0 + (705 - yy0) * s
        if zk > 0.7: L.n.rounded_rectangle((bx0 - 12, by0 - 12, bx1 + 12, by1 + 12), 16, outline=rgba(NEON, k * appear(t, t0 + 1.0)), width=6)
        pill(L, RPCX, y0 + 60, "WEEK 1", k, filled=True, fnt=font("Black", 60), h=96, padx=40)
        pill(L, RPCX, RPY1 - 50, "Earned: ₹14,312", k, fnt=TITLE, h=90, padx=36)
    elif kind == "fulltime":
        glass(L, (RPX0, y0, RPX1, RPY1), k)
        ctext(L.t, (RPCX, y0 + 70), "Ravi's path", TITLE, WHITE, k)
        rows = [("Before", "Rickshaw driver", t0), ("Then", "Rickshaw + KoiPay", t0 + 0.35), ("Now", "KoiPay full-time ✓", cue("full-time", 2) - 0.2)]
        for j, (tag, lab, at) in enumerate(rows):
            kk = k * appear(t, at, 0.25); y = y0 + 190 + j * 165; on = j == 2
            box = (RPX0 + 40, y - 62, RPX1 - 40, y + 62)
            L.f.rounded_rectangle(box, 28, fill=rgba(NEON_DARK if (on and kk > 0.5) else (10, 26, 16), max(kk, 0.96 * k))); L.n.rounded_rectangle(box, 28, outline=rgba(NEON, kk), width=3)
            ctext(L.t, (RPX0 + 80, y), tag, SMALL, WHITE if on else NEON, kk, "lm")
            ctext(L.t, (RPX0 + 215, y), lab, fit(L.t, lab, "Bold", 42, RPX1 - 80 - (RPX0 + 215)), WHITE, kk, "lm")
    elif kind == "income":
        glass(L, (RPX0, y0, RPX1, RPY1), k)
        ctext(L.t, (RPCX, y0 + 90), "Ravi now earns", LABEL, GREY, k)
        at = cue("₹2", 2); kk = k * appear(t, at - 0.2, 0.2)
        n = int(200000 * ease((t - at + 0.2) / 1.0)); txt = f"₹{n // 100000},{(n // 1000) % 100:02d},{n % 1000:03d}" if n >= 100000 else f"₹{n // 1000},{n % 1000:03d}" if n >= 1000 else f"₹{n}"
        if n >= 200000: txt += "+"
        ctext(L.t, (RPCX, y0 + 250), txt, font("Black", 104), NEON, kk)
        ctext(L.t, (RPCX, y0 + 370), "per month", TITLE, WHITE, k * appear(t, cue("month", 2) - 0.2))
        kd = k * appear(t, cue("month", 2) + 0.2)
        ctext(L.t, (RPCX, RPY1 - 120), "Individual result", font("SemiBold", 34), GREY, kd)
        ctext(L.t, (RPCX, RPY1 - 72), "Depends on volume · not a guarantee", font("SemiBold", 32), GREY, kd)

# ---------- side panel in the office ----------
OPX0, OPY0, OPX1, OPY1 = 1240, 150, 1870, 900
OPCX = (OPX0 + OPX1) // 2
def office_panel(img, L, t, i):
    if i == 5:
        a = min(appear(t, cue("why", 4) - 0.1, 0.3), 1.0)
        glass(L, (OPX0, OPY0, OPX1, OPY1), a)
        ctext(L.t, (OPCX, OPY0 + 80), "Why KoiPay?", TITLE, WHITE, a)
        rows = [("PayIn", "≈ 3%", "incoming payment", "↓", cue("3%", 4)), ("PayOut", "≈ 1%", "outgoing payment", "↑", cue("1%", 4))]
        for j, (tag, rate, sub, arr, at) in enumerate(rows):
            k = a * appear(t, at - 0.25, 0.3); y = OPY0 + 170 + j * 260
            box = (OPX0 + 40, y, OPX1 - 40, y + 225)
            L.f.rounded_rectangle(box, 30, fill=rgba((10, 26, 16) if k > 0.05 else (6, 16, 10), max(k, 0.96 * a))); L.n.rounded_rectangle(box, 30, outline=rgba(NEON, k), width=3)
            ctext(L.t, (OPCX, y + 48), f"{tag} {arr}", font("ExtraBold", 46), WHITE, k)
            ctext(L.t, (OPCX, y + 125), rate, font("Black", 100), NEON, k)
            ctext(L.t, (OPCX, y + 192), sub, font("SemiBold", 32), GREY, k)
        ctext(L.t, (OPCX, OPY1 - 60), "Base rates · terms confirmed at onboarding", fit(L.t, "Base rates · terms confirmed at onboarding", "SemiBold", 30, OPX1 - OPX0 - 70), GREY, a * appear(t, cue("payout", 4)))
    elif i == 6:
        ts = cue("support", 5)
        kA = 1 - appear(t, ts - 0.3, 0.25)
        glass(L, (OPX0, OPY0, OPX1, OPY1), 1.0)
        if kA > 0:
            ctext(L.t, (OPCX, OPY0 + 70), "One simple dashboard", fit(L.t, "One simple dashboard", "ExtraBold", 54, OPX1 - OPX0 - 70), WHITE, kA)
            k0 = kA * appear(t, cue("dashboard", 5) - 0.2)
            pic = dash_home(t - CUTS[6]); paste_top(L, pic, OPCX - pic.width / 2, OPY0 + 130, k0)
            yb = OPY0 + 130 + pic.height + 70
            for j, (lab, ic, w_) in enumerate((("Requests", icon_list, "requests"), ("History", icon_clock, "history"), ("Commission", icon_coin, "commission"))):
                k = kA * appear(t, cue(w_, 5) - 0.15); y = yb + j * 100
                box = (OPX0 + 40, y - 40, OPX1 - 40, y + 40)
                L.f.rounded_rectangle(box, 24, fill=rgba((10, 26, 16) if k > 0.05 else (6, 16, 10), max(k, 0.96))); L.n.rounded_rectangle(box, 24, outline=rgba(NEON, k), width=3)
                ic(L.n, OPX0 + 95, y, 48, k); ctext(L.t, (OPX0 + 145, y), lab, font("Bold", 40), WHITE, k, "lm")
        kB = appear(t, ts - 0.15, 0.3)
        if kB > 0:
            g = TGI.copy(); g.putalpha(g.getchannel("A").point(lambda v: int(v * kB))); L.text.alpha_composite(g, (OPCX - 75, OPY0 + 90))
            ctext(L.t, (OPCX, OPY0 + 330), "Support in Telegram", fit(L.t, "Support in Telegram", "ExtraBold", 50, OPX1 - OPX0 - 70), WHITE, kB)
            k24 = kB * appear(t, cue("24/7", 5) - 0.3)
            ctext(L.t, (OPCX, OPY0 + 500), "24/7", font("Black", 150), NEON, k24)
            ctext(L.t, (OPCX, OPY0 + 620), "every day, any hour", font("SemiBold", 36), GREY, k24)

# ---------- end card ----------
T_END = None
def endcard(L, t, t0):
    k0 = appear(t, t0 + 0.2, 0.35)
    ctext(L.t, (960, 150), "Start now", font("Black", 92), WHITE, k0)
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
    k3 = appear(t, cue("under", 6) - 0.2)
    if k3 > 0:
        txt = "Links under this video ↓"; fnt = font("Black", 50); tw = L.t.textlength(txt, font=fnt)
        L.f.rounded_rectangle((960 - tw / 2 - 44, 825, 960 + tw / 2 + 44, 905), 40, fill=rgba(NEON, k3))
        ctext(L.t, (960, 866), txt, fnt, (4, 20, 10), k3)

# ---------- full-frame overlays ----------
def overlays(img, L, t, i):
    if i == 0:
        k = win(t, 0.6, 4.3)
        pill(L, 470, 870, "Arnold · KoiPay manager", k, filled=True, fnt=TITLE, h=96, padx=44)
        k2 = win(t, cue("guest", 0) - 0.1, CUTS[1] - 0.3)
        pill(L, 1450, 870, "Today's guest: a KoiPay trader", k2, fnt=PILL, h=84)
    elif i == 1:
        cx0, cy0, cw, ch = 690, 60, 540, 960
        L.n.rounded_rectangle((cx0 - 3, cy0 - 3, cx0 + cw + 3, cy0 + ch + 3), 8, outline=rgba(NEON, 1), width=5)
        u = t - CUTS[1]
        ka = appear(u, 0.15, 0.35)
        pic, _ = cover(PHOTOS["rick"], 460, 600, 1.05 + 0.04 * u, 520, 640); paste_card(img, L, pic, 130, 260 + 20 * (1 - ka), ka)
        pill(L, 360, 200, "Remember Ravi?", ka, filled=True, fnt=font("ExtraBold", 48), h=88, padx=36)
        pill(L, 360, 930, "Rickshaw driver · Delhi", appear(u, 0.6), fnt=PILL, h=78)
        kb = appear(u, 1.3, 0.35)
        pic, _ = cover(PHOTOS["selfie"], 460, 600, 1.08, 520, 700); paste_card(img, L, pic, 1330, 260 + 20 * (1 - kb), kb)
        pill(L, 1560, 200, "First video: week 1", kb, filled=True, fnt=font("ExtraBold", 44), h=88, padx=32)
        pill(L, 1560, 930, "Earned ₹14,312", appear(u, 1.8), fnt=PILL, h=78)
    elif i in (2, 3):
        if t < cue("rickshaw", 1) - 0.45:
            k = win(t, cue("ravi", 1) - 0.1, cue("rickshaw", 1) - 0.6)
            pill(L, 1450, 870, "Ravi · KoiPay trader", k, filled=True, fnt=TITLE, h=96, padx=44)
    elif i == 4:
        k = win(t, cue("steady", 3) - 0.2, CUTS[5] - 0.3)
        pill(L, 960, 150, "Results come from steady daily work", k, filled=True, fnt=PILL, h=84)
    elif i in (5, 6):
        office_panel(img, L, t, i)
    elif i == 7:
        k = win(t, cue("start", 6) - 0.2, cue("all", 6) - 0.4)
        pill(L, 1450, 870, "Start today", k, filled=True, fnt=TITLE, h=96, padx=44)

#@@SUBS@@
# ---------- compose ----------
def finish(img, L):
    out = img.convert("RGBA"); out = Image.alpha_composite(out, L.fill)
    glow = L.neon.resize((W // 2, H // 2), Image.BILINEAR).filter(ImageFilter.GaussianBlur(9)).resize((W, H), Image.BILINEAR)
    out = Image.alpha_composite(Image.alpha_composite(out, glow), glow); out = Image.alpha_composite(out, L.neon); return Image.alpha_composite(out, L.text)

def punch(frame, z, cx=960, cy=470):
    if z <= 1.001: return frame
    w_, h_ = W / z, H / z; x0 = clamp(cx - w_ / 2, 0, W - w_); y0 = clamp(cy - h_ / 2, 0, H - h_)
    return frame.resize((W, H), Image.BICUBIC, box=(x0, y0, x0 + w_, y0 + h_))

def compose(t, frame):
    global T_END
    T_END = cue("all", 6) - 0.35
    L = Layers(); i = seg_of(t)
    if i == 4: frame = punch(frame, 1.0 + 0.06 * ease((t - CUTS[4]) / 0.5), 900, 430)
    sp = split_amount(t) if i in (2, 3) else 0.0
    if t >= T_END:
        p = ease_io((t - T_END) / 0.45)
        fs = FS_BG.copy(); L2 = Layers(); endcard(L2, t, T_END); fs = finish(fs, L2)
        out = frame.convert("RGBA")
        xe = int(W * (1 - p)); out.paste(fs.crop((xe, 0, W, H)), (xe, 0))
        if p < 1: ImageDraw.Draw(out).rectangle((xe - 6, 0, xe + 6, H), fill=rgba(NEON, 0.9))
    elif sp > 0:
        img = FS_BG.copy()
        x0, y0 = VCARD[0] * sp, VCARD[1] * sp; x1, y1 = W + (VCARD[2] - W) * sp, H + (VCARD[3] - H) * sp
        v = frame.resize((int(x1 - x0), int(y1 - y0)), Image.BICUBIC)
        m = Image.new("L", v.size, 0); ImageDraw.Draw(m).rounded_rectangle((0, 0, v.width - 1, v.height - 1), int(28 * sp), fill=255)
        img.paste(v, (int(x0), int(y0)), m)
        L.n.rounded_rectangle((x0 - 3, y0 - 3, x1 + 3, y1 + 3), 30, outline=rgba(NEON, sp), width=4)
        story_panel(img, L, t)
        out = finish(img, L)
    else:
        img = frame.copy(); overlays(img, L, t, i); out = finish(img, L)
    for c in (CUTS[1], CUTS[2], CUTS[5]):                                   # neon flash on scene changes
        d = t - c
        if -0.04 <= d < 0.16: out = Image.blend(out.convert("RGB"), Image.new("RGB", (W, H), (200, 255, 220)), (1 - max(0, d) / 0.16) * 0.7).convert("RGBA")
    draw_brand(out); draw_subs(t, out)
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
