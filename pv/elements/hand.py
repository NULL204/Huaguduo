"""Large articulated puppet hand for close-ups (front view, palm toward camera).

Fingers curl in 2.5D: each phalanx rotates about its knuckle; its projected length is L*cos(cumulative
angle), so a fist folds the fingers down over the palm.
"""
import math

import numpy as np
import skia

from ..core import gfx
from ..core import easing as E
from ..core.noise import noise1
from . import style as S

FINGERS = [  # name, base (x,y), length, width, splay angle (deg from vertical)
    ("index", (-54, -232), 158, 31, -10),
    ("middle", (-16, -248), 178, 32, -2),
    ("ring", (22, -240), 164, 30, 6),
    ("pinky", (56, -218), 128, 26, 15),
]
SEG = (0.46, 0.31, 0.23)


def palm_path():
    return gfx.smooth_path([(-50, 0), (50, 0), (68, -60), (80, -150), (74, -214), (40, -244), (0, -254),
                            (-42, -246), (-74, -226), (-88, -168), (-80, -92), (-64, -30)], closed=True, tension=0.45)


_PALM = None


def draw_big_hand(canvas, x, y, scale=1.0, rot=0.0, openness=1.0, spread=1.0, redness=1.0, t=0.0,
                  alpha=1.0, flip=False, tremble=0.0, seed=0, curl_order=None, lines=True, sleeve=True):
    global _PALM
    if _PALM is None:
        _PALM = palm_path()
    canvas.save()
    canvas.translate(x, y)
    canvas.rotate(math.degrees(rot))
    canvas.scale(-scale if flip else scale, scale)
    col = S.arm_color(redness)
    fill = gfx.paint(col, 0.94 * alpha, blend=gfx.MULTIPLY)
    shade = gfx.paint((60, 30, 30), 0.45 * alpha, blend=gfx.MULTIPLY)
    line = gfx.paint(S.INK, alpha, stroke=3.2)
    thin = gfx.paint(S.INK, alpha * 0.8, stroke=1.8)
    curl = 1 - E.clamp(openness)
    # sleeve / cuff
    if sleeve:
        cuff = gfx.smooth_path([(-66, 10), (64, 10), (80, 120), (96, 400), (-104, 400), (-84, 120)], closed=True)
        canvas.drawPath(cuff, gfx.paint(S.INK, 0.96 * alpha))
        canvas.drawPath(gfx.rect(-70, -4, 138, 20), gfx.paint(S.LEATHER_RED_DEEP, 0.9 * alpha, blend=gfx.MULTIPLY))
        canvas.drawPath(gfx.rect(-70, -4, 138, 20), gfx.paint(S.INK, alpha, stroke=2.4))
        canvas.drawCircle(0, 6, 5, gfx.paint(S.INK, alpha))
    folded = []
    behind = []
    # fingers behind the palm first (extended parts), folded parts drawn after the palm
    for i, (name, (bx, by), L, w, splay) in enumerate(FINGERS):
        delay = (curl_order[i] if curl_order else i * 0.08)
        c = E.clamp((curl - delay) / max(0.2, 1 - delay)) if curl_order else curl
        ang = math.radians(splay * (0.6 + 0.6 * spread))
        tr = tremble * 3 * noise1(t * 8 + i * 2, seed + i)
        angles = [math.radians(85 * c + tr), math.radians(105 * c), math.radians(70 * c)]
        cum = 0.0
        px, py = bx, by
        segs = []
        for k in range(3):
            cum += angles[k]
            Lk = L * SEG[k]
            proj = Lk * math.cos(cum)
            dx = math.sin(ang) * proj
            dy = -math.cos(ang) * proj
            nx, ny = px + dx, py + dy
            wk = w * (1 - 0.12 * k)
            segs.append(((px, py), (nx, ny), wk, cum))
            px, py = nx, ny
        for (a, b, wk, cum) in segs:
            front = math.cos(cum) < 0  # folded toward viewer over the palm
            (folded if front else behind).append((a, b, wk, cum, i))
    for item in behind:
        _draw_seg(canvas, item, fill, shade, line, alpha)
    # thumb (drawn with palm, folds across)
    tc = curl
    tb = (-70, -84)
    ta = math.radians(-36 + 70 * tc)
    tl = [72, 60]
    px, py = tb
    thumb_segs = []
    cum = 0
    for k in range(2):
        cum += math.radians((10 + 30 * tc) if k else 0)
        dx = math.sin(ta + cum) * tl[k]
        dy = -math.cos(ta + cum) * tl[k]
        thumb_segs.append(((px, py), (px + dx, py + dy), 34 - 5 * k, 0.0, 9))
        px, py = px + dx, py + dy
    # palm
    canvas.drawPath(_PALM, fill)
    if lines:
        # palm creases (heart, head, life lines) as carved strokes
        canvas.drawPath(gfx.smooth_path([(-92, -170), (-40, -182), (20, -192), (84, -186)]), thin)
        canvas.drawPath(gfx.smooth_path([(-98, -150), (-40, -140), (30, -120), (70, -96)]), thin)
        canvas.drawPath(gfx.smooth_path([(-90, -160), (-60, -120), (-46, -70), (-40, -18)]), thin)
        # carved cloud motif
        canvas.drawPath(gfx.smooth_path([(10, -70), (24, -82), (40, -74), (36, -58), (22, -56)], closed=True), thin)
    canvas.drawPath(_PALM, line)
    for (a, b, wk, cum, i) in thumb_segs:
        _draw_seg(canvas, (a, b, wk, 0.0, i), fill, shade, line, alpha)
    for item in folded:
        _draw_seg(canvas, item, fill, shade, line, alpha)
    canvas.restore()


def _draw_seg(canvas, item, fill, shade, line, alpha):
    (a, b, wk, cum, i) = item
    L = math.hypot(b[0] - a[0], b[1] - a[1])
    ang = math.atan2(b[1] - a[1], b[0] - a[0])
    canvas.save()
    canvas.translate(a[0], a[1])
    canvas.rotate(math.degrees(ang))
    r = wk / 2
    if L < 2:
        # seen end-on: a knuckle disc
        canvas.drawPath(gfx.circle(0, 0, r), fill)
        canvas.drawPath(gfx.circle(0, 0, r), line)
    else:
        tip = i != 9 and item is not None
        p = gfx.smooth_path([(-r * 0.2, -r), (L * 0.5, -r * 0.92), (L + r * 0.55, -r * 0.6), (L + r * 0.9, 0),
                             (L + r * 0.55, r * 0.6), (L * 0.5, r * 0.92), (-r * 0.2, r)], closed=True, tension=0.5)
        canvas.drawPath(p, fill)
        if math.cos(cum) < 0.2:
            canvas.drawPath(p, shade)
        canvas.drawPath(p, line)
        # joint crease
        canvas.drawLine(L * 0.02, -r * 0.55, L * 0.02, r * 0.55, gfx.paint(S.INK, alpha * 0.6, stroke=1.6))
    canvas.restore()
