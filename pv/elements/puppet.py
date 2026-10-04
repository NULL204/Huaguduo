"""Articulated shadow-puppet (皮影) rig and the original cast.

All characters are original designs for this fan PV:
  阿朵 (A-Duo)  — the flower-bud girl: poppy bud ornament, carved hollow face, red forehead mark,
                  translucent red-leather arms (her ideals) that drain to pale over the story.
  children      — two small puppets playing cat's cradle (one in red: her younger self).
  brides        — same frame as A-Duo, red veil, bloomed poppy, pale arms, empty face.
  husband       — tall hatted figure.

Coordinates: origin on the ground between the feet, facing +x, ~650 px tall at scale 1.
"""
import math

import numpy as np
import skia

from ..core import gfx
from ..core import easing as E
from ..core.noise import noise1, fbm1
from . import style as S
from .flower import draw_poppy_side

D2R = math.pi / 180


def mcopy(m):
    return skia.Matrix.Concat(m, skia.Matrix())


# ----------------------------------------------------------------------------- part shapes

def _cut_pattern_scales(x0, y0, x1, y1, r=7.0, gap=1.25):
    """Fish-scale arcs pattern (as thin crescent cut-outs) inside a rect."""
    p = skia.Path()
    row = 0
    y = y0
    while y < y1:
        off = (r * gap) if row % 2 else 0
        x = x0 + off
        while x < x1:
            outer = gfx.circle(x, y, r)
            inner = gfx.circle(x, y - r * 0.45, r * 0.85)
            p.addPath(gfx.op(outer, inner, "diff"))
            x += r * gap * 2
        y += r * 1.15
        row += 1
    return p


def _cut_clouds(cx, cy, s=1.0):
    """A ruyi cloud motif cut-out."""
    p = skia.Path()
    for dx, dy, r in ((0, 0, 7), (9, -3, 6), (-9, -3, 6), (4, 6, 4.5), (-4, 6, 4.5)):
        p = gfx.op(p, gfx.circle(cx + dx * s, cy + dy * s, r * s), "union")
    inner = skia.Path()
    for dx, dy, r in ((0, 0, 3.2), (9, -3, 2.6), (-9, -3, 2.6)):
        inner.addCircle(cx + dx * s, cy + dy * s, r * s)
    return gfx.op(p, inner, "diff")


def _slits(x, y0, y1, n, spread, w=2.4):
    p = skia.Path()
    for i in range(n):
        u = (i + 0.5) / n - 0.5
        xa = x + u * spread * 0.4
        xb = x + u * spread
        p.addPath(gfx.ribbon([(xa, y0), ((xa + xb) / 2, (y0 + y1) / 2), (xb, y1)], [0.5, w, 0.5]))
    return p


