"""Low level drawing helpers on top of skia + numpy/cv2."""
import math

import cv2
import numpy as np
import skia

from .. import config
from .noise import noise1, hash01

W, H = config.W, config.H

RGBA = skia.kRGBA_8888_ColorType
PREMUL = skia.kPremul_AlphaType


def C(r, g, b, a=255):
    return skia.Color(int(max(0, min(255, r))), int(max(0, min(255, g))), int(max(0, min(255, b))),
                      int(max(0, min(255, a))))


def mix(c1, c2, t):
    return tuple(a + (b - a) * t for a, b in zip(c1, c2))


def paint(color=(0, 0, 0), alpha=1.0, blur=0.0, stroke=None, cap="round", blend=None, aa=True,
          shader=None, path_effect=None, join="round", color_filter=None):
    """Build a skia.Paint in one constructor call (setShader() on large image shaders is very slow
    in skia-python, while the Shader= constructor kwarg is not)."""
    if len(color) == 4:
        r, g, b, a0 = color
        a = a0 * alpha
    else:
        r, g, b = color
        a = 255 * alpha
    kw = dict(AntiAlias=aa, Color=C(r, g, b, a))
    if stroke is not None:
        kw["Style"] = skia.Paint.kStroke_Style
        kw["StrokeWidth"] = stroke
        kw["StrokeCap"] = {"round": skia.Paint.kRound_Cap, "butt": skia.Paint.kButt_Cap,
                           "square": skia.Paint.kSquare_Cap}[cap]
        kw["StrokeJoin"] = {"round": skia.Paint.kRound_Join, "miter": skia.Paint.kMiter_Join,
                            "bevel": skia.Paint.kBevel_Join}[join]
    if blur and blur > 0.05:
        kw["MaskFilter"] = skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, blur)
    if blend is not None:
        kw["BlendMode"] = blend
    if shader is not None:
        kw["Shader"] = shader
    if path_effect is not None:
        kw["PathEffect"] = path_effect
    if color_filter is not None:
        kw["ColorFilter"] = color_filter
    return skia.Paint(**kw)


MULTIPLY = skia.BlendMode.kMultiply
SCREEN = skia.BlendMode.kScreen
PLUS = skia.BlendMode.kPlus
DST_OUT = skia.BlendMode.kDstOut
SRC_OVER = skia.BlendMode.kSrcOver


# --------------------------------------------------------------------------- surfaces

class Surf:
    """numpy-backed RGBA premultiplied surface."""

    def __init__(self, w=W, h=H):
        self.w, self.h = w, h
        self.arr = np.zeros((h, w, 4), np.uint8)
        self.surface = skia.Surface(self.arr)
        self.canvas = self.surface.getCanvas()

    def clear(self, color=(0, 0, 0, 0)):
        self.canvas.clear(C(*color) if len(color) == 4 else C(*color, 255))

    def image(self, copy=True):
        return skia.Image.fromarray(self.arr, colorType=RGBA, alphaType=PREMUL, copy=copy)


_POOL = {}


def pooled(name, w=W, h=H):
    key = (name, w, h)
    if key not in _POOL:
        _POOL[key] = Surf(w, h)
    return _POOL[key]


def arr_to_image(a, premul=True):
    a = np.ascontiguousarray(a)
    return skia.Image.fromarray(a, colorType=RGBA, alphaType=PREMUL if premul else skia.kUnpremul_AlphaType)


