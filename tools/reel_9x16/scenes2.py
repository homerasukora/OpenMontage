# ---------- icons (video 2) ----------
def icon_shield(d, cx, cy, s, a, ok=1.0):
    p = [(cx, cy - 0.5 * s), (cx + 0.42 * s, cy - 0.34 * s), (cx + 0.38 * s, cy + 0.12 * s), (cx, cy + 0.5 * s),
         (cx - 0.38 * s, cy + 0.12 * s), (cx - 0.42 * s, cy - 0.34 * s)]
    d.line(p + [p[0]], fill=rgba(NEON, a), width=6, joint="curve")
    if ok > 0:
        d.line([(cx - 0.17 * s, cy), (cx - 0.04 * s, cy + 0.14 * s), (cx + 0.2 * s, cy - 0.14 * s)], fill=rgba(NEON, a * ok), width=6)

def icon_warn(d, cx, cy, s, a, filled=False):
    """Warning triangle with '!', drawn 4x supersampled for clean edges."""
    if a <= 0: return
    K = 4; size = int(s * 1.2); S_ = size * K
    tile = Image.new("RGBA", (S_, S_), (0, 0, 0, 0)); td = ImageDraw.Draw(tile)
    c, r = S_ / 2, 0.5 * s * K
    pts = [(c, c - r * 0.92), (c + r, c + r * 0.80), (c - r, c + r * 0.80)]
    col = rgba(NEON, 1.0); w = int(0.10 * s * K) if not filled else 0
    if filled:
        td.polygon(pts, fill=col)
        j = int(0.09 * s * K)                      # round the corners
        for x, y in pts: td.ellipse((x - j, y - j, x + j, y + j), fill=col)
        td.line(pts + [pts[0]], fill=col, width=2 * j)
        mark = (4, 14, 8, 255)
    else:
        td.line(pts + [pts[0]], fill=col, width=w, joint="curve")
        for x, y in pts: td.ellipse((x - w / 2, y - w / 2, x + w / 2, y + w / 2), fill=col)
        mark = col
    bw = 0.12 * s * K                              # exclamation bar + dot
    td.rounded_rectangle((c - bw / 2, c - r * 0.38, c + bw / 2, c + r * 0.30), radius=bw / 2, fill=mark)
    td.ellipse((c - bw * 0.6, c + r * 0.44, c + bw * 0.6, c + r * 0.44 + bw * 1.2), fill=mark)
    tile = tile.resize((size, size), Image.LANCZOS)
    if a < 1:
        al = tile.getchannel("A").point(lambda v: int(v * a)); tile.putalpha(al)
    d._image.alpha_composite(tile, (int(cx - size / 2), int(cy - size / 2)))

def icon_store(d, cx, cy, s, a):
    d.line([(cx - 0.5 * s, cy - 0.1 * s), (cx - 0.38 * s, cy - 0.42 * s), (cx + 0.38 * s, cy - 0.42 * s), (cx + 0.5 * s, cy - 0.1 * s), (cx - 0.5 * s, cy - 0.1 * s)], fill=rgba(NEON, a), width=5)
    d.rectangle((cx - 0.42 * s, cy - 0.1 * s, cx + 0.42 * s, cy + 0.45 * s), outline=rgba(NEON, a), width=5)
    d.rectangle((cx - 0.12 * s, cy + 0.12 * s, cx + 0.12 * s, cy + 0.45 * s), outline=rgba(NEON, a), width=4)

def icon_chat(d, cx, cy, s, a):
    d.rounded_rectangle((cx - 0.5 * s, cy - 0.38 * s, cx + 0.5 * s, cy + 0.22 * s), int(0.16 * s), outline=rgba(NEON, a), width=5)
    d.line([(cx - 0.2 * s, cy + 0.22 * s), (cx - 0.3 * s, cy + 0.45 * s), (cx + 0.02 * s, cy + 0.22 * s)], fill=rgba(NEON, a), width=5)
    for k in (-1, 0, 1):
        x = cx + k * 0.22 * s
        d.ellipse((x - 7, cy - 0.08 * s - 7, x + 7, cy - 0.08 * s + 7), fill=rgba(NEON, a))

def check_mark(L, x, y, k):
    L.n.ellipse((x - 30, y - 30, x + 30, y + 30), outline=rgba(NEON, k), width=5)
    L.n.line([(x - 14, y), (x - 3, y + 12), (x + 16, y - 12)], fill=rgba(NEON, k), width=6)

# ---------- scenes (video 2) ----------
CX, CARD = W // 2, (95, 60, 985, 625)

def scene_hook(L, t, a):
    card(L, CARD, a)
    k = a * appear(t, cue(0, "can") - 0.1)
    icon_bank(L.n, CX, 200, 150, k)
    kk = a * appear(t, cue(0, "blocked") - 0.1, 0.2)
    if kk > 0:   # alert badge on the bank
        L.f.ellipse((CX + 78, 78, CX + 162, 162), fill=rgba((4, 14, 8), kk))
        icon_warn(L.n, CX + 120, 122, 58, kk, filled=True)
    ctext(L.t, (CX, 365), "Bank account", TITLE, WHITE, a * appear(t, cue(0, "bank")))
    ctext(L.t, (CX, 445), "blocked?", BIG, NEON, kk)
    k3 = a * appear(t, cue(0, "p2p") - 0.1)
    if k3 > 0: pill(L, CX, 545, "while working with P2P processing", k3, fnt=SMALL, h=58)