class Shapes:
    """Pre-built (cached) part paths for one body type."""
    _cache = {}

    @classmethod
    def get(cls, kind):
        if kind not in cls._cache:
            cls._cache[kind] = cls(kind)
        return cls._cache[kind]

    def __init__(self, kind):
        self.kind = kind
        if kind in ("woman", "bride"):
            self._woman(kind == "bride")
        elif kind == "child":
            self._child()
        elif kind == "man":
            self._man()

    # ------------------------------------------------------------------ woman / bride
    def _woman(self, bride):
        # skirt: local pivot at waist
        sk = gfx.smooth_path([(34, 0), (44, 80), (58, 200), (80, 300), (100, 348), (60, 356), (10, 352),
                              (-40, 356), (-90, 350), (-70, 290), (-52, 180), (-42, 80), (-34, 0)], closed=True)
        hem = gfx.op(sk, gfx.rect(-120, 300, 260, 70), "inter")
        cuts = skia.Path()
        cuts.addPath(_slits(4, 40, 285, 7, 110, 2.6))
        # band of scales above the hem
        band = gfx.op(_cut_pattern_scales(-90, 306, 104, 340, r=6.5), sk, "inter")
        cuts.addPath(band)
        for k, (cx, cy) in enumerate(((-12, 120), (22, 200), (-30, 230))):
            cuts.addPath(_cut_clouds(cx, cy, 1.15))
        self.skirt = gfx.op(sk, cuts, "diff")
        self.skirt_outline = sk
        # torso: pivot at waist
        to = gfx.smooth_path([(32, 4), (35, -30), (44, -72), (47, -90), (38, -110), (16, -128), (-4, -132),
                              (-22, -122), (-31, -86), (-33, -40), (-33, 4)], closed=True)
        tcut = skia.Path()
        # cross collar: a carved band from neck to waist-side
        collar = gfx.ribbon([(12, -126), (24, -90), (34, -50), (36, -16)], [5, 5, 5, 4])
        tcut.addPath(collar)
        tcut.addPath(_cut_clouds(-8, -70, 1.0))
        tcut.addPath(gfx.op(_cut_pattern_scales(-28, -46, 30, -18, r=5.0), to, "inter"))
        self.torso = gfx.op(to, tcut, "diff")
        self.torso_outline = to
        # belt (drawn red), pivot waist
        self.belt = gfx.smooth_path([(36, -16), (37, 2), (-34, 4), (-33, -14)], closed=True)
        # head: pivot at neck base
        neck = gfx.poly([(-7, 2), (9, 2), (11, -22), (-5, -24)])
        face_front = [(9, -22), (18, -30), (24, -37), (21, -41), (25, -45), (24, -51), (32, -59), (25, -70),
                      (27, -79), (23, -93), (15, -101)]
        skull_back = [(15, -101), (0, -113), (-20, -111), (-34, -94), (-32, -70), (-22, -50), (-6, -38), (9, -22)]
        self.face_outline = gfx.smooth_path(face_front, closed=False, tension=0.35)
        head_full = gfx.smooth_path(face_front + skull_back[1:], closed=True, tension=0.35)
        self.head_full = head_full
        hair = gfx.smooth_path([(17, -98), (22, -92), (12, -88), (4, -80), (-2, -68), (-10, -56), (-22, -48),
                                (-34, -58), (-40, -78), (-38, -100), (-24, -116), (-2, -118), (14, -108)], closed=True)
        bun = gfx.smooth_path([(-26, -112), (-34, -134), (-52, -138), (-64, -122), (-58, -104), (-40, -98)], closed=True)
        hair = gfx.op(hair, bun, "union")
        hair_cut = skia.Path()
        # fine comb-lines carved into the hair
        for i in range(6):
            a0 = -0.3 + i * 0.32
            hair_cut.addPath(gfx.ribbon(gfx.bezier_pts((-6 - i * 4, -112 + i * 2), (-20 - i * 3, -100), (-26 - i * 2, -82), (-22 - i * 2, -62), 10),
                                        [0.3, 1.4, 1.6, 1.4, 1.0, 0.8, 0.6, 0.5, 0.4, 0.3, 0.2]))
        hair_cut.addPath(gfx.ribbon(gfx.bezier_pts((-36, -130), (-46, -136), (-56, -128), (-58, -114), 8), [0.4, 1.4, 1.8, 1.8, 1.6, 1.2, 0.8, 0.5, 0.3]))
        self.hair = gfx.op(hair, hair_cut, "diff")
        self.neck = neck
        self.eye = gfx.smooth_path([(10, -66), (14, -69), (19, -67), (15, -64.5)], closed=True)
        self.brow = gfx.ribbon([(7, -73), (13, -76.5), (21, -75)], [0.6, 2.2, 0.6])
        self.mouth = gfx.ribbon([(19, -42), (22, -42.6)], [1.6, 0.8])
        self.bun_anchor = (-44, -136)
        self.crown = (-8, -116)
        self.huadian = (22.5, -85)
        self.hair_tail_root = (-30, -66)
        # arm segments (pivots at their top)
        self.upper = gfx.smooth_path([(-11, -4), (11, -4), (9, 60), (8, 104), (-7, 104), (-9, 60)], closed=True)
        self.fore = gfx.smooth_path([(-8, -3), (8, -3), (7, 50), (6, 96), (-5, 96), (-7, 50)], closed=True)
        self.sleeve_cap = gfx.smooth_path([(-15, -8), (16, -10), (17, 22), (8, 36), (-10, 34), (-16, 18)], closed=True)
        self.cuff = gfx.rect(-7.5, 78, 14.5, 9)
        # feet (pivot at ankle)
        self.foot = gfx.smooth_path([(-10, -8), (6, -10), (22, -6), (34, -1), (24, 2), (-10, 2)], closed=True)
        if bride:
            # cloud collar (云肩) over the shoulders, drawn on torso
            cc = gfx.smooth_path([(-30, -124), (30, -128), (52, -100), (40, -84), (22, -92), (6, -78),
                                  (-12, -90), (-30, -80), (-44, -98)], closed=True)
            cc_cut = skia.Path()
            for cx, cy in ((-20, -104), (4, -106), (28, -106)):
                cc_cut.addPath(_cut_clouds(cx, cy, 0.85))
            self.cloud_collar = gfx.op(cc, cc_cut, "diff")
            veil = gfx.smooth_path([(14, -122), (34, -112), (40, -80), (44, -44), (40, -14), (14, -8), (-14, -10),
                                    (-38, -14), (-44, -50), (-40, -94), (-20, -122)], closed=True)
            self.veil = veil

    # ------------------------------------------------------------------ child
    def _child(self):
        # proportions: ~330 px tall, bigger head
        self.skirt = gfx.smooth_path([(24, 0), (30, 50), (40, 108), (8, 112), (-36, 110), (-30, 50), (-24, 0)], closed=True)
        self.skirt_outline = self.skirt
        to = gfx.smooth_path([(24, 4), (28, -30), (30, -60), (12, -78), (-8, -80), (-24, -66), (-26, -30), (-24, 4)], closed=True)
        cut = skia.Path()
        cut.addPath(_cut_clouds(0, -36, 0.8))
        self.torso = gfx.op(to, cut, "diff")
        self.torso_outline = to
        self.belt = gfx.smooth_path([(27, -10), (28, 2), (-25, 4), (-25, -9)], closed=True)
        face_front = [(8, -16), (16, -24), (21, -30), (19, -34), (22, -38), (21, -44), (27, -50), (22, -60),
                      (24, -70), (20, -84), (12, -92)]
        skull_back = [(12, -92), (-4, -100), (-24, -96), (-38, -78), (-36, -54), (-24, -34), (-6, -26), (8, -16)]
        self.face_outline = gfx.smooth_path(face_front, closed=False, tension=0.35)
        self.head_full = gfx.smooth_path(face_front + skull_back[1:], closed=True, tension=0.35)
        hair = gfx.smooth_path([(14, -90), (18, -82), (8, -78), (-2, -70), (-12, -52), (-26, -40), (-40, -58),
                                (-40, -84), (-24, -100), (0, -102)], closed=True)
        for cx, cy, r in ((-6, -104, 12), (-32, -96, 12)):  # twin buns 双丫髻
            hair = gfx.op(hair, gfx.circle(cx, cy, r), "union")
        self.hair = gfx.op(hair, gfx.circle(-6, -104, 4), "diff")
        self.neck = gfx.poly([(-6, 2), (8, 2), (9, -18), (-4, -20)])
        self.eye = gfx.smooth_path([(9, -56), (13, -59), (18, -57), (14, -54.5)], closed=True)
        self.brow = gfx.ribbon([(7, -63), (12, -66), (19, -65)], [0.6, 2.0, 0.6])
        self.mouth = gfx.ribbon([(16, -32), (19, -32.4)], [1.4, 0.7])
        self.bun_anchor = (-6, -114)
        self.crown = (-14, -104)
        self.huadian = None
        self.hair_tail_root = (-30, -50)
        self.upper = gfx.smooth_path([(-8, -3), (8, -3), (7, 34), (6, 58), (-5, 58), (-7, 34)], closed=True)
        self.fore = gfx.smooth_path([(-6, -2), (6, -2), (5, 28), (5, 54), (-4, 54), (-5, 28)], closed=True)
        self.sleeve_cap = gfx.smooth_path([(-12, -6), (12, -7), (13, 16), (6, 26), (-8, 25), (-12, 13)], closed=True)
        self.cuff = gfx.rect(-5.5, 44, 10.5, 7)
        self.foot = gfx.smooth_path([(-8, -7), (5, -8), (16, -5), (24, -1), (17, 2), (-8, 2)], closed=True)

    # ------------------------------------------------------------------ man
    def _man(self):
        sk = gfx.smooth_path([(38, 0), (46, 100), (56, 240), (66, 350), (20, 356), (-40, 356), (-70, 350),
                              (-58, 240), (-48, 100), (-38, 0)], closed=True)
        cuts = skia.Path()
        cuts.addPath(_slits(0, 60, 320, 5, 90, 2.4))
        cuts.addPath(gfx.op(_cut_pattern_scales(-66, 310, 66, 344, r=7.0), sk, "inter"))
        self.skirt = gfx.op(sk, cuts, "diff")
        self.skirt_outline = sk
        to = gfx.smooth_path([(38, 4), (42, -40), (46, -96), (34, -128), (14, -142), (-8, -146), (-30, -132),
                              (-38, -90), (-40, -40), (-38, 4)], closed=True)
        tcut = skia.Path()
        tcut.addPath(gfx.ribbon([(12, -138), (26, -100), (36, -60), (40, -16)], [5, 5, 5, 4]))
        tcut.addPath(gfx.circle(-6, -70, 16))
        tcut = gfx.op(tcut, gfx.circle(-6, -70, 11), "diff")
        self.torso = gfx.op(to, tcut, "diff")
        self.torso_outline = to
        self.belt = gfx.smooth_path([(42, -18), (43, 2), (-40, 4), (-40, -16)], closed=True)
        face_front = [(10, -24), (20, -34), (26, -42), (23, -46), (27, -50), (26, -56), (35, -64), (27, -76),
                      (29, -86), (25, -100), (17, -108)]
        skull_back = [(17, -108), (0, -120), (-22, -117), (-36, -100), (-34, -74), (-22, -54), (-6, -42), (10, -24)]
        self.face_outline = gfx.smooth_path(face_front, closed=False, tension=0.35)
        self.head_full = gfx.smooth_path(face_front + skull_back[1:], closed=True, tension=0.35)
        # official's hat with side wings (乌纱帽)
        hat = gfx.smooth_path([(20, -104), (22, -122), (8, -138), (-20, -140), (-36, -124), (-36, -100), (-10, -106)], closed=True)
        hat = gfx.op(hat, gfx.rect(-40, -118, 64, 6), "diff")
        wing = gfx.op(gfx.ellipse(-64, -114, 22, 8), gfx.rect(-78, -115, 28, 2.4), "diff")
        hat = gfx.op(hat, wing, "union")
        hat = gfx.op(hat, gfx.rect(-40, -114, 20, 4), "union")
        beard = gfx.smooth_path([(22, -36), (26, -26), (24, -10), (16, 6), (14, -16), (12, -30)], closed=True)
        self.hair = gfx.op(hat, beard, "union")
        self.neck = gfx.poly([(-8, 2), (10, 2), (12, -26), (-6, -28)])
        self.eye = gfx.smooth_path([(12, -74), (16, -77), (21, -75), (17, -72.5)], closed=True)
        self.brow = gfx.ribbon([(8, -82), (15, -86), (24, -84)], [1.0, 3.0, 1.0])
        self.mouth = gfx.ribbon([(21, -46), (24, -46.6)], [1.6, 0.8])
        self.bun_anchor = (-10, -138)
        self.crown = (-8, -140)
        self.huadian = None
        self.hair_tail_root = None
        self.upper = gfx.smooth_path([(-13, -4), (13, -4), (11, 64), (9, 110), (-8, 110), (-11, 64)], closed=True)
        self.fore = gfx.smooth_path([(-9, -3), (9, -3), (8, 52), (7, 100), (-6, 100), (-8, 52)], closed=True)
        self.sleeve_cap = gfx.smooth_path([(-18, -8), (18, -10), (20, 60), (10, 90), (-14, 88), (-20, 40)], closed=True)
        self.cuff = gfx.rect(-8, 82, 16, 10)
        self.foot = gfx.smooth_path([(-12, -9), (8, -11), (26, -7), (36, -1), (26, 2), (-12, 2)], closed=True)


