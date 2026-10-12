import sys, json, soundfile as sf, sherpa_onnx
d = sys.argv[1]
r = sherpa_onnx.OfflineRecognizer.from_transducer(encoder=f"{d}/encoder.int8.onnx", decoder=f"{d}/decoder.int8.onnx", joiner=f"{d}/joiner.int8.onnx", tokens=f"{d}/tokens.txt", model_type="nemo_transducer", num_threads=4)
out = {}
for i in range(int(sys.argv[4]) if len(sys.argv) > 4 else 10):
    a, sr = sf.read(f"{sys.argv[2]}/c{i}.wav", dtype="float32")
    s = r.create_stream(); s.accept_waveform(sr, a); r.decode_stream(s)
    res = s.result
    # merge BPE tokens into words
    words = []
    for t, ts in zip(res.tokens, res.timestamps):
        if t.startswith((" ", "▁")) or not words:
            words.append(dict(w=t.strip().lstrip("▁"), s=round(ts, 2)))
        else:
            words[-1]["w"] += t
    for k, w in enumerate(words):
        w["e"] = words[k+1]["s"] if k+1 < len(words) else round(len(a)/sr, 2)
    out[i] = words
    print(i, res.text, flush=True)
json.dump(out, open(sys.argv[3], "w"), indent=1)
