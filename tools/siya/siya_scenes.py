SUB = font("Black", 60)

# ---------- extra icons ----------
def icon_store(d, cx, cy, s, a):
    d.line([(cx - 0.5 * s, cy - 0.1 * s), (cx - 0.38 * s, cy - 0.42 * s), (cx + 0.38 * s, cy - 0.42 * s), (cx + 0.5 * s, cy - 0.1 * s), (cx - 0.5 * s, cy - 0.1 * s)], fill=rgba(NEON, a), width=5)
    d.rectangle((cx - 0.42 * s, cy - 0.1 * s, cx + 0.42 * s, cy + 0.45 * s), outline=rgba(NEON, a), width=5)
    d.rectangle((cx - 0.12 * s, cy + 0.12 * s, cx + 0.12 * s, cy + 0.45 * s), outline=rgba(NEON, a), width=4)
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
def icon_coin(d, cx, cy, s, a):
    r = 0.45 * s; d.ellipse((cx - r, cy - r, cx + r, cy + r), outline=rgba(NEON, a), width=5)
    d.text((cx, cy + 2), "₹", font=font("Black", int(s * 0.62)), fill=rgba(NEON, a), anchor="mm")
def arrow_v(L, x, y0, y1, prog, a, t):
    if prog <= 0: return
    ye = y0 + (y1 - y0) * prog
    L.n.line([(x, y0), (x, ye)], fill=rgba(NEON, 0.5 * a), width=4)
    if prog >= 1:
        L.n.line([(x, y1), (x - 14, y1 - 16)], fill=rgba(NEON, a), width=5); L.n.line([(x, y1), (x + 14, y1 - 16)], fill=rgba(NEON, a), width=5)
        f = (t * 1.1) % 1.0; py = y0 + (y1 - y0) * f; L.n.ellipse((x - 6, py - 6, x + 6, py + 6), fill=rgba(NEON, a))

# ---------- media ----------
def cover(im, cw, ch, z=1.0, fx=None, fy=None):
    pw, ph = im.size; s = max(cw / pw, ch / ph) * z; w_, h_ = cw / s, ch / s
    fx = pw / 2 if fx is None else fx; fy = ph / 2 if fy is None else fy
    x0 = clamp(fx - w_ / 2, 0, pw - w_); y0 = clamp(fy - h_ / 2, 0, ph - h_)
    return im.crop((int(x0), int(y0), int(x0 + w_), int(y0 + h_))).resize((cw, ch), Image.BICUBIC), (s, x0, y0)
def video_still(path, ts, cw, ch):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{ts:.3f}", "-i", path, "-frames:v", "1", "-vf",
                          f"scale={cw}:{ch}:force_original_aspect_ratio=increase,crop={cw}:{ch}", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True).stdout
    return Image.frombuffer("RGB", (cw, ch), raw).copy()

# right-hand panel area (over the neon K)
RX0, RY0, RX1, RY1 = 1180, 130, 1860, 900
RCX, RW, RH = (RX0 + RX1) // 2, RX1 - RX0, RY1 - RY0

def media_card(img, L, pic, a):
    """Photo/video card in the right panel with neon border."""
    if a <= 0: return
    m = Image.new("L", pic.size, 0); ImageDraw.Draw(m).rounded_rectangle((0, 0, pic.width - 1, pic.height - 1), 30, fill=int(255 * a))
    y = RY0 + int(24 * (1 - a)); img.paste(pic, (RX0, y), m)
    L.n.rounded_rectangle((RX0 - 3, y - 3, RX1 + 3, y + RH + 3), 32, outline=rgba(NEON, a), width=4)

def glass(L, a, box=(RX0, RY0, RX1, RY1)):
    if a <= 0: return
    L.f.rounded_rectangle(box, 36, fill=(6, 16, 10, int(246 * a))); L.n.rounded_rectangle(box, 36, outline=rgba(NEON, 0.9 * a), width=4)

def seg_of(t):
    return max(i for i, c in enumerate(CUTS) if c <= t + 1e-6)
