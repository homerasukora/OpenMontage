#!/usr/bin/env python3
"""free-video — CLI over the MuAPI engine used by Open Generative AI (github.com/anil-matcha/open-generative-ai).

The repo is a web studio; generation itself runs on api.muapi.ai (pay per generation, needs a MuAPI key).
Its local engines (sd.cpp / Wan2GP) need a GPU, which cloud sessions don't have.

Key: env MUAPI_API_KEY (set it in the environment's secrets) or the file ~/.config/free_video/key (chmod 600).

  free-video models [--kind t2v|i2v|v2v|lipsync|t2i|i2i] [--search wan] [--show MODEL_ID]
  free-video t2v     --model ID --prompt "..." [--aspect-ratio 9:16] [--duration 5] [--resolution 1080p] -o out.mp4
  free-video i2v     --model ID --image photo.png [--last-image end.png] --prompt "..." [...] -o out.mp4
  free-video lipsync --model ID (--image face.png | --video in.mp4) --audio voice.mp3 [--prompt "..."] [--resolution 720p] -o out.mp4
  free-video v2v     --model ID --video in.mp4 [--image ref.png] [--prompt "..."] -o out.mp4
  free-video result  REQUEST_ID [-o out.mp4]          # resume / fetch a finished job
  Add --dry-run to any generate command to print the request without sending (no credits spent).
  --set key=value adds any extra model input (e.g. --set fps=25 --set seed=7).
"""
import argparse, json, os, sys, time, pathlib
import requests

BASE = "https://api.muapi.ai"
HERE = pathlib.Path(__file__).resolve().parent
MODELS = json.loads((HERE / "models.json").read_text())
OK = {"completed", "succeeded", "success"}; BAD = {"failed", "error", "cancelled", "canceled"}

def key():
    k = os.environ.get("MUAPI_API_KEY", "").strip()
    f = pathlib.Path.home() / ".config/free_video/key"
    if not k and f.exists(): k = f.read_text().strip()
    return k            # empty -> no header; a Network secret for api.muapi.ai is then added by the session proxy

def H(k, json_=False):
    h = {"x-api-key": k} if k else {}
    if json_: h["Content-Type"] = "application/json"
    return h

def model(kind, mid):
    for m in MODELS:
        if m["id"] == mid and (kind is None or m["kind"] == kind): return m
    near = [m["id"] for m in MODELS if m["kind"] == kind and mid.split("-")[0] in m["id"]][:12]
    sys.exit(f"Unknown {kind} model '{mid}'. Close matches: {', '.join(near) or '-'}  (see: free-video models --kind {kind})")

def upload(path_or_url, k):
    if str(path_or_url).startswith(("http://", "https://")): return path_or_url
    p = pathlib.Path(path_or_url)
    with p.open("rb") as fh:
        r = requests.post(f"{BASE}/api/v1/upload_file", headers=H(k), files={"file": (p.name, fh)}, timeout=600)
    if not r.ok: sys.exit(f"Upload failed {r.status_code}: {r.text[:200]}")
    d = r.json(); url = d.get("url") or d.get("file_url") or (d.get("data") or {}).get("url")
    if not url: sys.exit(f"Upload returned no URL: {str(d)[:200]}")
    print(f"uploaded {p.name} -> {url}", file=sys.stderr); return url

def err(r):
    if r.status_code in (401, 403): return "Invalid or missing MuAPI key (env MUAPI_API_KEY or a Network secret for api.muapi.ai)."
    if r.status_code == 402: return "Insufficient MuAPI credits — top up at muapi.ai."
    return f"{r.status_code}: {r.text[:300]}"

def poll(rid, k, timeout=1800):
    t0 = time.time(); last = None
    while time.time() - t0 < timeout:
        time.sleep(3)
        try: r = requests.get(f"{BASE}/api/v1/predictions/{rid}/result", headers=H(k), timeout=60)
        except requests.RequestException: continue
        if r.status_code >= 500: continue
        if not r.ok: sys.exit(f"Poll failed {err(r)}")
        d = r.json(); st = str(d.get("status", "")).lower()
        if st != last: print(f"[{int(time.time() - t0)}s] {st}", file=sys.stderr); last = st
        if st in OK: return d
        if st in BAD: sys.exit(f"Generation failed: {d.get('error') or d}")
    sys.exit(f"Timed out; resume later with: free-video result {rid}")

