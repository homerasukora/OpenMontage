# footage (cover-fit to 9:16)
def video_frame(path, src_t, zoom=1.0):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{src_t:.3f}", "-i", path, "-frames:v", "1",
                          "-vf", "scale=1080:1920:force_original_aspect_ratio=increase:flags=lanczos,crop=1080:1920",
                          "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True).stdout
    fr = Image.frombuffer("RGB", (W, H), raw)
    if zoom > 1:
        dx, dy = W * (1 - 1 / zoom) / 2, H * (1 - 1 / zoom) / 2
        fr = fr.crop((int(dx), int(dy), int(W - dx), int(H - dy))).resize((W, H), Image.BICUBIC)
    return fr

DASH = Image.open(A["dash"]).convert("RGB")

def phone(L, img, x, y, w, scroll, a):
    """Phone mockup with neon edge; screen shows `img` scrolled by `scroll` (0..1)."""
    if a <= 0: return
    sw = w - 28; scale = sw / DASH.width; sh = int(sw * 2.05)
    full = DASH.resize((sw, int(DASH.height * scale)), Image.BICUBIC)
    off = int((full.height - sh) * clamp(scroll)) if full.height > sh else 0
    scr = full.crop((0, off, sw, off + sh)) if full.height > sh else full
    h = scr.height + 28
    L.f.rounded_rectangle((x, y, x + w, y + h), 44, fill=(4, 8, 6, int(255 * a)))
    m = Image.new("L", scr.size, 0); ImageDraw.Draw(m).rounded_rectangle((0, 0, scr.width, scr.height), 32, fill=int(255 * a))
    L.fill.paste(scr, (x + 14, y + 14), m)
    L.n.rounded_rectangle((x, y, x + w, y + h), 44, outline=rgba(NEON, a), width=4)

def icon_sun(d, cx, cy, s, a):
    r = 0.22 * s; d.ellipse((cx - r, cy - r, cx + r, cy + r), outline=rgba(NEON, a), width=4)
    for k in range(8):
        an = k * math.pi / 4; d.line([(cx + math.cos(an) * 0.32 * s, cy + math.sin(an) * 0.32 * s), (cx + math.cos(an) * 0.46 * s, cy + math.sin(an) * 0.46 * s)], fill=rgba(NEON, a), width=4)
def icon_moon(d, cx, cy, s, a):
    r = 0.4 * s; d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=rgba(NEON, a))
    d.ellipse((cx - r + 0.28 * s, cy - r - 0.1 * s, cx + r + 0.28 * s, cy + r - 0.1 * s), fill=(6, 18, 10, int(255 * a)))
def icon_up(d, cx, cy, s, a):
    pts = [(cx - 0.45 * s, cy + 0.3 * s), (cx - 0.1 * s, cy - 0.05 * s), (cx + 0.1 * s, cy + 0.12 * s), (cx + 0.45 * s, cy - 0.3 * s)]
    d.line(pts, fill=rgba(NEON, a), width=5, joint="curve")
    d.line([(cx + 0.45 * s, cy - 0.3 * s), (cx + 0.22 * s, cy - 0.3 * s)], fill=rgba(NEON, a), width=5); d.line([(cx + 0.45 * s, cy - 0.3 * s), (cx + 0.45 * s, cy - 0.08 * s)], fill=rgba(NEON, a), width=5)

# ---------- timeline ----------
T_FR = LT[2][0] - 0.15; T2 = LT[3][0] - 0.12; T3 = LT[4][0] - 0.05; T3b = cue("upi") - 0.25
T5 = LT[6][0] - 0.15; T6 = LT[7][0]; T7 = LT[8][0] - 0.15; T8 = LT[9][0] - 0.15
T_NR = LT[1][0] - 0.05

def map_pt(px, py, tr): s, x0, y0 = tr; return (px - x0) * s, (py - y0) * s
RAVI_G = (540, 690)                         # Ravi's face in the group photo (centre, red T-shirt)

