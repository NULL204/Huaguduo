"""Effects: ink splash, seal stamp, frost, cracks, holes, ink blots, rays."""
import math

import cv2
import numpy as np
import skia

from .. import config
from ..core import gfx
from ..core import easing as E
from ..core import text as TXT
from ..core import textures as TX
from ..core.noise import noise1, RNG, hash01
from . import style as S

W, H = config.W, config.H


def splash_path(cx, cy, r, seed=0, spikes=14, spike_len=0.8, growth=1.0, wobble=0.18):
    """Ink/rouge splat: a lumpy core with tapering radial spikes."""
    rng = RNG(seed)
    g = E.out_expo(growth)
    core = gfx.blob(cx, cy, r * (0.35 + 0.65 * g), wobble, seed=seed, n=28)
    p = skia.Path(core)
    for k in range(spikes):
        a = rng.u(0, 2 * math.pi)
        L = r * (1 + rng.u(0.2, 1.0) * spike_len) * g
        w = r * rng.u(0.06, 0.16)
        bx, by = cx + math.cos(a) * r * 0.5 * g, cy + math.sin(a) * r * 0.5 * g
        ex, ey = cx + math.cos(a) * L, cy + math.sin(a) * L
        nx, ny = -math.sin(a), math.cos(a)
        spike = gfx.smooth_path([(bx + nx * w, by + ny * w), ((bx + ex) / 2 + nx * w * 0.4, (by + ey) / 2 + ny * w * 0.4),
                                 (ex, ey), ((bx + ex) / 2 - nx * w * 0.4, (by + ey) / 2 - ny * w * 0.4), (bx - nx * w, by - ny * w)], closed=True)
        p = gfx.op(p, spike, "union")
        # droplet at the end
        dr = w * rng.u(0.6, 1.4)
        dd = L * rng.u(1.05, 1.35)
        p.addCircle(cx + math.cos(a) * dd, cy + math.sin(a) * dd, dr * g)
    return p


def draw_splash(canvas, cx, cy, r, color=S.ROUGE, growth=1.0, seed=0, alpha=1.0, blend=None, edge=True,
                spikes=14, spike_len=0.8):
    p = splash_path(cx, cy, r, seed, spikes, spike_len, growth)
    canvas.drawPath(p, gfx.paint(color, alpha * 0.35, blur=r * 0.06, blend=blend))
    canvas.drawPath(p, gfx.paint(color, alpha * 0.92, blur=1.0, blend=blend))
    if edge:
        # pooled darker rim, like wet pigment drying
        deep = tuple(max(0, int(c * 0.6)) for c in color)
        canvas.drawPath(p, gfx.paint(deep, alpha * 0.5, stroke=max(1.5, r * 0.025), blur=r * 0.02, blend=blend))


def draw_seal(canvas, x, y, size, chars, t_stamp=None, t=0.0, color=S.ROUGE, style="zhu", rot=-0.03,
              alpha=1.0, face="serif_black", seed=3):
    """Red seal (印章).  style 'zhu' (red characters) or 'bai' (white characters on red).
    chars laid out in 1 or 2 columns, right-to-left."""
    k = 1.0
    sc = 1.0
    if t_stamp is not None:
        dt = t - t_stamp
        if dt < -0.12:
            return
        k = E.clamp((dt + 0.12) / 0.12)
        sc = 1.0 + 0.6 * (1 - E.out_cubic(k))
    canvas.save()
    canvas.translate(x, y)
    canvas.rotate(math.degrees(rot))
    canvas.scale(sc, sc)
    a = alpha * k
    s = size
    box = gfx.rough(gfx.rect(-s / 2, -s / 2, s, s), seg=5, dev=s * 0.012, seed=seed)
    n = len(chars)
    cols = 1 if n <= 2 else 2
    rows = int(math.ceil(n / cols))
    cs = s * 0.84 / max(rows, cols)
    txt = skia.Path()
    for i, ch in enumerate(chars):
        col = i // rows
        row = i % rows
        cx = (s * 0.42 - cs * (col + 0.5)) if cols == 2 else 0
        cy = -s * 0.42 + cs * (row + 0.5)
        gp = TXT.glyph_path(face, ch)
        if gp is None:
            continue
        m = skia.Matrix()
        f = cs / 100.0 * (0.98 if cols == 2 else 1.0)
        fy = f
        if n == 3 and col == 1:
            # 3-character seal: the lone left character is stretched to the full height
            cy = 0.0
            fy = f * 1.9
        m.setScaleTranslate(f, fy, cx - 50 * f, cy + 38 * fy - (12 * fy if n == 3 and col == 1 else 0))
        q = skia.Path(gp)
        q.transform(m)
        txt.addPath(q)
    tex = TX.ink_shader(scale=0.35, seed=19, lo=0.0, hi=0.22)
    cf = skia.ColorFilters.Blend(gfx.C(*color, 255), skia.BlendMode.kSrcIn)
    if style == "bai":
        shape = gfx.op(box, txt, "diff")
        inner = gfx.op(shape, gfx.rect(-s / 2 + s * 0.04, -s / 2 + s * 0.04, s * 0.92, s * 0.92), "inter")
        canvas.drawPath(shape, gfx.paint(color, a * 0.95, shader=tex, color_filter=cf))
    else:
        frame = gfx.op(box, gfx.rect(-s / 2 + s * 0.07, -s / 2 + s * 0.07, s * 0.86, s * 0.86), "diff")
        canvas.drawPath(frame, gfx.paint(color, a * 0.95, shader=tex, color_filter=cf))
        canvas.drawPath(txt, gfx.paint(color, a * 0.95, shader=tex, color_filter=cf))
    canvas.restore()


