"""Word-level timestamps with sherpa-onnx Parakeet. Usage: asr_words.py <model_dir> <wav16k> <out.json>"""
import sys, json, soundfile as sf, sherpa_onnx
d, wav, out = sys.argv[1:4]
r = sherpa_onnx.OfflineRecognizer.from_transducer(encoder=f"{d}/encoder.int8.onnx", decoder=f"{d}/decoder.int8.onnx",
    joiner=f"{d}/joiner.int8.onnx", tokens=f"{d}/tokens.txt", model_type="nemo_transducer", num_threads=4)
a, sr = sf.read(wav, dtype="float32")
if a.ndim > 1: a = a.mean(1)
s = r.create_stream(); s.accept_waveform(sr, a); r.decode_stream(s)
words = []
for t, ts in zip(s.result.tokens, s.result.timestamps):
    if t.startswith((" ", "▁")) or not words: words.append(dict(w=t.strip().lstrip("▁"), s=round(ts, 2)))
    else: words[-1]["w"] += t
for i, w in enumerate(words): w["e"] = words[i + 1]["s"] if i + 1 < len(words) else round(len(a) / sr, 2)
json.dump(words, open(out, "w"), indent=0)
print(s.result.text)