# hand shapes, wrist at origin, fingers along +y (hanging)
def _hand(kind, scale=1.0):
    s = scale
    if kind == "relax":
        pts = [(-6, 0), (6, 0), (9, 12), (8, 26), (4, 36), (-1, 38), (-4, 30), (-7, 18), (-11, 14), (-9, 8)]
    elif kind == "open":   # palm up, fingers forward (cupping)
        pts = [(-6, 0), (7, -1), (12, 8), (24, 14), (36, 15), (38, 18), (26, 21), (12, 22), (0, 20), (-7, 12)]
    elif kind == "point":
        pts = [(-6, 0), (6, 0), (9, 10), (10, 18), (12, 30), (13, 44), (10, 45), (7, 32), (2, 26), (-4, 26), (-8, 16)]
    elif kind == "fist":
        pts = [(-6, 0), (7, 0), (11, 8), (12, 18), (6, 24), (-4, 24), (-9, 16), (-9, 7)]
    elif kind == "flat":   # fingers extended straight
        pts = [(-6, 0), (6, 0), (8, 12), (7, 30), (4, 44), (0, 46), (-3, 42), (-5, 28), (-9, 18), (-11, 12)]
    elif kind == "spread":
        pts = [(-6, 0), (7, 0), (14, 10), (20, 30), (16, 31), (10, 18), (8, 34), (5, 46), (1, 46), (1, 30),
               (-3, 44), (-7, 42), (-4, 24), (-12, 30), (-15, 27), (-8, 12)]
    else:
        pts = [(-6, 0), (6, 0), (8, 14), (4, 30), (-4, 30), (-8, 14)]
    return gfx.smooth_path([(x * s, y * s) for x, y in pts], closed=True, tension=0.45)


