"""Build the VO track: Kokoro lines + Musk clip segments, with pauses.
Usage: vo.py <kokoro_dir> <lines.json> <musk_audio.wav> <out_dir> [sid=27] [speed=0.92]
Writes out_dir/vo.wav (48 kHz mono), out_dir/vo_musk.wav (Musk-only stem), out_dir/timing.json
"""
import sys, os, json, numpy as np, soundfile as sf
from math import gcd
from scipy.signal import resample_poly
kd, lines_f, musk_f, out = sys.argv[1:5]
sid = int(sys.argv[5]) if len(sys.argv) > 5 else 27
speed = float(sys.argv[6]) if len(sys.argv) > 6 else 0.92
SR = 48000
GAP = {"L1": 1.1, "L2": .55, "L3": .45, "L4": .3, "MB": .6, "L5": 1.0, "L6a": .9, "L6b": .9, "L6c": .9, "L6d": .9,
       "L7": .6, "L8": 1.4, "L9": .7, "L10": .25, "MC": .5, "L11": .9, "L12": .45, "L13": 1.8}
LEAD = .5
WAVDIR = os.environ.get("WAVDIR")  # pre-rendered lines (<KEY>.wav), e.g. OmniVoice; otherwise Kokoro
if not WAVDIR:
  import sherpa_onnx
  cfg = sherpa_onnx.OfflineTtsConfig(model=sherpa_onnx.OfflineTtsModelConfig(kokoro=sherpa_onnx.OfflineTtsKokoroModelConfig(
    model=f"{kd}/model.onnx", voices=f"{kd}/voices.bin", tokens=f"{kd}/tokens.txt", data_dir=f"{kd}/espeak-ng-data",
    lexicon=f"{kd}/lexicon-us-en.txt", lang="en-us"), num_threads=4))
  tts = sherpa_onnx.OfflineTts(cfg)
musk, msr = sf.read(musk_f, dtype="float32")
if musk.ndim > 1: musk = musk.mean(1)
if msr != SR: musk = resample_poly(musk, SR // gcd(SR, msr), msr // gcd(SR, msr)).astype(np.float32)

def trim(a, thr=.012):
    nz = np.where(np.abs(a) > thr)[0]
    return a[max(nz[0] - int(.03 * SR), 0): nz[-1] + int(.08 * SR)]

vo, mk, timing, t = [np.zeros(int(LEAD * SR))], [np.zeros(int(LEAD * SR))], [], LEAD
for key, text in json.load(open(lines_f)):
    if key.startswith("M"):
        _, s, e = text.split(); a = musk[int(float(s) * SR): int(float(e) * SR)].copy()
        fade = int(.03 * SR); a[:fade] *= np.linspace(0, 1, fade); a[-fade:] *= np.linspace(1, 0, fade)
        a = a / (np.abs(a).max() + 1e-6) * .8
        typ, src = "musk", [float(s), float(e)]
    else:
        if WAVDIR:
            a, gsr = sf.read(f"{WAVDIR}/{key}.wav", dtype="float32"); a = a.mean(1) if a.ndim > 1 else a
        else:
            g = tts.generate(text, sid=sid, speed=speed); a, gsr = np.asarray(g.samples, np.float32), g.sample_rate
        a = resample_poly(a, SR // gcd(SR, gsr), gsr // gcd(SR, gsr)).astype(np.float32)
        a = trim(a); a = a / (np.abs(a).max() + 1e-6) * .85
        typ, src = "vo", None
    z = np.zeros_like(a)
    vo.append(a if typ == "vo" else z); mk.append(a if typ == "musk" else z)
    timing.append(dict(key=key, type=typ, text=text, s=round(t, 3), e=round(t + len(a) / SR, 3), src=src))
    gap = np.zeros(int(GAP.get(key, .35) * SR)); vo.append(gap); mk.append(gap)
    t += len(a) / SR + GAP.get(key, .35)
sf.write(f"{out}/vo.wav", np.concatenate(vo), SR)
sf.write(f"{out}/vo_musk.wav", np.concatenate(mk), SR)
json.dump(dict(dur=round(t, 3), segments=timing), open(f"{out}/timing.json", "w"), indent=1)
for x in timing: print(f"{x['key']:4s} {x['s']:6.2f}-{x['e']:6.2f}  {x['text'][:70]}")
print("total", round(t, 2))
