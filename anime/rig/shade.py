"""Illustration-style shading: feathered cel shadow, warm rim light, light-dependent line weight."""
import math

import numpy as np
import skia

from pv.core import gfx

INVERSE = skia.ClipOp.kDifference
INTERSECT = skia.ClipOp.kIntersect


class Light:
    """Screen-space lighting for a shot.

    dir      : unit 2D vector pointing from the subject TOWARD the key light (screen coords, y down)
    rim      : rim/back light colour (drawn with screen blend on the lit edge)
    rim_amt  : 0..1 strength
    shadow_k : how dark/cool shadows are (0..1)
    tint     : multiply colour applied to shadows (cool lavender by default)
    """

    def __init__(self, dir=(-0.62, -0.78), rim=(255, 236, 228), rim_amt=0.85, shadow_k=1.0,
                 tint=(206, 208, 236), ambient=(255, 255, 255), line=(78, 62, 88), line_k=1.0):
        d = np.asarray(dir, np.float64)
        self.dir = d / (np.linalg.norm(d) + 1e-9)
        self.rim = rim
        self.rim_amt = rim_amt
        self.shadow_k = shadow_k
        self.tint = tint
        self.ambient = ambient
        self.line = line
        self.line_k = line_k

    def shade_col(self, base, deeper=0.0):
        """Shadow colour for a base colour: multiply by the cool tint (and darken)."""
        t = np.asarray(self.tint, np.float64) / 255.0
        k = self.shadow_k
        c = np.asarray(base, np.float64) * (1 - k + k * t) * (1 - 0.18 * deeper * k)
        return tuple(int(max(0, min(255, v))) for v in c)

    def lit(self, base):
        a = np.asarray(self.ambient, np.float64) / 255.0
        return tuple(int(max(0, min(255, v))) for v in np.asarray(base) * a)


def cel(c, path, base, L: Light, d=6.0, feather=2.5, rim_w=2.5, rim=True, shade=None, alpha=1.0,
        deep=None, deep_d=None):
    """Fill `path` with base colour, a soft shadow on the side away from the light and a rim on the lit edge."""
    sh = shade if shade is not None else L.shade_col(base)
    lx, ly = L.dir
    c.save()
    c.clipPath(path, INTERSECT, True)
    c.drawPath(path, gfx.paint(sh, alpha))
    lit_path = gfx.transformed(path, gfx.mat(lx * d, ly * d))
    c.drawPath(lit_path, gfx.paint(L.lit(base), alpha, blur=feather))
    if deep is not None:
        dd = deep_d if deep_d is not None else d * 2.2
        far = gfx.transformed(path, gfx.mat(lx * dd, ly * dd))
        c.save()
        c.clipPath(far, INVERSE, True)
        c.drawPaint(gfx.paint(deep, alpha * 0.55, blur=feather))
        c.restore()
    if rim and L.rim_amt > 0 and rim_w > 0:
        away = gfx.transformed(path, gfx.mat(-lx * rim_w, -ly * rim_w))
        c.save()
        c.clipPath(away, INVERSE, True)
        c.drawPaint(gfx.paint(L.rim, alpha * L.rim_amt, blend=gfx.SCREEN))
        c.restore()
    c.restore()


def sample(path, step=4.0, closed=True):
    meas = skia.PathMeasure(path, closed)
    out = []
    while True:
        Ln = meas.getLength()
        if Ln <= 0:
            if not meas.nextContour():
                break
            continue
        n = max(4, int(Ln / step))
        pts = []
        for k in range(n + (0 if closed else 1)):
            r = meas.getPosTan(Ln * k / n)
            pos = r[1] if len(r) == 3 else r[0]
            pts.append((pos.x(), pos.y()))
        out.append(pts)
        if not meas.nextContour():
            break
    return out


def outline(c, path, L: Light, w=1.6, var=0.9, color=None, alpha=1.0, closed=True, step=4.0, taper_ends=False):
    """Variable-weight contour: thinner on the lit side, heavier on the shadow side."""
    col = color if color is not None else L.line
    for pts in sample(path, step, closed):
        if len(pts) < 3:
            continue
        P = np.asarray(pts, np.float64)
        if closed:
            Pn = np.vstack([P[-1:], P, P[:1]])
            tang = Pn[2:] - Pn[:-2]
        else:
            tang = np.gradient(P, axis=0)
        tl = np.linalg.norm(tang, axis=1, keepdims=True) + 1e-9
        nrm = np.stack([tang[:, 1], -tang[:, 0]], axis=1) / tl   # outward normal for clockwise paths
        dl = nrm @ (-L.dir)                                        # 1 = facing away from light
        ws = w * L.line_k * (1 - var * 0.5 + var * 0.5 * (np.clip(dl, -1, 1) + 1) * 0.75)
        ws = np.maximum(ws, 0.35)
        if taper_ends and not closed:
            n = len(ws)
            t = np.minimum(np.arange(n), np.arange(n)[::-1]) / max(1, n * 0.15)
            ws = ws * np.clip(t, 0.15, 1.0)
        if closed:
            pts2 = list(map(tuple, P)) + [tuple(P[0]), tuple(P[1])]
            ws2 = list(ws) + [ws[0], ws[1]]
        else:
            pts2, ws2 = list(map(tuple, P)), list(ws)
        c.drawPath(gfx.ribbon(pts2, ws2, smooth=False), gfx.paint(col, alpha))


def line(c, pts, w0, w1=None, color=(60, 50, 70), alpha=1.0, smooth=True, taper=True):
    """Tapered open stroke through pts (w0 at start, w1 at end, thin tips)."""
    if len(pts) < 2:
        return
    w1 = w0 if w1 is None else w1
    n = len(pts)
    if smooth and n >= 3:
        path = gfx.smooth_path(pts, closed=False)
        dense = sample(path, 3.0, closed=False)
        P = dense[0] if dense else pts
    else:
        P = pts
    m = len(P)
    ws = []
    for i in range(m):
        u = i / max(1, m - 1)
        wv = w0 + (w1 - w0) * u
        if taper:
            wv *= min(1.0, 0.25 + 3.0 * min(u, 1 - u)) if m > 4 else 1.0
        ws.append(max(0.3, wv))
    c.drawPath(gfx.ribbon(P, ws, smooth=False), gfx.paint(color, alpha))


def soft_ellipse(c, x, y, rx, ry, color, alpha, blur, blend=None):
    c.drawPath(gfx.ellipse(x, y, rx, ry), gfx.paint(color, alpha, blur=blur, blend=blend))


def gradient_fill(c, path, p0, p1, cols, stops=None, alpha=1.0, blend=None):
    sh = gfx.linear_grad(p0[0], p0[1], p1[0], p1[1], [tuple(cc) + (255,) if len(cc) == 3 else cc for cc in cols], stops)
    c.drawPath(path, gfx.paint((255, 255, 255), alpha, shader=sh, blend=blend))
