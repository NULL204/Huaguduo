"""Procedural textures: rice paper, lamp light maps, ink grain.  Cached per process."""
import math

import cv2
import numpy as np
import skia

from .. import config
from .noise import fbm_2d, value_noise_2d, tileable_noise
from . import gfx

W, H = config.W, config.H
_CACHE = {}


def cached(fn):
    def wrap(*a, **k):
        key = (fn.__name__, a, tuple(sorted(k.items())))
        if key not in _CACHE:
            _CACHE[key] = fn(*a, **k)
        return _CACHE[key]
    return wrap


@cached
def paper_fibers(seed=3):
    """float32 HxW, ~1.0 mean: rice-paper fibre texture."""
    rng = np.random.default_rng(seed)
    base = fbm_2d(H, W, W / 6, octaves=6, seed=seed)
    mott = fbm_2d(H, W, W / 40, octaves=3, seed=seed + 7)
    s = gfx.Surf(W, H)
    s.clear((128, 128, 128, 255))
    c = s.canvas
    # long fibres
    for i in range(int(2600 * W / 1920)):
        x, y = rng.uniform(-50, W + 50), rng.uniform(-50, H + 50)
        ang = rng.uniform(0, math.pi)
        L = rng.uniform(20, 160) * W / 1920
        pts = []
        cx, cy = x, y
        for k in range(8):
            ang += rng.normal(0, 0.25)
            cx += math.cos(ang) * L / 8
            cy += math.sin(ang) * L / 8
            pts.append((cx, cy))
        light = rng.random() < 0.55
        col = (190, 190, 190) if light else (85, 85, 85)
        p = gfx.paint(col, alpha=rng.uniform(0.08, 0.30), stroke=rng.uniform(0.5, 1.6) * W / 1920)
        c.drawPath(gfx.smooth_path(pts), p)
    fib = s.arr[..., 0].astype(np.float32) / 128.0 - 1.0
    fib = cv2.GaussianBlur(fib, (0, 0), 0.6)
    grain = rng.normal(0, 1, (H, W)).astype(np.float32)
    grain = cv2.GaussianBlur(grain, (0, 0), 0.7)
    tex = 1.0 + 0.045 * base + 0.03 * mott + 0.11 * fib + 0.018 * grain
    return tex.astype(np.float32)


_LS = 4  # the lamp falloff is smooth: compute it at 1/4 resolution and upsample


def lamp_map(cx=0.5, cy=0.45, radius=0.75, power=1.6, edge=0.18, warm=1.0):
    """Backlight falloff of an oil lamp behind the shadow screen.  float32 HxWx3 (not cached)."""
    h, w = H // _LS, W // _LS
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    dx = ((xx + 0.5) / w - cx) * (W / H)
    dy = ((yy + 0.5) / h - cy)
    d = np.sqrt(dx * dx + dy * dy) / radius
    f = np.clip(1 - d, 0, 1) ** power
    f = edge + (1 - edge) * f
    # warm tint deeper toward the edges
    r = f
    g = f ** (1.0 + 0.25 * warm)
    b = f ** (1.0 + 0.75 * warm)
    small = np.stack([r, g, b], axis=-1).astype(np.float32)
    return cv2.resize(small, (W, H), interpolation=cv2.INTER_LINEAR)


PAPER_RGB = np.array([248, 236, 212], np.float32) / 255.0


from collections import OrderedDict

_LIGHT_LRU = OrderedDict()
_LIGHT_MAX = 6   # light maps are 8 MB each; animated lights create a new one every frame


def screen_light(cx=0.5, cy=0.45, radius=0.75, power=1.6, edge=0.18, warm=1.0, paper=PAPER_RGB.tobytes()):
    """uint8 HxWx4 lit paper (lamp falloff x fibres x paper colour), alpha=255.  Small LRU cache."""
    key = (cx, cy, radius, power, edge, warm, paper)
    hit = _LIGHT_LRU.get(key)
    if hit is not None:
        _LIGHT_LRU.move_to_end(key)
        return hit
    pc = np.frombuffer(paper, np.float32)
    lm = lamp_map(cx, cy, radius, power, edge, warm)
    lm *= paper_fibers()[..., None]
    lm *= pc[None, None, :] * 255.0
    rgb = np.clip(lm, 0, 255).astype(np.uint8)
    img = np.ascontiguousarray(np.dstack([rgb, np.full((H, W), 255, np.uint8)]))
    _LIGHT_LRU[key] = img
    while len(_LIGHT_LRU) > _LIGHT_MAX:
        _LIGHT_LRU.popitem(last=False)
    return img


@cached
def ink_tex(size=512, seed=11):
    """Tileable ink texture (0..1) used to break up fills (dry brush)."""
    n = tileable_noise(size, size / 6, seed, octaves=6)
    streak = tileable_noise(size, size / 24, seed + 1, octaves=3)
    return np.clip(0.65 * n + 0.35 * streak, 0, 1).astype(np.float32)


@cached
def ink_shader_image(size=512, seed=11, lo=0.25, hi=0.75):
    """RGBA image whose alpha is a thresholded ink texture (white rgb, premultiplied)."""
    n = ink_tex(size, seed)
    a = np.clip((n - lo) / (hi - lo), 0, 1)
    a = (a * 255).astype(np.uint8)
    rgba = np.dstack([a, a, a, a])
    return skia.Image.fromarray(np.ascontiguousarray(rgba), colorType=gfx.RGBA, alphaType=gfx.PREMUL)


_SHADERS = {}


def ink_shader(scale=1.0, seed=11, lo=0.25, hi=0.75, dx=0.0, dy=0.0):
    """Tiling ink-texture shader (anchored in the canvas' local space).  Cached."""
    key = (round(scale, 3), seed, round(lo, 3), round(hi, 3), round(dx % 512, 0), round(dy % 512, 0))
    if key not in _SHADERS:
        img = ink_shader_image(512, seed, lo, hi)
        m = skia.Matrix()
        m.setScaleTranslate(scale, scale, key[4], key[5])
        _SHADERS[key] = img.makeShader(skia.TileMode.kRepeat, skia.TileMode.kRepeat,
                                       skia.SamplingOptions(skia.FilterMode.kLinear), m)
    return _SHADERS[key]


@cached
def grain_tiles(n=6, seed=21):
    rng = np.random.default_rng(seed)
    out = []
    for i in range(n):
        g = rng.normal(0, 1, (H // 2 + 8, W // 2 + 8)).astype(np.float32)
        g = cv2.resize(g, (W + 16, H + 16), interpolation=cv2.INTER_LINEAR)
        out.append(g)
    return out


@cached
def vignette(strength=0.55, power=2.2, cx=0.5, cy=0.5):
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    dx = (xx / W - cx) * 1.6
    dy = (yy / H - cy) * 1.6 * H / W * 1.4
    d = np.sqrt(dx * dx + dy * dy)
    v = 1 - strength * np.clip(d, 0, 1.5) ** power
    return np.clip(v, 0, 1).astype(np.float32)


@cached
def noise_field(cell=180, seed=5, octaves=5):
    """Large smooth noise field 0..1, used for ink-bleed transition thresholds."""
    n = fbm_2d(H, W, cell, octaves=octaves, seed=seed)
    n = (n - n.min()) / (n.max() - n.min() + 1e-6)
    return n.astype(np.float32)


@cached
def radial_field(cx=0.5, cy=0.5):
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    dx = (xx - cx * W) / W
    dy = (yy - cy * H) / W
    return np.sqrt(dx * dx + dy * dy).astype(np.float32)