_HANDS = {}


def hand_path(kind, scale=1.0):
    k = (kind, scale)
    if k not in _HANDS:
        _HANDS[k] = _hand(kind, scale)
    return _HANDS[k]


# ----------------------------------------------------------------------------- the rig

DEFAULT_POSE = dict(
    lean=0.0, torso=0.0, head=0.0,
    ua_f=8.0, fa_f=10.0, h_f=0.0, hand_f="relax",
    ua_b=-6.0, fa_b=8.0, h_b=0.0, hand_b="relax",
    skirt=0.0, step=None, bob=0.0, foot_f=(14, 0), foot_b=(-18, 0),
    bud_open=0.0, bud_rot=0.0, hair=0.0, sash=0.0,
)


class Puppet:
    def __init__(self, kind="woman", leather=S.INK, arm_red=1.0, bud=True, veil=False, face="carved",
                 bloom=0.0, seed=0, robe_color=None, huadian=True, hair_tail=True, body_color=None,
                 scale_parts=1.0, bead_strands=True):
        self.kind = kind
        self.sh = Shapes.get(kind)
        self.leather = leather
        self.arm_red = arm_red
        self.bud = bud
        self.veil = veil
        self.face = face          # "carved" | "empty" | "solid"
        self.bloom = bloom
        self.seed = seed
        self.robe_color = robe_color  # None => ink black, else translucent colour (multiply)
        self.body_color = body_color
        self.huadian = huadian
        self.hair_tail = hair_tail
        self.bead_strands = bead_strands
        if kind == "child":
            self.dims = dict(waist=(0, -112), neck=(2, -78), shoulder=(-2, -70), upper_len=56, fore_len=52,
                             hip_f=(10, -4), hip_b=(-12, -4))
        elif kind == "man":
            self.dims = dict(waist=(0, -356), neck=(4, -140), shoulder=(0, -128), upper_len=108, fore_len=98,
                             hip_f=(16, -6), hip_b=(-20, -6))
        else:
            self.dims = dict(waist=(0, -352), neck=(4, -126), shoulder=(2, -112), upper_len=102, fore_len=94,
                             hip_f=(16, -6), hip_b=(-20, -6))

    # --------------------------------------------------------------- matrices
    def _mats(self, pose):
        d = self.dims
        P = dict(DEFAULT_POSE)
        P.update(pose)
        mats = {}
        root = skia.Matrix()
        root.setRotate(-P["lean"])
        root.preTranslate(0, -P["bob"])
        mats["root"] = root
        waist = mcopy(root)
        waist.preTranslate(*d["waist"])
        mats["skirt"] = mcopy(waist)
        mats["skirt"].preRotate(-P["skirt"])
        torso = mcopy(waist)
        torso.preRotate(-P["torso"])
        mats["torso"] = torso
        head = mcopy(torso)
        head.preTranslate(*d["neck"])
        head.preRotate(-P["head"])
        mats["head"] = head
        for side in ("f", "b"):
            sh = mcopy(torso)
            sh.preTranslate(*d["shoulder"])
            sh.preRotate(-P["ua_" + side])
            mats["ua_" + side] = sh
            el = mcopy(sh)
            el.preTranslate(0, d["upper_len"])
            el.preRotate(-P["fa_" + side])
            mats["fa_" + side] = el
            wr = mcopy(el)
            wr.preTranslate(0, d["fore_len"])
            wr.preRotate(-P["h_" + side])
            mats["h_" + side] = wr
        for side in ("f", "b"):
            fx, fy = P["foot_" + side]
            fm = mcopy(root)
            fm.preTranslate(fx, fy)
            mats["foot_" + side] = fm
        return mats, P

    def joint(self, pose, name):
        """World position (in puppet space) of a named joint: 'hand_f','hand_b','head','neck','bud','waist'."""
        mats, P = self._mats(pose)
        if name in ("hand_f", "hand_b"):
            m = mats["h_" + name[-1]]
            pt = m.mapXY(0, 22 if self.kind != "child" else 14)
        elif name == "neck":
            pt = mats["head"].mapXY(0, 0)
        elif name == "head":
            pt = mats["head"].mapXY(4, -70)
        elif name == "bud":
            ax, ay = self.sh.crown
            pt = mats["head"].mapXY(ax + 8, ay - 40)
        elif name == "waist":
            pt = mats["torso"].mapXY(0, 0)
        elif name == "back":
            pt = mats["torso"].mapXY(-28, -80)
        elif name == "elbow_f":
            pt = mats["fa_f"].mapXY(0, 0)
        else:
            pt = mats["root"].mapXY(0, 0)
        return pt.x(), pt.y()

    # --------------------------------------------------------------- drawing
    def draw(self, canvas, x, y, scale=1.0, pose=None, t=0.0, flip=False, alpha=1.0, rods=0.0,
             arm_red=None, bloom=None, rivets=True, stem=0.0, stem_to=None, blend_body=None,
             only_silhouette=False, highlight=0.0):
        pose = pose or {}
        mats, P = self._mats(pose)
        red = self.arm_red if arm_red is None else arm_red
        bl = self.bloom if bloom is None else bloom
        canvas.save()
        canvas.translate(x, y)
        canvas.scale(-scale if flip else scale, scale)
        ink = self.leather
        body_p = gfx.paint(ink, 0.96 * alpha)
        robe_p = body_p if self.robe_color is None else gfx.paint(self.robe_color, 0.95 * alpha, blend=gfx.MULTIPLY)
        line_p = gfx.paint(ink, alpha, stroke=2.2)
        armcol = S.arm_color(red)
        arm_p = gfx.paint(armcol, 0.93 * alpha, blend=gfx.MULTIPLY)
        sh = self.sh

        def draw_in(m, path, p):
            canvas.save()
            canvas.concat(m)
            canvas.drawPath(path, p)
            canvas.restore()

        # back-stem (the twig tying her to the tree)
        if stem > 0 and stem_to is not None:
            bx, by = self.joint(pose, "back")
            self._draw_stem(canvas, bx, by, stem_to, stem, alpha, scale, flip)

        # hair tail behind everything
        if self.hair_tail and sh.hair_tail_root is not None:
            self._draw_hair_tail(canvas, mats["head"], P, t, alpha)

        # back arm
        self._draw_arm(canvas, mats, "b", P, arm_p, line_p, body_p, alpha, rivets, shade=0.82)
        # back foot
        draw_in(mats["foot_b"], sh.foot, body_p)
        # skirt + sash
        draw_in(mats["skirt"], sh.skirt, robe_p)
        if self.robe_color is not None:
            canvas.save()
            canvas.concat(mats["skirt"])
            canvas.drawPath(sh.skirt_outline, line_p)
            canvas.restore()
        self._draw_sash(canvas, mats["torso"], P, t, alpha)
        # front foot
        draw_in(mats["foot_f"], sh.foot, body_p)
        # torso
        draw_in(mats["torso"], sh.torso, robe_p)
        if self.robe_color is not None:
            draw_in(mats["torso"], sh.torso_outline, line_p)
        draw_in(mats["torso"], sh.belt, gfx.paint(S.LEATHER_RED if self.kind != "man" else S.LEATHER_GOLD, 0.9 * alpha, blend=gfx.MULTIPLY))
        draw_in(mats["torso"], sh.belt, gfx.paint(ink, alpha, stroke=1.6))
        if hasattr(sh, "cloud_collar"):
            draw_in(mats["torso"], sh.cloud_collar, gfx.paint(S.LEATHER_RED_DEEP, 0.92 * alpha, blend=gfx.MULTIPLY))
            draw_in(mats["torso"], sh.cloud_collar, gfx.paint(ink, alpha, stroke=1.8))
        # head
        self._draw_head(canvas, mats["head"], P, t, alpha, bl)
        # front arm
        self._draw_arm(canvas, mats, "f", P, arm_p, line_p, body_p, alpha, rivets, shade=1.0)
        # rivets on torso joints
        if rivets:
            for m, (rx, ry) in ((mats["torso"], (0, 0)), (mats["head"], (0, 0))):
                p = m.mapXY(rx, ry)
                self._rivet(canvas, p.x(), p.y(), alpha)
        canvas.restore()
        # rods (drawn in screen space, from joints down off-frame)
        if rods > 0:
            for jn in ("neck", "hand_f", "hand_b"):
                jx, jy = self.joint(pose, jn)
                sx = x + (-jx if flip else jx) * scale
                sy = y + jy * scale
                ex = sx + (40 if jn == "hand_f" else -30 if jn == "hand_b" else 10) * scale
                canvas.drawLine(sx, sy, ex, sy + 2000, gfx.paint(S.INK, 0.85 * rods * alpha, stroke=3.2 * scale))
                canvas.drawCircle(sx, sy, 5 * scale, gfx.paint(S.INK, rods * alpha))

    def _rivet(self, canvas, x, y, alpha):
        canvas.drawCircle(x, y, 4.6, gfx.paint(S.INK, alpha))
        canvas.drawCircle(x, y, 2.0, gfx.paint((170, 140, 100), alpha * 0.9, blend=gfx.MULTIPLY))

    def _draw_arm(self, canvas, mats, side, P, arm_p, line_p, body_p, alpha, rivets, shade=1.0):
        sh = self.sh
        for seg, path in (("ua_", sh.upper), ("fa_", sh.fore)):
            canvas.save()
            canvas.concat(mats[seg + side])
            canvas.drawPath(path, arm_p)
            if shade < 1.0:
                canvas.drawPath(path, gfx.paint((0, 0, 0), (1 - shade) * alpha * 0.8, blend=gfx.MULTIPLY))
            canvas.drawPath(path, line_p)
            if seg == "fa_":
                canvas.drawPath(sh.cuff, body_p)
            canvas.restore()
        # hand
        canvas.save()
        canvas.concat(mats["h_" + side])
        hs = 0.62 if self.kind == "child" else 1.0
        hp = hand_path(P["hand_" + side], hs)
        canvas.drawPath(hp, arm_p)
        canvas.drawPath(hp, gfx.paint(S.INK, alpha, stroke=1.8))
        canvas.restore()
        # sleeve cap over shoulder
        canvas.save()
        canvas.concat(mats["ua_" + side])
        canvas.drawPath(sh.sleeve_cap, body_p if self.robe_color is None else gfx.paint(self.robe_color, 0.95 * alpha, blend=gfx.MULTIPLY))
        if self.robe_color is not None:
            canvas.drawPath(sh.sleeve_cap, line_p)
        canvas.restore()
        if rivets:
            for seg in ("ua_", "fa_", "h_"):
                p = mats[seg + side].mapXY(0, 0)
                self._rivet(canvas, p.x(), p.y(), alpha)

    def _draw_head(self, canvas, m, P, t, alpha, bloom):
        sh = self.sh
        canvas.save()
        canvas.concat(m)
        ink = self.leather
        canvas.drawPath(sh.neck, gfx.paint(ink, 0.96 * alpha))
        if self.face == "solid":
            canvas.drawPath(sh.head_full, gfx.paint(ink, 0.96 * alpha))
        else:
            # carved face: pale translucent skin + outline
            canvas.drawPath(sh.head_full, gfx.paint((250, 236, 220), 0.5 * alpha, blend=gfx.MULTIPLY))
            canvas.drawPath(sh.face_outline, gfx.paint(ink, alpha, stroke=3.0))
            if self.face == "carved":
                canvas.drawPath(sh.eye, gfx.paint(ink, alpha, stroke=1.8))
                canvas.drawCircle(15.5, -66.8, 1.6, gfx.paint(ink, alpha))
                canvas.drawPath(sh.brow, gfx.paint(ink, alpha))
                canvas.drawPath(sh.mouth, gfx.paint(S.LEATHER_RED_DEEP, alpha))
            elif self.face == "empty":
                # hollow sockets: the bride's emptied face
                canvas.drawPath(gfx.ellipse(14.5, -66.5, 5.2, 3.4), gfx.paint(ink, alpha))
        canvas.drawPath(sh.hair, gfx.paint(ink, 0.97 * alpha))
        if self.huadian and sh.huadian is not None:
            hx, hy = sh.huadian
            for k in range(3):
                a = -math.pi / 2 + (k - 1) * 0.9
                canvas.drawPath(gfx.ellipse(hx + math.cos(a) * 2.4, hy + math.sin(a) * 2.4, 1.7, 2.6),
                                gfx.paint(S.ROUGE, alpha))
        # hairpin with swaying bead strands (步摇)
        if self.kind in ("woman", "bride") and self.bead_strands:
            ax, ay = sh.bun_anchor
            canvas.drawLine(ax - 18, ay + 14, ax + 30, ay - 4, gfx.paint(ink, alpha, stroke=2.6))
            sway = 6 * noise1(t * 1.3, self.seed + 3) + P["hair"] * 4
            for k in range(3):
                bx = ax + 24 - k * 6
                by = ay - 2 + k * 2
                ex = bx + sway * 0.6
                ey = by + 22 + k * 5
                canvas.drawLine(bx, by, ex, ey, gfx.paint(ink, alpha, stroke=1.0))
                canvas.drawCircle(ex, ey, 2.3, gfx.paint(S.LEATHER_RED, alpha, blend=gfx.MULTIPLY))
                canvas.drawCircle(ex, ey, 2.3, gfx.paint(ink, alpha, stroke=0.8))
        # bud / bloom on the bun
        if self.bud:
            ax, ay = sh.crown
            bscale = 0.8 if self.kind == "child" else 1.22
            wob = 3 * noise1(t * 1.1, self.seed + 7)
            draw_poppy_side(canvas, ax, ay + 4, scale=bscale, angle=math.radians(16 + wob + P["bud_rot"]),
                            openness=max(bloom, P["bud_open"]), seed=self.seed + 1, t=t, alpha=alpha,
                            stem_len=10, stem_curve=0.1)
        if self.veil and hasattr(sh, "veil"):
            vs = 2.0 * noise1(t * 0.8, self.seed + 9)
            canvas.save()
            canvas.skew(vs * 0.01, 0)
            canvas.drawPath(sh.veil, gfx.paint(S.LEATHER_RED, 0.95 * alpha, blend=gfx.MULTIPLY))
            canvas.drawPath(sh.veil, gfx.paint(ink, alpha, stroke=2.0))
            # tassels
            for k in range(9):
                tx = -40 + k * 10
                ty = -12 + (2 if k % 2 else 0)
                canvas.drawLine(tx, ty, tx + vs, ty + 14, gfx.paint(ink, alpha, stroke=1.2))
                canvas.drawCircle(tx + vs, ty + 15, 2, gfx.paint(S.LEATHER_GOLD, alpha, blend=gfx.MULTIPLY))
            # embroidered double-happiness ring
            canvas.drawCircle(0, -62, 12, gfx.paint(S.LEATHER_GOLD, 0.9 * alpha, blend=gfx.MULTIPLY))
            canvas.drawCircle(0, -62, 12, gfx.paint(ink, alpha, stroke=1.5))
            canvas.restore()
        canvas.restore()

    def _draw_hair_tail(self, canvas, m, P, t, alpha):
        sh = self.sh
        rx, ry = sh.hair_tail_root
        canvas.save()
        canvas.concat(m)
        L = 230 if self.kind != "child" else 0
        if L > 0:
            pts = []
            n = 12
            for i in range(n + 1):
                u = i / n
                sway = (8 * noise1(t * 0.9 + u * 1.5, self.seed + 11) + P["hair"] * 30 * u) * u
                pts.append((rx - 6 * u + sway - 14 * u * u, ry + L * u))
            wid = [16 - 12 * (i / n) ** 1.5 for i in range(n + 1)]
            canvas.drawPath(gfx.ribbon(pts, wid), gfx.paint(self.leather, 0.96 * alpha))
            # ribbon tie
            canvas.drawPath(gfx.ellipse(rx - 2, ry + 26, 8, 4), gfx.paint(S.LEATHER_RED, 0.9 * alpha, blend=gfx.MULTIPLY))
        canvas.restore()

    def _draw_sash(self, canvas, m, P, t, alpha):
        if self.kind == "child":
            return
        canvas.save()
        canvas.concat(m)
        for k, (x0, L) in enumerate(((40, 236), (33, 206))):
            pts = []
            n = 10
            for i in range(n + 1):
                u = i / n
                sway = (6 * noise1(t * 1.2 + u * 2 + k, self.seed + 21 + k) + P["sash"] * 40 * u) * u
                pts.append((x0 + 8 * u + sway, -4 + L * u))
            wid = [6.5 - 2.5 * (i / n) for i in range(n + 1)]
            canvas.drawPath(gfx.ribbon(pts, wid), gfx.paint(S.LEATHER_RED if k == 0 else S.LEATHER_RED_DEEP, 0.9 * alpha, blend=gfx.MULTIPLY))
            canvas.drawPath(gfx.ribbon(pts, wid), gfx.paint(S.INK, alpha, stroke=1.2))
        canvas.restore()

    def _draw_stem(self, canvas, bx, by, to, amount, alpha, scale, flip):
        # to: (x, y) in puppet space (unscaled)
        tx, ty = to
        pts = gfx.bezier_pts((bx, by), (bx - 60, by - 40), (tx + 40, ty + 80), (tx, ty), 20)
        pts = gfx.polyline_cut(pts, amount) if amount < 1 else pts
        wid = np.linspace(5, 11, len(pts))
        canvas.drawPath(gfx.ribbon(pts, wid), gfx.paint(S.INK, alpha))
        # small leaves along the stem
        for k in range(2, len(pts) - 2, 5):
            px, py = pts[k]
            canvas.drawPath(gfx.ellipse(px - 8, py - 6, 9, 4), gfx.paint(S.LEATHER_GREEN, alpha * 0.9, blend=gfx.MULTIPLY))
            canvas.drawPath(gfx.ellipse(px - 8, py - 6, 9, 4), gfx.paint(S.INK, alpha, stroke=1.2))


