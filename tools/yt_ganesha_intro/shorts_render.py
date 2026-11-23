"""9:16 Shorts/Reels cut of «Who we are» (no income hook), phone-first layout:
Arnold (vertical crop) on top, captions, one big native card with short phrases, wordmark centred under the card,
everything inside the Shorts/Reels safe zone (nothing below y≈1500, right margin for the action buttons).
usage: shorts_render.py out.mp4 [--preview t1,t2,... outdir]   (t = output seconds)"""
import sys
_argv = sys.argv[:]; sys.argv = ["x", "/dev/null"]
exec(open("/tmp/claude-0/-home-user/7c5690c1-77ca-5715-b441-4cc8e349293a/scratchpad/yt/yt_render.py").read().split("# ---------------- render ----------------")[0])
sys.argv = _argv
OUTV = sys.argv[1]
PREV = [float(x) for x in sys.argv[3].split(",")] if len(sys.argv) > 3 and sys.argv[2] == "--preview" else None
VW, VH = 1080, 1920
SEGS = [(23.88, 59.62), (97.45, 106.20), (132.27, 146.60)]   # source seconds of the 16:9 master
XF = 0.2
OUT_T, acc = [], 0.0
for a, b in SEGS:
    OUT_T.append((acc, a, b)); acc += (b - a) - XF
TOTAL_V = acc + XF
NFV = int(round(TOTAL_V * FPS))

# ---------- layout (safe zone: top ~180 px UI icons, bottom ~420 px caption/channel, right ~120 px buttons) ----------
AR_H = 860                       # Arnold area
SUB_Y = 805                      # caption centre
CX = 540; CW = 840; CARD_TOP = 900
LOGO_Y = 1432                    # wordmark under the card
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
    pad, th, rh, gap = 34, 86, 104, 14
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
    pad, bh, gap = 28, 150, 18; h = pad + max(n, 1) * bh + (gap if n > 1 else 0) + pad
    im, d = _base(h)
    for k, (lab, txt, ic) in enumerate([("NEW TO P2P", "Free Academy course", "cap"), ("ALREADY TRADING", "Message a manager", "plane")]):
        if k >= n: continue
        y = pad + k * (bh + gap)
        d.rounded_rectangle([pad * S, y * S, (CW - pad) * S, (y + bh) * S], radius=24 * S, fill=EMERALD + (215,), outline=GOLD + (220,), width=2 * S)
        im.alpha_composite(icon(ic, 60).resize((60 * S, 60 * S)), ((pad + 30) * S, (y + 45) * S))
        d.text(((CW // 2 + 40) * S, (y + 44) * S), lab, font=fS("Manrope", 34, "Bold"), fill=GOLD, anchor="mm")
        d.text(((CW // 2 + 40) * S, (y + 100) * S), txt, font=fS("Manrope", 56, "Bold"), fill=CHAMP, anchor="mm")
    return rgba(down(im))
LINK_PILL = pill("Links in the description", ic="down", fill=GOLD + (255,), border=GOLD, fg=ONYX, size=46, h=100, padx=46)
EMPTY = np.zeros((2, 2, 4), np.float32)

# card timeline in SOURCE seconds: (t_in, key, builder(n), row cues)
C = cue
CARDS = [
    (23.0, "hook", lambda n: card_title("How P2P processing", "works in India"), []),
    (C("s3", "verified") - .1, "how", lambda n: card_list("How it works", [("ok", "Verified merchants"), ("dot", "Payments via UPI"), ("ok", "Fixed commission")], n),
     [C("s3", "verified"), C("s3", "upi"), C("s3", "fixed")]),
    (C("s4", "customer") - .3, "round", lambda n: card_list("One round", [("dot", "Client pays via UPI"), ("ok", "You confirm it"), ("down", "You earn 3%")], n),
     [C("s4", "customer"), C("s4", "confirm"), C("s4", "3")]),
    (C("s4", "then") - .1, "rates", lambda n: card_rates(min(n + 1, 2), "Paid daily in USD" if n >= 2 else None), [C("s4", "payout"), C("s4", "commission")]),
    (97.3, "disp", lambda n: card_list("Disputes?", [("ok", "Your manager"), ("ok", "handles them")], n), [C("s6b", "manager"), C("s6b", "manager") + .25]),
    (C("s6b", "cyber") - .1, "stat", lambda n: card_stat(), []),
    (132.0, "link", lambda n: EMPTY, []),
    (C("s10", "already") - .15, "end", lambda n: card_end(n), [C("s10", "already") - .1, C("s10", "new")]),
]
_cc = {}
def cstate(i, n):
    k = (i, n)
    if k not in _cc: _cc[k] = CARDS[i][2](n)
    return _cc[k]
def put(img, L, al, dy=0):
    vover(img, L, CX - L.shape[1] // 2, CARD_TOP + dy, al)
def draw_card_v(img, ts):
    i = max([k for k, c in enumerate(CARDS) if c[0] <= ts] or [0])
    t_in, key, _, cues = CARDS[i]
    n = sum(1 for c in cues if ts >= c)
    lay = cstate(i, n); a = ease((ts - t_in) / .3)
    if i > 0 and ts - t_in < .3:                                  # outgoing card fades out
        pi = i - 1; pn = sum(1 for c in CARDS[pi][3] if ts >= c); put(img, cstate(pi, pn), 1 - a)
    if n and ts - cues[n - 1] < .25 and ts - t_in >= .3:          # newest row fades in
        f = ease((ts - cues[n - 1]) / .25); put(img, cstate(i, n - 1), 1 - f); put(img, lay, f)
    else:
        put(img, lay, a, int(24 * (1 - a)))
    if key in ("link", "end"):                                     # gold pill: alone first, then under the buttons
        y = CARD_TOP + 40 if key == "link" else CARD_TOP + lay.shape[0] + 20
        pa = ease((ts - CARDS[6][0]) / .35)
        vover(img, LINK_PILL, CX - LINK_PILL.shape[1] // 2, y, pa)

def vsub(img, t):
    for s0, e0, ws in SUBS:
        if s0 <= t < e0:
            L = sub_layer(ws); L = cv2.resize(L, (int(L.shape[1] * 1.3), int(L.shape[0] * 1.3)), interpolation=cv2.INTER_CUBIC)
            if L.shape[1] > 880: L = cv2.resize(L, (880, int(L.shape[0] * 880 / L.shape[1])), interpolation=cv2.INTER_AREA)
            vover(img, L, CX - L.shape[1] // 2, SUB_Y - L.shape[0] // 2, min(1, (t - s0) / .1 + .35)); return

def vframe(ts, raw):
    img = VBG.copy()
    crop = raw[20:20 + 484, 681:681 + 608]
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
        out = (img + VDITHER).clip(0, 255).astype(np.uint8)
        if enc: enc.stdin.write(out.tobytes())
        else: Image.fromarray(out).save(f"{sys.argv[4]}/v{t:06.2f}.png")
        if j % 300 == 0: print(j, NFV, flush=True)
    if enc: enc.stdin.close(); enc.wait()

if __name__ == "__main__":
    print("segments", OUT_T, "total", round(TOTAL_V, 2))
    main()
