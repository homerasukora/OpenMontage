"""Split speech at pauses into phrase pieces (<= 4 s) and transcribe each with Whisper (hi).
usage: hi_phrases.py audio out.json"""
import sys, json, subprocess, numpy as np, sherpa_onnx
SR = 16000
a = np.frombuffer(subprocess.run(["ffmpeg", "-v", "error", "-i", sys.argv[1], "-ac", "1", "-ar", str(SR), "-f", "f32le", "-"], capture_output=True).stdout, np.float32)
hop = SR // 100
e = np.array([np.sqrt((a[i:i + hop] ** 2).mean()) for i in range(0, len(a), hop)])
es = np.convolve(e, np.ones(5) / 5, "same")
v = es > np.median(es) * .35
# fixed-size phrase pieces: 1.2-3.2 s, each cut at the quietest point of its window (speech has few real pauses)
first = int(np.argmax(v)); last = len(v) - int(np.argmax(v[::-1]))
phr, s0 = [], first
while last - s0 > 320:
    lo, hi = s0 + 120, s0 + 320
    c = lo + int(np.argmin(es[lo:hi])); phr.append([s0, c]); s0 = c
phr.append([s0, last])
d = "models/sherpa-onnx-whisper-medium"
rec = sherpa_onnx.OfflineRecognizer.from_whisper(encoder=f"{d}/medium-encoder.int8.onnx", decoder=f"{d}/medium-decoder.int8.onnx",
                                                 tokens=f"{d}/medium-tokens.txt", language="hi", task="transcribe", num_threads=4)
out = []
for s0, s1 in phr:
    x = a[max(0, s0 - 5) * hop: (s1 + 5) * hop]
    st = rec.create_stream(); st.accept_waveform(SR, np.concatenate([x, np.zeros(SR * 3, np.float32)])); rec.decode_stream(st)
    out.append([round(s0 / 100, 2), round(s1 / 100, 2), st.result.text.strip()])
    print(f"{s0/100:6.2f}-{s1/100:6.2f} | {out[-1][2]}", flush=True)
json.dump(out, open(sys.argv[2], "w"), ensure_ascii=False, indent=0)