def scene_reviews(L, t, a):
    card(L, CARD, a)
    ctext(L.t, (CX, 135), "When do banks review accounts?", LABEL, GREY, a * appear(t, cue(1, "reviews") - 0.1))
    rows = [("Unverified payment", "sources", cue(1, "unverified") - 0.15),
            ("Patterns that don't match", "normal activity", cue(1, "transaction") - 0.15)]
    for i, (l1, l2, at) in enumerate(rows):
        k = a * appear(t, at, 0.25); y = 265 + i * 170 - 20 * (1 - appear(t, at, 0.25))
        box = (150, y - 68, 930, y + 68)
        L.f.rounded_rectangle(box, 26, fill=rgba((12, 30, 18), k))
        L.n.rounded_rectangle(box, 26, outline=rgba(NEON, 0.6 * k), width=3)
        icon_warn(L.n, 225, y, 70, k)
        ctext(L.t, (290, y - 22), l1, PILL, WHITE, k, "lm")
        ctext(L.t, (290, y + 26), l2, PILL, NEON, k, "lm")

def scene_platform(L, t, a):
    card(L, CARD, a)
    k = a * appear(t, cue(2, "that") - 0.1)
    ctext(L.t, (CX, 225), "Choosing the", TITLE, WHITE, k)
    ctext(L.t, (CX, 320), "platform", BIG, NEON, a * appear(t, cue(2, "platform") - 0.1))
    k2 = a * appear(t, cue(2, "matters") - 0.1)
    if k2 > 0: pill(L, CX, 460, "matters", k2, filled=True, fnt=TITLE, h=96, padx=48)

def scene_verified(L, t, a):
    card(L, CARD, a)
    ctext(L.t, (CX, 125), "KoiPay", TITLE, WHITE, a * appear(t, cue(3, "koipay") - 0.1))
    k = a * appear(t, cue(3, "verified") - 0.1)
    if k > 0: pill(L, CX, 205, "Verified gaming merchants only", k, filled=True)
    xs = (220, CX, 860); y = 370
    k1 = a * appear(t, cue(3, "every") - 0.1)
    icon_store(L.n, xs[0], y, 100, k1); ctext(L.t, (xs[0], y + 85), "Merchant", SMALL, WHITE, k1)
    arrow(L, (xs[0] + 75, y), (xs[1] - 75, y), ease((t - cue(3, "checked") + 0.1) / 0.5), a, t)
    k2 = a * appear(t, cue(3, "checked") + 0.3)
    icon_shield(L.n, xs[1], y, 110, k2, appear(t, cue(3, "checked") + 0.5, 0.2))
    ctext(L.t, (xs[1], y + 85), "Checked", SMALL, NEON, k2)
    arrow(L, (xs[1] + 75, y), (xs[2] - 75, y), ease((t - cue(3, "sent")) / 0.5), a, t)
    k3 = a * appear(t, cue(3, "traders") - 0.1)
    icon_people(L.n, xs[2], y, 110, k3); ctext(L.t, (xs[2], y + 85), "Traders", SMALL, WHITE, k3)
    k4 = a * appear(t, cue(3, "payment"))
    ctext(L.t, (CX, 545), "before any payment request is sent", SMALL, GREY, k4)

def scene_checklist(L, t, a):
    card(L, CARD, a)
    rows = [("Verified traffic", "verified"), ("Clear limits", "clear"), ("Proper operating steps", "proper")]
    for i, (name, wd) in enumerate(rows):
        y = 140 + i * 115
        at = cue(6, wd) - 0.1
        k = a * appear(t, at, 0.25)
        on = appear(t, at + 0.15, 0.2)
        box = (150, y - 48, 930, y + 48)
        L.f.rounded_rectangle(box, 24, fill=rgba(NEON_DARK if on > 0.5 else (12, 30, 18), k * 0.9))
        L.n.rounded_rectangle(box, 24, outline=rgba(NEON, k), width=3)
        ctext(L.t, (200, y), name, PILL, WHITE, k, "lm")
        if on > 0: check_mark(L, 870, y, k * on)
    k = a * appear(t, cue(6, "reduce") - 0.1)
    if k > 0:
        L.n.line([(200, 470), (880, 470)], fill=rgba(NEON, 0.35 * k), width=2)
        pill(L, CX, 540, "Helps reduce avoidable risk", k, filled=True, h=82)

def scene_cta(L, t, a):
    card(L, CARD, a)
    sw = cue(7, "you", 2) - 0.25                   # switch to the link plate on "You can find the link"
    k1 = a * (1 - ease((t - sw) / 0.25))
    if k1 > 0:
        icon_chat(L.n, CX, 170, 120, k1 * appear(t, cue(7, "manager") - 0.4))
        ctext(L.t, (CX, 305), "Questions about", TITLE, WHITE, k1 * appear(t, cue(7, "questions") - 0.2))
        ctext(L.t, (CX, 380), "your security?", TITLE, NEON, k1 * appear(t, cue(7, "questions")))
        k = k1 * appear(t, cue(7, "manager"))
        if k > 0: pill(L, CX, 500, "Ask our manager", k, filled=True, fnt=TITLE, h=100, padx=44)
    k2 = a * appear(t, sw + 0.15, 0.3)
    if k2 > 0:
        pill(L, CX, 342 + 15 * (1 - k2), "Link in bio", k2, filled=True, fnt=BIG, h=150, padx=64)

SCENES = []
for clip, fn in [(0, scene_hook), (1, scene_reviews), (2, scene_platform), (3, scene_verified), (6, scene_checklist), (7, scene_cta)]:
    s, e = clip_span(clip)
    SCENES.append((s, e, fn))

