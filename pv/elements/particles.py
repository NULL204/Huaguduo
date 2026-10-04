"""Deterministic (closed-form in time) particle systems."""
import math

import numpy as np
import skia

from .. import config
from ..core import gfx
from ..core.noise import noise1
from . import style as S

W, H = config.W, config.H


class Field:
    """Base: N particles with per-particle random attributes, positions as a function of t."""

    def __init__(self, n, seed=0, area=(-80, -80, W + 80, H + 80)):
        self.n = n
        self.seed = seed
        self.area = area
        r = np.random.default_rng(seed)
        x0, y0, x1, y1 = area
        self.x0 = r.uniform(x0, x1, n)
        self.y0 = r.uniform(y0, y1, n)
        self.z = r.uniform(0, 1, n) ** 1.6          # depth: 0 far .. 1 near
        self.ph = r.uniform(0, 2 * math.pi, n)
        self.fr = r.uniform(0.4, 1.4, n)
        self.rnd = r.uniform(0, 1, n)

    def wrap(self, x, y):
        x0, y0, x1, y1 = self.area
        return (x - x0) % (x1 - x0) + x0, (y - y0) % (y1 - y0) + y0


def draw_snow(canvas, t, n=320, seed=0, wind=30.0, fall=(40, 160), size=(1.2, 6.0), alpha=0.95,
              color=S.SNOW, blur_near=True, gust=0.0, field=None, count=1.0, blend=None, dir_y=1.0):
    f = field or _snow_fields.setdefault((n, seed), Field(n, seed))
    v = fall[0] + (fall[1] - fall[0]) * f.z
    sz = size[0] + (size[1] - size[0]) * f.z
    sway = 18 * f.fr * (0.4 + f.z)
    gx = gust * 120 * np.sin(t * 0.7 + f.rnd * 2)
    x = f.x0 + (wind * (0.5 + f.z)) * t + sway * np.sin(t * f.fr + f.ph) + gx * f.z
    y = f.y0 + v * t * dir_y
    x, y = f.wrap(x, y)
    m = int(f.n * max(0.0, min(1.0, count)))
    buckets = [(0.0, 0.45, 0.0), (0.45, 0.8, 0.8), (0.8, 1.01, 2.6)]
    for lo, hi, bl in buckets:
        p = skia.Path()
        idx = np.where((f.z[:m] >= lo) & (f.z[:m] < hi))[0]
        for i in idx:
            p.addCircle(float(x[i]), float(y[i]), float(sz[i]))
        a = alpha * (0.55 + 0.45 * (lo + hi) / 2)
        canvas.drawPath(p, gfx.paint(color, a, blur=(bl * (sz.mean() / 3) if blur_near else 0), blend=blend))


_snow_fields = {}


def draw_petals(canvas, t, n=60, seed=1, wind=60.0, fall=(30, 90), size=(6, 16), alpha=0.9,
                color=S.ROUGE, color2=S.ROUGE_DEEP, area=None, count=1.0, rise=False, blend=None,
                spin=1.0, outline=False):
    key = (n, seed, area)
    f = _petal_fields.get(key)
    if f is None:
        f = Field(n, seed, area or (-80, -80, W + 80, H + 80))
        _petal_fields[key] = f
    v = fall[0] + (fall[1] - fall[0]) * f.z
    sz = size[0] + (size[1] - size[0]) * f.z
    x = f.x0 + wind * (0.4 + f.z) * t + 30 * np.sin(t * f.fr * 0.8 + f.ph)
    y = f.y0 + (-1 if rise else 1) * v * t + 10 * np.sin(t * f.fr * 1.7 + f.ph)
    x, y = f.wrap(x, y)
    m = int(f.n * max(0.0, min(1.0, count)))
    for i in range(m):
        ang = (t * (0.8 + f.fr[i]) * spin + f.ph[i]) % (2 * math.pi)
        flip = abs(math.sin(t * f.fr[i] * 2.1 * spin + f.ph[i]))
        canvas.save()
        canvas.translate(float(x[i]), float(y[i]))
        canvas.rotate(math.degrees(ang))
        canvas.scale(1.0, 0.25 + 0.75 * flip)
        s = float(sz[i])
        p = gfx.smooth_path([(-s, 0), (-s * 0.3, -s * 0.55), (s * 0.7, -s * 0.45), (s, 0), (s * 0.6, s * 0.5), (-s * 0.4, s * 0.5)], closed=True)
        col = color if f.rnd[i] > 0.35 else color2
        canvas.drawPath(p, gfx.paint(col, alpha * (0.6 + 0.4 * f.z[i]), blur=1.5 * (f.z[i] > 0.85), blend=blend))
        if outline:
            canvas.drawPath(p, gfx.paint(S.INK, alpha * 0.8, stroke=1.0))
        canvas.restore()


