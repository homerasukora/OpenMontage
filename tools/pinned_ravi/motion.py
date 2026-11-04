import sys, cv2, numpy as np, json
f = sys.argv[1]; cap = cv2.VideoCapture(f); orb = cv2.ORB_create(3000); bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)
ok, f0 = cap.read(); g0 = cv2.cvtColor(f0, cv2.COLOR_BGR2GRAY); k0, d0 = orb.detectAndCompute(g0, None)
res = []; i = 0
while True:
    ok, fr = cap.read()
    if not ok: break
    i += 1
    if i % 6: continue
    g = cv2.cvtColor(fr, cv2.COLOR_BGR2GRAY); k, d = orb.detectAndCompute(g, None)
    m = sorted(bf.match(d0, d), key=lambda x: x.distance)[:600]
    p0 = np.float32([k0[x.queryIdx].pt for x in m]); p1 = np.float32([k[x.trainIdx].pt for x in m])
    M, inl = cv2.estimateAffinePartial2D(p0, p1, method=cv2.RANSAC, ransacReprojThreshold=2.0)
    s = float(np.hypot(M[0, 0], M[1, 0])); res.append((i, round(s, 4), round(float(M[0, 2]), 1), round(float(M[1, 2]), 1)))
print(f.split("/")[-1], res[::3], "last", res[-1])
