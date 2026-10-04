"""Frame post-processing on uint8 RGB numpy arrays."""
import math

import cv2
import numpy as np

from .. import config
from . import textures as T
from .noise import hash01, noise1

W, H = config.W, config.H


def glow(img, threshold=0.72, sigma=18, strength=0.6, red_bias=0.0):
    """Additive bloom of bright (and optionally red) regions."""
    f = img.astype(np.float32) * (1 / 255.0)
    lum = f[..., 0] * 0.3 + f[..., 1] * 0.59 + f[..., 2] * 0.11
    m = np.clip((lum - threshold) / (1 - threshold + 1e-6), 0, 1)
    if red_bias > 0:
        red = np.clip(f[..., 0] - 0.5 * (f[..., 1] + f[..., 2]) - 0.25, 0, 1) * 2.0
        m = np.maximum(m, red * red_bias)
    src = f * m[..., None]
    b = cv2.resize(src, (W // 4, H // 4), interpolation=cv2.INTER_AREA)
    b = cv2.GaussianBlur(b, (0, 0), sigma / 4)
    b2 = cv2.GaussianBlur(b, (0, 0), sigma / 2)
    b = cv2.resize(b * 0.6 + b2 * 0.6, (W, H), interpolation=cv2.INTER_LINEAR)
    out = 1 - (1 - f) * (1 - np.clip(b * strength, 0, 1))  # screen blend
    return np.clip(out * 255, 0, 255).astype(np.uint8)


def grade(img, lift=(0, 0, 0), gamma=(1, 1, 1), gain=(1, 1, 1), sat=1.0, contrast=1.0):
    """Lift/gamma/gain + saturation + contrast via LUTs (fast)."""
    x = np.arange(256, dtype=np.float32) / 255.0
    luts = []
    for c in range(3):
        y = x
        if contrast != 1.0:
            y = np.clip((y - 0.5) * contrast + 0.5, 0, 1)
        y = np.clip(y * gain[c] + lift[c] * (1 - y), 0, 1)
        y = y ** (1.0 / gamma[c])
        luts.append(np.clip(y * 255, 0, 255).astype(np.uint8))
    out = np.dstack([cv2.LUT(img[..., c], luts[c]) for c in range(3)])
    if sat != 1.0:
        g = cv2.cvtColor(out, cv2.COLOR_RGB2GRAY)
        g3 = np.dstack([g, g, g])
        out = cv2.addWeighted(out, sat, g3, 1 - sat, 0)
    return out


def tint_mul(img, rgb):
    """Multiply by a colour (0..1 floats)."""
    out = img.astype(np.float32)
    out *= np.asarray(rgb, np.float32)[None, None, :]
    return np.clip(out, 0, 255).astype(np.uint8)


def vignette(img, strength=0.5, power=2.2):
    v = T.vignette(round(strength, 2), power)
    return (img.astype(np.float32) * v[..., None]).astype(np.uint8)


def grain(img, t, amount=7.0, fps=config.FPS):
    tiles = T.grain_tiles()
    k = int(t * fps)
    g = tiles[k % len(tiles)]
    ox = int(hash01(k, 3) * 14)
    oy = int(hash01(k, 7) * 14)
    gg = g[oy:oy + H, ox:ox + W]
    f = img.astype(np.float32)
    # grain stronger in mid-tones
    lum = f.mean(axis=2, keepdims=True) / 255.0
    wgt = 0.5 + 2.0 * lum * (1 - lum)
    f += gg[..., None] * amount * wgt
    return np.clip(f, 0, 255).astype(np.uint8)


def chroma(img, amount=3.0):
    """Radial chromatic aberration (R out, B in)."""
    if amount < 0.3:
        return img
    s = 1 + amount / W
    M = cv2.getRotationMatrix2D((W / 2, H / 2), 0, s)
    r = cv2.warpAffine(img[..., 0], M, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
    M2 = cv2.getRotationMatrix2D((W / 2, H / 2), 0, 1 / s)
    b = cv2.warpAffine(img[..., 2], M2, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
    return np.dstack([r, img[..., 1], b])


def shake(img, dx, dy, rot=0.0, zoom=1.0):
    if abs(dx) < 0.2 and abs(dy) < 0.2 and abs(rot) < 1e-4 and abs(zoom - 1) < 1e-4:
        return img
    M = cv2.getRotationMatrix2D((W / 2, H / 2), math.degrees(rot), zoom)
    M[0, 2] += dx
    M[1, 2] += dy
    return cv2.warpAffine(img, M, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)


def old_film(img, t, amount=1.0, seed=0):
    """Aged photograph / old film: sepia, flicker, dust, scratches, gate weave, soft focus."""
    if amount <= 0.01:
        return img
    f = img.astype(np.float32) / 255.0
    lum = f[..., 0] * 0.3 + f[..., 1] * 0.59 + f[..., 2] * 0.11
    sep = np.dstack([lum * 1.07, lum * 0.92, lum * 0.70])
    # keep some red alive in the old photo
    f = f * (1 - 0.75 * amount) + np.clip(sep, 0, 1) * 0.75 * amount
    k = int(t * 24)
    flick = 1 + 0.06 * amount * (hash01(k, seed) - 0.5) * 2
    f *= flick
    # soft focus
    b = cv2.GaussianBlur(f, (0, 0), 1.6)
    f = f * (1 - 0.6 * amount) + b * 0.6 * amount
    # heavy dark vignette (old lens)
    v = T.vignette(0.85, 1.6)
    f *= (1 - amount + amount * v)[..., None]
    out = np.clip(f * 255, 0, 255).astype(np.uint8)
    # dust and scratches
    rng = np.random.default_rng(k * 7 + seed)
    nd = int(14 * amount)
    for i in range(nd):
        x, y = int(rng.uniform(0, W)), int(rng.uniform(0, H))
        r = int(rng.uniform(1, 4))
        col = int(rng.uniform(10, 60)) if rng.random() < 0.7 else 230
        cv2.circle(out, (x, y), r, (col, col, col), -1, lineType=cv2.LINE_AA)
    if rng.random() < 0.7 * amount:
        for i in range(rng.integers(1, 3)):
            x = int(rng.uniform(0, W))
            col = int(rng.uniform(150, 220))
            cv2.line(out, (x, 0), (x + int(rng.normal(0, 6)), H), (col, col - 10, col - 25), 1, lineType=cv2.LINE_AA)
    # gate weave
    dx = 2.0 * amount * noise1(t * 6, seed + 1)
    dy = 2.5 * amount * noise1(t * 5, seed + 2)
    return shake(out, dx, dy)


def letterbox(img, frac):
    if frac <= 0:
        return img
    h = int(H * frac / 2)
    out = img.copy()
    out[:h] = 0
    out[H - h:] = 0
    return out


def fade(img, k, color=(0, 0, 0)):
    """k=0: image, k=1: solid colour."""
    if k <= 0:
        return img
    if k >= 1:
        out = np.empty_like(img)
        out[:] = color
        return out
    col = np.empty_like(img)
    col[:] = color
    return cv2.addWeighted(img, 1 - k, col, k, 0)


def mix(a, b, k):
    if k <= 0:
        return a
    if k >= 1:
        return b
    return cv2.addWeighted(a, 1 - k, b, k, 0)


def mask_mix(a, b, m):
    """Per-pixel mix a->b by mask m (float32 HxW 0..1)."""
    m3 = m[..., None]
    out = a.astype(np.float32) * (1 - m3) + b.astype(np.float32) * m3
    return out.astype(np.uint8)
