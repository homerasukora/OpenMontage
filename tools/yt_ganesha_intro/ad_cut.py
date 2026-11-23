"""Ad cut from the finished 'Who we are' render: video segments with 0.2 s crossfades + matching voice, fresh bed, -15 LUFS."""
import subprocess, sys
Y = "/tmp/claude-0/-home-user/7c5690c1-77ca-5715-b441-4cc8e349293a/scratchpad/yt"
name, segs = sys.argv[1], [tuple(map(float, s.split(":"))) for s in sys.argv[2:]]
X = 0.2
durs = [b - a for a, b in segs]; total = sum(durs) - X * (len(segs) - 1)
subprocess.run(["python3", f"{Y}/../bn/bed.py", f"{Y}/ad/bed_{name}.wav", str(total + 1)], check=True, capture_output=True)
fc, vlast, alast, off = [], None, None, 0.0
for i, (a, b) in enumerate(segs):
    fc.append(f"[0:v]trim={a}:{b},setpts=PTS-STARTPTS[v{i}]")
    fc.append(f"[1:a]atrim={a}:{b},asetpts=PTS-STARTPTS[a{i}]")
for i in range(1, len(segs)):
    off += durs[i - 1] - X
    vin = f"[v0]" if i == 1 else f"[vx{i-1}]"; ain = f"[a0]" if i == 1 else f"[ax{i-1}]"
    fc.append(f"{vin}[v{i}]xfade=transition=fade:duration={X}:offset={off:.3f}[vx{i}]")
    fc.append(f"{ain}[a{i}]acrossfade=d={X}[ax{i}]")
n = len(segs) - 1
fc.append(f"[ax{n}]highpass=f=70,volume=13.5dB[vo]")
fc.append(f"[2:a]atrim=0:{total:.3f},volume=-19.8dB,afade=t=in:d=0.8,afade=t=out:st={total-2.5:.3f}:d=2.5[b]")
fc.append("[vo][b]amix=inputs=2:normalize=0,alimiter=limit=0.84:attack=3:release=60:level=false[ao]")
out = f"/home/user/OpenMontage/renders/ganesha_pay_ad_{name}.mp4"
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", f"{Y}/out_video.mp4", "-i", f"{Y}/voice.wav", "-i", f"{Y}/ad/bed_{name}.wav",
                "-filter_complex", ";".join(fc), "-map", f"[vx{n}]", "-map", "[ao]", "-c:v", "libx264", "-preset", "medium", "-crf", "17",
                "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "256k", "-movflags", "+faststart", out], check=True)
print(out, round(total, 2))