# ----------------------------------------------------------------------------- motion helpers

def walk(phase, stride=1.0, arm=1.0):
    """Pose delta for a gentle puppet walk.  phase in cycles."""
    a = 2 * math.pi * phase
    s = math.sin(a)
    c = math.cos(a)
    return dict(
        foot_f=(14 + 22 * s * stride, -max(0, c) * 8 * stride),
        foot_b=(-18 - 22 * s * stride, -max(0, -c) * 8 * stride),
        bob=abs(math.sin(a)) * 6 * stride,
        skirt=-3 * s * stride,
        ua_f=8 - 16 * s * arm, fa_f=12 - 6 * s * arm,
        ua_b=-6 + 16 * s * arm, fa_b=10 + 6 * s * arm,
        torso=2 + 1.5 * c * stride,
        head=-1 * c * stride,
        sash=-0.3 * s,
    )


def run(phase, amount=1.0):
    a = 2 * math.pi * phase
    s = math.sin(a)
    c = math.cos(a)
    return dict(
        foot_f=(18 + 42 * s * amount, -max(0, c) * 22 * amount),
        foot_b=(-22 - 42 * s * amount, -max(0, -c) * 22 * amount),
        bob=abs(s) * 16 * amount,
        skirt=-8 * s * amount - 6 * amount,
        lean=6 * amount,
        torso=10 * amount,
        ua_f=20 - 50 * s * amount, fa_f=60,
        ua_b=-20 + 50 * s * amount, fa_b=60,
        head=-4 * amount,
        hair=0.8 * amount,
        sash=-0.8 * amount,
    )


