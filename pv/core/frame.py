"""Frame context, scene base class and transitions."""
import math

import cv2
import numpy as np
import skia

from .. import config
from . import gfx, post
from . import textures as T
from . import easing as E

W, H = config.W, config.H


class FrameCtx:
    def __init__(self, t):
        self.t = t
        self.surf = gfx.pooled("main")
        self.canvas = self.surf.canvas
        self.post = {}

    @property
    def arr(self):
        return self.surf.arr

    def clear(self, color=(255, 255, 255)):
        self.canvas.restoreToCount(1)
        self.canvas.resetMatrix()
        self.surf.clear(tuple(color) + (255,) if len(color) == 3 else color)

    def light(self, cx=0.5, cy=0.45, radius=0.75, power=1.6, edge=0.18, warm=1.0, flicker=1.0,
              paper=None):
        """Multiply the transmittance drawn so far by the backlit paper screen."""
        kw = dict(cx=cx, cy=cy, radius=radius, power=power, edge=edge, warm=warm)
        if paper is not None:
            kw["paper"] = np.asarray(paper, np.float32).tobytes()
        L = T.screen_light(**{k: (round(v, 3) if isinstance(v, float) else v) for k, v in kw.items()})
        a = self.surf.arr
        cv2.multiply(a, L, dst=a, scale=flicker / 255.0)
        if flicker > 1.0:
            a[..., 3] = 255

    def rgb_copy(self):
        return self.surf.arr[..., :3].copy()

    def put_rgb(self, img):
        self.surf.arr[..., :3] = img
        self.surf.arr[..., 3] = 255


class Scene:
    """Base scene: override draw(fr, t, lt, u).  Return post params dict."""
    name = "scene"

    def __init__(self, start, end, **kw):
        self.start = start
        self.end = end
        self.kw = kw
        self.setup()

    def setup(self):
        pass

    def draw(self, fr, t, lt, u):
        raise NotImplementedError

    def render(self, t):
        fr = FrameCtx(t)
        fr.clear((255, 255, 255))
        lt = t - self.start
        u = (t - self.start) / max(1e-6, self.end - self.start)
        pp = self.draw(fr, t, lt, u) or {}
        img = fr.rgb_copy()
        return apply_post(img, t, pp)


def apply_post(img, t, pp):
    if "glow" in pp and pp["glow"]:
        g = pp["glow"]
        img = post.glow(img, threshold=g.get("thr", 0.75), sigma=g.get("sigma", 18),
                        strength=g.get("strength", 0.5), red_bias=g.get("red", 0.0))
    if "grade" in pp and pp["grade"]:
        img = post.grade(img, **pp["grade"])
    if pp.get("film", 0) > 0:
        img = post.old_film(img, t, pp["film"])
    if pp.get("chroma", 0) > 0.3:
        img = post.chroma(img, pp["chroma"])
    if "shake" in pp and pp["shake"]:
        dx, dy = pp["shake"][:2]
        rot = pp["shake"][2] if len(pp["shake"]) > 2 else 0
        img = post.shake(img, dx, dy, rot)
    if pp.get("flash", 0) > 0:
        col = pp.get("flash_color", (255, 250, 240))
        img = post.fade(img, min(1.0, pp["flash"]), col)
    if pp.get("fade", 0) > 0:
        img = post.fade(img, min(1.0, pp["fade"]), pp.get("fade_color", (0, 0, 0)))
    return img


# --------------------------------------------------------------------------- transitions

def trans_mask(kind, k, seed=0, params=None):
    """Mask (HxW float32 0..1): 1 where the incoming scene shows."""
    params = params or {}
    if kind == "fade":
        return None
    if kind in ("ink", "burn"):
        cx, cy = params.get("center", (0.5, 0.5))
        n = T.noise_field(params.get("cell", 160), seed=seed + 5)
        nf = T.noise_field(34, seed=seed + 11, octaves=3)
        r = T.radial_field(round(cx, 3), round(cy, 3))
        rmax = float(r.max())
        f = r / rmax * 0.7 + n * 0.32 + nf * 0.12
        f = (f - f.min()) / (f.max() - f.min() + 1e-6)
        edge = params.get("edge", 0.035)
        thr = k * (1.0 + 2 * edge + 0.12) - edge
        m = np.clip((thr - 0.12 - f) / edge + 0.5, 0, 1)
        if kind == "ink":
            # the ink front itself: a band just ahead of the reveal
            band = np.clip((thr - f) / 0.12, 0, 1) * (1 - m)
            return np.stack([m, band], axis=0)
        return m
    if kind in ("wipe_l", "wipe_r", "wipe_d", "wipe_u"):
        n = T.noise_field(90, seed=seed + 9)
        yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
        if kind == "wipe_l":
            g = 1 - xx / W
        elif kind == "wipe_r":
            g = xx / W
        elif kind == "wipe_d":
            g = yy / H
        else:
            g = 1 - yy / H
        f = g * 0.85 + n * 0.15
        edge = 0.04
        thr = k * (1 + edge * 2) - edge
        return np.clip((thr - f) / edge + 0.5, 0, 1).astype(np.float32)
    if kind == "iris":
        cx, cy = params.get("center", (0.5, 0.5))
        r = T.radial_field(round(cx, 3), round(cy, 3))
        rad = k * float(r.max()) * 1.05
        return np.clip((rad - r) * 60 + 0.5, 0, 1).astype(np.float32)
    return None


def blend(a, b, kind, k, seed=0, params=None):
    if kind == "cut":
        return b if k >= 0.5 else a
    if kind == "fade":
        return post.mix(a, b, E.smooth(k))
    if kind == "black":
        if k < 0.5:
            return post.fade(a, E.smooth(k * 2))
        return post.fade(b, 1 - E.smooth((k - 0.5) * 2))
    if kind == "white":
        if k < 0.5:
            return post.fade(a, E.smooth(k * 2), (250, 244, 232))
        return post.fade(b, 1 - E.smooth((k - 0.5) * 2), (250, 244, 232))
    m = trans_mask(kind, k, seed, params)
    if m is None:
        return post.mix(a, b, k)
    band = None
    if m.ndim == 3:
        m, band = m[0], m[1]
    out = post.mask_mix(a, b, m)
    if kind == "burn":
        band = np.clip(1 - np.abs(m - 0.5) * 2.2, 0, 1) ** 2
        col = np.asarray(params.get("color", (255, 70, 40)) if params else (255, 70, 40), np.float32)
        o = out.astype(np.float32)
        o = o + band[..., None] * (col[None, None, :] - o * 0.3)
        out = np.clip(o, 0, 255).astype(np.uint8)
    if kind == "ink" and band is not None:
        col = np.asarray(params.get("color", (16, 12, 12)) if params else (16, 12, 12), np.float32)
        a_ = np.clip(band * 1.25, 0, 1) ** 0.8
        o = out.astype(np.float32)
        o = o * (1 - a_[..., None] * 0.96) + a_[..., None] * 0.96 * col[None, None, :]
        out = np.clip(o, 0, 255).astype(np.uint8)
    return out