def background(t, L):
    if t < T_FR:
        if t < T_NR: fr, _ = photo_frame("rick", 1.0 + 0.07 * t / T_NR, 540, 660)
        else: fr, _ = photo_frame("rick", 1.30 + 0.05 * (t - T_NR), 545, 560)       # punch-in on "but not from rides"
        return fr, True
    if t < T2:
        k = (t - T_FR) / (T2 - T_FR); fr, tr = photo_frame("group", 1.12 + 0.10 * k, 540, 820)
        cx, cy = map_pt(*RAVI_G, tr); a = appear(t, T_FR + 0.15)
        r = 120 * (1.2 - 0.2 * a) * tr[0] / 1.5
        L.n.ellipse((cx - r, cy - r * 1.2, cx + r, cy + r * 1.2), outline=rgba(NEON, a), width=6)
        pill(L, cx, cy - r * 1.2 - 60, "Ravi", appear(t, cue("ravi", line=2) - 0.1), filled=True, fnt=PILL, h=76, padx=30)
        return fr, True
    if t < T3: return video_frame(A["rk2"], 2.5 + (t - T2)), True
    if t < T3b: return video_frame(A["rk1"], 1.5 + (t - T3), 1.0 + 0.04 * (t - T3)), True
    if t < T5: return NEON_BG.copy(), False
    if t < T6:
        k = (t - T5) / (T6 - T5); fr, _ = photo_frame("rick", 1.25 + 0.08 * k, 545, 620); return fr, True
    if t < T7:
        k = (t - T6) / (T7 - T6); fr, tr = photo_frame("selfie", 2.4 + 0.15 * k, 670, 640)
        x0, y0 = map_pt(585, 652, tr); x1, y1 = map_pt(760, 705, tr)
        L.n.rounded_rectangle((x0 - 16, y0 - 16, x1 + 16, y1 + 16), 20, outline=rgba(NEON, appear(t, T6 + 0.2)), width=7)
        return fr, True
    if t < T8:
        fr, _ = photo_frame("group", 1.05, 540, 760, grade="past"); return fr, True
    k = (t - T8) / (DUR - T8); fr, _ = photo_frame("selfie", 1.08 - 0.05 * k, 470, 700); return fr, True