class Frost:
    """Dendritic frost growing in from the frame edges."""

    def __init__(self, seed=0, n=26, length=(120, 320)):
        rng = RNG(seed)
        self.branches = []
        for i in range(n):
            side = i % 4
            u = rng.u(0, 1)
            if side == 0:
                x, y, a = u * W, -5, math.pi / 2
            elif side == 1:
                x, y, a = W + 5, u * H, math.pi
            elif side == 2:
                x, y, a = u * W, H + 5, -math.pi / 2
            else:
                x, y, a = -5, u * H, 0.0
            a += rng.n(0, 0.35)
            self._grow(rng, x, y, a, rng.u(*length), 3, 0.0, 1.0)

    def _grow(self, rng, x, y, a, L, depth, t0, dur):
        n = max(3, int(L / 14))
        pts = [(x, y)]
        for i in range(n):
            a += rng.n(0, 0.08)
            x += math.cos(a) * L / n
            y += math.sin(a) * L / n
            pts.append((x, y))
        self.branches.append((pts, t0, dur, depth))
        if depth > 0:
            for k in range(1, n, 2):
                for side in (-1, 1):
                    if rng.u() < 0.8:
                        u = k / n
                        bx, by = pts[k]
                        self._grow(rng, bx, by, a + side * math.radians(60 + rng.n(0, 6)), L * 0.32 * (1 - u * 0.5),
                                   depth - 1, t0 + dur * u, dur * 0.5)

    def draw(self, canvas, growth, color=(236, 244, 255), alpha=0.85, width=1.6):
        for pts, t0, dur, depth in self.branches:
            g = E.clamp((growth - t0) / dur)
            if g <= 0:
                continue
            seg = gfx.polyline_cut(pts, g)
            canvas.drawPath(gfx.poly(seg, closed=False), gfx.paint(color, alpha * (0.5 + 0.15 * depth), stroke=width * (0.6 + 0.4 * depth)))
            canvas.drawPath(gfx.poly(seg, closed=False), gfx.paint(color, alpha * 0.25, stroke=width * 4, blur=3))


