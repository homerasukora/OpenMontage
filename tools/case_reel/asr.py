import sys, soundfile as sf, sherpa_onnx, numpy as np
d = sys.argv[1]
r = sherpa_onnx.OfflineRecognizer.from_transducer(encoder=f"{d}/encoder.int8.onnx", decoder=f"{d}/decoder.int8.onnx", joiner=f"{d}/joiner.int8.onnx", tokens=f"{d}/tokens.txt", model_type="nemo_transducer", num_threads=4)
for f in sys.argv[2:]:
    a, sr = sf.read(f, dtype="float32")
    if a.ndim > 1: a = a.mean(1)
    s = r.create_stream(); s.accept_waveform(sr, a); r.decode_stream(s)
    print(f.split("/")[-1], "|", s.result.text)
