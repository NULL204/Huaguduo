#!/usr/bin/env python3
"""novelai_gen.py -- generate the film's illustrations with the NovelAI image API (anime diffusion), then key the
cut-outs with tools/alpha_matte.py.  Same JSONL job idea as tools/imagegen.py (one job per line), NovelAI fields:

  {"id": "pose_palm", "out": "assets/char/pose_palm.png", "prompt": "...tags...", "negative": "...",
   "width": 832, "height": 1216, "seed": 50701, "steps": 28, "scale": 5.5,
   "cutout": true,                 # generated on a flat key colour -> keyed RGBA + trimmed (raw kept as *_raw.png)
   "img2img": {"image": "assets/char/REF_master.png", "strength": 0.55},     # optional
   "chars": [{"caption": "...", "x": 0.5, "y": 0.5}]}                          # optional V4 character captions

The API key is read from $NOVELAI_API_KEY or ~/.config/novelai/key -- it is never written anywhere else and never
printed.  NovelAI allows one generation at a time per account: jobs run sequentially, 429s are retried.
Opus accounts generate free at <= 1 MP and <= 28 steps with one sample: every job here stays inside that.

  python tools/novelai_gen.py assets/char/jobs_nai.jsonl                 # all jobs (skips files that exist)
  python tools/novelai_gen.py assets/char/jobs_nai.jsonl --only master_a,master_b --force
  python tools/novelai_gen.py assets/char/jobs_nai.jsonl --dry-run       # print the payloads, no request
  python tools/novelai_gen.py --check                                     # can we reach NovelAI with this key?
"""
from __future__ import annotations

import argparse
import base64
import io
import json
import os
import sys
import time
import urllib.error
import urllib.request
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

API = "https://image.novelai.net/ai/generate-image"
USER_API = "https://api.novelai.net/user/subscription"
MODELS = ["nai-diffusion-4-5-full", "nai-diffusion-4-5-curated", "nai-diffusion-4-full", "nai-diffusion-3"]
FREE_PIXELS = 1024 * 1024


def api_key() -> str:
    k = os.environ.get("NOVELAI_API_KEY", "").strip()
    if not k:
        p = Path.home() / ".config" / "novelai" / "key"
        if p.exists():
            k = p.read_text(encoding="utf-8").strip()
    if not k:
        sys.exit("no NovelAI key: set NOVELAI_API_KEY or write it to ~/.config/novelai/key")
    return k


