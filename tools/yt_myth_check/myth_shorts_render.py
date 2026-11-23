"""9:16 Shorts/Reels: P2P Myth Check — «Is P2P processing a scam?» (myth 1 + CTA), same phone-first layout as the
Who-we-are Shorts: Arnold on top (face never covered), captions under him, big short-phrase cards, wordmark under the card.
usage: myth_shorts_render.py out.mp4 [--preview t1,t2,... outdir]   (t = output seconds)"""
import sys
_argv = sys.argv[:]; sys.argv = ["x", "/dev/null"]
exec(open("/tmp/claude-0/-home-user/7c5690c1-77ca-5715-b441-4cc8e349293a/scratchpad/myth/myth_render.py").read().split("# ---------------- render ----------------")[0])
sys.argv = _argv
OUTV = sys.argv[1]
PREV = [float(x) for x in sys.argv[3].split(",")] if len(sys.argv) > 3 and sys.argv[2] == "--preview" else None
VW, VH = 1080, 1920
SEGS = [(22.20, 59.44), (106.36, 127.60)]                     # source seconds of the Myth Check master
XF = 0.2
OUT_T, acc = [], 0.0
for a, b in SEGS:
    OUT_T.append((acc, a, b)); acc += (b - a) - XF
TOTAL_V = acc + XF
NFV = int(round(TOTAL_V * FPS))

# ---------- layout (safe zone: top ~180 px UI icons, bottom ~420 px caption/channel, right ~120 px buttons) ----------
AR_H = 960                       # Arnold area
SUB_Y = 1012                      # caption centre
CX = 540; CW = 840; CARD_TOP = 1085
LOGO_Y = 1592                    # wordmark under the card
vy, vx = np.mgrid[0:VH, 0:VW].astype(np.float32)
vr = np.sqrt(((vx - VW * .5) / (VW * .9)) ** 2 + ((vy - VH * .58) / (VH * .5)) ** 2)
VBG = np.array(ONYX, np.float32) + np.clip(1 - vr, 0, 1)[..., None] ** 1.8 * (np.array(EMERALD, np.float32) * 1.5 - np.array(ONYX, np.float32))
VDITHER = np.random.default_rng(5).uniform(-1, 1, (VH, VW, 1)).astype(np.float32)
AGRAD = np.clip((np.arange(AR_H, dtype=np.float32)[:, None, None] - AR_H * .5) / (AR_H * .5), 0, 1) ** 1.25 * .9
_wmv = Image.open(f"{D}/ganesha_wordmark_noir.png").convert("RGBA"); _wmv = _wmv.resize((330, round(_wmv.height * 330 / _wmv.width)), Image.LANCZOS)
VLOGO = rgba(_wmv)

def vover(dst, src, x, y, a=1.0):
    h, w = src.shape[:2]; x0, y0 = max(0, x), max(0, y); x1, y1 = min(VW, x + w), min(VH, y + h)
    if x1 <= x0 or y1 <= y0 or a <= 0: return
    s = src[y0 - y:y1 - y, x0 - x:x1 - x]; al = s[..., 3:] / 255 * a
    dst[y0:y1, x0:x1] = dst[y0:y1, x0:x1] * (1 - al) + s[..., :3] * al

