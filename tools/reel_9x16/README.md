# 9:16 reel pipeline (split screen)

Speaker on top (native 1080 px crop, no upscale; jump cuts alternate with a 1.12 punch-in), neon infographic panel below, subtitles on the seam.

1. `transcribe.py <parakeet_model_dir> <clips_dir> words.json` — word timestamps (sherpa-onnx + NeMo Parakeet TDT 0.6B v2 int8, from k2-fsa/sherpa-onnx GitHub releases). Clips are named `c0.mp4 … c9.mp4`.
2. `edit.py <clips_dir>` — prints ffmpeg args for the edit list `SEGS` (clip, in, out); concat + loudnorm -14 LUFS → `base.mov`.
3. `render.py base.mov words.json out.mp4` — composites the frames. Pass a 4th arg `t1,t2,...` and an output dir instead of a file for preview stills.

Scenes in `render.py` are keyed to spoken words via `cue(clip, word)`, so the graphics stay in sync after re-cuts.
Requires: ffmpeg, numpy, pillow, Inter Display fonts.
