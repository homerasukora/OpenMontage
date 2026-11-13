import sys, subprocess, numpy as np, onnxruntime as ort, time
model, src, out = sys.argv[1:4]; dsr=float(sys.argv[4]); maxf=int(sys.argv[5]) if len(sys.argv)>5 else 10**9
W,H=1918,1080
so=ort.SessionOptions(); so.intra_op_num_threads=4
sess=ort.InferenceSession(model, so, providers=["CPUExecutionProvider"])
dec=subprocess.Popen(["ffmpeg","-v","error","-i",src,"-f","rawvideo","-pix_fmt","rgb24","-"],stdout=subprocess.PIPE)
enc=subprocess.Popen(["ffmpeg","-v","error","-y","-f","rawvideo","-pix_fmt","gray","-s",f"{W}x{H}","-r","30","-i","-","-c:v","ffv1",out],stdin=subprocess.PIPE)
rec=[np.zeros([1,1,1,1],np.float32)]*4; d=np.array([dsr],np.float32); n=0; t0=time.time()
while n<maxf:
    b=dec.stdout.read(W*H*3)
    if len(b)<W*H*3: break
    x=np.frombuffer(b,np.uint8).reshape(H,W,3).transpose(2,0,1)[None].astype(np.float32)/255
    fgr,pha,*rec=sess.run(None,{"src":x,"r1i":rec[0],"r2i":rec[1],"r3i":rec[2],"r4i":rec[3],"downsample_ratio":d})
    enc.stdin.write((pha[0,0]*255+.5).clip(0,255).astype(np.uint8).tobytes()); n+=1
    if n%100==0: print(n, round((time.time()-t0)/n,3), flush=True)
enc.stdin.close(); enc.wait(); print("done",n,round((time.time()-t0)/max(n,1),3))