def seg_a(t, i, d=0.3):
    s0 = CUTS[i]; s1 = CUTS[i + 1] if i + 1 < len(CUTS) else DUR + 1
    return min(appear(t, s0 + 0.05, d), 1 - ease((t - (s1 - 0.12)) / 0.12))

RAVI_G = (540, 690)
CLOSE = {0, 2, 4, 5, 8, 10, 12}

def hook(img, L, t):
    bg, _ = cover(PHOTOS["rick"], W, H, 1.1)
    bg = bg.filter(ImageFilter.GaussianBlur(28)); bg = Image.eval(bg, lambda v: int(v * 0.35)); img.paste(bg)
    k = appear(t, 0.0, 0.35); cw, ch = 600, 800
    pic, _ = cover(PHOTOS["rick"], cw, ch, 1.02 + 0.05 * t / CUTS[1], 520, 640)
    m = Image.new("L", (cw, ch), 0); ImageDraw.Draw(m).rounded_rectangle((0, 0, cw - 1, ch - 1), 30, fill=int(255 * k))
    img.paste(pic, (240, 120), m); L.n.rounded_rectangle((237, 117, 243 + cw, 123 + ch), 32, outline=rgba(NEON, k), width=4)
    pill(L, 540, 170, "Rickshaw driver · Delhi", appear(t, cue("rickshaw", 0) - 0.1), filled=True, fnt=PILL, h=76)
    at = cue("₹14,000", 0); kk = appear(t, at - 0.15, 0.2)
    n = int(14000 * ease((t - at + 0.15) / 0.9)); txt = (f"₹{n // 1000},{n % 1000:03d}" if n >= 1000 else f"₹{n}") + ("+" if n >= 14000 else "")
    if kk > 0: L.t.text((1340, 420), txt, font=font("Black", 150), fill=rgba(NEON, kk), anchor="mm", stroke_width=8, stroke_fill=(0, 0, 0, int(190 * kk)))
    pill(L, 1340, 560, "last week", appear(t, cue("last", 0) - 0.1), fnt=PILL, h=78)
    pill(L, 1340, 690, "Not from rides", appear(t, cue("not", 0) - 0.1, 0.15), filled=True, fnt=TITLE, h=104, padx=46)

