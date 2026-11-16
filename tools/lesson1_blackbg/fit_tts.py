"""Per-sentence Piper synthesis with a native speaking rate chosen so each sentence fits its English slot.
usage: fit_tts.py model.onnx script.txt out_dir"""
import sys, subprocess, numpy as np, soundfile as sf
model, script, out = sys.argv[1:4]
EN_START = [0.24, 2.48, 7.36, 10.16, 18.32, 22.72, 27.16, 34.28, 37.32, 42.28, 48.28, 50.56, 53.92]
VIDEO_END = 56.3                        # last word must end before the picture fades
BASE, FASTEST = 0.90, 0.80              # Piper length_scale: 1.0 = model default, lower = faster
lines = [l.strip() for l in open(script, encoding="utf-8") if l.strip()]
def synth(t, ls, p):
    subprocess.run(["python3", "-m", "piper", "-m", model, "--length-scale", f"{ls:.3f}", "-f", p], input=t.encode(), capture_output=True, check=True)
    a, sr = sf.read(p); e = np.abs(a) > .01; idx = np.where(e)[0]
    return (idx[-1] - idx[0]) / sr
import os; os.makedirs(out, exist_ok=True)
for k, t in enumerate(lines):
    slot = (EN_START[k + 1] if k + 1 < len(lines) else VIDEO_END + .12) - EN_START[k] - .2 + (.3 if k else 0)
    p = f"{out}/s{k+1:02d}.wav"; ls = BASE; d = synth(t, ls, p)
    if d > slot:
        ls = max(FASTEST, BASE * slot / d); d = synth(t, ls, p)
    print(f"{k+1:2d} slot {slot:5.2f} speech {d:5.2f} length_scale {ls:.3f} {'(still long)' if d > slot + .05 else ''}", flush=True)
