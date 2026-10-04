"""Render the video cover (16:9, Chinese) with the PV's own engine.

    python tools/make_cover.py [--face brush|running]   -> out/cover.png, out/cover.jpg

Original artwork: 阿朵 (the PV's original protagonist) backlit on the shadow screen, her bud starting
to open, red threads tied to her wrist and neck, a cochineal in her palm; brush-calligraphy title.
"""
import argparse
import math
import os
import sys

import cv2
import numpy as np
import skia

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from pv import config  # noqa: E402
from pv.core import gfx, post  # noqa: E402
from pv.core import easing as E  # noqa: E402
from pv.core import text as TXT  # noqa: E402
from pv.core.frame import FrameCtx, apply_post  # noqa: E402
from pv.core.noise import noise1, RNG  # noqa: E402
from pv.elements import style as S  # noqa: E402
from pv.elements import fx, particles as PT, thread as TH  # noqa: E402
from pv.elements.puppet import Puppet  # noqa: E402
from pv.elements.flower import draw_poppy_side  # noqa: E402
from pv.elements.insects import draw_cochineal  # noqa: E402
from pv.elements.landscape import Mountains  # noqa: E402
from pv.elements.branch import BranchTree  # noqa: E402

W, H = config.W, config.H
T = 7.3  # a frozen moment for the noise-driven details


def glyph_column(c, s, x, y, size, face, color, spacing=1.0, halo=None, halo_blur=14, shadow=None):
    """Vertical column of characters centred on x, starting at y (top)."""
    for k, ch in enumerate(s):
        gp = TXT.glyph_path(face, ch)
        if gp is None:
            continue
        c.save()
        c.translate(x - size / 2, y + (k * spacing + 0.88) * size)
        c.scale(size / 100.0, size / 100.0)
        if halo is not None:
            c.drawPath(gp, gfx.paint(halo[:3], halo[3] / 255.0 if len(halo) > 3 else 0.8, blur=halo_blur))
        if shadow is not None:
            c.save()
            c.translate(2.5, 3.5)
            c.drawPath(gp, gfx.paint(shadow[:3], shadow[3] / 255.0 if len(shadow) > 3 else 0.5, blur=3))
            c.restore()
        c.drawPath(gp, gfx.paint(color[:3], color[3] / 255.0 if len(color) > 3 else 1.0))
        c.restore()


