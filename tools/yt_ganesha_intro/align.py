"""TTS-time -> clip-time map from word alignment (clip audio vs clean TTS)."""
import json, sys, re, difflib
tts, vid, out = sys.argv[1:4]
a = json.load(open(tts)); b = json.load(open(vid))
n = lambda w: re.sub(r"[^a-z0-9]", "", w.lower())
sm = difflib.SequenceMatcher(None, [n(x["w"]) for x in a], [n(x["w"]) for x in b], autojunk=False)
pairs = []
for blk in sm.get_matching_blocks():
    for k in range(blk.size): pairs.append((a[blk.a + k]["s"], b[blk.b + k]["s"]))
# also map word ends of the last word
if pairs and a and b: pairs.append((a[-1]["e"], b[-1]["e"]))
pairs = sorted(set(pairs))
mono = []
for p in pairs:
    if not mono or (p[0] > mono[-1][0] and p[1] > mono[-1][1]): mono.append(p)
json.dump(mono, open(out, "w"))
sl = (mono[-1][1] - mono[0][1]) / (mono[-1][0] - mono[0][0])
print(out, len(a), len(b), "matched", len(mono), "start", mono[0], "slope", round(sl, 3))
