"""Replace broken transition frames with a clean crossfade between two good frames of the finished video.
usage: patch_frames.py in.mp4 out.mp4 fps first_bad last_bad"""
import sys, subprocess, numpy as np
src, dst, fps, a, b = sys.argv[1], sys.argv[2], sys.argv[3], int(sys.argv[4]), int(sys.argv[5])
W, H = 1920, 1080
dec = subprocess.Popen(["ffmpeg", "-v", "error", "-i", src, "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], stdout=subprocess.PIPE)
frames = []
while True:
    x = dec.stdout.read(W * H * 3)
    if len(x) < W * H * 3: break
    frames.append(x)
A = np.frombuffer(frames[a - 1], np.uint8).reshape(H, W, 3).astype(np.float32)
B = np.frombuffer(frames[b + 1], np.uint8).reshape(H, W, 3).astype(np.float32)
n = b - a + 1
for i in range(n):
    t = (i + 1) / (n + 1); t = t * t * (3 - 2 * t)
    frames[a + i] = (A * (1 - t) + B * t).clip(0, 255).astype(np.uint8).tobytes()
enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", fps, "-i", "-",
                        "-c:v", "libx264", "-preset", "slow", "-crf", "16", "-pix_fmt", "yuv420p", dst], stdin=subprocess.PIPE)
for f in frames: enc.stdin.write(f)
enc.stdin.close(); enc.wait(); print("patched", a, "-", b, "of", len(frames))
