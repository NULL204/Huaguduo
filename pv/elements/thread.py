"""The red thread (红线): cat's cradle → marriage thread → puppet strings."""
import math

import numpy as np
import skia

from ..core import gfx
from ..core import easing as E
from ..core.noise import noise1
from . import style as S


def draw_thread(canvas, pts, width=3.0, color=S.ROUGE, glow=1.0, alpha=1.0, smooth=True, closed=False,
                cut=1.0, glow_color=(255, 70, 80)):
    """Glowing red thread through pts (polyline or spline)."""
    if len(pts) < 2:
        return
    if cut < 1.0:
        dense = _densify(pts, closed)
        pts = gfx.polyline_cut(dense, cut)
        closed = False
        smooth = False
    path = gfx.smooth_path(pts, closed=closed) if smooth else gfx.poly(pts, closed=closed)
    if glow > 0:
        canvas.drawPath(path, gfx.paint(glow_color, alpha * 0.28 * glow, stroke=width * 5, blur=width * 2.4))
    canvas.drawPath(path, gfx.paint(color, alpha, stroke=width))
    canvas.drawPath(path, gfx.paint((255, 150, 150), alpha * 0.45, stroke=max(0.6, width * 0.3)))


def _densify(pts, closed, step=6.0):
    P = list(pts) + ([pts[0]] if closed else [])
    out = []
    for i in range(len(P) - 1):
        a, b = P[i], P[i + 1]
        n = max(1, int(math.hypot(b[0] - a[0], b[1] - a[1]) / step))
        for k in range(n):
            u = k / n
            out.append((a[0] + (b[0] - a[0]) * u, a[1] + (b[1] - a[1]) * u))
    out.append(P[-1])
    return out


def sag(a, b, amount=0.06, n=10, t=0.0, wob=0.0, seed=0):
    """Points along a slightly sagging/wobbling string segment from a to b."""
    out = []
    L = math.hypot(b[0] - a[0], b[1] - a[1])
    for i in range(n + 1):
        u = i / n
        x = a[0] + (b[0] - a[0]) * u
        y = a[1] + (b[1] - a[1]) * u + math.sin(u * math.pi) * L * amount
        if wob:
            y += wob * math.sin(u * math.pi) * noise1(t * 3 + seed, seed)
        out.append((x, y))
    return out


# --- cat's cradle -------------------------------------------------------------------------
# A figure is a closed sequence of anchor names; anchors are finger points supplied per frame.
# L/R = left/right hand of the holder; t=thumb, i=index, p=pinky.
FIGURES = {
    "cradle":   ["Lt", "Rt", "Rp", "Lp", "Li", "Rp", "Rt", "Ri", "Lt", "Lp", "Rp", "Lt"],
    "soldier":  ["Lt", "Ri", "Rp", "Li", "Lp", "Rt", "Rp", "Lt", "Li", "Ri", "Rt", "Lp"],
    "candles":  ["Lt", "Lp", "Rt", "Rp", "Li", "Ri", "Lt", "Rp", "Lp", "Ri", "Rt", "Li"],
    "manger":   ["Lt", "Rt", "Li", "Ri", "Lp", "Rp", "Rt", "Li", "Lp", "Ri", "Rp", "Lt"],
    "diamond":  ["Lt", "Ri", "Lp", "Rt", "Li", "Rp", "Lt", "Rt", "Lp", "Ri", "Li", "Rp"],
}


def cradle_points(anchors, figure, t=0.0, wob=1.5, seed=0):
    seq = FIGURES[figure]
    pts = []
    for k in range(len(seq)):
        a = anchors[seq[k]]
        b = anchors[seq[(k + 1) % len(seq)]]
        seg = sag(a, b, 0.03, 6, t, wob, seed + k)
        pts.extend(seg[:-1])
    pts.append(pts[0])
    return pts


def morph_points(pa, pb, k):
    """Morph between two point lists by resampling to equal length."""
    n = max(len(pa), len(pb), 80)
    A = _resample(pa, n)
    B = _resample(pb, n)
    return [(a[0] + (b[0] - a[0]) * k, a[1] + (b[1] - a[1]) * k) for a, b in zip(A, B)]


def _resample(pts, n):
    P = np.asarray(pts, np.float64)
    seg = np.hypot(np.diff(P[:, 0]), np.diff(P[:, 1]))
    s = np.concatenate([[0], np.cumsum(seg)])
    if s[-1] <= 0:
        return [tuple(P[0])] * n
    u = np.linspace(0, s[-1], n)
    x = np.interp(u, s, P[:, 0])
    y = np.interp(u, s, P[:, 1])
    return list(zip(x, y))
