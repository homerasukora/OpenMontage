import sys, json, re, difflib, soundfile as sf, sherpa_onnx
d, wav, lines_f, out = sys.argv[1:5]
r = sherpa_onnx.OfflineRecognizer.from_transducer(encoder=f"{d}/encoder.int8.onnx", decoder=f"{d}/decoder.int8.onnx", joiner=f"{d}/joiner.int8.onnx", tokens=f"{d}/tokens.txt", model_type="nemo_transducer", num_threads=4)
a, sr = sf.read(wav, dtype="float32"); s = r.create_stream(); s.accept_waveform(sr, a); r.decode_stream(s)
asr = []
for t, ts in zip(s.result.tokens, s.result.timestamps):
    if t.startswith((" ", "▁")) or not asr: asr.append(dict(w=t.strip().lstrip("▁"), s=ts))
    else: asr[-1]["w"] += t
norm = lambda w: re.sub(r"[^a-z0-9]", "", w.lower())
lines = json.load(open(lines_f)); disp = []
for li, l in enumerate(lines):
    for w in l.split(): disp.append(dict(w=w, line=li))
A = [norm(x["w"]) for x in asr]; D = [norm(x["w"]) for x in disp]
sm = difflib.SequenceMatcher(a=D, b=A, autojunk=False)
for blk in sm.get_matching_blocks():
    for k in range(blk.size): disp[blk.a + k]["s"] = asr[blk.b + k]["s"]
# interpolate gaps
known = [i for i, x in enumerate(disp) if "s" in x]
for i, x in enumerate(disp):
    if "s" in x: continue
    p = max([k for k in known if k < i], default=None); n = min([k for k in known if k > i], default=None)
    if p is None: x["s"] = disp[n]["s"] - 0.3 * (n - i)
    elif n is None: x["s"] = disp[p]["s"] + 0.35 * (i - p)
    else: x["s"] = disp[p]["s"] + (disp[n]["s"] - disp[p]["s"]) * (i - p) / (n - p)
dur = len(a) / sr
for i, x in enumerate(disp):
    x["e"] = min(disp[i + 1]["s"] if i + 1 < len(disp) else dur, x["s"] + 0.8); x["s"] = round(x["s"], 3); x["e"] = round(x["e"], 3)
LT = []
for li in range(len(lines)):
    ws = [x for x in disp if x["line"] == li]; LT.append([ws[0]["s"], ws[-1]["e"]])
json.dump(disp, open(out + "/words.json", "w"), indent=0)
json.dump(dict(lines=LT, dur=round(dur, 3)), open(out + "/vo.json", "w"))
print("matched", len(known), "/", len(disp)); print([[round(a, 2), round(b, 2)] for a, b in LT], round(dur, 2))