def request(url: str, body: dict | None, key: str, timeout: int = 180) -> tuple[int, bytes, str]:
    data = None if body is None else json.dumps(body).encode("utf-8")
    req = urllib.request.Request(url, data=data, method="POST" if body is not None else "GET",
                                 headers={"Authorization": "Bearer " + key, "Content-Type": "application/json",
                                          "Accept": "*/*", "User-Agent": "huaguduo-mv/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, r.read(), r.headers.get("Content-Type", "")
    except urllib.error.HTTPError as e:
        return e.code, e.read(), e.headers.get("Content-Type", "") if e.headers else ""


def payload(job: dict, model: str) -> dict:
    w, h = int(job.get("width", 832)), int(job.get("height", 1216))
    if w % 64 or h % 64:
        raise ValueError(f"{job['id']}: width/height must be multiples of 64")
    if w * h > FREE_PIXELS:
        print(f"  ! {job['id']}: {w}x{h} is above 1 MP (costs Anlas even on Opus)")
    steps = min(28, int(job.get("steps", 28)))
    prompt, neg = job["prompt"], job.get("negative", "")
    p = {
        "params_version": 3, "width": w, "height": h, "scale": float(job.get("scale", 5.5)),
        "sampler": job.get("sampler", "k_euler_ancestral"), "steps": steps, "n_samples": 1,
        "ucPreset": int(job.get("ucPreset", 0)), "qualityToggle": bool(job.get("quality", True)),
        "autoSmea": False, "dynamic_thresholding": False, "controlnet_strength": 1, "legacy": False,
        "add_original_image": True, "cfg_rescale": float(job.get("cfg_rescale", 0.0)),
        "noise_schedule": job.get("noise_schedule", "karras"), "legacy_v3_extend": False, "skip_cfg_above_sigma": None,
        "use_coords": bool(job.get("chars")), "legacy_uc": False, "normalize_reference_strength_multiple": True,
        "seed": int(job.get("seed", 0)) or int(time.time()) % 4294967295,
        "negative_prompt": neg, "deliberate_euler_ancestral_bug": False, "prefer_brownian": True,
    }
    if model.startswith("nai-diffusion-4"):
        chars = job.get("chars") or []
        p["characterPrompts"] = [{"prompt": c["caption"], "uc": c.get("uc", ""), "center": {"x": c.get("x", 0.5), "y": c.get("y", 0.5)},
                                  "enabled": True} for c in chars]
        p["v4_prompt"] = {"caption": {"base_caption": prompt, "char_captions": [
            {"char_caption": c["caption"], "centers": [{"x": c.get("x", 0.5), "y": c.get("y", 0.5)}]} for c in chars]},
            "use_coords": bool(chars), "use_order": True}
        p["v4_negative_prompt"] = {"caption": {"base_caption": neg, "char_captions": [
            {"char_caption": c.get("uc", ""), "centers": [{"x": c.get("x", 0.5), "y": c.get("y", 0.5)}]} for c in chars]},
            "legacy_uc": False}
    body = {"input": prompt, "model": model, "action": "generate", "parameters": p}
    if job.get("img2img"):
        src = ROOT / job["img2img"]["image"]
        from PIL import Image
        im = Image.open(src).convert("RGB").resize((w, h), Image.LANCZOS)
        buf = io.BytesIO(); im.save(buf, "PNG")
        body["action"] = "img2img"
        p.update({"image": base64.b64encode(buf.getvalue()).decode("ascii"), "strength": float(job["img2img"].get("strength", 0.55)),
                  "noise": float(job["img2img"].get("noise", 0.0)), "extra_noise_seed": p["seed"]})
    return body


def unzip_png(data: bytes) -> bytes:
    if data[:8] == b"\x89PNG\r\n\x1a\n":
        return data
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        names = [n for n in z.namelist() if n.lower().endswith(".png")]
        if not names:
            raise RuntimeError("zip without png: " + ", ".join(z.namelist()))
        return z.read(names[0])


def cutout(raw_path: Path, out_path: Path) -> dict:
    import alpha_matte as am
    from PIL import Image
    img, stats = am.key_out(Image.open(raw_path).convert("RGB"))
    img, box = am.trim_to_content(img, margin=16)
    img.save(out_path)
    return {"key": stats.get("key"), "size": img.size}


def run_job(job: dict, key: str, models: list[str], force: bool, dry: bool) -> str:
    out = ROOT / job["out"]
    raw = out.with_name(out.stem + "_raw.png") if job.get("cutout") else out
    if out.exists() and not force:
        return "kept"
    out.parent.mkdir(parents=True, exist_ok=True)
    for model in models:
        body = payload(job, model)
        if dry:
            shown = json.loads(json.dumps(body))
            if "image" in shown["parameters"]:
                shown["parameters"]["image"] = "<base64 png>"
            print(json.dumps(shown, ensure_ascii=False)[:1500])
            return "dry"
        for attempt in range(6):
            code, data, ctype = request(API, body, key)
            if code == 200:
                png = unzip_png(data)
                raw.write_bytes(png)
                if job.get("cutout"):
                    info = cutout(raw, out)
                    return f"ok {model} cutout {info['size']}"
                return f"ok {model}"
            msg = data[:300].decode("utf-8", "replace")
            if code == 429 or code >= 500:                 # concurrent generation lock / server busy
                time.sleep(6 * (attempt + 1)); continue
            if code in (400, 404) and ("model" in msg.lower() or "not found" in msg.lower()):
                print(f"  model {model} refused ({code}): {msg}"); break    # try the next model
            raise RuntimeError(f"HTTP {code}: {msg}")
    raise RuntimeError("no model accepted the request")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("jobs", nargs="?")
    ap.add_argument("--only", default="")
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--model", default="", help="force one model id (default: try " + ", ".join(MODELS) + ")")
    a = ap.parse_args()
    if a.check:
        code, data, _ = request(USER_API, None, api_key(), timeout=30)
        try:
            d = json.loads(data)
            perks = d.get("perks") or {}
            print(json.dumps({"http": code, "tier": d.get("tier"), "active": d.get("active"),
                              "unlimitedImageGeneration": perks.get("unlimitedImageGeneration"),
                              "anlas": (d.get("trainingStepsLeft") or {})}, ensure_ascii=False))
        except Exception:
            print(json.dumps({"http": code, "body": data[:200].decode("utf-8", "replace")}))
        return 0 if code == 200 else 1
    if not a.jobs:
        ap.error("jobs file required")
    jobs = [json.loads(l) for l in Path(a.jobs).read_text(encoding="utf-8-sig").splitlines() if l.strip() and not l.lstrip().startswith("//")]
    only = {x.strip() for x in a.only.split(",") if x.strip()}
    key = "" if a.dry_run else api_key()
    models = [a.model] if a.model else MODELS
    failed = 0
    for job in jobs:
        if only and job["id"] not in only:
            continue
        t0 = time.time()
        try:
            r = run_job(job, key, models, a.force, a.dry_run)
            print(f"{job['id']:22s} {r}  ({time.time() - t0:.1f}s)", flush=True)
        except Exception as e:  # noqa: BLE001
            failed += 1
            print(f"{job['id']:22s} FAILED {e}", flush=True)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
