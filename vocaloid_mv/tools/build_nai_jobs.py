#!/usr/bin/env python3
"""build_nai_jobs.py -- the NovelAI prompt set for 阿朵 (the film's original singer) -> assets/char/jobs_nai.jsonl.

Danbooru-tag prompts for NovelAI Diffusion V4.5, aimed at the user's reference look: a clean, high-key modern anime
illustration (thin loose lineart, muted cool palette, lots of white space, chromatic-aberration sparkle) with this
film's carmine accent.  Original character -- NOT Luo Tianyi, NOT Hatsune Miku (see docs/CHARACTER.md); the negative
prompt keeps those designs out.  Every job stays inside Opus' free size (<= 1 MP, 28 steps, 1 sample).

Cut-outs (`cutout: true`) are generated on a flat blue key and keyed by tools/alpha_matte.py (the design has no blue).

    python tools/build_nai_jobs.py && python tools/novelai_gen.py assets/char/jobs_nai.jsonl
"""
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "assets", "char", "jobs_nai.jsonl")

CHAR = ("1girl, solo, original, long hair, straight hair, very long hair, black hair, red inner hair, colored inner hair, "
        "two-tone hair, blunt bangs, sidelocks, side braid, single braid, hair flower, red flower bud, poppy, hair ornament, "
        "facial mark, red forehead mark, red eyes, gradient eyes, orange pupils, white shirt, sleeveless shirt, high collar, "
        "chinese clothes, red knot button, detached sleeves, white sleeves, see-through sleeves, gradient sleeves, red sleeves, "
        "red fingernails, black skirt, pleated skirt, red trim, black pantyhose, mary janes, red shawl, see-through shawl, "
        "shawl, floating shawl")
STYLE = ("anime illustration, clean thin lineart, sketchy lineart, flat color, soft shading, muted colors, limited palette, "
         "red accent, high contrast, white space, chromatic aberration, light particles, sparkle, delicate, elegant, "
         "beautiful detailed eyes")
NEG = ("lowres, bad anatomy, bad hands, missing fingers, extra digits, fewer digits, extra arms, cropped, worst quality, "
       "low quality, jpeg artifacts, signature, watermark, username, artist name, blurry, text, logo, speech bubble, "
       "aqua hair, green hair, grey hair, blonde hair, twintails, hatsune miku, luo tianyi, vocaloid, headphones, "
       "headset, 3d, realistic, photo")
KEYBG = "simple background, blue background"


def job(id_, scene, w=832, h=1216, seed=50700, cutout=False, extra_neg="", char=True):
    prompt = ", ".join(x for x in [CHAR if char else "", scene, KEYBG if cutout else "", STYLE] if x)
    neg = NEG + (", multiple views" if "character sheet" not in scene else "") + (", " + extra_neg if extra_neg else "")
    return {"id": id_, "out": f"assets/char/{id_}.png", "prompt": prompt, "negative": neg, "width": w, "height": h,
            "seed": seed, "steps": 28, "scale": 5.5, "cutout": cutout}


JOBS = [
    # ---- masters (pipeline asset phase: identity reference for everything else)
    job("master_a", "full body, standing, three-quarter view, looking at viewer, calm, slight smile, wind, shawl flowing", seed=50701, cutout=True),
    job("master_b", "full body, from behind, looking back, looking over shoulder, wind, hair flowing", seed=50702, cutout=True),
    job("master_c", "full body, standing, straight-on, arms at sides, neutral expression, character sheet, white background", seed=50703),
    # ---- cut-outs, composited into the procedural shots (film order)
    job("walk_left", "full body, walking, from side, facing left, looking ahead, expressionless", seed=50711, cutout=True),
    job("walk_right", "full body, walking, from side, facing right, looking ahead, expressionless", seed=50712, cutout=True),
    job("palm", "upper body, looking at own hand, open palm, small white insect on palm, cupped hand, close-up, hand focus", seed=50713, cutout=True),
    job("bust_down", "portrait, upper body, looking down, half-closed eyes, sad, hair ornament focus, red flower bud", seed=50714, cutout=True),
    job("snow_back", "full body, from behind, standing, head down, arms at sides, snow on hair", seed=50715, cutout=True),
    job("sit_knees", "full body, sitting, hugging own legs, head on knees, lonely, from side", seed=50716, cutout=True),
    job("veil", "upper body, red veil, bridal veil, veil over face, chinese wedding, red dress, gold embroidery, holding fan", seed=50717, cutout=True, extra_neg="white shirt"),
    job("lookup", "upper body, looking up, determined, wind, snow, falling snow, shawl flowing, hair flowing", seed=50718, cutout=True),
    job("pull", "upper body, hand on own head, grabbing hair ornament, pulling flower from hair, intense, clenched teeth, wind", seed=50719, cutout=True),
    job("run", "full body, running, dynamic pose, from side, facing right, motion blur, shawl streaming behind, determined", seed=50720, cutout=True),
    job("child", "child, younger, aged down, cat's cradle, red string, playing, smile, sitting", seed=50721, cutout=True),
    # ---- full-frame key illustrations (1216x832 landscape)
    job("eye", "close-up, eye focus, red eyes, eyelashes, looking at viewer, reflection in eye, white background", w=1216, h=832, seed=50731),
    job("lips", "close-up, lips focus, red lipstick, finger on own lips, applying lipstick, red nails, white background", w=1216, h=832, seed=50732),
    job("lying_flowers", "from above, lying, on back, eyes closed, red poppy field, flowers around, hair spread out, peaceful, spring", w=1216, h=832, seed=50733),
    job("neon", "upper body, looking at viewer, glaring, angry, night, neon lights, red light, rim light, dark background", w=1216, h=832, seed=50734),
    job("fist", "close-up, clenched hand, fist, red liquid dripping between fingers, red nails, dark background, hand focus", w=1216, h=832, seed=50735),
    job("photo", "upper body, holding photograph, looking at photo, sad, sepia, indoors, window light, dust", w=1216, h=832, seed=50736),
    job("bed", "lying on bed, from above, back turned, curled up, white sheets, pillow, alone, soft light, night", w=1216, h=832, seed=50737),
    job("desk", "sitting at desk, office, documents, paper stack, tired, head on hand, fluorescent light, night, window", w=1216, h=832, seed=50738),
    job("snow_field", "full body, standing in field, summer, green grass, falling snow, looking up, sunlight, wide shot", w=1216, h=832, seed=50739),
    job("bloom", "upper body, arms spread, eyes closed, red petals swirling, giant red poppy blooming behind her, wind, white background", w=1216, h=832, seed=50740),
]

if __name__ == "__main__":
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        for j in JOBS:
            f.write(json.dumps(j, ensure_ascii=False) + "\n")
    print(f"{len(JOBS)} jobs -> {OUT}")