def save(d, out):
    url = (d.get("outputs") or [None])[0] or d.get("url") or (d.get("output") or {}).get("url")
    if not url: print(json.dumps(d, indent=1)); return
    print(url)
    if out:
        with requests.get(url, stream=True, timeout=600) as r:
            r.raise_for_status(); pathlib.Path(out).write_bytes(r.content)
        print(f"saved {out}", file=sys.stderr)

def run(kind, a):
    m = model(kind, a.model); k = None if a.dry_run else key()
    up = (lambda v: v) if a.dry_run else (lambda v: upload(v, k))
    p = {}
    if getattr(a, "prompt", None) is not None and (kind != "lipsync" or m.get("hasPrompt") or a.prompt): p["prompt"] = a.prompt
    for f in ("aspect_ratio", "duration", "resolution", "quality", "mode"):
        v = getattr(a, f, None)
        if v is not None: p[f] = v
    if kind == "i2v":
        fld = m.get("imageField") or "image_url"; img = up(a.image)
        p[fld] = [img] if fld == "images_list" else img
        if a.last_image:
            lf = m.get("lastImageField") or "last_image"; li = up(a.last_image)
            if lf == "images_list": p.setdefault("images_list", []).append(li)
            else: p[lf] = li
    if kind in ("lipsync", "v2v"):
        if a.image: p["image_url"] = up(a.image)
        if getattr(a, "video", None): p["video_url"] = up(a.video)
    if kind == "lipsync": p["audio_url"] = up(a.audio)
    for kv in a.set or []:
        kk, vv = kv.split("=", 1)
        try: vv = json.loads(vv)
        except ValueError: pass
        p[kk] = vv
    url = f"{BASE}/api/v1/{m['endpoint']}"
    if a.dry_run:
        print(json.dumps({"POST": url, "payload": p, "model_inputs": m["inputs"]}, indent=1)); return
    r = requests.post(url, headers=H(k, True), json=p, timeout=120)
    if not r.ok: sys.exit(f"Submit failed {err(r)}")
    d = r.json(); rid = d.get("request_id") or d.get("id")
    if not rid: return save(d, a.output)
    print(f"request_id {rid}", file=sys.stderr)
    save(poll(rid, k), a.output)

def main():
    ap = argparse.ArgumentParser(prog="free-video", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sp = ap.add_subparsers(dest="cmd", required=True)
    mo = sp.add_parser("models"); mo.add_argument("--kind"); mo.add_argument("--search"); mo.add_argument("--show")
    def gen(name, needs_prompt=False):
        g = sp.add_parser(name); g.add_argument("--model", required=True); g.add_argument("--prompt", required=needs_prompt)
        g.add_argument("--aspect-ratio", dest="aspect_ratio"); g.add_argument("--duration", type=int); g.add_argument("--resolution")
        g.add_argument("--quality"); g.add_argument("--mode"); g.add_argument("--set", action="append")
        g.add_argument("-o", "--output"); g.add_argument("--dry-run", action="store_true"); return g
    gen("t2v", True)
    i = gen("i2v"); i.add_argument("--image", required=True); i.add_argument("--last-image")
    l = gen("lipsync"); l.add_argument("--image"); l.add_argument("--video"); l.add_argument("--audio", required=True)
    v = gen("v2v"); v.add_argument("--video", required=True); v.add_argument("--image")
    r = sp.add_parser("result"); r.add_argument("request_id"); r.add_argument("-o", "--output")
    a = ap.parse_args()
    if a.cmd == "models":
        if a.show:
            print(json.dumps([m for m in MODELS if m["id"] == a.show], indent=1)); return
        for m in MODELS:
            if (not a.kind or m["kind"] == a.kind) and (not a.search or a.search.lower() in (m["id"] + m["name"]).lower()):
                ins = ",".join(f"{k}" + (f"[{'/'.join(map(str, v['enum']))}]" if v.get("enum") else "") for k, v in m["inputs"].items() if k not in ("prompt",))
                print(f"{m['kind']:7} {m['id']:45} {m['name'][:38]:38} {ins[:110]}")
    elif a.cmd == "result":
        save(poll(a.request_id, key()), a.output)
    else:
        run(a.cmd, a)

if __name__ == "__main__":
    main()
