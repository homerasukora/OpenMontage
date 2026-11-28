"""OmniVoice (k2-fsa) narration: design a voice once from a VoiceStudio preset, then clone it for every line.
Usage: vo_omni.py <omnivoice_repo> <model_dir> <lines.json> <out_dir> <instruct> [seed] [only_ref]
Writes out_dir/ref.wav (+ ref.txt) and out_dir/<KEY>.wav for each non-Musk line (24 kHz).
NOTE: OmniVoice weights are CC-BY-NC (non-commercial) — drafts only.
"""
import sys, json, os, torch
repo, model_dir, lines_f, out, instruct = sys.argv[1:6]
seed = int(sys.argv[6]) if len(sys.argv) > 6 else 7
only_ref = len(sys.argv) > 7 and sys.argv[7] == "ref"
sys.path.insert(0, repo)
from omnivoice.models.omnivoice import OmniVoice
from omnivoice.utils.audio import save_audio
torch.set_num_threads(4)
os.makedirs(out, exist_ok=True)
model = OmniVoice.from_pretrained(model_dir, device_map="cpu", dtype=torch.float32, allow_tokenizer_fallback=True)
REF_TEXT = "Some signals arrive long before anyone is ready to hear them. This is one of them."
ref = f"{out}/ref.wav"
if not os.path.exists(ref):
    torch.manual_seed(seed)
    a = model.generate(text=REF_TEXT, language="English", instruct=instruct, num_step=32, guidance_scale=2.0)
    save_audio(ref, a[0], model.sampling_rate); open(f"{out}/ref.txt", "w").write(REF_TEXT)
    print("ref done", flush=True)
if only_ref: sys.exit(0)
for key, text in json.load(open(lines_f)):
    if key.startswith("M"): continue
    p = f"{out}/{key}.wav"
    if os.path.exists(p): continue
    torch.manual_seed(seed)
    a = model.generate(text=text, language="English", ref_audio=ref, ref_text=REF_TEXT, num_step=32, guidance_scale=2.0, speed=0.95)
    save_audio(p, a[0], model.sampling_rate); print(key, "done", flush=True)
