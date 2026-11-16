"""Robust Video Matting (ONNX) -> lossless gray alpha video.
usage: matte.py model.onnx src.mov alpha.mkv downsample_ratio [cuts_csv]
At frame 0 and at every hard cut the recurrent state is reset and warmed up on the
first WARM frames of the new shot, so the previous shot's matte never bleeds through.
"""
import sys, subprocess, numpy as np, onnxruntime as ort, time
model, src, out = sys.argv[1:4]; dsr = float(sys.argv[4])
CUTS = set(int(x) for x in sys.argv[5].split(",")) if len(sys.argv) > 5 and sys.argv[5] else set()
WARM = 12
import os; FPS_OUT = os.environ.get("FPS", "30")
W, H = 1918, 1080
so = ort.SessionOptions(); so.intra_op_num_threads = 4
sess = ort.InferenceSession(model, so, providers=["CPUExecutionProvider"])
dec = subprocess.Popen(["ffmpeg", "-v", "error", "-i", src, "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], stdout=subprocess.PIPE)
enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "gray", "-s", f"{W}x{H}", "-r", FPS_OUT, "-i", "-", "-c:v", "ffv1", out], stdin=subprocess.PIPE)
d = np.array([dsr], np.float32)
zero = lambda: [np.zeros([1, 1, 1, 1], np.float32)] * 4

def read():
    b = dec.stdout.read(W * H * 3)
    return None if len(b) < W * H * 3 else np.frombuffer(b, np.uint8).reshape(H, W, 3).transpose(2, 0, 1)[None].astype(np.float32) / 255

def step(x, rec):
    fgr, pha, *rec = sess.run(None, {"src": x, "r1i": rec[0], "r2i": rec[1], "r3i": rec[2], "r4i": rec[3], "downsample_ratio": d})
    return pha, rec

buf, n, t0, rec = [], 0, time.time(), zero()
while True:
    x = buf.pop(0) if buf else read()
    if x is None: break
    if n == 0 or n in CUTS:
        # look ahead within the new shot, warm the state, then process from the shot start
        ahead = [x] + buf
        while len(ahead) < WARM:
            y = read()
            if y is None: break
            ahead.append(y)
        stop = min((c - n for c in CUTS if c > n), default=10**9)
        rec = zero()
        for y in ahead[:min(WARM, stop)]: _, rec = step(y, rec)
        for y in ahead[:min(WARM, stop)][::-1]: _, rec = step(y, rec)   # settle back on the first frame
        buf = ahead[1:]
    pha, rec = step(x, rec)
    enc.stdin.write((pha[0, 0] * 255 + .5).clip(0, 255).astype(np.uint8).tobytes()); n += 1
    if n % 100 == 0: print(n, round((time.time() - t0) / n, 3), flush=True)
enc.stdin.close(); enc.wait(); print("done", n, round((time.time() - t0) / max(n, 1), 3))
