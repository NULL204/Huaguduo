"""Poppy (虞美人) — the flower bud at the heart of the PV.

side view  : used as the puppet's head ornament and on branches
front view : used for the close-up bloom
"""
import math

import numpy as np
import skia

from ..core import gfx
from ..core import easing as E
from ..core.noise import noise1, hash01
from . import style as S


def _petal_side(openness, w, h, crumple, seed, k):
    """A single side-view petal as a path, base at origin, opening upward (-y).
    Rounded, bulging sides and a ruffled crown so it reads as crumpled silk."""
    left, right = [], []
    n = 12
    for i in range(n + 1):
        u = i / n
        bulge = math.sin(min(1.0, u * 1.08) * math.pi * 0.62) ** 0.7
        wid = w * (0.14 + 0.86 * bulge)
        y = -h * u
        wl = crumple * 0.10 * w * noise1(u * 4 + k * 3.1, seed)
        wr = crumple * 0.10 * w * noise1(u * 4 + k * 5.7, seed + 1)
        left.append((-wid / 2 + wl, y))
        right.append((wid / 2 + wr, y))
    top = []
    m = 12
    for j in range(1, m):
        v = j / m
        x = -w / 2 * (1 - v) + w / 2 * v
        ruff = (0.05 + 0.09 * crumple) * h * noise1(v * 7 + k * 2.3, seed + 3)
        y = -h - h * 0.16 * math.sin(v * math.pi) + ruff
        top.append((x * 0.98, y))
    outline = left + top + right[::-1]
    return gfx.smooth_path(outline, closed=True, tension=0.42)


def draw_poppy_side(canvas, x, y, scale=1.0, angle=0.0, openness=0.0, stem=1.0, seed=0, t=0.0,
                    petal=S.LEATHER_RED, sepal=S.LEATHER_GREEN, ink=S.INK, alpha=1.0, outline=True,
                    blend=gfx.MULTIPLY, stem_len=40.0, stem_curve=0.3):
    """Side view poppy.  (x,y) is the stem base; flower points up (-y) before `angle` (radians).
    openness: 0 closed bud (sepals hug), 0.25 sepals split / red bulges, 0.6 cup, 1 open."""
    o = E.clamp(openness)
    canvas.save()
    canvas.translate(x, y)
    canvas.rotate(math.degrees(angle))
    canvas.scale(scale, scale)
    lw = 2.2
    # stem
    if stem > 0:
        sp = gfx.bezier_pts((0, 0), (stem_curve * 12, -stem_len * 0.4), (-stem_curve * 10, -stem_len * 0.75), (0, -stem_len), 12)
        canvas.drawPath(gfx.ribbon(sp, np.linspace(5, 3.4, len(sp))), gfx.paint(ink, alpha))
    canvas.translate(0, -stem_len)
    # receptacle
    canvas.drawPath(gfx.ellipse(0, -2, 7, 5), gfx.paint(ink, alpha))
    bud_h = 46
    bud_w = 32
    if o < 0.35:
        # closed / splitting bud: red core + two green sepals
        q = o / 0.35
        core_w = bud_w * (0.55 + 0.6 * q)
        core_h = bud_h * (0.95 + 0.25 * q)
        core = gfx.blob(0, -core_h / 2 - 2, core_w / 2, 0.06 + 0.14 * q, seed=seed, n=20, t=t * 0.2,
                        aspect=1.0, rot=0)
        m = skia.Matrix()
        m.setScaleTranslate(1, core_h / core_w, 0, -(core_h / 2 + 2) * (1 - core_h / core_w))
        core = gfx.transformed(core, m)
        canvas.drawPath(core, gfx.paint(petal, alpha, blend=blend))
        if outline:
            canvas.drawPath(core, gfx.paint(ink, alpha * 0.9, stroke=lw))
            # crumple lines on the red
            for j in range(3):
                xx = (j - 1) * core_w * 0.22
                canvas.drawPath(gfx.smooth_path([(xx, -6), (xx + 3 * noise1(j, seed), -core_h * 0.5), (xx * 0.6, -core_h * 0.9)]),
                                gfx.paint(S.LEATHER_RED_DEEP, alpha * 0.8, stroke=1.4))
        # sepals open outward with q
        for sgn in (-1, 1):
            canvas.save()
            canvas.rotate(sgn * (4 + 38 * E.in_quad(q)))
            sep = gfx.smooth_path([(0, 0), (sgn * bud_w * 0.62, -bud_h * 0.35), (sgn * bud_w * 0.52, -bud_h * 0.82),
                                   (sgn * bud_w * 0.06, -bud_h * 1.04), (sgn * bud_w * 0.12, -bud_h * 0.6),
                                   (sgn * bud_w * 0.05, -bud_h * 0.2)], closed=True)
            canvas.drawPath(sep, gfx.paint(sepal, alpha * (1 - E.smooth((q - 0.85) / 0.15)), blend=blend))
            if outline:
                canvas.drawPath(sep, gfx.paint(ink, alpha * (1 - E.smooth((q - 0.85) / 0.15)), stroke=lw))
                # hairs on sepal
                for hh in range(6):
                    u = (hh + 0.5) / 6
                    px = sgn * bud_w * (0.5 - 0.3 * u)
                    py = -bud_h * (0.2 + 0.7 * u)
                    canvas.drawLine(px, py, px + sgn * 5, py - 2, gfx.paint(ink, alpha * 0.8, stroke=1.0))
            canvas.restore()
    else:
        # cup -> open: four petals (two at the sides, one front, one back)
        q = (o - 0.35) / 0.65
        spread = E.out_cubic(q)
        crumple = 1 - q
        ph = bud_h * (1.0 + 0.5 * q)
        pw = bud_w * (1.1 + 0.6 * q)
        order = [(-1, 0.55), (1, 0.55), (0, 1.0)]
        # back petal (darker)
        back = _petal_side(o, pw * 1.05, ph * 0.95, crumple, seed, 9)
        canvas.drawPath(back, gfx.paint(S.LEATHER_RED_DEEP, alpha, blend=blend))
        if outline:
            canvas.drawPath(back, gfx.paint(ink, alpha, stroke=lw))
        # pod visible when open
        if q > 0.4:
            pa = E.smooth((q - 0.4) / 0.6)
            canvas.drawPath(gfx.ellipse(0, -ph * 0.32, 9, 12), gfx.paint(S.LEATHER_GREEN_DEEP, alpha * pa, blend=blend))
            canvas.drawPath(gfx.ellipse(0, -ph * 0.42, 12, 3.2), gfx.paint(ink, alpha * pa))
            for j in range(10):
                a = -math.pi * (0.1 + 0.8 * j / 9)
                canvas.drawLine(math.cos(a) * 8, -ph * 0.36 + math.sin(a) * 4,
                                math.cos(a) * 20 * pa, -ph * 0.36 + math.sin(a) * 14 * pa - 6,
                                gfx.paint(ink, alpha * pa, stroke=1.2))
                canvas.drawCircle(math.cos(a) * 20 * pa, -ph * 0.36 + math.sin(a) * 14 * pa - 6, 2.0,
                                  gfx.paint(ink, alpha * pa))
        for k, (side, wscale) in enumerate(order):
            canvas.save()
            ang = side * (8 + 52 * spread)
            canvas.rotate(ang)
            pp = _petal_side(o, pw * wscale, ph, crumple, seed, k)
            canvas.drawPath(pp, gfx.paint(petal, alpha, blend=blend))
            # dark blotch at base
            canvas.drawPath(gfx.ellipse(0, -ph * 0.16, pw * wscale * 0.18, ph * 0.12),
                            gfx.paint(S.INK, alpha * 0.85 * E.smooth(q * 2)))
            if outline:
                canvas.drawPath(pp, gfx.paint(ink, alpha, stroke=lw))
                for v in range(3):
                    vx = (v - 1) * pw * wscale * 0.2
                    bend = 4 * noise1(v + k * 3, seed + 8)
                    canvas.drawPath(gfx.smooth_path([(vx * 0.2, -ph * 0.22), (vx * 0.7 + bend, -ph * 0.55), (vx * 1.05, -ph * 0.9)]),
                                    gfx.paint(S.LEATHER_RED_DEEP, alpha * 0.55, stroke=1.0))
            canvas.restore()
    canvas.restore()


