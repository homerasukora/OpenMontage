import sys, sherpa_onnx, soundfile as sf
d = sys.argv[1]
cfg = sherpa_onnx.OfflineTtsConfig(model=sherpa_onnx.OfflineTtsModelConfig(kokoro=sherpa_onnx.OfflineTtsKokoroModelConfig(
    model=f"{d}/model.onnx", voices=f"{d}/voices.bin", tokens=f"{d}/tokens.txt", data_dir=f"{d}/espeak-ng-data",
    lexicon=f"{d}/lexicon-us-en.txt", lang="en-us"), num_threads=4))
tts = sherpa_onnx.OfflineTts(cfg)
text, sid, speed, out = sys.argv[2], int(sys.argv[3]), float(sys.argv[4]), sys.argv[5]
a = tts.generate(text, sid=sid, speed=speed)
sf.write(out, a.samples, a.sample_rate)
print(out, len(a.samples) / a.sample_rate)
