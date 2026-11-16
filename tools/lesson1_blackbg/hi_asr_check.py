"""Intelligibility proxy: split each sentence wav at pauses into <=3.5 s pieces, Whisper-transcribe, CER vs script."""
import sys, re, subprocess, numpy as np, sherpa_onnx
d = "models/sherpa-onnx-whisper-medium"
r = sherpa_onnx.OfflineRecognizer.from_whisper(encoder=f"{d}/medium-encoder.int8.onnx", decoder=f"{d}/medium-decoder.int8.onnx",
                                               tokens=f"{d}/medium-tokens.txt", language="hi", task="transcribe", num_threads=4)
SR = 16000
def load(p): return np.frombuffer(subprocess.run(["ffmpeg", "-v", "error", "-i", p, "-ac", "1", "-ar", str(SR), "-f", "f32le", "-"], capture_output=True).stdout, np.float32)
def pieces(a):
    hop = SR // 100; e = np.array([np.sqrt((a[i:i + hop] ** 2).mean()) for i in range(0, len(a), hop)])
    out, s = [], 0
    while s < len(e):
        if len(e) - s <= 350: out.append((s, len(e))); break
        lo, hi = s + 150, min(s + 350, len(e))
        c = lo + int(np.argmin(e[lo:hi])); out.append((s, c)); s = c
    return [a[x * hop:y * hop] for x, y in out]
def asr(a):
    txt = []
    for p in pieces(a):
        s = r.create_stream(); s.accept_waveform(SR, np.concatenate([p, np.zeros(SR * 6, np.float32)])); r.decode_stream(s); txt.append(s.result.text)
    return " ".join(txt)
norm = lambda t: re.sub(r"[^ऀ-ॿ]", "", t).replace("़", "").replace("।", "")
def cer(ref, hyp):
    a, b = norm(ref), norm(hyp); dp = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        prev, dp[0] = dp[0], i
        for j, cb in enumerate(b, 1):
            prev, dp[j] = dp[j], min(dp[j] + 1, dp[j - 1] + 1, prev + (ca != cb))
    return dp[-1] / max(len(a), 1)
lines = [l.strip() for l in open("hi/script_hi.txt", encoding="utf-8") if l.strip()]
for d_ in sys.argv[1:]:
    cs = []
    for i, ref in enumerate(lines, 1):
        hyp = asr(load(f"{d_}/s{i:02d}.wav")); c = cer(ref, hyp); cs.append(c)
        if "-v" in sys.argv[0:1] or c > .25: print(f"   {d_} s{i:02d} CER {c:.2f} | {hyp}")
    print(f"{d_}: mean CER {np.mean(cs):.3f}  worst {max(cs):.2f}", flush=True)
