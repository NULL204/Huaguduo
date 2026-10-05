#!/usr/bin/env python3
"""key_unmix.py -- colour-difference chroma key that keeps translucency (sheer fabric, hair wisps, glass).

Why: 阿朵's ice-blue shawl and sleeves are see-through, so the generator paints them as fabric *mixed with* the key
green. A tolerance key (tools/alpha_matte.py `key`) treats those pixels as opaque foreground and leaves a mint tint.
Here every pixel is unmixed against the key colour K instead:

    excess(C) = G - max(R, B)          (green key; magenta: min(R, B) - G; blue: B - max(R, G))
    alpha     = 1 - excess(C) / excess(K)                 (clamped; the design contains no key-coloured parts)
    F         = (C - (1 - alpha) * K) / alpha             (the foreground colour with the key removed)

K is measured from the image border (median), so off-pure screens work. Pixels below `--floor` alpha become fully
transparent, above `--ceil` fully opaque; specks (connected opaque bits smaller than `--speck` px) are removed;
transparent pixels are filled with the nearest foreground colour so bilinear scaling never pulls in the key.

  python tools/key_unmix.py assets/char/master_a.raw.png assets/char/master_a.png [--trim 16]
  python tools/key_unmix.py --batch assets/char            # re-key every *.raw.png in the folder

Used by tools/imagegen.py for transparent jobs.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
from PIL import Image


def border_key(rgb: np.ndarray, width: int = 6) -> np.ndarray:
    b = np.concatenate([rgb[:width].reshape(-1, 3), rgb[-width:].reshape(-1, 3),
                        rgb[:, :width].reshape(-1, 3), rgb[:, -width:].reshape(-1, 3)])
    return np.median(b, axis=0)


def excess(rgb: np.ndarray, kind: str) -> np.ndarray:
    r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    if kind == "green":
        return g - np.maximum(r, b)
    if kind == "magenta":
        return np.minimum(r, b) - g
    return b - np.maximum(r, g)   # blue


def key_kind(k: np.ndarray) -> str:
    r, g, b = k
    if g >= max(r, b):
        return "green"
    if b >= max(r, g) and r < 0.5 * b:
        return "blue"
    return "magenta"


def unmix(img: Image.Image, floor: float = 0.04, ceil: float = 0.97, speck: int = 40,
          soften: float = 1.0) -> tuple[Image.Image, dict]:
    rgb = np.asarray(img.convert("RGB")).astype(np.float32)
    K = border_key(rgb)
    kind = key_kind(K)
    eK = float(excess(K[None, None, :], kind)[0, 0])
    if eK < 40:
        raise ValueError(f"border colour {K.round()} is not a usable chroma key")
    e = excess(rgb, kind)
    a = 1.0 - np.clip(e / eK, 0.0, 1.0)
    if soften != 1.0:                       # >1 keeps faint wisps a little more opaque
        a = a ** (1.0 / soften)
    # the screen is never perfectly flat (compression noise at the edges): raise the floor to the border's noise
    eb = excess(np.concatenate([rgb[:6].reshape(-1, 3), rgb[-6:].reshape(-1, 3),
                                rgb[:, :6].reshape(-1, 3), rgb[:, -6:].reshape(-1, 3)])[None], kind)
    floor = max(floor, min(0.2, 1.0 - float(np.percentile(eb, 0.05)) / eK + 0.01))
    a[a < floor] = 0.0
    a[a > ceil] = 1.0
    # remove isolated specks and faint noise blobs (generator flecks on the screen): any connected bit of
    # non-zero alpha that is small, or that never gets half-opaque, is background
    if speck > 0:
        try:
            from scipy import ndimage
            lab, n = ndimage.label(a > 0)
            if n > 1:
                idx = np.arange(1, n + 1)
                sizes = ndimage.sum(np.ones_like(a), lab, index=idx)
                peak = ndimage.maximum(a, lab, index=idx)
                drop = idx[(sizes < speck) | (peak < 0.5)]
                a[np.isin(lab, drop)] = 0.0
        except ImportError:
            pass
    safe = np.maximum(a, 1e-3)[..., None]
    F = (rgb - (1.0 - a)[..., None] * K[None, None, :]) / safe
    F = np.clip(F, 0, 255)
    # fill fully transparent pixels with the nearest opaque colour (no key bleed when scaled)
    try:
        from scipy import ndimage
        hole = a <= 0.0
        if hole.any() and (~hole).any():
            idx = ndimage.distance_transform_edt(hole, return_distances=False, return_indices=True)
            F = F[idx[0], idx[1]]
    except ImportError:
        pass
    out = np.dstack([F, a * 255.0]).round().astype(np.uint8)
    stats = {"key": [int(x) for x in K.round()], "kind": kind,
             "transparent_pct": round(float((a <= 0).mean() * 100), 2),
             "partial_pct": round(float(((a > 0) & (a < 1)).mean() * 100), 2)}
    return Image.fromarray(out, "RGBA"), stats


def trim(img: Image.Image, margin: int = 16) -> Image.Image:
    a = np.asarray(img)[..., 3]
    ys, xs = np.nonzero(a > 2)
    if not len(xs):
        return img
    x0, y0 = max(0, xs.min() - margin), max(0, ys.min() - margin)
    x1, y1 = min(img.width, xs.max() + 1 + margin), min(img.height, ys.max() + 1 + margin)
    return img.crop((x0, y0, x1, y1))


def process(src: Path, dst: Path, margin: int | None, **kw) -> dict:
    img, st = unmix(Image.open(src), **kw)
    if margin is not None:
        img = trim(img, margin)
    img.save(dst)
    st["size"] = list(img.size)
    return st


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("src", nargs="?")
    ap.add_argument("dst", nargs="?")
    ap.add_argument("--batch", help="folder: re-key every *.raw.png to <stem>.png")
    ap.add_argument("--trim", type=int, default=16, help="trim margin in px (-1 = no trim)")
    ap.add_argument("--floor", type=float, default=0.04)
    ap.add_argument("--ceil", type=float, default=0.97)
    ap.add_argument("--speck", type=int, default=40)
    ap.add_argument("--soften", type=float, default=1.0)
    a = ap.parse_args()
    kw = dict(floor=a.floor, ceil=a.ceil, speck=a.speck, soften=a.soften)
    margin = None if a.trim < 0 else a.trim
    pairs = []
    if a.batch:
        pairs = [(p, p.with_name(p.name.replace(".raw.png", ".png"))) for p in sorted(Path(a.batch).glob("*.raw.png"))]
    elif a.src and a.dst:
        pairs = [(Path(a.src), Path(a.dst))]
    else:
        ap.error("give SRC DST or --batch DIR")
    for s, d in pairs:
        st = process(s, d, margin, **kw)
        print(f"{d.name:28s} {st}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