def blur_arr(a, sigma, fast=True):
    """Gaussian blur numpy image (any channels).  Large sigmas use a pyramid shortcut."""
    if sigma <= 0.3:
        return a
    if fast and sigma > 6:
        f = 2 if sigma < 16 else 4 if sigma < 40 else 8
        h, w = a.shape[:2]
        sm = cv2.resize(a, (w // f, h // f), interpolation=cv2.INTER_AREA)
        sm = cv2.GaussianBlur(sm, (0, 0), sigma / f)
        return cv2.resize(sm, (w, h), interpolation=cv2.INTER_LINEAR)
    return cv2.GaussianBlur(a, (0, 0), sigma)


def draw_arr(canvas, a, x=0, y=0, alpha=1.0, blend=None, premul=True):
    img = arr_to_image(a, premul)
    p = skia.Paint()
    if alpha < 1:
        p.setAlphaf(max(0.0, alpha))
    if blend is not None:
        p.setBlendMode(blend)
    canvas.drawImage(img, x, y, skia.SamplingOptions(skia.FilterMode.kLinear), p)


class Layer:
    """Draw into an offscreen surface, optionally blur, then composite onto `dst` canvas.

        with Layer(dst_canvas, blur=8) as c:
            c.drawPath(...)
    """

    def __init__(self, dst, blur=0.0, alpha=1.0, blend=None, scale=1.0, name="layer", matrix=None):
        self.dst = dst
        self.blur = blur
        self.alpha = alpha
        self.blend = blend
        self.scale = scale
        self.name = name
        self.matrix = matrix

    def __enter__(self):
        s = self.scale
        self.surf = pooled(self.name, int(W * s), int(H * s))
        self.surf.clear()
        c = self.surf.canvas
        c.save()
        if s != 1.0:
            c.scale(s, s)
        if self.matrix is not None:
            c.concat(self.matrix)
        return c

    def __exit__(self, *exc):
        self.surf.canvas.restore()
        a = self.surf.arr
        if self.blur > 0.3:
            a = blur_arr(a, self.blur * self.scale)
        img = arr_to_image(a)
        p = skia.Paint()
        if self.alpha < 1:
            p.setAlphaf(max(0.0, self.alpha))
        if self.blend is not None:
            p.setBlendMode(self.blend)
        self.dst.save()
        self.dst.resetMatrix()
        if self.scale != 1.0:
            self.dst.scale(1 / self.scale, 1 / self.scale)
        self.dst.drawImage(img, 0, 0, skia.SamplingOptions(skia.FilterMode.kLinear), p)
        self.dst.restore()
        return False


# --------------------------------------------------------------------------- paths

def poly(pts, closed=True):
    p = skia.Path()
    if len(pts) == 0:
        return p
    p.moveTo(*pts[0])
    for q in pts[1:]:
        p.lineTo(*q)
    if closed:
        p.close()
    return p


def smooth_path(pts, closed=False, tension=0.5):
    """Catmull-Rom through points, as cubic beziers."""
    p = skia.Path()
    n = len(pts)
    if n < 2:
        return p
    P = [tuple(map(float, q)) for q in pts]
    p.moveTo(*P[0])
    rng = range(n) if closed else range(n - 1)
    for i in rng:
        p0 = P[(i - 1) % n] if (closed or i > 0) else P[i]
        p1 = P[i]
        p2 = P[(i + 1) % n]
        p3 = P[(i + 2) % n] if (closed or i + 2 < n) else P[(i + 1) % n]
        k = tension / 3.0 * 2
        c1 = (p1[0] + (p2[0] - p0[0]) * k / 2, p1[1] + (p2[1] - p0[1]) * k / 2)
        c2 = (p2[0] - (p3[0] - p1[0]) * k / 2, p2[1] - (p3[1] - p1[1]) * k / 2)
        p.cubicTo(c1[0], c1[1], c2[0], c2[1], p2[0], p2[1])
    if closed:
        p.close()
    return p


def ribbon(pts, widths, closed_caps=True, smooth=True):
    """Variable width stroke outline (tapered brush stroke) through pts."""
    n = len(pts)
    if n < 2:
        return skia.Path()
    P = np.asarray(pts, dtype=np.float64)
    Wd = np.asarray(widths, dtype=np.float64) if np.ndim(widths) else np.full(n, float(widths))
    d = np.gradient(P, axis=0)
    ln = np.linalg.norm(d, axis=1, keepdims=True) + 1e-9
    nrm = np.stack([-d[:, 1], d[:, 0]], axis=1) / ln
    L = P + nrm * (Wd[:, None] / 2)
    R = P - nrm * (Wd[:, None] / 2)
    outline = list(map(tuple, L)) + list(map(tuple, R[::-1]))
    if smooth:
        return smooth_path(outline, closed=True)
    return poly(outline, True)


def blob(cx, cy, r, wobble=0.15, seed=0, n=24, t=0.0, aspect=1.0, rot=0.0):
    pts = []
    for k in range(n):
        a = 2 * math.pi * k / n
        rr = r * (1 + wobble * noise1(k * 0.7 + t, seed) + 0.5 * wobble * noise1(k * 1.9 + t * 1.7, seed + 9))
        x = math.cos(a) * rr * aspect
        y = math.sin(a) * rr
        ca, sa = math.cos(rot), math.sin(rot)
        pts.append((cx + x * ca - y * sa, cy + x * sa + y * ca))
    return smooth_path(pts, closed=True)


def ellipse(cx, cy, rx, ry):
    p = skia.Path()
    p.addOval(skia.Rect(cx - rx, cy - ry, cx + rx, cy + ry))
    return p


def circle(cx, cy, r):
    p = skia.Path()
    p.addCircle(cx, cy, r)
    return p


def rect(x, y, w, h):
    p = skia.Path()
    p.addRect(skia.Rect(x, y, x + w, y + h))
    return p


def transformed(path, m):
    p = skia.Path(path)
    p.transform(m)
    return p


def mat(tx=0, ty=0, rot=0.0, sx=1.0, sy=None, px=0.0, py=0.0):
    """Matrix: translate(tx,ty) * rotate(rot rad about origin) * scale, about pivot (px,py)."""
    if sy is None:
        sy = sx
    m = skia.Matrix()
    m.setTranslate(tx, ty)
    m.preRotate(math.degrees(rot))
    m.preScale(sx, sy)
    m.preTranslate(-px, -py)
    return m


def op(a, b, kind="diff"):
    k = {"diff": skia.PathOp.kDifference_PathOp, "union": skia.PathOp.kUnion_PathOp,
         "inter": skia.PathOp.kIntersect_PathOp, "xor": skia.PathOp.kXOR_PathOp}[kind]
    r = skia.Op(a, b, k)
    return r if r is not None else a


def rough(path, seg=6.0, dev=2.0, seed=1):
    """Return a roughened copy of path (paper-cut / torn edge)."""
    pe = skia.DiscretePathEffect.Make(seg, dev, seed)
    dst = skia.Path()
    p = skia.Paint(PathEffect=pe)
    rec = skia.StrokeRec(skia.StrokeRec.kFill_InitStyle)
    try:
        pe.filterPath(dst, path, rec, path.getBounds())
        return dst
    except Exception:
        return path


def radial(cx, cy, r, colors, stops=None):
    cols = [C(*c) if len(c) == 4 else C(*c, 255) for c in colors]
    return skia.GradientShader.MakeRadial(skia.Point(cx, cy), r, cols, stops)


def linear_grad(x0, y0, x1, y1, colors, stops=None):
    cols = [C(*c) if len(c) == 4 else C(*c, 255) for c in colors]
    return skia.GradientShader.MakeLinear([skia.Point(x0, y0), skia.Point(x1, y1)], cols, stops)


def fill_rect(canvas, color, x=0, y=0, w=W, h=H, alpha=1.0, blend=None, shader=None):
    canvas.drawRect(skia.Rect(x, y, x + w, y + h), paint(color, alpha, blend=blend, shader=shader))


def bezier_pts(p0, p1, p2, p3, n=24):
    out = []
    for i in range(n + 1):
        t = i / n
        a = (1 - t) ** 3
        b = 3 * (1 - t) ** 2 * t
        c = 3 * (1 - t) * t * t
        d = t ** 3
        out.append((a * p0[0] + b * p1[0] + c * p2[0] + d * p3[0], a * p0[1] + b * p1[1] + c * p2[1] + d * p3[1]))
    return out


def polyline_length(pts):
    return sum(math.hypot(pts[i + 1][0] - pts[i][0], pts[i + 1][1] - pts[i][1]) for i in range(len(pts) - 1))


def polyline_cut(pts, u):
    """First fraction u (0..1) of a polyline by length."""
    if u >= 1:
        return list(pts)
    if u <= 0:
        return [pts[0], pts[0]]
    total = polyline_length(pts)
    target = total * u
    acc = 0
    out = [pts[0]]
    for i in range(len(pts) - 1):
        seg = math.hypot(pts[i + 1][0] - pts[i][0], pts[i + 1][1] - pts[i][1])
        if acc + seg >= target:
            f = (target - acc) / (seg + 1e-9)
            out.append((pts[i][0] + (pts[i + 1][0] - pts[i][0]) * f, pts[i][1] + (pts[i + 1][1] - pts[i][1]) * f))
            return out
        acc += seg
        out.append(pts[i + 1])
    return out
