#!/usr/bin/env python3
"""contact_sheet.py -- lay RGBA cut-outs / plates side by side on paper white with labels (asset review).
  python tools/contact_sheet.py OUT.jpg img1.png img2.png ... [--h 520] [--cols 6]"""
import argparse
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ap = argparse.ArgumentParser()
ap.add_argument("out"); ap.add_argument("imgs", nargs="+")
ap.add_argument("--h", type=int, default=520); ap.add_argument("--cols", type=int, default=6)
a = ap.parse_args()
try:
    font = ImageFont.truetype("C:/Windows/Fonts/segoeui.ttf", 22)
except Exception:
    font = ImageFont.load_default()
tiles = []
for p in a.imgs:
    im = Image.open(p).convert("RGBA")
    w = max(1, int(im.width * a.h / im.height))
    tiles.append((Path(p).stem, im.resize((w, a.h), Image.LANCZOS)))
rows = [tiles[i:i + a.cols] for i in range(0, len(tiles), a.cols)]
W = max(sum(t.width for _, t in r) + 24 * (len(r) + 1) for r in rows)
H = len(rows) * (a.h + 50) + 24
sheet = Image.new("RGB", (W, H), (244, 247, 250))
d = ImageDraw.Draw(sheet)
y = 24
for r in rows:
    x = 24
    for name, t in r:
        sheet.paste(t, (x, y + 30), t)
        d.text((x, y), name, fill=(26, 29, 38), font=font)
        x += t.width + 24
    y += a.h + 50
sheet.save(a.out, quality=88)
print(a.out, sheet.size)