# ---------- native cards: short phrases, big type ----------
def _base(h):
    im = Image.new("RGBA", (CW * S, h * S), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle([0, 0, CW * S - 1, h * S - 1], radius=34 * S, fill=ONYX + (225,), outline=GOLD + (235,), width=3 * S)
    return im, d
def card_list(title, rows, n):
    pad, th, rh, gap = 32, 84, 98, 14
    h = pad + th + n * (rh + gap) + pad - (gap if n else 0)
    im, d = _base(h)
    d.text((CW * S // 2, (pad + th // 2 - 4) * S), title, font=fS("Cormorant", 72, "SemiBold"), fill=GOLD, anchor="mm", features=["lnum"])
    y = pad + th
    for ic, txt in rows[:n]:
        d.rounded_rectangle([pad * S, y * S, (CW - pad) * S, (y + rh) * S], radius=22 * S, fill=EMERALD + (170,), outline=GOLD + (110,), width=S)
        im.alpha_composite(icon(ic, 56).resize((56 * S, 56 * S)), ((pad + 26) * S, (y + (rh - 56) // 2) * S))
        d.text(((pad + 106) * S, (y + rh // 2) * S), txt, font=fS("Manrope", 54, "Bold"), fill=CHAMP, anchor="lm")
        y += rh + gap
    return rgba(down(im))
def card_title(l1, l2):
    im, d = _base(270)
    d.text((CW * S // 2, 100 * S), l1, font=fS("Cormorant", 84, "SemiBold"), fill=CHAMP, anchor="mm", features=["lnum"])
    d.text((CW * S // 2, 190 * S), l2, font=fS("Cormorant", 84, "SemiBold"), fill=GOLD, anchor="mm", features=["lnum"])
    return rgba(down(im))
def card_rates(n, footer):
    h = 470 if footer else 380; im, d = _base(h)
    tw, gap = 360, 48; x0 = (CW - 2 * tw - gap) // 2
    for k, (lab, num, ic) in enumerate([("PayIn", "3%", "down"), ("PayOut", "+1%", "up")]):
        if k >= n: continue
        x = x0 + k * (tw + gap)
        d.rounded_rectangle([x * S, 36 * S, (x + tw) * S, 344 * S], radius=26 * S, fill=EMERALD + (200,), outline=GOLD + (200,), width=2 * S)
        im.alpha_composite(icon(ic, 50).resize((50 * S, 50 * S)), ((x + 28) * S, 62 * S))
        d.text(((x + tw // 2) * S, 90 * S), lab, font=fS("Manrope", 50, "Bold"), fill=CHAMP, anchor="mm")
        d.text(((x + tw // 2) * S, 230 * S), num, font=fS("Manrope", 140, "Bold"), fill=GOLD, anchor="mm")
    if footer: d.text((CW * S // 2, 410 * S), footer, font=fS("Manrope", 50, "Bold"), fill=CHAMP, anchor="mm")
    return rgba(down(im))
def card_stat():
    im, d = _base(440)
    d.text((CW * S // 2, 80 * S), "Cyber complaints", font=fS("Manrope", 50, "Bold"), fill=CHAMP, anchor="mm")
    d.text((CW * S // 2, 215 * S), "~5", font=fS("Manrope", 170, "Bold"), fill=GOLD, anchor="mm")
    d.text((CW * S // 2, 345 * S), "per 10,000 payments", font=fS("Manrope", 50, "Bold"), fill=CHAMP, anchor="mm")
    d.text((CW * S // 2, 405 * S), "≈ 0.05%", font=fS("Manrope", 38, "SemiBold"), fill=(200, 190, 160), anchor="mm")
    return rgba(down(im))
def card_end(n):
    pad, bh, gap = 26, 138, 16; h = pad + max(n, 1) * bh + (gap if n > 1 else 0) + pad
    im, d = _base(h)
    for k, (lab, txt, ic) in enumerate([("NEW TO P2P", "Free Academy course", "cap"), ("ALREADY TRADING", "Message a manager", "plane")]):
        if k >= n: continue
        y = pad + k * (bh + gap)
        d.rounded_rectangle([pad * S, y * S, (CW - pad) * S, (y + bh) * S], radius=24 * S, fill=EMERALD + (215,), outline=GOLD + (220,), width=2 * S)
        im.alpha_composite(icon(ic, 58).resize((58 * S, 58 * S)), ((pad + 30) * S, (y + 40) * S))
        d.text(((CW // 2 + 40) * S, (y + 40) * S), lab, font=fS("Manrope", 33, "Bold"), fill=GOLD, anchor="mm")
        d.text(((CW // 2 + 40) * S, (y + 93) * S), txt, font=fS("Manrope", 56, "Bold"), fill=CHAMP, anchor="mm")
    return rgba(down(im))
LINK_PILL = pill("Links in the description", ic="down", fill=GOLD + (255,), border=GOLD, fg=ONYX, size=46, h=100, padx=46)
EMPTY = np.zeros((2, 2, 4), np.float32)

# ---------- Myth Check cards (source seconds of the myth master) ----------
def card_quote(lines):
    im, d = _base(330)
    d.text((CW * S // 2, 44 * S), "P2P MYTH CHECK", font=fS("Manrope", 30, "ExtraBold"), fill=GOLD, anchor="mm")
    d.text((40 * S, 20 * S), "“", font=fS("Cormorant", 200, "SemiBold"), fill=GOLD + (200,))
    for k, ln in enumerate(lines):
        d.text((CW * S // 2, (150 + k * 92) * S), ln, font=fS("CormorantItalic", 84, "SemiBold Italic"), fill=CHAMP, anchor="mm", features=["lnum"])
    return rgba(down(im))
QUOTE = card_quote(["P2P processing", "is a scam."])
STAMP_T1 = cue("m3", "scam") + .5            # MYTH? lands after "…is a scam."
STAMP_T2 = SE["m3"] + .25                     # MYTH at the end of the myth
STAMPS_V = [(STAMP_T1, "q"), (STAMP_T2, "myth")]
C = cue
CARDS = [
    (22.0, "quote", lambda n: QUOTE, []),
    (C("m3", "heres") + .3, "red", lambda n: card_list("Red flags", [("x", "A stranger's DM"), ("x", "Huge percentages"), ("x", "Deposit… then silence")], n),
     [C("m3", "stranger"), C("m3", "huge"), C("m3", "disappears")]),
    (C("m3", "a", 3) - .1, "green1", lambda n: card_list("Green flags", [("ok", "KYB-checked merchants"), ("ok", "Fixed 3% + 1%"), ("ok", "Live volume online")], n),
     [C("m3", "every"), C("m3", "rates"), C("m3", "our")]),
    (C("m3", "manager") - .3, "green2", lambda n: card_list("Green flags", [("ok", "A real manager"), ("ok", "Real agent results"), ("cap", "Free Academy first")], n),
     [C("m3", "manager"), C("m3", "agents"), C("m3", "learn")]),
    (SE["m3"], "quote2", lambda n: QUOTE, []),
    (106.2, "acad", lambda n: card_list("Ganesha Pay Academy", [("ok", "Free course"), ("ok", "How it really works"), ("ok", "Step by step")], n),
     [C("m6", "free"), C("m6", "really"), C("m6", "step")]),
    (END_FS, "end", lambda n: card_end(n), [END_FS + .05, C("m6", "message")]),
]
_cc = {}
def cstate(i, n):
    k = (i, n)
    if k not in _cc: _cc[k] = CARDS[i][2](n)
    return _cc[k]
def put(img, L, al, dy=0):
    vover(img, L, CX - L.shape[1] // 2, CARD_TOP + dy, al)
def vstamp(img, st, cx, cy, t, t0, scale):
    if t < t0: return
    k = t - t0; sc = scale * (1 + .75 * (1 - ease(k / .13))); a = min(1, k / .05)
    L = cv2.resize(st, (max(2, int(st.shape[1] * sc)), max(2, int(st.shape[0] * sc))), interpolation=cv2.INTER_AREA)
    vover(img, L, cx - L.shape[1] // 2, cy - L.shape[0] // 2, a)
def draw_card_v(img, ts):
    i = max([k for k, c in enumerate(CARDS) if c[0] <= ts] or [0])
    t_in, key, _, cues = CARDS[i]
    n = sum(1 for c in cues if ts >= c)
    lay = cstate(i, n); a = ease((ts - t_in) / .3)
    if i > 0 and ts - t_in < .3:
        pi = i - 1; pn = sum(1 for c in CARDS[pi][3] if ts >= c); put(img, cstate(pi, pn), 1 - a)
    if n and ts - cues[n - 1] < .25 and ts - t_in >= .3:
        f = ease((ts - cues[n - 1]) / .25); put(img, cstate(i, n - 1), 1 - f); put(img, lay, f)
    else:
        put(img, lay, a, int(24 * (1 - a)))
    if key == "quote": vstamp(img, STAMP_Q, CX + 230, CARD_TOP + 300, ts, STAMP_T1, .8)
    if key == "quote2": vstamp(img, STAMP_MYTH, CX + 200, CARD_TOP + 290, ts, STAMP_T2, 1.0)
    if key == "end":
        vover(img, LINK_PILL, CX - LINK_PILL.shape[1] // 2, CARD_TOP + lay.shape[0] + 16, ease((ts - t_in) / .35))
def vshake(ts):
    for t0, kind in STAMPS_V:
        k = ts - t0 - .1
        if 0 <= k < .22:
            amp = (12 if kind == "myth" else 7) * (1 - k / .22)
            return int(amp * math.sin(k * 90)), int(amp * .6 * math.cos(k * 70))
    return 0, 0

def vsub(img, t):
    for s0, e0, ws in SUBS:
        if s0 <= t < e0:
            L = sub_layer(ws); L = cv2.resize(L, (int(L.shape[1] * 1.3), int(L.shape[0] * 1.3)), interpolation=cv2.INTER_CUBIC)
            if L.shape[1] > 880: L = cv2.resize(L, (880, int(L.shape[0] * 880 / L.shape[1])), interpolation=cv2.INTER_AREA)
            vover(img, L, CX - L.shape[1] // 2, SUB_Y - L.shape[0] // 2, min(1, (t - s0) / .1 + .35)); return

def vframe(ts, raw):
    img = VBG.copy()
    crop = raw[20:20 + 540, 681:681 + 608]
    ar = cv2.resize(np.ascontiguousarray(crop), (VW, AR_H), interpolation=cv2.INTER_CUBIC).astype(np.float32)
    bl = cv2.GaussianBlur(ar, (0, 0), 1.4); ar = np.clip(ar * 1.35 - bl * .35, 0, 255)
    img[:AR_H] = ar * (1 - AGRAD) + img[:AR_H] * AGRAD
    draw_card_v(img, ts)
    vover(img, VLOGO, CX - VLOGO.shape[1] // 2, LOGO_Y)
    if ts < SPEECH_END + .05: vsub(img, ts)
    return img

READERS = {}
def raw_at(ts):
    k = max(i for i, c in enumerate(CLIPS) if c["t0"] <= ts + 1e-6); c = CLIPS[k]
    if PREV:
        rr = Reader(c["f"], W, H, t0=clip_time(c, ts - c["t0"])); f = rr.next(); rr.p.kill(); return f.astype(np.float32)
    if k not in READERS: READERS[k] = SeqReader(c["f"])
    return READERS[k].get(clip_time(c, ts - c["t0"]) * FPS)

def src_times(t):
    out = [(a + t - o0, i) for i, (o0, a, b) in enumerate(OUT_T) if o0 <= t < o0 + (b - a)]
    if len(out) == 2:
        q = ease((t - OUT_T[out[1][1]][0]) / XF); return [(out[0][0], 1 - q), (out[1][0], q)]
    return [(out[-1][0], 1.0)] if out else [(SEGS[-1][1], 1.0)]

def main():
    enc = None
    if not PREV:
        enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{VW}x{VH}", "-r", str(FPS), "-i", "-",
                                "-c:v", "libx264", "-preset", "medium", "-crf", "17", "-pix_fmt", "yuv420p", OUTV], stdin=subprocess.PIPE)
    targets = sorted(int(round(x * FPS)) for x in PREV) if PREV else None
    for j in range(NFV):
        t = j / FPS
        if targets is not None and j not in targets:
            if j > max(targets): break
            continue
        img = None
        for ts, wgt in src_times(t):
            fr = vframe(ts, raw_at(ts)); img = fr * wgt if img is None else img + fr * wgt
        dx, dy = vshake(src_times(t)[-1][0])
        if dx or dy: img = np.roll(np.roll(img, dx, axis=1), dy, axis=0)
        out = (img + VDITHER).clip(0, 255).astype(np.uint8)
        if enc: enc.stdin.write(out.tobytes())
        else: Image.fromarray(out).save(f"{sys.argv[4]}/v{t:06.2f}.png")
        if j % 300 == 0: print(j, NFV, flush=True)
    if enc: enc.stdin.close(); enc.wait()

if __name__ == "__main__":
    print("segments", OUT_T, "total", round(TOTAL_V, 2))
    main()
