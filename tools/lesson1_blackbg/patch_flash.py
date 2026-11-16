"""Replace a source light-leak/flash transition (unmattable whiteout frames) with a brand-palette flash:
frame first-1 -> warm champagne/gold bloom -> frame last+1. usage: patch_flash.py in.mp4 out.mp4 fps first last"""
import sys, subprocess, numpy as np
src, dst, fps, a, b = sys.argv[1], sys.argv[2], sys.argv[3], int(sys.argv[4]), int(sys.argv[5])
W, H = 1920, 1080
yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
CHAMPAGNE = np.array([230, 214, 168], np.float32); GOLD = np.array([207, 165, 74], np.float32)
# soft bloom from the upper right (where the source leak came from), champagne core, gold rim
r = np.sqrt(((xx - W * .78) / (W * .9)) ** 2 + ((yy - H * .25) / (H * 1.1)) ** 2)
core = np.clip(1 - r, 0, 1)[..., None]
BLOOM = GOLD + (CHAMPAGNE - GOLD) * core
SHAPE = np.clip(.55 + .45 * core, 0, 1)            # bloom covers the upper right first
def grab(i):
    x = subprocess.run(["ffmpeg", "-v", "error", "-i", src, "-vf", f"select=eq(n\\,{i})", "-vsync", "0", "-frames:v", "1",
                        "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True).stdout
    return np.frombuffer(x, np.uint8).reshape(H, W, 3).astype(np.float32)
A, B = grab(a - 1), grab(b + 1)
n = b - a + 1
def flash(i):
    t = (i + 1) / (n + 1)
    base = A if t < .5 else B                          # switch shots under the brightest moment
    k = np.sin(np.pi * t) ** 1.5 * .92                 # flash intensity, peak 0.92 in the middle
    m = np.clip(k * SHAPE * 1.25, 0, .92)
    return (base * (1 - m) + BLOOM * m).clip(0, 255).astype(np.uint8).tobytes()
dec = subprocess.Popen(["ffmpeg", "-v", "error", "-i", src, "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], stdout=subprocess.PIPE)
enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", fps, "-i", "-",
                        "-c:v", "libx264", "-preset", "slow", "-crf", "16", "-pix_fmt", "yuv420p", dst], stdin=subprocess.PIPE)
j = 0
while True:
    x = dec.stdout.read(W * H * 3)
    if len(x) < W * H * 3: break
    enc.stdin.write(flash(j - a) if a <= j <= b else x); j += 1
enc.stdin.close(); enc.wait(); print("flash", a, "-", b, "of", j)