def breathe(t, seed=0, amt=1.0):
    return dict(torso=1.2 * amt * math.sin(t * 1.6 + seed), head=0.8 * amt * noise1(t * 0.5, seed + 2),
                ua_f=8 + 1.5 * amt * noise1(t * 0.7, seed + 3), ua_b=-6 + 1.5 * amt * noise1(t * 0.7, seed + 4))


def merge(*poses):
    out = {}
    for p in poses:
        out.update(p)
    return out


def blend_pose(a, b, k):
    """Blend two pose dicts (numeric fields), k in 0..1."""
    out = dict(a)
    for key, vb in b.items():
        va = a.get(key, DEFAULT_POSE.get(key))
        if isinstance(vb, (int, float)) and isinstance(va, (int, float)):
            out[key] = va + (vb - va) * k
        elif isinstance(vb, tuple) and isinstance(va, tuple):
            out[key] = tuple(x + (y - x) * k for x, y in zip(va, vb))
        else:
            out[key] = vb if k >= 0.5 else va
    return out


class PoseTrack:
    """Keyframed poses: list of (time, posedict, ease)."""

    def __init__(self, keys):
        self.keys = sorted(keys, key=lambda k: k[0])

    def __call__(self, t):
        ks = self.keys
        if t <= ks[0][0]:
            return dict(ks[0][1])
        if t >= ks[-1][0]:
            return dict(ks[-1][1])
        for i in range(1, len(ks)):
            if t <= ks[i][0]:
                t0, p0 = ks[i - 1][0], ks[i - 1][1]
                t1, p1 = ks[i][0], ks[i][1]
                e = ks[i][2] if len(ks[i]) > 2 else "in_out_cubic"
                k = E.EASES[e]((t - t0) / (t1 - t0))
                full0 = dict(DEFAULT_POSE)
                full0.update(p0)
                full1 = dict(full0)
                full1.update(p1)
                return blend_pose(full0, full1, k)
        return dict(ks[-1][1])
