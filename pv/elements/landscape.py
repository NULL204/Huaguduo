"""Ink-wash mountains and mist."""
import math

import numpy as np
import skia

from .. import config
from ..core import gfx
from ..core import textures as TX
from ..core.noise import fbm1_np, noise1, RNG
from . import style as S

W, H = config.W, config.H


class Mountains:
    def __init__(self, seed=0, base=760, height=380, freq=0.0026, sharp=1.6, x0=-400, x1=W + 400, step=6):
        self.seed = seed
        xs = np.arange(x0, x1 + step, step, dtype=np.float64)
        n = fbm1_np(xs * freq, seed, 5)
        n2 = fbm1_np(xs * freq * 0.35, seed + 7, 2)
        h = (0.55 + 0.45 * n) * (0.6 + 0.4 * n2)
        h = np.clip(h, 0, None) ** sharp
        h = h / (h.max() + 1e-6)
        self.xs = xs
        self.ridge = base - height * h
        self.base = base
        self.height = height
        # cun-strokes (皴): short strokes down the slopes
        rng = RNG(seed + 3)
        self.strokes = []
        for k in range(int(len(xs) * 0.6)):
            i = int(rng.i(1, len(xs) - 1))
            x = xs[i]
            y = self.ridge[i] + rng.u(4, 60)
            slope = (self.ridge[i + 1] - self.ridge[i - 1]) / (2 * step)
            L = rng.u(14, 50)
            a = math.atan2(1, -slope * 0.8) if abs(slope) > 0.05 else math.pi / 2
            self.strokes.append((x, y, a, L, rng.u(0.3, 1.0)))

    def path(self, dx=0.0, bottom=None):
        bottom = bottom if bottom is not None else H + 50
        pts = [(float(x + dx), float(y)) for x, y in zip(self.xs, self.ridge)]
        pts = pts + [(pts[-1][0], bottom), (pts[0][0], bottom)]
        return gfx.poly(pts, True)

    def draw(self, canvas, dx=0.0, tone=S.INK, alpha=0.8, blur=2.0, mist=0.6, fade_h=None, cun=True,
             snow=0.0):
        p = self.path(dx)
        top = float(self.ridge.min())
        fh = fade_h if fade_h is not None else self.height * 1.1
        sh = gfx.linear_grad(0, top, 0, top + fh, [tone + (int(255 * alpha),), tone + (int(255 * alpha * (1 - mist)),)])
        canvas.drawPath(p, gfx.paint((255, 255, 255), 1.0, blur=blur, shader=sh))
        # darker ridge line (pooled ink)
        ridge = gfx.poly([(float(x + dx), float(y)) for x, y in zip(self.xs, self.ridge)], closed=False)
        canvas.drawPath(ridge, gfx.paint(tone, alpha * 0.8, stroke=2.5, blur=blur * 0.8 + 0.8))
        if cun:
            pa = skia.Path()
            for x, y, a, L, w in self.strokes:
                pa.moveTo(x + dx, y)
                pa.lineTo(x + dx + math.cos(a) * L, y + math.sin(a) * L)
            canvas.drawPath(pa, gfx.paint(tone, alpha * 0.35, stroke=1.6, blur=blur * 0.5 + 0.5))
        if snow > 0:
            # white caps along the ridge
            caps = []
            for x, y in zip(self.xs, self.ridge):
                caps.append((float(x + dx), float(y)))
            for x, y in zip(self.xs[::-1], self.ridge[::-1]):
                caps.append((float(x + dx), float(y + 18 + 14 * noise1(x * 0.02, self.seed))))
            canvas.drawPath(gfx.poly(caps, True), gfx.paint(S.SNOW, snow, blur=3))


def draw_mist(canvas, y, h, t=0.0, color=S.PAPER, alpha=0.7, seed=0, speed=12.0):
    for k in range(5):
        yy = y + (k - 2) * h * 0.25 + 10 * noise1(t * 0.1 + k, seed)
        x = (t * speed * (0.6 + 0.2 * k) + k * 400) % (W + 1200) - 600
        canvas.drawPath(gfx.ellipse(x, yy, 700, h * 0.35), gfx.paint(color, alpha * 0.45, blur=h * 0.25))
        canvas.drawPath(gfx.ellipse(x + 900, yy + 20, 600, h * 0.3), gfx.paint(color, alpha * 0.35, blur=h * 0.25))
