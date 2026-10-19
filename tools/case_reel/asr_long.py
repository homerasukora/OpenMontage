import sys, soundfile as sf, sherpa_onnx, json
d, wav, out = sys.argv[1:4]
r = sherpa_onnx.OfflineRecognizer.from_transducer(encoder=f"{d}/encoder.int8.onnx", decoder=f"{d}/decoder.int8.onnx", joiner=f"{d}/joiner.int8.onnx", tokens=f"{d}/tokens.txt", model_type="nemo_transducer", num_threads=4)
a, sr = sf.read(wav, dtype="float32"); CH = 20 * sr; res = []
for i in range(0, len(a), CH):
    s = r.create_stream(); s.accept_waveform(sr, a[i:i + CH]); r.decode_stream(s)
    res.append(dict(t=round(i / sr, 1), text=s.result.text)); print(f"[{i//sr//60:02d}:{i//sr%60:02d}] {s.result.text}", flush=True)
json.dump(res, open(out, "w"), indent=1)
