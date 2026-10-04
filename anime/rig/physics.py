"""Secondary motion: Verlet chains (ponytail, side locks, thread, sleeve tails) and a skirt hem ring.

Simulation runs at a fixed 120 Hz from the start of a shot, so every render process reproduces exactly
the same motion for a given frame (results are cached per process).
"""
import math

import numpy as np

G = np.array([0.0, -980.0, 0.0])
DT = 1.0 / 120.0


class Chain:
    def __init__(self, n, seg, root, direction=(0, -1, 0), damping=0.06, stiffness=0.3, iters=6, radius=1.0,
                 gravity_scale=1.0, drag=0.0):
        self.n = n
        self.seg = seg if np.ndim(seg) else np.full(n - 1, float(seg))
        d = np.asarray(direction, np.float64)
        d = d / (np.linalg.norm(d) + 1e-9)
        self.p = np.array([np.asarray(root, np.float64) + d * np.sum(self.seg[:i]) for i in range(n)])
        self.pp = self.p.copy()
        self.damping = damping
        self.stiffness = stiffness
        self.iters = iters
        self.radius = radius
        self.gs = gravity_scale
        self.drag = drag

    def step(self, root, root_dir=None, wind=None, colliders=(), dt=DT):
        p, pp = self.p, self.pp
        vel = (p - pp) * (1 - self.damping)
        acc = G * self.gs
        if wind is not None:
            w = np.asarray(wind, np.float64)
            # wind acts on relative velocity (drag-like) so strands stream with it
            acc = acc + (w - vel / dt) * self.drag
        new = p + vel + acc * dt * dt
        new[0] = root
        if root_dir is not None:
            # second point is pulled toward the root direction (hair grows out of the scalp)
            rd = np.asarray(root_dir, np.float64)
            new[1] = new[1] * 0.4 + (root + rd * self.seg[0]) * 0.6
        self.pp = p
        self.p = new
        for _ in range(self.iters):
            self._constrain(root, colliders)

    def _constrain(self, root, colliders):
        p = self.p
        p[0] = root
        for i in range(self.n - 1):
            a, b = p[i], p[i + 1]
            d = b - a
            L = math.sqrt(d @ d) + 1e-9
            diff = (L - self.seg[i]) / L
            if i == 0:
                p[i + 1] = b - d * diff
            else:
                p[i] = a + d * diff * 0.5
                p[i + 1] = b - d * diff * 0.5
        # bending stiffness: pull i+1 toward the midpoint of i and i+2
        if self.stiffness > 0:
            for i in range(1, self.n - 1):
                mid = (p[i - 1] + p[i + 1]) * 0.5
                p[i] = p[i] + (mid - p[i]) * self.stiffness * 0.5
        for (c, r) in colliders:
            d = p - c
            dist = np.sqrt(np.sum(d * d, axis=1)) + 1e-9
            rr = r + self.radius
            inside = dist < rr
            if np.any(inside):
                p[inside] = c + d[inside] / dist[inside, None] * rr
        p[0] = root


class SkirtRing:
    """Hem ring attached to a waist ellipse; hem points keep their distance from the waist (cloth length)
    and a minimum flare angle, and are pushed out by the thighs."""

    def __init__(self, n=18, length=46.0, flare=0.34, damping=0.08):
        self.n = n
        self.length = length
        self.flare = flare
        self.damping = damping
        self.p = None
        self.pp = None

    def waist_points(self, center, R, rx=14.5, rz=10.5):
        ang = np.linspace(0, 2 * math.pi, self.n, endpoint=False)
        local = np.stack([np.sin(ang) * rx, np.zeros_like(ang), np.cos(ang) * rz], axis=1)
        return center + local @ R.T, ang

    def init(self, center, R):
        w, ang = self.waist_points(center, R)
        down = -R[:, 1]
        out = (w - center)
        out = out / (np.linalg.norm(out, axis=1, keepdims=True) + 1e-9)
        self.p = w + (down * math.cos(self.flare) + out * math.sin(self.flare)) * self.length
        self.pp = self.p.copy()

    def step(self, center, R, thighs=(), wind=None, dt=DT):
        if self.p is None:
            self.init(center, R)
        w, ang = self.waist_points(center, R)
        vel = (self.p - self.pp) * (1 - self.damping)
        acc = G * 0.9
        if wind is not None:
            acc = acc + (np.asarray(wind) - vel / dt) * 0.6
        new = self.p + vel + acc * dt * dt
        self.pp = self.p
        self.p = new
        down = -R[:, 1]
        for _ in range(5):
            # length constraint (max) from waist
            d = self.p - w
            L = np.linalg.norm(d, axis=1, keepdims=True) + 1e-9
            over = np.maximum(L - self.length, 0)
            self.p -= d / L * over
            under = np.maximum(self.length * 0.94 - L, 0)
            self.p += d / L * under * 0.5
            # minimum flare: keep each hem point outside a cone around the body axis
            rel = self.p - center
            h = rel @ down
            radial = rel - np.outer(h, down)
            rlen = np.linalg.norm(radial, axis=1) + 1e-9
            need = 13.0 + np.maximum(h, 0) * math.tan(self.flare * 0.65)
            fix = rlen < need
            if np.any(fix):
                self.p[fix] = center + np.outer(h[fix], down) + radial[fix] / rlen[fix, None] * need[fix, None]
            # neighbours (circumference)
            nb = np.roll(self.p, -1, axis=0)
            d = nb - self.p
            L = np.linalg.norm(d, axis=1, keepdims=True) + 1e-9
            target = 2 * math.pi * (16.5 + self.length * math.sin(self.flare)) / self.n
            corr = d / L * (L - target) * 0.25
            corr = np.where(L > target, corr, corr * 0.2)
            self.p += corr
            self.p -= np.roll(corr, 1, axis=0)
            # thigh capsules push the cloth out
            for (a, b, r) in thighs:
                ab = b - a
                t = np.clip(((self.p - a) @ ab) / (ab @ ab + 1e-9), 0, 1)
                closest = a + np.outer(t, ab)
                d = self.p - closest
                dist = np.linalg.norm(d, axis=1) + 1e-9
                inside = dist < r + 1.5
                if np.any(inside):
                    self.p[inside] = closest[inside] + d[inside] / dist[inside, None] * (r + 1.5)
        return w


class Sim:
    """Runs a shot's secondary motion; `rig_at(t)` must return the driver state for time t."""

    def __init__(self, rig_at, t0, setup, preroll=1.0):
        self.rig_at = rig_at
        self.t0 = t0
        self.setup = setup
        self.preroll = preroll
        self.cache = {}
        self.state = None
        self.t_sim = None

    def at(self, t):
        key = round(t * 240) / 240
        if key in self.cache:
            return self.cache[key]
        if self.state is None or self.t_sim is None or key < self.t_sim:
            self.state = self.setup(self.rig_at(self.t0 - self.preroll))
            self.t_sim = self.t0 - self.preroll
        while self.t_sim < key - 1e-9:
            tt = self.t_sim + DT
            drv = self.rig_at(tt)
            self.state["step"](self.state, drv, DT)
            self.t_sim = tt
        snap = self.state["snap"](self.state)
        self.cache[key] = snap
        if len(self.cache) > 4000:
            self.cache.clear()
        return snap
