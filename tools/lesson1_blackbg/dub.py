"""Place a one-take Hindi TTS onto the Lesson 1 v4 timeline sentence by sentence and build Hindi subtitles.
usage: dub.py clips_dir(s01.wav..s13.wav) script_hi.txt out_audio.wav out_subs.json [subs_hi.txt with | breaks]
Each sentence starts where the English one did, is sped up
(max 1.15x, pitch kept) only if it would overrun its slot, and is pushed later if the previous one still speaks."""
import sys, json, re, subprocess, numpy as np
take, script, out_wav, out_subs = sys.argv[1:5]
SR = 44100
MAX_TEMPO = float(__import__("os").environ.get("MAX_TEMPO", "1.06"))  # post-synthesis speed-up hurts intelligibility; keep it small
EN_START = [0.24, 2.48, 7.36, 10.16, 18.32, 22.72, 27.16, 34.28, 37.32, 42.28, 48.28, 50.56, 53.92]  # output time
VIDEO_END = 56.6
HARD_END = 56.45  # audio may not run past the picture
CUT_A, CUT_B = 1645 / 30, 1691 / 30
sents = [l.strip() for l in open(script, encoding="utf-8") if l.strip()]
assert len(sents) == len(EN_START)

def load(p):
    b = subprocess.run(["ffmpeg", "-v", "error", "-i", p, "-ac", "1", "-ar", str(SR), "-f", "f32le", "-"], capture_output=True).stdout
    return np.frombuffer(b, np.float32).copy()
def trim(x, thr=.008):
    hop = SR // 100; e = np.array([np.sqrt((x[i:i + hop] ** 2).mean()) for i in range(0, len(x), hop)])
    v = np.where(e > thr)[0]
    return x[max(0, (v[0] - 3) * hop): (v[-1] + 6) * hop] if len(v) else x
clips = [trim(load(f"{take}/s{k+1:02d}.wav")) for k in range(len(sents))]   # take = dir with one wav per sentence
def stretch(x, r):
    if abs(r - 1) < .01: return x
    p = subprocess.run(["ffmpeg", "-v", "error", "-f", "f32le", "-ar", str(SR), "-ac", "1", "-i", "-", "-af", f"atempo={r:.4f}",
                        "-f", "f32le", "-"], input=x.tobytes(), capture_output=True).stdout
    return np.frombuffer(p, np.float32)

out = np.zeros(int((VIDEO_END + 3) * SR), np.float32)
placed, cursor = [], 0.0
for k, (x, txt) in enumerate(zip(clips, sents)):
    slot_end = EN_START[k + 1] - .12 if k + 1 < len(sents) else VIDEO_END - .3
    start = max(EN_START[k] - (.3 if k else 0), cursor + .08)   # may lead the English line by up to 0.3 s
    dur = len(x) / SR
    r = min(max(dur / max(slot_end - start, .1), 1.0), MAX_TEMPO)
    y = stretch(x, r)
    i0 = int(start * SR); out[i0:i0 + len(y)] += y
    cursor = start + len(y) / SR
    placed.append((start, cursor, txt, r))
    print(f"{k+1:2d} start {start:6.2f} end {cursor:6.2f} slot_end {slot_end:6.2f} speed x{r:.2f} {'OVER' if cursor > slot_end + .05 else ''}")
out = out[:int(max(cursor + .4, VIDEO_END) * SR)]
fade = int(.3 * SR); out[-fade:] *= np.linspace(1, 0, fade)
subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "f32le", "-ar", str(SR), "-ac", "1", "-i", "-", "-af", "loudnorm=I=-16:TP=-1.5",
                "-ar", "44100", "-ac", "2", out_wav], input=out.tobytes())

# subtitles: split every sentence into short screens (break after commas, <= 24 chars), time by character share
def to_src(t): return t if t < CUT_A else t + (CUT_B - CUT_A)
subs = []
SUB_LINES = [l.strip() for l in open(sys.argv[5], encoding="utf-8") if l.strip()] if len(sys.argv) > 5 else None
for k, (start, end, txt, r) in enumerate(placed):
    if SUB_LINES:                                     # hand-made breaks: "part | part | part"
        chunks = [c.strip().split() for c in SUB_LINES[k].split("|")]
    else:
        words = txt.split(); chunks, cur = [], []
        for w in words:
            if cur and (len(" ".join(cur + [w])) > 24): chunks.append(cur); cur = []
            cur.append(w)
            if re.search(r"[,]$", w): chunks.append(cur); cur = []
        if cur: chunks.append(cur)
    total = sum(len(" ".join(c)) for c in chunks); t = start
    for c in chunks:
        d = (end - start) * len(" ".join(c)) / total
        text = re.sub(r"[,।]$", "", " ".join(c))
        subs.append([round(to_src(t), 3), round(to_src(t + d), 3), text]); t += d
json.dump(subs, open(out_subs, "w"), ensure_ascii=False, indent=0)
print("subs:", " | ".join(x[2] for x in subs))
