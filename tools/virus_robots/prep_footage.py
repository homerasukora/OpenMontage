#!/usr/bin/env python3
"""Cut + crop source footage into a JPG frame sequence the renderer can preload.

Usage: python3 prep_footage.py <src.mp4> <name> <start> <end> <x> <y> <w> <h> [fps=15] [height=560]
Writes web/footage/<name>/0001.jpg ... and updates web/footage/manifest.json
(crop box is in source pixels; text overlays/logos are removed by choosing the crop).
"""
import json, subprocess, sys
from pathlib import Path

src, name, start, end, x, y, w, h = sys.argv[1:9]
fps = int(sys.argv[9]) if len(sys.argv) > 9 else 15
height = int(sys.argv[10]) if len(sys.argv) > 10 else 560
root = Path(__file__).resolve().parent / 'web' / 'footage'
out = root / name
out.mkdir(parents=True, exist_ok=True)
for f in out.glob('*.jpg'):
    f.unlink()
vf = f'crop={w}:{h}:{x}:{y},fps={fps},scale=-2:{height}:flags=lanczos'
subprocess.run(['ffmpeg', '-v', 'error', '-y', '-ss', start, '-to', end, '-i', src, '-vf', vf,
                '-q:v', '3', str(out / '%04d.jpg')], check=True)
frames = sorted(out.glob('*.jpg'))
man_path = root / 'manifest.json'
man = json.loads(man_path.read_text()) if man_path.exists() else {}
man[name] = {'frames': len(frames), 'fps': fps, 'aspect': int(w) / int(h), 'src': Path(src).name,
             'range': [float(start), float(end)], 'crop': [int(x), int(y), int(w), int(h)]}
man_path.write_text(json.dumps(man, indent=2))
print(name, len(frames), 'frames')