class Cracks:
    """Branching crack lines radiating from a point."""

    def __init__(self, cx, cy, seed=0, n=9, length=(250, 700)):
        rng = RNG(seed)
        self.lines = []
        for i in range(n):
            a = 2 * math.pi * i / n + rng.n(0, 0.25)
            self._grow(rng, cx, cy, a, rng.u(*length), 2, 0.0, 1.0)

    def _grow(self, rng, x, y, a, L, depth, t0, dur):
        n = max(3, int(L / 22))
        pts = [(x, y)]
        for i in range(n):
            a += rng.n(0, 0.28)
            x += math.cos(a) * L / n
            y += math.sin(a) * L / n
            pts.append((x, y))
        self.lines.append((pts, t0, dur, depth))
        if depth > 0:
            for k in range(2, n, 3):
                if rng.u() < 0.6:
                    bx, by = pts[k]
                    self._grow(rng, bx, by, a + rng.choice([-1, 1]) * rng.u(0.4, 1.0), L * 0.4, depth - 1, t0 + dur * k / n, dur * 0.5)

    def draw(self, canvas, growth, color=S.INK, alpha=1.0, width=3.0, glow=None):
        for pts, t0, dur, depth in self.lines:
            g = E.clamp((growth - t0) / dur)
            if g <= 0:
                continue
            seg = gfx.polyline_cut(pts, g)
            path = gfx.poly(seg, closed=False)
            if glow is not None:
                canvas.drawPath(path, gfx.paint(glow, alpha * 0.5, stroke=width * 4, blur=width * 2))
            canvas.drawPath(path, gfx.paint(color, alpha, stroke=width * (0.4 + 0.3 * depth), join="miter"))


class Holes:
    """Silverfish-eaten holes: each eater walks a path; the eaten area grows along it over time."""

    def __init__(self, seed=0, n=14, t_start=0.0, t_end=4.0, speed=(140, 260)):
        rng = RNG(seed)
        self.eaters = []
        for i in range(n):
            x, y = rng.u(0.05, 0.95) * W, rng.u(0.05, 0.95) * H
            a = rng.u(0, 2 * math.pi)
            ts = t_start + rng.u(0, 0.45) * (t_end - t_start)
            sp = rng.u(*speed)
            pts = [(x, y)]
            for k in range(160):
                a += rng.n(0, 0.35) + 0.15 * math.sin(k * 0.2 + i)
                x += math.cos(a) * 12
                y += math.sin(a) * 12
                x = min(max(x, -40), W + 40)
                y = min(max(y, -40), H + 40)
                pts.append((x, y))
            self.eaters.append(dict(pts=pts, ts=ts, sp=sp, r0=rng.u(6, 14), seed=i))

    def state(self, t):
        """List of (eaten polyline, radius, head position, head angle) at time t."""
        out = []
        for e in self.eaters:
            dt = t - e["ts"]
            if dt <= 0:
                continue
            L = dt * e["sp"]
            pts = e["pts"]
            n = min(len(pts) - 1, int(L / 12))
            path = pts[:n + 1]
            if len(path) < 2:
                path = [pts[0], pts[1]]
            hx, hy = path[-1]
            px, py = path[-2]
            r = e["r0"] + 5 * dt
            out.append((path, r, (hx, hy), math.atan2(hy - py, hx - px), e["seed"]))
        return out

    def mask_path(self, t):
        p = skia.Path()
        for path, r, head, ang, sd in self.state(t):
            # ragged tube along the eaten path, thicker where it has been eaten longer
            n = len(path)
            for i in range(0, n, 2):
                age = (n - i) / max(1, n)
                rr = r * (0.35 + 0.65 * age)
                x, y = path[i]
                p.addCircle(x + 3 * noise1(i * 0.7, sd), y + 3 * noise1(i * 0.9, sd + 3), max(2.0, rr))
        return p


def ink_blot(canvas, cx, cy, r, color=S.INK, alpha=1.0, seed=0, t=0.0, growth=1.0, blur=None):
    p = gfx.blob(cx, cy, r * E.out_cubic(growth), 0.22, seed=seed, n=26, t=t)
    canvas.drawPath(p, gfx.paint(color, alpha * 0.5, blur=(r * 0.12) if blur is None else blur))
    canvas.drawPath(p, gfx.paint(color, alpha * 0.85, blur=2))


def god_rays(canvas, cx, cy, n=14, length=1600, width=0.12, color=(255, 230, 190), alpha=0.25, t=0.0, seed=0):
    for k in range(n):
        a = 2 * math.pi * k / n + 0.3 * noise1(t * 0.2 + k, seed)
        w = width * (0.5 + 0.5 * hash01(k, seed))
        p = gfx.poly([(cx, cy), (cx + math.cos(a - w) * length, cy + math.sin(a - w) * length),
                      (cx + math.cos(a + w) * length, cy + math.sin(a + w) * length)])
        canvas.drawPath(p, gfx.paint(color, alpha * (0.4 + 0.6 * hash01(k + 9, seed)), blur=30, blend=gfx.SCREEN))
