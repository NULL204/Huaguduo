"""Easing curves, interpolation and keyframe tracks."""
import math


def clamp(x, a=0.0, b=1.0):
    return a if x < a else b if x > b else x


def lerp(a, b, t):
    return a + (b - a) * t


def lerp_t(a, b, t):
    """Lerp scalars or tuples."""
    if isinstance(a, (tuple, list)):
        return tuple(x + (y - x) * t for x, y in zip(a, b))
    return a + (b - a) * t


def remap(x, a, b, c=0.0, d=1.0, clip=True):
    if b == a:
        return d
    u = (x - a) / (b - a)
    if clip:
        u = clamp(u)
    return c + (d - c) * u


def prog(t, a, b):
    """Normalized progress of t inside [a, b], clipped."""
    return clamp((t - a) / (b - a)) if b != a else (1.0 if t >= b else 0.0)


def linear(t):
    return t


def smooth(t):
    t = clamp(t)
    return t * t * (3 - 2 * t)


def smoother(t):
    t = clamp(t)
    return t * t * t * (t * (t * 6 - 15) + 10)


def in_quad(t):
    t = clamp(t)
    return t * t


def out_quad(t):
    t = clamp(t)
    return 1 - (1 - t) * (1 - t)


def in_cubic(t):
    t = clamp(t)
    return t * t * t


def out_cubic(t):
    t = clamp(t)
    return 1 - (1 - t) ** 3


def in_out_cubic(t):
    t = clamp(t)
    return 4 * t * t * t if t < 0.5 else 1 - (-2 * t + 2) ** 3 / 2


def in_out_sine(t):
    t = clamp(t)
    return -(math.cos(math.pi * t) - 1) / 2


def out_sine(t):
    t = clamp(t)
    return math.sin(t * math.pi / 2)


def in_sine(t):
    t = clamp(t)
    return 1 - math.cos(t * math.pi / 2)


def out_expo(t):
    t = clamp(t)
    return 1.0 if t >= 1 else 1 - 2 ** (-10 * t)


def in_expo(t):
    t = clamp(t)
    return 0.0 if t <= 0 else 2 ** (10 * t - 10)


def in_out_expo(t):
    t = clamp(t)
    if t <= 0:
        return 0.0
    if t >= 1:
        return 1.0
    return 2 ** (20 * t - 10) / 2 if t < 0.5 else (2 - 2 ** (-20 * t + 10)) / 2


def out_back(t, s=1.70158):
    t = clamp(t)
    c3 = s + 1
    return 1 + c3 * (t - 1) ** 3 + s * (t - 1) ** 2


def out_elastic(t):
    t = clamp(t)
    if t in (0.0, 1.0):
        return t
    c4 = (2 * math.pi) / 3
    return 2 ** (-10 * t) * math.sin((t * 10 - 0.75) * c4) + 1


def bump(t, a, b, c, d):
    """0 before a, ramps to 1 by b, holds, ramps down to 0 from c to d."""
    if t <= a or t >= d:
        return 0.0
    if t < b:
        return smooth((t - a) / (b - a))
    if t <= c:
        return 1.0
    return 1 - smooth((t - c) / (d - c))


def pulse(t, t0, attack=0.02, decay=0.35):
    """Sharp attack, exponential decay impulse centred at t0."""
    dt = t - t0
    if dt < -attack:
        return 0.0
    if dt < 0:
        return 1 + dt / attack
    return math.exp(-dt / decay)


EASES = {
    "linear": linear, "smooth": smooth, "smoother": smoother,
    "in_quad": in_quad, "out_quad": out_quad, "in_cubic": in_cubic, "out_cubic": out_cubic,
    "in_out_cubic": in_out_cubic, "in_out_sine": in_out_sine, "out_sine": out_sine, "in_sine": in_sine,
    "out_expo": out_expo, "in_expo": in_expo, "in_out_expo": in_out_expo, "out_back": out_back,
    "out_elastic": out_elastic, "hold": lambda t: 0.0 if t < 1 else 1.0,
}


class Track:
    """Keyframe track.  keys: list of (time, value[, ease]) where ease applies to
    the segment arriving at that key.  Values may be floats or tuples."""

    def __init__(self, keys, default_ease="in_out_cubic"):
        ks = []
        for k in keys:
            if len(k) == 2:
                ks.append((k[0], k[1], default_ease))
            else:
                ks.append((k[0], k[1], k[2]))
        ks.sort(key=lambda k: k[0])
        self.keys = ks

    def __call__(self, t):
        ks = self.keys
        if t <= ks[0][0]:
            return ks[0][1]
        if t >= ks[-1][0]:
            return ks[-1][1]
        for i in range(1, len(ks)):
            if t <= ks[i][0]:
                t0, v0, _ = ks[i - 1]
                t1, v1, e = ks[i]
                f = EASES[e] if isinstance(e, str) else e
                u = f((t - t0) / (t1 - t0)) if t1 > t0 else 1.0
                return lerp_t(v0, v1, u)
        return ks[-1][1]


def seq_index(t, times):
    """Index of the last time in sorted `times` that is <= t (or -1)."""
    idx = -1
    for i, x in enumerate(times):
        if t >= x:
            idx = i
        else:
            break
    return idx
