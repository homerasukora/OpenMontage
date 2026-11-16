"""Final QA on the delivered file, using the camera-transformed matte written by render.py --qa.
usage: qa_final.py video.mp4 alpha_final.mkv"""
import sys, subprocess, numpy as np, cv2
vid, al = sys.argv[1:3]
W, H = 960, 540
po = subprocess.Popen(['ffmpeg', '-v', 'error', '-i', vid, '-vf', f'scale={W}:{H}', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'], stdout=subprocess.PIPE)
pa = subprocess.Popen(['ffmpeg', '-v', 'error', '-i', al, '-vf', f'scale={W}:{H}', '-f', 'rawvideo', '-pix_fmt', 'gray', '-'], stdout=subprocess.PIPE)
excl = np.zeros((H, W), bool); excl[:80] = True; excl[455:] = True     # label/logo band, subtitle band
green, struct, n = [], [], 0
while True:
    b = po.stdout.read(W * H * 3); a = pa.stdout.read(W * H)
    if len(b) < W * H * 3 or len(a) < W * H: break
    F = np.frombuffer(b, np.uint8).reshape(H, W, 3).astype(np.float32); A = np.frombuffer(a, np.uint8).reshape(H, W)
    green.append(int(((F[..., 1] - np.maximum(F[..., 0], F[..., 2]) > 45) & (F[..., 1] > 110)).sum()))
    out = ~(cv2.dilate((A > 10).astype(np.uint8), np.ones((25, 25), np.uint8)) > 0) & ~excl
    # background structure = edges stronger than the +-1 dither grain (blur first so grain disappears)
    g = cv2.GaussianBlur(F.mean(2), (0, 0), 1.5)
    lap = np.abs(cv2.Laplacian(g, cv2.CV_32F))
    struct.append(int(((lap > 4) & out).sum()))
    n += 1
green, struct = np.array(green), np.array(struct)
print('frames', n)
print('neon-green px (whole frame): max', green.max())
print('background structure px outside speaker: max', struct.max(), 'at', struct.argmax(), '| p99', int(np.percentile(struct, 99)))
