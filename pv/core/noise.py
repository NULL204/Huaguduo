"""Deterministic noise helpers (scalar + numpy) and textures."""
import math
import numpy as np
import cv2


def hash01(i, seed=0):
    i = (int(i) * 374761393 + int(seed) * 668265263 + 0x9E3779B9) & 0xFFFFFFFF
    i = ((i ^ (i >> 13)) * 1274126177) & 0xFFFFFFFF
    i = (i ^ (i >> 16)) & 0xFFFFFF
    return i / float(0x1000000)


def noise1(x, seed=0):
    """Smooth value noise in [-1, 1]."""
    i = math.floor(x)
    f = x - i
    a = hash01(i, seed)
    b = hash01(i + 1, seed)
    u = f * f * (3 - 2 * f)
    return (a + (b - a) * u) * 2 - 1


def fbm1(x, seed=0, octaves=3, lac=2.0, gain=0.5):
    amp, freq, s, norm = 1.0, 1.0, 0.0, 0.0
    for o in range(octaves):
        s += amp * noise1(x * freq, seed + o * 17)
        norm += amp
        amp *= gain
        freq *= lac
    return s / norm


def noise1_np(x, seed=0):
    x = np.asarray(x, dtype=np.float64)
    i = np.floor(x).astype(np.int64)
    f = x - i

    def h(ii):
        v = (ii * 374761393 + seed * 668265263 + 0x9E3779B9) & 0xFFFFFFFF
        v = ((v ^ (v >> 13)) * 1274126177) & 0xFFFFFFFF
        v = (v ^ (v >> 16)) & 0xFFFFFF
        return v / float(0x1000000)

    a = h(i)
    b = h(i + 1)
    u = f * f * (3 - 2 * f)
    return (a + (b - a) * u) * 2 - 1


def fbm1_np(x, seed=0, octaves=3, lac=2.0, gain=0.5):
    amp, freq = 1.0, 1.0
    s = np.zeros_like(np.asarray(x, dtype=np.float64))
    norm = 0.0
    for o in range(octaves):
        s = s + amp * noise1_np(np.asarray(x) * freq, seed + o * 17)
        norm += amp
        amp *= gain
        freq *= lac
    return s / norm


class RNG:
    """Small wrapper so every element can own a deterministic generator."""

    def __init__(self, seed):
        self.r = np.random.default_rng(int(seed) % (2 ** 32))

    def u(self, a=0.0, b=1.0, n=None):
        return self.r.uniform(a, b, n)

    def n(self, mu=0.0, sd=1.0, n=None):
        return self.r.normal(mu, sd, n)

    def i(self, a, b, n=None):
        return self.r.integers(a, b, n)

    def choice(self, seq):
        return seq[int(self.r.integers(0, len(seq)))]


def value_noise_2d(h, w, cell, seed=0, interp=cv2.INTER_CUBIC):
    """Smooth 2D noise in [-1,1] by upscaling a random grid."""
    rng = np.random.default_rng(seed)
    gh = max(2, int(math.ceil(h / cell)) + 3)
    gw = max(2, int(math.ceil(w / cell)) + 3)
    g = rng.uniform(-1, 1, (gh, gw)).astype(np.float32)
    big = cv2.resize(g, (int(gw * cell), int(gh * cell)), interpolation=interp)
    oy = int(cell)
    ox = int(cell)
    return big[oy:oy + h, ox:ox + w]


def fbm_2d(h, w, base_cell, octaves=5, seed=0, gain=0.5):
    out = np.zeros((h, w), np.float32)
    amp, cell, norm = 1.0, float(base_cell), 0.0
    for o in range(octaves):
        if cell < 1.5:
            break
        out += amp * value_noise_2d(h, w, cell, seed + o * 101)
        norm += amp
        amp *= gain
        cell /= 2.0
    return out / max(norm, 1e-6)


def tileable_noise(size, cell, seed=0, octaves=4):
    """Tileable fbm noise in [0,1] (wraps by padding then cropping a period)."""
    out = np.zeros((size, size), np.float32)
    amp, norm = 1.0, 0.0
    rng = np.random.default_rng(seed)
    c = float(cell)
    for o in range(octaves):
        n = max(2, int(round(size / c)))
        g = rng.uniform(-1, 1, (n, n)).astype(np.float32)
        g = np.tile(g, (3, 3))
        big = cv2.resize(g, (size * 3, size * 3), interpolation=cv2.INTER_CUBIC)
        out += amp * big[size:2 * size, size:2 * size]
        norm += amp
        amp *= 0.5
        c /= 2
        if c < 2:
            break
    out = out / norm
    out = (out - out.min()) / (out.max() - out.min() + 1e-6)
    return out