_petal_fields = {}


def draw_dust(canvas, t, n=90, seed=3, alpha=0.5, color=(255, 236, 200), size=(0.8, 2.6), blend=gfx.SCREEN,
              area=None, speed=1.0):
    key = (n, seed, area)
    f = _dust_fields.get(key)
    if f is None:
        f = Field(n, seed, area or (0, 0, W, H))
        _dust_fields[key] = f
    p_near = skia.Path()
    p_far = skia.Path()
    for i in range(f.n):
        x = f.x0[i] + 40 * noise1(t * 0.12 * speed * f.fr[i] + i * 3.1, seed) + 8 * t * speed
        y = f.y0[i] + 40 * noise1(t * 0.10 * speed * f.fr[i] + i * 1.7, seed + 1) - 6 * t * speed
        x, y = f.wrap(x, y)
        s = size[0] + (size[1] - size[0]) * f.z[i]
        tw = 0.5 + 0.5 * math.sin(t * 2.0 * f.fr[i] + f.ph[i])
        (p_near if f.z[i] > 0.6 else p_far).addCircle(float(x), float(y), float(s * (0.7 + 0.5 * tw)))
    canvas.drawPath(p_far, gfx.paint(color, alpha * 0.6, blur=0.6, blend=blend))
    canvas.drawPath(p_near, gfx.paint(color, alpha, blur=1.6, blend=blend))


_dust_fields = {}


def draw_embers(canvas, t, n=60, seed=5, alpha=0.9, color=(255, 120, 70), area=None, rise=120.0, size=(1.0, 3.5),
                blend=gfx.SCREEN, count=1.0):
    key = (n, seed, area)
    f = _ember_fields.get(key)
    if f is None:
        f = Field(n, seed, area or (-40, -40, W + 40, H + 40))
        _ember_fields[key] = f
    m = int(f.n * max(0.0, min(1.0, count)))
    p = skia.Path()
    pg = skia.Path()
    for i in range(m):
        x = f.x0[i] + 30 * math.sin(t * f.fr[i] + f.ph[i]) + 20 * noise1(t * 0.5 + i, seed)
        y = f.y0[i] - rise * (0.5 + f.z[i]) * t
        x, y = f.wrap(x, y)
        s = size[0] + (size[1] - size[0]) * f.z[i]
        fl = 0.6 + 0.4 * math.sin(t * 9 * f.fr[i] + f.ph[i])
        p.addCircle(float(x), float(y), float(s * fl))
        pg.addCircle(float(x), float(y), float(s * 3.5 * fl))
    canvas.drawPath(pg, gfx.paint(color, alpha * 0.25, blur=6, blend=blend))
    canvas.drawPath(p, gfx.paint((255, 220, 180), alpha, blur=0.5, blend=blend))


_ember_fields = {}


def draw_burst(canvas, t, t0, cx, cy, n=40, seed=7, speed=(200, 700), size=(2, 9), color=S.ROUGE,
               gravity=900.0, life=1.4, alpha=1.0, drag=1.8, blend=None, spread=(0, 2 * math.pi)):
    """Radial droplet burst at time t0 (ballistic with drag)."""
    dt = t - t0
    if dt < 0 or dt > life:
        return
    r = np.random.default_rng(seed)
    ang = r.uniform(spread[0], spread[1], n)
    sp = r.uniform(speed[0], speed[1], n)
    sz = r.uniform(size[0], size[1], n)
    k = (1 - math.exp(-drag * dt)) / drag
    fade = 1 - (dt / life) ** 2
    for i in range(n):
        x = cx + math.cos(ang[i]) * sp[i] * k
        y = cy + math.sin(ang[i]) * sp[i] * k + 0.5 * gravity * dt * dt * 0.6
        vx = math.cos(ang[i]) * sp[i] * math.exp(-drag * dt)
        vy = math.sin(ang[i]) * sp[i] * math.exp(-drag * dt) + gravity * dt * 0.6
        L = min(40, math.hypot(vx, vy) * 0.02)
        a = math.atan2(vy, vx)
        canvas.save()
        canvas.translate(x, y)
        canvas.rotate(math.degrees(a))
        s = float(sz[i]) * (1 - 0.5 * dt / life)
        canvas.drawPath(gfx.ellipse(-L / 2, 0, s + L / 2, s), gfx.paint(color, alpha * fade, blend=blend))
        canvas.restore()
