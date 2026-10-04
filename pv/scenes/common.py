"""Shared stage helpers for scenes."""
import math

import numpy as np
import skia

from .. import config
from ..core import gfx, audio
from ..core import easing as E
from ..core.frame import Scene, FrameCtx
from ..core.camera import Cam
from ..core.noise import noise1, fbm1, hash01, RNG
from ..elements import style as S

W, H = config.W, config.H

LIGHTS = {
    # warm oil lamp behind the screen
    "warm": dict(cx=0.5, cy=0.42, radius=1.15, power=1.25, edge=0.32, warm=1.0),
    "soft": dict(cx=0.5, cy=0.45, radius=1.6, power=1.0, edge=0.62, warm=0.55),
    "spot": dict(cx=0.5, cy=0.45, radius=0.72, power=1.7, edge=0.06, warm=1.2),
    "low": dict(cx=0.5, cy=0.62, radius=0.9, power=1.5, edge=0.1, warm=1.3),
    "cold": dict(cx=0.5, cy=0.35, radius=1.3, power=1.1, edge=0.35, warm=0.2,
                 paper=(0.80, 0.86, 0.96)),
    "night": dict(cx=0.5, cy=0.4, radius=1.0, power=1.4, edge=0.12, warm=0.3,
                  paper=(0.55, 0.62, 0.78)),
    "spring": dict(cx=0.5, cy=0.4, radius=1.5, power=1.0, edge=0.6, warm=0.4,
                   paper=(0.99, 0.97, 0.90)),
    "paper": dict(cx=0.5, cy=0.5, radius=1.8, power=1.0, edge=0.78, warm=0.35,
                  paper=(0.96, 0.92, 0.84)),
    "white": dict(cx=0.5, cy=0.45, radius=1.8, power=0.9, edge=0.8, warm=0.15,
                  paper=(0.98, 0.98, 0.97)),
    "red": dict(cx=0.5, cy=0.45, radius=1.1, power=1.2, edge=0.25, warm=1.0,
                paper=(1.0, 0.62, 0.55)),
}


def flicker(t, amt=1.0, seed=0):
    f = 1.0 + amt * (0.018 * noise1(t * 7.3, seed) + 0.012 * noise1(t * 19.1, seed + 1))
    return f


def stage_light(fr, preset="warm", t=0.0, flick=1.0, boost=0.0, **over):
    kw = dict(LIGHTS[preset])
    kw.update(over)
    f = flicker(t, flick) * (1.0 + boost)
    fr.light(flicker=f, **kw)


def ground(canvas, y, color=S.INK, alpha=1.0, seed=0, style="grass", x0=-200, x1=W + 200, height=60, t=0.0):
    """Stage floor: a carved strip with grass tufts or a stone edge."""
    rng = RNG(seed)
    pts = [(x0, y)]
    x = x0
    while x < x1:
        x += rng.u(30, 70)
        pts.append((x, y + rng.n(0, 3)))
    pts += [(x1, y + height + 400), (x0, y + height + 400)]
    canvas.drawPath(gfx.poly(pts), gfx.paint(color, alpha))
    if style == "grass":
        p = skia.Path()
        for k in range(int((x1 - x0) / 9)):
            gx = x0 + k * 9 + rng.u(-4, 4)
            gh = rng.u(8, 28)
            lean = rng.n(0, 5) + 4 * noise1(t * 0.7 + gx * 0.01, seed)
            p.moveTo(gx - 2.5, y + 2)
            p.quadTo(gx + lean * 0.4, y - gh * 0.6, gx + lean, y - gh)
            p.quadTo(gx + lean * 0.3 + 1, y - gh * 0.5, gx + 2.5, y + 2)
            p.close()
        canvas.drawPath(p, gfx.paint(color, alpha))
    # carved band in the floor
    cut = skia.Path()
    for k in range(int((x1 - x0) / 46)):
        cx = x0 + k * 46 + 23
        cut.addCircle(cx, y + height * 0.5, 7)
    canvas.drawPath(cut, gfx.paint((236, 220, 190), alpha * 0.55, blend=gfx.SCREEN))


def lerp_pos(a, b, k):
    return (a[0] + (b[0] - a[0]) * k, a[1] + (b[1] - a[1]) * k)


def shake_amt(t, decay=0.25, every=2, offset=0):
    return audio.beat_pulse(t, decay=decay, every=every, offset=offset)


class Stage(Scene):
    """Scene whose draw() paints transmittance onto white, then applies the lamp."""
    light = "warm"

    def light_params(self, t, lt, u):
        return {}

    def draw(self, fr, t, lt, u):
        pp = self.paint(fr, t, lt, u) or {}
        over = self.light_params(t, lt, u)
        preset = over.pop("preset", self.light)
        stage_light(fr, preset, t, **over)
        extra = self.after_light(fr, t, lt, u)
        if extra:
            pp.update(extra)
        return pp

    def paint(self, fr, t, lt, u):
        raise NotImplementedError

    def after_light(self, fr, t, lt, u):
        return None
