"""Word timestamps with sherpa-onnx Parakeet TDT. Audio is split at the quietest point
in each 15-24 s window (never mid-word), so no words are lost at chunk borders."""
import sys, json, numpy as np, soundfile as sf, sherpa_onnx
d = sys.argv[1]
r = sherpa_onnx.OfflineRecognizer.from_transducer(encoder=f"{d}/encoder.int8.onnx", decoder=f"{d}/decoder.int8.onnx", joiner=f"{d}/joiner.int8.onnx", tokens=f"{d}/tokens.txt", model_type="nemo_transducer", num_threads=4)
a, sr = sf.read(sys.argv[2], dtype="float32")
if a.ndim > 1: a = a.mean(1)
hop = int(.02 * sr); env = np.sqrt(np.convolve(a ** 2, np.ones(hop * 10) / (hop * 10), "same"))[::hop]
cuts, pos = [0], 0
while len(a) - pos > 24 * sr:
    lo, hi = (pos + 15 * sr) // hop, (pos + 24 * sr) // hop
    pos = int((lo + np.argmin(env[lo:hi])) * hop); cuts.append(pos)
cuts.append(len(a))
words = []
for c0, c1 in zip(cuts[:-1], cuts[1:]):
    s = r.create_stream(); s.accept_waveform(sr, a[c0:c1]); r.decode_stream(s)
    first = True
    for t, ts in zip(s.result.tokens, s.result.timestamps):
        if t.startswith((" ", "▁")) or first:
            words.append(dict(w=t.strip().lstrip("▁"), s=round(ts + c0 / sr, 2))); first = False
        else: words[-1]["w"] += t
for k, w in enumerate(words):
    w["e"] = words[k + 1]["s"] if k + 1 < len(words) else round(len(a) / sr, 2)
json.dump(words, open(sys.argv[3], "w"), indent=0)
print("split at", [round(c / sr, 2) for c in cuts])
print(" ".join(f"{w['w']}[{w['s']}]" for w in words))
