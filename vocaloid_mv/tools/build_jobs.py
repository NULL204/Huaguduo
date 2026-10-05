#!/usr/bin/env python3
"""build_jobs.py -- write the image-generation job files (JSONL for tools/imagegen.py) from one source of truth.

The character sentence and style blocks live in docs/CHARACTER.md (fenced ```text blocks, in order: character
sentence, character style block, background style block) and are pasted verbatim into every prompt, so the
character never drifts between batches.

    python tools/build_jobs.py            # -> assets/char/jobs_master.jsonl (+ more batches as they are added)
"""
import json
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def blocks():
    with open(os.path.join(ROOT, "docs", "CHARACTER.md"), encoding="utf-8") as f:
        md = f.read()
    b = [" ".join(x.split()) for x in re.findall(r"```text\n(.*?)```", md, re.S)]
    if len(b) < 3:
        raise SystemExit("docs/CHARACTER.md needs three ```text blocks (sentence, char style, bg style)")
    return b[0], b[1], b[2]


SENT, STYLE, BGSTYLE = blocks()
BIBLE = SENT.replace("The same original character as in the reference image (", "").rstrip(").")
KEY = "#0000FF"


def char_job(id_, framing, ref=True, transparent=True, out=None):
    prompt = f"{framing} {SENT if ref else BIBLE + '.'} {STYLE}"
    j = {"id": id_, "out": out or f"{id_}.png", "transparent": transparent, "prompt": prompt}
    if transparent:
        j["key"] = KEY
    if ref:
        j["images"] = ["assets/char/REF_master.png"]
    return j


def bg_job(id_, desc):
    return {"id": id_, "out": f"{id_}.png", "transparent": False, "prompt": f"{desc} {BGSTYLE}"}


MASTERS = [
    char_job("master_a", "Character design key art, full body, standing, front three-quarter view, relaxed pose, "
             "left hand lifted slightly so the silk shawl flows in a soft wind, gentle melancholic half-smile, looking at "
             "the viewer.", ref=False),
    char_job("master_b", "Character design key art, full body, standing three-quarter back view turning to look over "
             "her LEFT shoulder (the poppy-bud hairpin and braid visible), wind from the left lifting her long hair and "
             "the shawl, calm sad eyes.", ref=False),
    char_job("master_c", "Character design key art, full body, standing straight facing the viewer, arms loose at her "
             "sides, the shawl hanging over both elbows, eyes half-closed, quiet expression, simple neutral pose for a "
             "model sheet.", ref=False),
]


def write(name, jobs):
    p = os.path.join(ROOT, name)
    with open(p, "w", encoding="utf-8") as f:
        for j in jobs:
            f.write(json.dumps(j, ensure_ascii=False) + "\n")
    print(f"wrote {name}: {len(jobs)} jobs")


if __name__ == "__main__":
    write("assets/char/jobs_master.jsonl", MASTERS)