def overlays(img, L, t, i):
    a = seg_a(t, i)
    if i == 1:
        k = appear(t, CUTS[1] + 0.2) * (1 - appear(t, cue("ravi", 1) - 0.4, 0.2))
        pill(L, 420, 860, "Siya · KoiPay", k, filled=True, fnt=TITLE, h=96, padx=44)
        tr, te = cue("ravi", 1), cue("evening", 1)
        if t >= tr - 0.2:
            if t < te - 0.1: pic = video_still(A["rk2"], 2.5 + (t - tr), RW, RH); lab, ic = "Morning · rickshaw", None
            else: pic = video_still(A["rk1"], 1.5 + (t - te), RW, RH); lab = "Evening · processing"
            ka = a * appear(t, tr - 0.2); media_card(img, L, pic, ka)
            pill(L, RCX, RY1 - 70, lab, ka, filled=True, fnt=PILL, h=80)
    elif i == 2:
        tw = cue("in", 2)
        if t < tw - 0.1:
            pic, tr = cover(PHOTOS["group"], RW, RH, 1.25, 540, 760); media_card(img, L, pic, a)
            s, x0, y0 = tr; cx, cy = RX0 + (RAVI_G[0] - x0) * s, RY0 + (RAVI_G[1] - y0) * s; r = 95
            L.n.ellipse((cx - r, cy - r * 1.2, cx + r, cy + r * 1.2), outline=rgba(NEON, a), width=5)
            pill(L, cx, cy - r * 1.2 - 44, "Ravi", a, filled=True, fnt=SMALL, h=60, padx=24)
            pill(L, RCX, RY1 - 70, "$500 saved from driving", appear(t, cue("$500", 2) - 0.1), filled=True, fnt=PILL, h=80)
        else:
            te = cue("earned", 2); zk = ease((t - te + 0.2) / 0.7)
            pic, tr = cover(PHOTOS["selfie"], RW, RH, 1.0 + 1.6 * zk, 480 + 190 * zk, 640 + 20 * zk); media_card(img, L, pic, a)
            s, x0, y0 = tr; bx0, by0 = RX0 + (585 - x0) * s, RY0 + (652 - y0) * s; bx1, by1 = RX0 + (760 - x0) * s, RY0 + (705 - y0) * s
            if zk > 0.6: L.n.rounded_rectangle((bx0 - 12, by0 - 12, bx1 + 12, by1 + 12), 16, outline=rgba(NEON, a * appear(t, te + 0.5)), width=6)
            pill(L, RCX, RY0 + 70, "WEEK 1", a, filled=True, fnt=BIG, h=120, padx=48)
            pill(L, RCX, RY1 - 70, "Earned: ₹14,312", a * appear(t, te + 0.5), fnt=TITLE, h=96, padx=40)
    elif i == 3:
        glass(L, a)
        ctext(L.t, (RCX, RY0 + 90), "Ravi's next goal", TITLE, WHITE, a)
        rows = [("Now", "Rickshaw + KoiPay", CUTS[3] + 0.3), ("Goal", "Processing full-time", cue("full-time", 3) - 0.2)]
        for j, (tag, lab, at) in enumerate(rows):
            k = a * appear(t, at); y = RY0 + 250 + j * 200; on = j == 1
            L.f.rounded_rectangle((RX0 + 50, y - 70, RX1 - 50, y + 70), 30, fill=rgba(NEON_DARK if (on and k > 0.5) else (10, 26, 16), max(k, 0.965 * a)))
            L.n.rounded_rectangle((RX0 + 50, y - 70, RX1 - 50, y + 70), 30, outline=rgba(NEON, k), width=3)
            ctext(L.t, (RX0 + 90, y), tag, SMALL, WHITE if on else NEON, k, "lm"); ctext(L.t, (RX0 + 200, y), lab, PILL, WHITE, k, "lm")
            if j: arrow_v(L, RCX, y - 200 + 72, y - 72, ease((t - at + 0.1) / 0.3), a, t)
        pill(L, RCX, RY1 - 90, "He's not the only one", a * appear(t, cue("not", 3) - 0.1), filled=True, fnt=PILL, h=84)
    elif i == 4:
        glass(L, a)
        ctext(L.t, (RCX, RY0 + 120), "You can earn", LABEL, GREY, a)
        ctext(L.t, (RCX, RY0 + 290), "₹1,00,000+", font("Black", 104), NEON, a * appear(t, cue("₹1", 4) - 0.1, 0.25))
        ctext(L.t, (RCX, RY0 + 420), "per month", TITLE, WHITE, a * appear(t, cue("month", 4) - 0.1))
        pill(L, RCX, RY1 - 120, "Possible · not a promise", a * appear(t, cue("promise", 4) - 0.2), fnt=PILL, h=84)
    elif i == 5:
        glass(L, a)
        ctext(L.t, (RCX, RY0 + 110), "Our traders earn on average", LABEL, GREY, a)
        k = a * appear(t, cue("₹2–4", 5) - 0.1, 0.25)
        ctext(L.t, (RCX, RY0 + 260), "₹2,00,000 –", font("Black", 100), NEON, k)
        ctext(L.t, (RCX, RY0 + 380), "₹4,00,000", font("Black", 100), NEON, k)
        ctext(L.t, (RCX, RY0 + 490), "per month", TITLE, WHITE, a * appear(t, cue("month", 5) - 0.1))
        pill(L, RCX, RY1 - 110, "Depends on completed volume", a * appear(t, cue("depends", 5) - 0.1), filled=True, fnt=PILL, h=84)
    elif i in (6, 7):
        A_ = appear(t, CUTS[6] + 0.05) * (1 - ease((t - (CUTS[8] - 0.12)) / 0.12))
        glass(L, A_)
        ctext(L.t, (RCX, RY0 + 70), "P2P processing", TITLE, WHITE, A_)
        nodes = [("Business", icon_store, cue("businesses", 6) - 0.1), ("UPI payment", icon_phone, cue("upi", 6) - 0.1),
                 ("Trader's bank account", icon_bank, cue("bank", 7) - 0.1)]
        ys = [RY0 + 200, RY0 + 365, RY0 + 530]
        for j, (lab, ic, at) in enumerate(nodes):
            k = A_ * appear(t, at, 0.25)
            box = (RX0 + 50, ys[j] - 58, RX1 - 50, ys[j] + 58)
            L.f.rounded_rectangle(box, 28, fill=rgba((10, 26, 16) if k > 0.05 else (6, 16, 10), max(k, 0.965 * A_))); L.n.rounded_rectangle(box, 28, outline=rgba(NEON, k), width=3)
            ic(L.n, RX0 + 120, ys[j], 66, k); ctext(L.t, (RX0 + 185, ys[j]), lab, PILL, WHITE, k, "lm")
            if j: arrow_v(L, RCX, ys[j - 1] + 60, ys[j] - 60, ease((t - at + 0.1) / 0.3), A_, t)
        kc = A_ * appear(t, cue("commission", 7) - 0.1)
        if kc > 0:
            arrow_v(L, RCX, ys[2] + 60, RY1 - 150, ease((t - cue("commission", 7) + 0.1) / 0.3), A_, t)
            pill(L, RCX, RY1 - 95, "+ commission", kc, filled=True, fnt=TITLE, h=100, padx=44, icon=icon_coin)
    elif i == 8:
        glass(L, a)
        ctext(L.t, (RCX, RY0 + 80), "Two types of operations", LABEL, GREY, a)
        rows = [("PayIn", "Incoming payment", "you confirm", "↓", cue("payin", 8)), ("PayOut", "Outgoing payment", "you send", "↑", cue("payout", 8))]
        for j, (tag, l1, l2, arr, at) in enumerate(rows):
            k = a * appear(t, at - 0.1); y0 = RY0 + 150 + j * 330
            L.f.rounded_rectangle((RX0 + 50, y0, RX1 - 50, y0 + 290), 30, fill=rgba((10, 26, 16) if k > 0.05 else (6, 16, 10), max(k, 0.965 * a))); L.n.rounded_rectangle((RX0 + 50, y0, RX1 - 50, y0 + 290), 30, outline=rgba(NEON, k), width=3)
            ctext(L.t, (RX0 + 100, y0 + 80), tag, font("Black", 84), NEON, k, "lm"); ctext(L.t, (RX1 - 110, y0 + 80), arr, font("Black", 90), NEON, k)
            ctext(L.t, (RX0 + 100, y0 + 175), l1, PILL, WHITE, k, "lm"); ctext(L.t, (RX0 + 100, y0 + 235), l2, LABEL, GREY, k, "lm")
    elif i in (9, 10):
        if i == 9: A_ = seg_a(t, 9) if t < CUTS[10] else 1
        else: A_ = 1 - ease((t - (CUTS[11] - 0.12)) / 0.12)
        glass(L, A_)
        tg = TG.copy(); tg.putalpha(tg.getchannel("A").point(lambda v: int(v * A_))); L.text.alpha_composite(tg, (RCX - 85, RY0 + 50))
        ctext(L.t, (RCX, RY0 + 280), "New to P2P?", LABEL, GREY, A_)
        ctext(L.t, (RCX, RY0 + 350), "Free training", TITLE, WHITE, A_)
        pill(L, RCX, RY0 + 470, "@koiedubot", A_ * appear(t, cue("free", 9) - 0.1), filled=True, fnt=font("Black", 64), h=110, padx=46)
        ctext(L.t, (RCX, RY0 + 590), "PayIns · PayOuts · Dashboard", PILL, NEON, A_ * appear(t, cue("you'll", 9) - 0.1))
        k3 = A_ * appear(t, cue("link", 10) - 0.2) if i == 10 else 0
        if k3 > 0:
            txt = "Link in the description ↓"; fnt = font("Black", 46); tw = L.t.textlength(txt, font=fnt)
            box = (RCX - tw / 2 - 40, RY1 - 100 - 44, RCX + tw / 2 + 40, RY1 - 100 + 44)
            L.f.rounded_rectangle(box, 44, fill=rgba(NEON, k3)); ctext(L.t, (RCX, RY1 - 99), txt, fnt, (4, 20, 10), k3)
    elif i == 11:
        glass(L, a)
        tg = TG.copy(); tg.putalpha(tg.getchannel("A").point(lambda v: int(v * a))); L.text.alpha_composite(tg, (RCX - 85, RY0 + 50))
        ctext(L.t, (RCX, RY0 + 280), "Already experienced?", LABEL, GREY, a)
        ctext(L.t, (RCX, RY0 + 350), "Start working", TITLE, WHITE, a)
        pill(L, RCX, RY0 + 470, "@koipayp2p2bot", a * appear(t, cue("second", 11) - 0.1), filled=True, fnt=font("Black", 58), h=110, padx=44)
        for j, lab in enumerate(("Bank requirements", "Working funds", "Onboarding")):
            ctext(L.t, (RCX, RY0 + 580 + j * 55), "✓ " + lab, PILL, NEON, a * appear(t, cue("manager", 11) + 0.4 * j))
    elif i == 12:
        k = appear(t, CUTS[12] + 0.05)
        glass(L, k)
        ctext(L.t, (RCX, RY0 + 80), "Start with KoiPay", TITLE, WHITE, k)
        tg = TG.resize((110, 110), Image.LANCZOS); tg.putalpha(tg.getchannel("A").point(lambda v: int(v * k)))
        for j, (tagl, user) in enumerate((("Free training · new to P2P", "@koiedubot"), ("Start working · experienced", "@koipayp2p2bot"))):
            y = RY0 + 230 + j * 220
            L.text.alpha_composite(tg, (RX0 + 60, y - 55))
            ctext(L.t, (RX0 + 200, y - 30), tagl, SMALL, GREY, k, "lm"); ctext(L.t, (RX0 + 200, y + 25), user, font("Black", 48), NEON, k, "lm")
        k3 = appear(t, cue("description", 12) - 0.2)
        if k3 > 0:
            txt = "Links in the description ↓"; fnt = font("Black", 46); tw = L.t.textlength(txt, font=fnt)
            box = (RCX - tw / 2 - 40, RY1 - 110 - 44, RCX + tw / 2 + 40, RY1 - 110 + 44)
            L.f.rounded_rectangle(box, 44, fill=rgba(NEON, k3)); ctext(L.t, (RCX, RY1 - 109), txt, fnt, (4, 20, 10), k3)

#@@SUBS@@
# ---------- compose ----------
def compose(t, frame):
    L = Layers(); i = seg_of(t)
    if i == 0:
        img = Image.new("RGB", (W, H)); hook(img, L, t)
    else:
        if i in CLOSE:
            z = 1.10; cx, cy = 760, 470; w_, h_ = W / z, H / z
            x0 = clamp(cx - w_ / 2, 0, W - w_); y0 = clamp(cy - h_ / 2, 0, H - h_)
            frame = frame.crop((int(x0), int(y0), int(x0 + w_), int(y0 + h_))).resize((W, H), Image.LANCZOS)
        img = frame
        overlays(img, L, t, i)
    out = img.convert("RGBA")
    out = Image.alpha_composite(out, L.fill)
    glow = L.neon.resize((W // 2, H // 2), Image.BILINEAR).filter(ImageFilter.GaussianBlur(9)).resize((W, H), Image.BILINEAR)
    out = Image.alpha_composite(Image.alpha_composite(out, glow), glow)
    out = Image.alpha_composite(out, L.neon); out = Image.alpha_composite(out, L.text)
    draw_brand(out); draw_subs(t, out)
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
    if k % 200 == 0: print(k, flush=True)
enc.stdin.close(); enc.wait(); print("done", n)