def overlays(t, L):
    if t < T_FR:
        at = cue("₹14,000"); k = appear(t, at - 0.15, 0.2)
        n = int(14000 * ease((t - at + 0.15) / 0.9)); txt = (f"₹{n // 1000},{n % 1000:03d}" if n >= 1000 else f"₹{n}") + ("+" if n >= 14000 else "")
        if k > 0: L.t.text((540, 280), txt, font=HUGE, fill=rgba(NEON, k), anchor="mm", stroke_width=8, stroke_fill=(0, 0, 0, int(190 * k)))
        pill(L, 540, 420, "last week", appear(t, cue("last") - 0.1) * (1 - appear(t, T_NR - 0.1, 0.12)), fnt=PILL, h=78)
        kn = appear(t, cue("not") - 0.1, 0.15)
        if kn > 0:
            pill(L, 540, 420, "Not from rides", kn, filled=True, fnt=TITLE, h=104, padx=44, icon=icon_rickshaw)
            # strike-through over the rickshaw icon
            L.n.line([(540 - 245, 395), (540 - 175, 445)], fill=rgba((255, 90, 90), kn), width=6)
    elif t < T2:
        pill(L, 540, 230, "Delhi", appear(t, cue("delhi") - 0.1), filled=True, fnt=TITLE, h=96, padx=40, icon=icon_pin)
    elif t < T3:
        pill(L, 540, 240, "Morning · rickshaw", appear(t, T2 + 0.1), filled=True, fnt=TITLE, h=104, padx=44, icon=icon_sun)
    elif t < T3b:
        pill(L, 540, 240, "Evening · KoiPay", appear(t, T3 + 0.05), filled=True, fnt=TITLE, h=104, padx=44, icon=icon_moon)
    elif t < T5:
        a = 1 - appear(t, T5 - 0.15, 0.15)
        phone(L, DASH, 55, 300, 470, (t - T3b) / (T5 - T3b), a * appear(t, T3b, 0.3))
        rows = [("UPI payments", icon_phone, cue("upi") - 0.05), ("Peak traffic", icon_up, cue("peaks") - 0.15),
                ("His bank account", icon_bank, cue("bank") - 0.15)]
        ys = [400, 600, 800]
        for i, (lab, ic, at) in enumerate(rows):
            k = a * appear(t, at, 0.25); xo = 30 * (1 - appear(t, at, 0.25))
            box = (560 + xo, ys[i] - 70, 1035 + xo, ys[i] + 70)
            L.f.rounded_rectangle(box, 28, fill=rgba((8, 22, 13), k)); L.n.rounded_rectangle(box, 28, outline=rgba(NEON, k), width=3)
            ic(L.n, 625 + xo, ys[i], 70, k); ctext(L.t, (680 + xo, ys[i]), lab, LABEL, WHITE, k, "lm")
        k = a * appear(t, cue("commission") - 0.1)
        pill(L, 797, 1000, "+ commission", k, filled=True, fnt=PILL, h=96, padx=30, icon=icon_coin)
    elif t < T6:
        pill(L, 540, 240, "Started with $500", appear(t, cue("$500") - 0.15), filled=True, fnt=TITLE, h=104, padx=44, icon=icon_coin)
        pill(L, 540, 360, "saved from driving", appear(t, cue("saved") - 0.1), fnt=PILL, h=78, icon=icon_rickshaw)
    elif t < T7:
        f = 1 - clamp((t - T6) / 0.25)
        if f > 0: L.fill.alpha_composite(Image.new("RGBA", (W, H), rgba((210, 255, 225), 0.8 * f)))
        pill(L, 540, 240, "MONTH 1", appear(t, T6 + 0.05, 0.15), filled=True, fnt=BIG, h=140, padx=56)
        pill(L, 540, 385, "Last 7 days: ₹14,312", appear(t, T6 + 0.35), fnt=TITLE, h=100, padx=44)
    elif t < T8:
        a = 1 - appear(t, T8 - 0.12, 0.12)
        card(L, (110, 300, 970, 1120), a * appear(t, T7))
        ctext(L.t, (540, 390), "Ravi's plan", TITLE, WHITE, a * appear(t, T7 + 0.05))
        nodes = [("Now", "Rickshaw + Koi", T7 + 0.15), ("Next", "Grow the deposit", cue("grow") - 0.1), ("Goal", "Koi full-time", cue("full-time") - 0.15)]
        ys = [540, 740, 940]
        for i, (tag, lab, at) in enumerate(nodes):
            k = a * appear(t, at, 0.25); on = i == 2
            box = (180, ys[i] - 64, 900, ys[i] + 64)
            L.f.rounded_rectangle(box, 30, fill=rgba(NEON_DARK if on else (8, 22, 13), k)); L.n.rounded_rectangle(box, 30, outline=rgba(NEON, k), width=3)
            ctext(L.t, (230, ys[i]), tag, SMALL, NEON if not on else WHITE, k, "lm"); ctext(L.t, (370, ys[i]), lab, PILL, WHITE, k, "lm")
            if i: arrow_v(L, 540, ys[i - 1] + 66, ys[i] - 66, ease((t - at + 0.1) / 0.3), a, t)
    else:
        k1 = appear(t, T8 + 0.1)
        card(L, (110, 900, 970, 1170), k1)
        icon_chat(L.n, 540, 965, 80, k1)
        ctext(L.t, (540, 1035), "Want to start like Ravi?", LABEL, GREY, k1)
        pill(L, 540, 1110, "Message our manager", appear(t, cue("message") - 0.1), filled=True, fnt=TITLE, h=100, padx=44)
        pill(L, 540, 240, "Link in bio", appear(t, cue("link") - 0.1), filled=True, fnt=BIG, h=150, padx=60)

