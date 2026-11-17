"""Head position per frame from an RVM matte (mobilenet, low res). usage: headtrack.py src t0 t1 out.json"""
import sys, json, subprocess, numpy as np, onnxruntime as ort
src, t0, t1, out = sys.argv[1], float(sys.argv[2]), float(sys.argv[3]), sys.argv[4]
W, H = 480, 270
sess = ort.InferenceSession("models/rvm_mobilenetv3_fp32.onnx", providers=["CPUExecutionProvider"])
b = subprocess.run(["ffmpeg", "-v", "error", "-ss", str(t0), "-to", str(t1), "-i", src, "-vf", f"fps=25,scale={W}:{H}", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True).stdout
F = np.frombuffer(b, np.uint8).reshape(-1, H, W, 3)
rec = [np.zeros([1, 1, 1, 1], np.float32)] * 4; d = np.array([.5], np.float32); res = []
for f in F:
    x = f.transpose(2, 0, 1)[None].astype(np.float32) / 255
    _, pha, *rec = sess.run(None, {"src": x, "r1i": rec[0], "r2i": rec[1], "r3i": rec[2], "r4i": rec[3], "downsample_ratio": d})
    a = pha[0, 0] > .5
    rows = np.where(a[:, W // 6: 5 * W // 6].any(1))[0]
    if len(rows) == 0: res.append(res[-1] if res else [.5, .35]); continue
    y0 = rows[0]; band = a[y0:y0 + int(H * .22)]
    xs = np.where(band.any(0))[0]
    res.append([float((xs.min() + xs.max()) / 2 / W), float((y0 + H * .13) / H)])   # face centre (normalised)
r = np.array(res)
k = 9; pad = np.pad(r, ((k, k), (0, 0)), mode="edge")
sm = np.array([pad[i:i + 2 * k + 1].mean(0) for i in range(len(r))])          # smooth over ~0.7 s
json.dump(sm.tolist(), open(out, "w")); print(out, len(sm), sm.min(0).round(2), sm.max(0).round(2))