# ---------------------------------------------------------------- front view

def _petal_front(R, crumple, seed, k, cup=0.0):
    """Petal radiating along +x from the origin: a narrow claw that swells into rounded shoulders and
    a broad, crinkled rim (avoids the 'pie wedge' look)."""
    pts = []
    n = 30
    half = math.radians(66)
    for i in range(n + 1):
        a = -half + 2 * half * i / n
        r = R * (0.80 + 0.20 * math.cos(a * 1.5))
        r *= 1 + crumple * 0.10 * noise1(i * 0.9 + k * 7, seed) + 0.04 * noise1(i * 2.7 + k, seed + 4)
        pts.append((math.cos(a) * r, math.sin(a) * r * (1 - 0.45 * cup)))
    sq = (1 - 0.45 * cup)
    shoulder_r = [(R * 0.42, R * 0.34 * sq), (R * 0.16, R * 0.11 * sq), (R * 0.04, R * 0.03 * sq)]
    left = [(x, -y) for (x, y) in shoulder_r[::-1]]
    right = shoulder_r
    return gfx.smooth_path(left[::-1][::-1] + pts + right, closed=True, tension=0.45)


def draw_poppy_front(canvas, x, y, R, openness=1.0, rot=0.0, seed=0, t=0.0, alpha=1.0,
                     petal=(214, 38, 48), deep=(130, 10, 26), ink=S.INK, glow=False, veins=True):
    """Front view poppy of radius R.  openness 0..1 (0 = tight cup seen from above)."""
    o = E.clamp(openness)
    canvas.save()
    canvas.translate(x, y)
    canvas.rotate(math.degrees(rot))
    spread = E.out_cubic(o)
    crumple = 1 - o
    layers = [(0, 1.0, 0.0), (90, 1.0, 0.0), (45, 0.86, 0.5), (135, 0.86, 0.5)]
    for k, (base_ang, rs, depth) in enumerate(layers):
        ang = math.radians(base_ang + 180 * (k % 2)) + 0.15 * noise1(seed + k, 2)
        for side in (0, 1):
            a = ang + math.pi * side
            canvas.save()
            canvas.rotate(math.degrees(a + (1 - spread) * 0.6 * (1 if side else -1)))
            r_eff = R * rs * (0.30 + 0.70 * spread)
            pp = _petal_front(r_eff, crumple, seed + side * 5, k, cup=1 - spread)
            # translucent petal: gradient from deep base to bright rim
            sh = gfx.radial(0, 0, max(1.0, r_eff), [deep + (255,), petal + (255,), (min(255, petal[0] + 30), petal[1] + 20, petal[2] + 20, 255)],
                            [0.0, 0.55, 1.0])
            p = gfx.paint((255, 255, 255), alpha * (0.82 if depth > 0 else 0.92), blend=gfx.MULTIPLY, shader=sh)
            canvas.drawPath(pp, p)
            if veins:
                for v in range(9):
                    va = math.radians(-44 + 88 * v / 8)
                    vp = [(r_eff * 0.1 * math.cos(va), r_eff * 0.1 * math.sin(va)),
                          (r_eff * 0.5 * math.cos(va * 0.9), r_eff * 0.5 * math.sin(va * 0.9) + crumple * 4 * noise1(v, seed)),
                          (r_eff * 0.92 * math.cos(va * 0.95), r_eff * 0.92 * math.sin(va * 0.95))]
                    canvas.drawPath(gfx.smooth_path(vp), gfx.paint(deep, alpha * 0.18, stroke=max(0.8, R * 0.005)))
            # dark basal blotch
            canvas.drawPath(gfx.ellipse(r_eff * 0.16, 0, r_eff * 0.16, r_eff * 0.12),
                            gfx.paint(ink, alpha * 0.9 * E.smooth(o * 1.5), blur=R * 0.015))
            canvas.restore()
    # centre: stamens ring + pod with stigma rays
    pa = E.smooth((o - 0.3) / 0.7)
    if pa > 0:
        rng = np.random.default_rng(seed)
        for j in range(70):
            a = rng.uniform(0, 2 * math.pi)
            rr = R * rng.uniform(0.13, 0.24) * (0.6 + 0.4 * pa)
            canvas.drawLine(math.cos(a) * R * 0.08, math.sin(a) * R * 0.08, math.cos(a) * rr, math.sin(a) * rr,
                            gfx.paint(ink, alpha * pa * 0.8, stroke=max(0.7, R * 0.004)))
            canvas.drawCircle(math.cos(a) * rr, math.sin(a) * rr, max(1.0, R * 0.012), gfx.paint(ink, alpha * pa))
        canvas.drawCircle(0, 0, R * 0.10, gfx.paint(S.LEATHER_GREEN_DEEP, alpha * pa, blend=gfx.MULTIPLY))
        canvas.drawCircle(0, 0, R * 0.10, gfx.paint(ink, alpha * pa, stroke=max(1.0, R * 0.006)))
        for j in range(9):
            a = 2 * math.pi * j / 9 + seed
            canvas.drawLine(0, 0, math.cos(a) * R * 0.095, math.sin(a) * R * 0.095,
                            gfx.paint(ink, alpha * pa, stroke=max(1.0, R * 0.01)))
    canvas.restore()


