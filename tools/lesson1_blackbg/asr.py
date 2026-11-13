import sys, json, soundfile as sf, sherpa_onnx
d=sys.argv[1]
r = sherpa_onnx.OfflineRecognizer.from_transducer(encoder=f"{d}/encoder.int8.onnx", decoder=f"{d}/decoder.int8.onnx", joiner=f"{d}/joiner.int8.onnx", tokens=f"{d}/tokens.txt", model_type="nemo_transducer", num_threads=4)
a, sr = sf.read(sys.argv[2], dtype="float32")
words=[]; CH=25
for off in range(0, len(a), CH*sr):
    seg=a[off:off+CH*sr]; s=r.create_stream(); s.accept_waveform(sr, seg); r.decode_stream(s)
    for t, ts in zip(s.result.tokens, s.result.timestamps):
        if t.startswith((" ","▁")) or not words or words[-1].get("chunk")!=off:
            words.append(dict(w=t.strip().lstrip("▁"), s=round(ts+off/sr,2), chunk=off))
        else: words[-1]["w"]+=t
for k,w in enumerate(words):
    w.pop("chunk"); w["e"]=words[k+1]["s"] if k+1<len(words) else round(len(a)/sr,2)
json.dump(words, open(sys.argv[3],"w"), indent=0)
print(" ".join(f"{w['w']}[{w['s']}]" for w in words))