def draw_string(c, s, x, y, size, face, color, align="start", shadow=None):
    f = TXT.font(face, size)
    w = f.measureText(s)
    if align == "end":
        x -= w
    elif align == "center":
        x -= w / 2
    if shadow is not None:
        c.drawString(s, x + 2, y + 3, f, gfx.paint(shadow[:3], shadow[3] / 255.0, blur=3))
    c.drawString(s, x, y, f, gfx.paint(color[:3], color[3] / 255.0 if len(color) > 3 else 1.0))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--face", default="brush")
    ap.add_argument("--out", default=os.path.join(config.OUT, "cover"))
    a = ap.parse_args()

    fr = FrameCtx(T)
    fr.clear((255, 255, 255))
    c = fr.canvas

    # ---- scenery on the screen (transmittance) -------------------------------------------
    m = Mountains(seed=12, base=1000, height=300, freq=0.0021)
    m.draw(c, tone=(150, 136, 124), alpha=0.35, blur=6, mist=0.85, cun=False)
    # ---- 阿朵, large, backlit -----------------------------------------------------------
    duo = Puppet("woman", arm_red=1.0, seed=1)
    sc = 2.55
    ox, oy = 640, 1860
    pose = {"head": -10, "torso": -3, "ua_f": 104, "fa_f": 34, "hand_f": "open", "h_f": -10,
            "ua_b": -10, "fa_b": 30, "hair": -0.9, "sash": -1.1, "bud_open": 0.5}
    duo.draw(c, ox, oy, sc, pose=pose, t=T)
    # the cochineal on her palm
    hx, hy = duo.joint(pose, "hand_f")
    px, py = ox + hx * sc + 6, oy + hy * sc - 30
    draw_cochineal(c, px, py, 0.95, -math.pi / 2 - 0.25, t=T, walk=0.3, seed=3)

    # ---- red threads tied to her (the cat's-cradle thread turned puppet string) ----------
    anchors = {"hand_f": (1190, -60), "neck": (430, -60), "hand_b": (150, -60), "waist": (-60, 330)}
    for jn, (axx, ayy) in anchors.items():
        jx, jy = duo.joint(pose, jn)
        jx, jy = ox + jx * sc, oy + jy * sc
        if jy > H + 40:
            continue
        mid = ((axx + jx) / 2 + 10, (ayy + jy) / 2 + 18)
        TH.draw_thread(c, [(axx, ayy), mid, (jx, jy)], width=3.4, glow=1.2, smooth=True)
        c.drawCircle(jx, jy, 6, gfx.paint(S.ROUGE, 1.0))

    # ---- the lamp behind her head ------------------------------------------------------
    fr.light(cx=0.40, cy=0.32, radius=1.35, power=1.3, edge=0.28, warm=1.05, flicker=1.04)

    # ---- in front of the screen: falling petals and snow --------------------------------
    PT.draw_petals(c, T, n=70, seed=88, wind=-200, fall=(40, 120), size=(7, 18), alpha=0.95, count=0.75)
    PT.draw_snow(c, T, n=200, seed=89, wind=-60, fall=(40, 140), size=(1.5, 6.0), alpha=0.85, color=(255, 255, 255))
    PT.draw_dust(c, T, n=80, alpha=0.5)
    # glow around the opening bud
    bx, by = duo.joint(pose, "bud")
    bx, by = ox + bx * sc, oy + by * sc
    c.drawCircle(bx, by + 30, 120, gfx.paint((255, 90, 80), 0.28, blur=60, blend=gfx.SCREEN))

    # ---- typography ---------------------------------------------------------------------
    face = a.face
    tsize = 250
    tx, ty = 1650, 92
    # a pale ink wash behind the title for contrast
    c.drawPath(gfx.blob(tx, ty + tsize * 1.55, 260, 0.18, seed=5, aspect=0.62),
               gfx.paint((248, 236, 212), 0.55, blur=60))
    glyph_column(c, "花骨朵", tx, ty, tsize, face, (22, 16, 14, 255), spacing=0.98,
                 halo=(250, 238, 214, 200), halo_blur=18)
    fx.draw_seal(c, tx, ty + tsize * 3 * 0.98 + 66, 96, "胭脂", style="bai", rot=-0.03)
    # tagline (original), a column to the left of the title
    glyph_column(c, "一朵不肯开的花", 1405, 300, 60, "brush", (146, 12, 28, 255), spacing=1.1,
                 halo=(252, 240, 216, 230), halo_blur=10)
    # style tag + credits along the bottom
    draw_string(c, "皮影 × 水墨  ·  同人动画 PV", 1880, 1004, 40, "serif_black", (252, 242, 222, 245), align="end",
                shadow=(10, 6, 6, 160))
    draw_string(c, "演唱：洛天依  ·  非官方同人作品", 1880, 1052, 30, "serif", (236, 220, 196, 230), align="end",
                shadow=(10, 6, 6, 160))

    img = fr.rgb_copy()
    img = apply_post(img, T, {"glow": {"thr": 0.76, "strength": 0.42, "red": 0.7}, "grade": dict(contrast=1.08, sat=1.06)})
    img = post.vignette(img, 0.32, 2.4)
    img = post.grain(img, T, amount=4.0)
    os.makedirs(os.path.dirname(a.out), exist_ok=True)
    bgr = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
    cv2.imwrite(a.out + ".png", bgr)
    cv2.imwrite(a.out + ".jpg", bgr, [cv2.IMWRITE_JPEG_QUALITY, 95])
    print("wrote", a.out + ".png", a.out + ".jpg")


if __name__ == "__main__":
    main()
