import sys, json, soundfile as sf, sherpa_onnx
d, wav, lines_f, vo_json, out = sys.argv[1:6]
r = sherpa_onnx.OfflineRecognizer.from_transducer(encoder=f"{d}/encoder.int8.onnx", decoder=f"{d}/decoder.int8.onnx", joiner=f"{d}/joiner.int8.onnx", tokens=f"{d}/tokens.txt", model_type="nemo_transducer", num_threads=4)
a, sr = sf.read(wav, dtype="float32"); s = r.create_stream(); s.accept_waveform(sr, a); r.decode_stream(s)
asr = []
for t, ts in zip(s.result.tokens, s.result.timestamps):
    if t.startswith((" ", "▁")) or not asr: asr.append(dict(w=t.strip().lstrip("▁"), s=ts))
    else: asr[-1]["w"] += t
lines = [l[1] for l in json.load(open(lines_f))]; LT = json.load(open(vo_json))["lines"]
words = []
for li, (text, (ls, le)) in enumerate(zip(lines, LT)):
    disp = text.split(); hits = [w for w in asr if ls - 0.15 <= w["s"] < le]
    if len(hits) == len(disp): starts = [max(h["s"], ls) for h in hits]
    else:                                           # proportional by characters
        tot = sum(len(x) + 1 for x in disp); acc = 0; starts = []
        for x in disp: starts.append(ls + (le - ls) * acc / tot); acc += len(x) + 1
        print("proportional line", li, len(hits), len(disp))
    for k, x in enumerate(disp):
        words.append(dict(w=x, s=round(starts[k], 3), e=round(starts[k + 1] if k + 1 < len(disp) else le, 3), line=li))
json.dump(words, open(out, "w"), indent=0)
print(len(words), "words")
