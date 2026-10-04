"""Cochineal (胭脂虫) and silverfish (衣鱼)."""
import math

import numpy as np
import skia

from ..core import gfx
from ..core import easing as E
from ..core.noise import noise1
from . import style as S


def draw_cochineal(canvas, x, y, scale=1.0, angle=0.0, t=0.0, walk=0.0, wings=0.0, flap=0.0,
                   crushed=0.0, alpha=1.0, seed=0, wax=0.8, style="cut"):
    """Cochineal seen from above, head toward +x.  Body ~ 60x40 px at scale 1.
    wax: amount of white powdery coating; crushed: 0..1 flattens and bleeds carmine."""
    canvas.save()
    canvas.translate(x, y)
    canvas.rotate(math.degrees(angle))
    canvas.scale(scale, scale)
    ink = S.INK
    if crushed > 0:
        c = E.clamp(crushed)
        # carmine pool
        pool = gfx.blob(0, 0, 30 + 40 * E.out_cubic(c), 0.25, seed=seed + 3, n=22)
        canvas.drawPath(pool, gfx.paint(S.ROUGE, alpha * min(1, c * 2), blur=2))
        canvas.drawPath(pool, gfx.paint(S.ROUGE_DEEP, alpha * min(1, c * 2) * 0.6, stroke=3, blur=2))
    # legs (6), alternating tripod gait
    lp = gfx.paint(ink, alpha, stroke=2.4)
    for i in range(3):
        for side in (-1, 1):
            ph = walk * 2 * math.pi + (i + (0 if side > 0 else 1)) * math.pi
            sw = 8 * math.sin(ph)
            bx = 14 - i * 14
            by = side * 12
            kx = bx + sw * 0.5 + 4
            ky = side * 24
            fx = bx + sw + 6
            fy = side * 31
            canvas.drawPath(gfx.poly([(bx, by), (kx, ky), (fx, fy)], closed=False), lp)
    sq = 1 - 0.55 * E.clamp(crushed)
    # wings (male cochineal) — translucent white, flapping
    if wings > 0:
        for side in (-1, 1):
            canvas.save()
            fl = math.sin(flap * 2 * math.pi) if flap else 0
            canvas.rotate(side * (20 + 35 * wings + 25 * fl))
            wing = gfx.smooth_path([(4, 0), (-20, side * 8), (-58 * wings, side * 26 * wings), (-62 * wings, side * 12), (-20, side * 2)], closed=True)
            canvas.drawPath(wing, gfx.paint((248, 244, 236), alpha * 0.75 * wings, blend=gfx.MULTIPLY))
            canvas.drawPath(wing, gfx.paint(ink, alpha * wings, stroke=1.4))
            canvas.restore()
    # body: segmented oval, carmine under white wax
    body = gfx.ellipse(-2, 0, 26, 18 * (1 + 0.4 * E.clamp(crushed)))
    m = skia.Matrix()
    m.setScale(1, sq)
    body = gfx.transformed(body, m)
    canvas.drawPath(body, gfx.paint(S.LEATHER_RED, alpha, blend=gfx.MULTIPLY))
    if wax > 0:
        rng = np.random.default_rng(seed)
        wx = skia.Path()
        for k in range(26):
            a = rng.uniform(0, 2 * math.pi)
            rr = rng.uniform(0, 1) ** 0.5
            wx.addCircle(-2 + math.cos(a) * 22 * rr, math.sin(a) * 14 * rr * sq, rng.uniform(2.5, 5.5))
        canvas.drawPath(wx, gfx.paint((252, 248, 240), alpha * wax * (1 - E.clamp(crushed)), blur=1.2))
    for k in range(5):
        xx = -20 + k * 9
        canvas.drawPath(gfx.smooth_path([(xx, -15 * sq), (xx + 2, 0), (xx, 15 * sq)]), gfx.paint(ink, alpha * 0.7, stroke=1.4))
    canvas.drawPath(body, gfx.paint(ink, alpha, stroke=2.2))
    # head + antennae
    canvas.drawCircle(25, 0, 7, gfx.paint(ink, alpha))
    for side in (-1, 1):
        ant = gfx.smooth_path([(28, side * 3), (38, side * (8 + 2 * math.sin(t * 6 + side))), (46, side * 6)])
        canvas.drawPath(ant, gfx.paint(ink, alpha, stroke=1.4))
    canvas.restore()


def draw_silverfish(canvas, x, y, scale=1.0, angle=0.0, t=0.0, alpha=1.0, seed=0, color=S.SILVER):
    """Silverfish: tapered segmented body, long antennae, three tail filaments; wriggles."""
    canvas.save()
    canvas.translate(x, y)
    canvas.rotate(math.degrees(angle))
    canvas.scale(scale, scale)
    n = 10
    pts = []
    for i in range(n + 1):
        u = i / n
        xx = 30 - 70 * u
        yy = 4 * math.sin(t * 14 + u * 5 + seed) * u
        pts.append((xx, yy))
    widths = [10 * (1 - u) ** 0.6 + 2 for u in np.linspace(0, 1, n + 1)]
    body = gfx.ribbon(pts, widths)
    canvas.drawPath(body, gfx.paint(color, alpha))
    canvas.drawPath(body, gfx.paint(S.INK, alpha * 0.9, stroke=1.4))
    for i in range(1, n):
        px, py = pts[i]
        w = widths[i] / 2
        canvas.drawLine(px, py - w, px, py + w, gfx.paint(S.INK, alpha * 0.5, stroke=0.9))
    # antennae
    for side in (-1, 1):
        ant = gfx.smooth_path([(30, side * 2), (44, side * (6 + 3 * math.sin(t * 9 + side))), (60, side * (4 + 6 * math.sin(t * 7 + side)))])
        canvas.drawPath(ant, gfx.paint(S.INK, alpha, stroke=1.0))
    # tails
    tx, ty = pts[-1]
    for k in (-1, 0, 1):
        tail = gfx.smooth_path([(tx, ty), (tx - 14, ty + k * 5 + 2 * math.sin(t * 10 + k)), (tx - 28, ty + k * 10)])
        canvas.drawPath(tail, gfx.paint(S.INK, alpha, stroke=1.0))
    canvas.restore()
