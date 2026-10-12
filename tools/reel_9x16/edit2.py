# Edit decision list: (clip, in, out) — times snapped to 25fps frames
import json
SEGS = [
    (0, 0.24, 4.68),
    (1, 0.12, 3.98), (1, 4.40, 7.80),
    (2, 0.24, 2.48),
    (3, 0.24, 2.90), (3, 3.24, 6.84),
    (6, 0.20, 1.40), (6, 1.70, 6.60),
    (7, 0.20, 4.00),
]
def snap(x): return round(round(x * 25) / 25, 2)
SEGS = [(c, snap(a), snap(b)) for c, a, b in SEGS]
if __name__ == "__main__":
    import sys
    clips = sys.argv[1]
    inputs, fc, cat = [], [], ""
    for k, (c, a, b) in enumerate(SEGS):
        inputs += ["-i", f"{clips}/c{c}.mp4"]
        fc.append(f"[{k}:v]trim={a}:{b},setpts=PTS-STARTPTS,fps=25[v{k}];"
                  f"[{k}:a]atrim={a}:{b},asetpts=PTS-STARTPTS,afade=t=in:d=0.01,afade=t=out:st={b-a-0.012:.3f}:d=0.012[a{k}];")
        cat += f"[v{k}][a{k}]"
    fc.append(f"{cat}concat=n={len(SEGS)}:v=1:a=1[v][a0];[a0]loudnorm=I=-14:TP=-1.5:LRA=11,aresample=48000[a]")
    print(json.dumps(inputs + ["-filter_complex", "".join(fc)]))