def draw_chrysanthemum(canvas, x, y, R, rot=0.0, seed=0, alpha=1.0, color=(250, 248, 244), line=(120, 116, 120),
                       layers=3, openness=1.0):
    """White chrysanthemum (白菊) seen from the front — the funeral flower."""
    o = E.clamp(openness)
    rng = np.random.default_rng(seed)
    canvas.save()
    canvas.translate(x, y)
    canvas.rotate(math.degrees(rot))
    for L in range(layers):
        n = 26 - L * 5
        rr = R * (1.0 - L * 0.24) * (0.45 + 0.55 * o)
        for k in range(n):
            a = 2 * math.pi * (k + 0.5 * L) / n + rng.normal(0, 0.04)
            canvas.save()
            canvas.rotate(math.degrees(a))
            w = rr * (0.10 + 0.03 * L)
            p = gfx.smooth_path([(rr * 0.12, 0), (rr * 0.55, -w), (rr * 0.98, -w * 0.4), (rr, 0), (rr * 0.98, w * 0.4),
                                 (rr * 0.55, w)], closed=True)
            canvas.drawPath(p, gfx.paint(color, alpha * 0.96))
            canvas.drawPath(p, gfx.paint(line, alpha * 0.8, stroke=max(0.8, R * 0.012)))
            canvas.restore()
    canvas.drawCircle(0, 0, R * 0.16, gfx.paint((226, 214, 160), alpha, blend=gfx.MULTIPLY))
    canvas.drawCircle(0, 0, R * 0.16, gfx.paint(line, alpha, stroke=max(0.8, R * 0.012)))
    canvas.restore()
