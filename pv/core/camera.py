"""2D virtual camera with zoom/rotation/shake and parallax helpers."""
import math

import skia

from .. import config
from .noise import fbm1

W, H = config.W, config.H


class Cam:
    def __init__(self, x=W / 2, y=H / 2, zoom=1.0, rot=0.0, shake=0.0, t=0.0, seed=0):
        self.x, self.y, self.zoom, self.rot = x, y, zoom, rot
        self.shake = shake
        self.t = t
        self.seed = seed

    def matrix(self, depth=1.0):
        """World->screen.  depth<1 moves slower (background), >1 faster (foreground)."""
        sx = self.shake * fbm1(self.t * 7.0, self.seed + 1, 2) * 18
        sy = self.shake * fbm1(self.t * 7.0, self.seed + 2, 2) * 18
        sr = self.shake * fbm1(self.t * 5.0, self.seed + 3, 2) * 0.012
        z = 1 + (self.zoom - 1) * depth
        cx = W / 2 + (self.x - W / 2) * depth
        cy = H / 2 + (self.y - H / 2) * depth
        m = skia.Matrix()
        m.setTranslate(W / 2 + sx * depth, H / 2 + sy * depth)
        m.preRotate(math.degrees((self.rot + sr) * min(1.0, depth)))
        m.preScale(z, z)
        m.preTranslate(-cx, -cy)
        return m

    def apply(self, canvas, depth=1.0):
        canvas.concat(self.matrix(depth))

    def to_screen(self, x, y, depth=1.0):
        p = self.matrix(depth).mapXY(x, y)
        return p.x(), p.y()
