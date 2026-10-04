"""阿朵 (original character) — refined anime head in a light illustration style.

Head-local 2D space: origin at the middle of the eye line, y down; the face is ~206 units wide at the
cheekbones and ~150 units from eye line to chin.

* The face contour and features are 2D keys at yaw 0 (front), 0.5 (three-quarter, ~42 deg) and 1
  (profile, ~85 deg), blended continuously (negative yaw mirrors).  |yaw| > 1 fades into the back view.
* Bangs, the hairpin, the ear and the hair-mass silhouette live on a small 3D model of the skull and are
  rotated/projected, so they stay consistent with any yaw/pitch.
* Line widths are given in screen pixels and divided by `px` (screen px per head unit), so close-ups
  keep delicate lines instead of scaling them up.
"""
import math

import numpy as np
import skia

from pv.core import gfx
from pv.core import easing as E
from pv.core.noise import noise1
from . import palette as P
from . import shade as SH

YAW_DEG = 85.0


def L(a, b, t):
    return a + (b - a) * t


# ----------------------------------------------------------------------------- 2D keys

FACE_F = [(0, -148), (50, -144), (84, -124), (98, -88), (102, -46), (103, -6), (100, 34), (92, 70), (78, 100),
          (56, 126), (28, 144), (0, 150), (-28, 144), (-56, 126), (-78, 100), (-92, 70), (-100, 34), (-103, -6),
          (-102, -46), (-98, -88), (-84, -124), (-50, -144)]
FACE_Q = [(16, -150), (64, -144), (92, -122), (102, -86), (102, -46), (95, -12), (99, 26), (92, 64), (79, 98),
          (62, 124), (42, 142), (24, 149), (0, 148), (-34, 138), (-66, 118), (-92, 86), (-110, 46), (-116, 4),
          (-116, -40), (-110, -84), (-94, -122), (-50, -146)]
FACE_P = [(8, -152), (52, -142), (78, -116), (88, -82), (92, -46), (86, -18), (98, 22), (112, 46), (100, 58),
          (99, 74), (94, 90), (92, 104), (88, 126), (60, 144), (20, 136), (-20, 104), (-46, 62), (-70, 20),
          (-90, -28), (-96, -80), (-80, -124), (-40, -150)]

# eyes: (cx, cy, w, h, visibility, turn) for the near eye (screen-left when turning right) and the far eye
EYES_F = ((-47, 0, 72, 52, 1.0, 0.0), (47, 0, 72, 52, 1.0, 0.0))
EYES_Q = ((-27, 2, 74, 53, 1.0, 0.22), (58, 1, 46, 49, 1.0, 0.62))
EYES_P = ((56, 0, 38, 47, 1.0, 1.0), (94, 0, 4, 44, 0.0, 1.0))
NOSE = {0.0: (0, 64), 0.5: (52, 62), 1.0: (110, 46)}
MOUTH = {0.0: (0, 104, 30), 0.5: (38, 102, 24), 1.0: (92, 90, 12)}


def _mirror_ring(pts):
    n = len(pts)
    return [(-pts[(n - i) % n][0], pts[(n - i) % n][1]) for i in range(n)]


def _key_blend(keys, yaw):
    a = abs(yaw)
    if a <= 0.5:
        A, B, t = keys[0.0], keys[0.5], a / 0.5
    else:
        A, B, t = keys[0.5], keys[1.0], (a - 0.5) / 0.5
    pts = [(L(x0, x1, t), L(y0, y1, t)) for (x0, y0), (x1, y1) in zip(A, B)]
    if yaw < 0:
        pts = _mirror_ring(pts)
    return pts


def _val_blend(keys, yaw):
    a = min(1.0, abs(yaw))
    if a <= 0.5:
        A, B, t = keys[0.0], keys[0.5], a / 0.5
    else:
        A, B, t = keys[0.5], keys[1.0], (a - 0.5) / 0.5
    v = tuple(L(x, y, t) for x, y in zip(A, B))
    if yaw < 0:
        v = (-v[0],) + v[1:]
    return v


def _eyes(yaw):
    a = min(1.0, abs(yaw))
    if a <= 0.5:
        A, B, t = EYES_F, EYES_Q, a / 0.5
    else:
        A, B, t = EYES_Q, EYES_P, (a - 0.5) / 0.5
    e = [tuple(L(x, y, t) for x, y in zip(A[i], B[i])) for i in range(2)]
    if yaw < 0:
        e = [(-e[i][0],) + e[i][1:] for i in range(2)]
    return e


# ----------------------------------------------------------------------------- 3D skull helpers

def rot3(yaw, pitch):
    th = yaw * YAW_DEG * math.pi / 180
    ph = pitch * 28 * math.pi / 180
    cy, sy = math.cos(th), math.sin(th)
    cp, sp = math.cos(ph), math.sin(ph)
    Ry = np.array([[cy, 0, sy], [0, 1, 0], [-sy, 0, cy]])
    Rx = np.array([[1, 0, 0], [0, cp, sp], [0, -sp, cp]])
    return Rx @ Ry


def proj(R, pts):
    """Rotate head-local 3D points (x right, y down, z toward camera) -> (2D pts, depth z)."""
    q = np.asarray(pts, np.float64) @ R.T
    return q[:, :2], q[:, 2]


SKULL_C = np.array([0.0, -34.0, -6.0])
SKULL_R = np.array([108.0, 132.0, 116.0])


def skull_point(u, v, lift=1.0):
    """Point on the hair-covered skull: u = azimuth (0 front, +90 = her left), v = elevation (deg)."""
    a, e = math.radians(u), math.radians(v)
    x = math.sin(a) * math.cos(e) * SKULL_R[0] * lift
    y = -math.sin(e) * SKULL_R[1] * lift
    z = math.cos(a) * math.cos(e) * SKULL_R[2] * lift
    return SKULL_C + np.array([x, y, z])


# hairline: elevation (deg) of the hair edge as a function of azimuth (deg)
def hairline_elev(u):
    return 22 + 30 * math.cos(math.radians(u) * 0.95) ** 2


# bang clumps: (root azimuth, tip x, tip y, root width, bulge)
BANGS = [
    (-74, -108, 30, 44, 12),
    (-56, -92, 2, 52, 16),
    (-37, -66, -10, 54, 20),
    (-19, -38, -26, 46, 20),
    (-6, -14, -58, 30, 16),
    (6, 12, -50, 32, 16),
    (20, 40, -22, 48, 20),
    (38, 68, -8, 54, 19),
    (57, 94, 6, 50, 15),
    (75, 110, 32, 42, 12),
]
# a few thin see-through strands between the clumps
THIN = [(-28, -50, -2, 10), (13, 28, 4, 9), (46, 82, 14, 9), (-46, -80, 20, 9)]
FLYAWAY = [(-30, 80, -120, -20), (20, 82, 128, 10), (-8, 86, -40, -110)]

DEFAULT = dict(
    yaw=0.0, pitch=0.0, px=1.0,
    eye_open=1.0, look=(0.0, 0.0), eye_shape="normal", dull=0.0, sparkle=0.0,
    brow=0.0, brow_sad=0.0, brow_angry=0.0,
    mouth="closed", mouth_open=0.0, smile=0.0,
    blush=0.45, tears=0.0, tear_well=0.0, shadow_eyes=0.0,
    bud_open=0.0, hair_sway=(0.0, 0.0), wind=0.0, step=0,
)


class Head:
    def __init__(self, light=None):
        self.light = light or SH.Light()

    # ------------------------------------------------------------------ geometry
    def geom(self, s):
        yaw = max(-1.6, min(1.6, s["yaw"]))
        fy = max(-1.0, min(1.0, yaw))
        pitch = max(-1.0, min(1.0, s["pitch"]))
        g = {"yaw": yaw, "fyaw": fy, "pitch": pitch}
        face = _key_blend({0.0: FACE_F, 0.5: FACE_Q, 1.0: FACE_P}, fy)
        face = [(x, y * (1 - 0.10 * pitch) + (8 * pitch if y < 0 else 0)) for x, y in face]
        g["face"] = face
        dy = 14 * pitch
        g["eyes"] = [(cx, cy + dy, w, h * (1 - 0.08 * abs(pitch)), vis, turn) for cx, cy, w, h, vis, turn in _eyes(fy)]
        nx, ny = _val_blend(NOSE, fy)
        g["nose"] = (nx, ny + dy * 0.9)
        mx, my, mw = _val_blend(MOUTH, fy)
        g["mouth"] = (mx, my * (1 - 0.08 * pitch) + dy * 0.6, mw)
        g["R"] = rot3(yaw, pitch)
        return g

    # ------------------------------------------------------------------ passes
    def draw_hood(self, c, s):
        """Hair volume around/behind the skull (drawn before the face)."""
        s = {**DEFAULT, **s}
        g = self.geom(s)
        R = g["R"]
        px = s["px"]
        pts = []
        for u in range(0, 360, 12):
            for v in (-20, 0, 25, 50, 72):
                pts.append(skull_point(u, v, 1.04))
        p2, z = proj(R, pts)
        hull = _convex_hull(p2)
        ext = []
        for x, y in hull:
            if y > -30:
                ext.append((x * 1.02, y + 110 + 0.4 * max(0, y)))
            else:
                ext.append((x, y))
        hood = gfx.smooth_path(_convex_hull(np.array(ext)), closed=True, tension=0.42)
        Lt = self.light
        SH.cel(c, hood, P.HAIR, Lt, d=10, feather=6, rim_w=4.8 / px, shade=P.HAIR_SH)
        SH.outline(c, hood, Lt, w=1.7 / px, var=1.0, color=P.LINE_HAIR)
        g["hood"] = hood
        return g

    def draw_face(self, c, s):
        s = {**DEFAULT, **s}
        g = self.geom(s)
        fy = g["fyaw"]
        px = s["px"]
        Lt = self.light
        vis = 1.0 - E.smooth((abs(g["yaw"]) - 1.0) / 0.25)
        if vis <= 0.01:
            return g
        face = gfx.smooth_path(g["face"], closed=True, tension=0.38)
        g["face_path"] = face
        self._ear(c, g, s)
        c.save()
        c.clipPath(face, SH.INTERSECT, True)
        c.drawPath(face, gfx.paint(P.SKIN, vis))
        side = 1 if fy >= 0 else -1
        if abs(fy) > 0.05:
            far = gfx.transformed(face, gfx.mat(-side * (5 + 9 * abs(fy)), 3))
            c.save()
            c.clipPath(far, SH.INVERSE, True)
            c.drawPaint(gfx.paint(P.SKIN_SH, 0.9 * vis, blur=5))
            c.restore()
        sh = skia.Path()
        for path in self._bang_paths(g, s, grow=1.0, drop=16):
            sh.addPath(path)
        c.drawPath(sh, gfx.paint(P.SKIN_SH, 0.95 * vis, blur=4.5))
        for (cx, cy, w, h, ev, turn) in g["eyes"]:
            if ev > 0.1:
                c.drawPath(gfx.ellipse(cx + (6 if cx > g["nose"][0] else -6), cy + 56, w * 0.40, h * 0.20),
                           gfx.paint(P.BLUSH, 0.32 * s["blush"] * ev * vis, blur=12))
        c.drawPath(gfx.ellipse(g["mouth"][0], 150, 70, 16), gfx.paint(P.SKIN_SH2, 0.35 * vis, blur=10))
        lx, ly = Lt.dir
        away = gfx.transformed(face, gfx.mat(-lx * 4.0 / px, -ly * 4.0 / px))
        c.save()
        c.clipPath(away, SH.INVERSE, True)
        c.drawPaint(gfx.paint(Lt.rim, 0.75 * Lt.rim_amt * vis, blend=gfx.SCREEN))
        c.restore()
        if s["shadow_eyes"] > 0:
            c.drawRect(skia.Rect(-220, -160, 220, 34), gfx.paint((90, 70, 120), 0.5 * s["shadow_eyes"] * vis, blend=gfx.MULTIPLY,
                       shader=gfx.linear_grad(0, -160, 0, 34, [(255, 255, 255, 255), (255, 255, 255, 0)])))
        c.restore()
        SH.outline(c, face, Lt, w=1.5 / px, var=1.1, color=P.LINE_SKIN, alpha=vis)
        for i, e in enumerate(g["eyes"]):
            if e[4] > 0.02 and e[2] > 6:
                self._eye(c, e, s, near=(i == 0), px=px, vis=vis)
        self._nose(c, g, s, px, vis)
        self._mouth(c, g, s, px, vis)
        self._blush_lines(c, g, s, px, vis)
        self._tears(c, g, s, px, vis)
        return g

    def draw_front_hair(self, c, s):
        s = {**DEFAULT, **s}
        g = self.geom(s)
        px = s["px"]
        Lt = self.light
        self._cap(c, g, s, px)
        if abs(g["yaw"]) < 1.25:
            paths = self._bang_paths(g, s)
            tips = self._bang_tips(g, s)
            for k, path in enumerate(paths):
                SH.cel(c, path, P.HAIR, Lt, d=7, feather=3.0, rim_w=3.0 / px, shade=P.HAIR_SH)
                tx, ty = tips[k]
                c.save()
                c.clipPath(path, SH.INTERSECT, True)
                c.drawRect(skia.Rect(tx - 60, ty - 70, tx + 60, ty + 10), gfx.paint((255, 255, 255), 0.9,
                           shader=gfx.linear_grad(0, ty - 70, 0, ty, [P.HAIR_RED + (0,), P.HAIR_RED + (255,)])))
                c.restore()
            self._sheen(c, g, s, paths)
            for path in paths:
                SH.outline(c, path, Lt, w=1.25 / px, var=0.9, color=P.LINE_HAIR)
            self._strand_lines(c, g, s, px)
            for i, e in enumerate(g["eyes"]):
                if e[4] > 0.05 and e[2] > 10:
                    self._brow(c, e, s, px, alpha=0.55)
        self._hairpin(c, g, s, px)
        return g

    # ------------------------------------------------------------------ hair parts
    def _cap_path(self, g):
        R = g["R"]
        # silhouette of the upper skull + the hairline arc, projected
        top = []
        for u in range(-180, 181, 10):
            for v in (30, 50, 70, 88):
                top.append(skull_point(u, v, 1.05))
        p2, z = proj(R, top)
        hull = _convex_hull(p2)
        hl = [skull_point(u, hairline_elev(u), 1.05) for u in range(-120, 121, 8)]
        hp, hz = proj(R, hl)
        # region above the hairline (front-facing part) unioned with the back of the skull top
        poly = [tuple(q) for q in hp] + [(hp[-1][0], -400), (hp[0][0], -400)]
        above = gfx.poly(poly)
        hullp = gfx.smooth_path(hull, closed=True, tension=0.4)
        cap = gfx.op(hullp, above, "inter")
        return cap, hullp

    def _cap(self, c, g, s, px):
        cap, hullp = self._cap_path(g)
        Lt = self.light
        SH.cel(c, cap, P.HAIR, Lt, d=12, feather=6, rim_w=4.0 / px, shade=P.HAIR_SH)
        # soft sheen band
        R = g["R"]
        band = []
        for u in range(-80, 81, 8):
            band.append(skull_point(u, 62 + 6 * math.sin(u * 0.2), 1.06))
        for u in range(80, -81, -8):
            band.append(skull_point(u, 54 + 6 * math.sin(u * 0.2 + 1), 1.06))
        bp, bz = proj(R, band)
        c.save()
        c.clipPath(cap, SH.INTERSECT, True)
        c.drawPath(gfx.smooth_path([tuple(q) for q in bp], closed=True, tension=0.3), gfx.paint(P.HAIR_HI, 0.45, blur=4))
        c.restore()
        SH.outline(c, cap, Lt, w=1.3 / px, var=0.9, color=P.LINE_HAIR)

    def _bang_geo(self, g, s, grow=1.0, drop=0.0):
        R = g["R"]
        sx, sy = s["hair_sway"]
        out = []
        for k, (au, tx, ty, w, bulge) in enumerate(BANGS):
            root = skull_point(au, hairline_elev(au) + 10, 1.06)
            tip = np.array([tx + sx * (0.5 + 0.5 * abs(tx) / 110), ty + sy + 4 * s["wind"] * noise1(k * 1.7 + s["step"] * 0.3, 3), 0.0])
            q = 1 - (tip[0] / SKULL_R[0]) ** 2 - ((tip[1] - SKULL_C[1]) / SKULL_R[1]) ** 2
            tip[2] = SKULL_C[2] + SKULL_R[2] * math.sqrt(max(0.02, q)) + 14
            mid = (root + tip) / 2
            n = mid - SKULL_C
            n = n / (np.linalg.norm(n) + 1e-9)
            ctrl = mid + n * bulge * 1.6
            p2, z = proj(R, np.array([root, ctrl, tip]))
            nrm = R @ n
            wf = 0.45 + 0.55 * abs(nrm[2])
            out.append((p2 + np.array([0, drop]), z, w * grow * wf))
        return out

    def _bang_paths(self, g, s, grow=1.0, drop=0.0):
        paths = []
        for p2, z, w in self._bang_geo(g, s, grow, drop):
            a, b, cc = p2
            pts, ws = [], []
            for i in range(15):
                t = i / 14
                pts.append(((1 - t) ** 2 * a[0] + 2 * (1 - t) * t * b[0] + t * t * cc[0],
                            (1 - t) ** 2 * a[1] + 2 * (1 - t) * t * b[1] + t * t * cc[1]))
                ws.append(max(0.3, w * (1 - t) ** 1.25))
            paths.append(gfx.ribbon(pts, ws))
        return paths

    def _bang_tips(self, g, s):
        return [tuple(p2[2]) for p2, z, w in self._bang_geo(g, s)]

    def _sheen(self, c, g, s, paths):
        R = g["R"]
        glints = skia.Path()
        for k in range(11):
            u = -70 + 140 * k / 10
            p = skull_point(u, hairline_elev(u) + 4, 1.07)
            q = skull_point(u + 2, hairline_elev(u) - 3, 1.07)
            p2, z = proj(R, [p, q])
            if z[0] < 0:
                continue
            (x0, y0), (x1, y1) = p2
            L1 = 20 + 6 * math.sin(k * 2.1)
            ang = math.atan2(y1 - y0, x1 - x0)
            lens = gfx.smooth_path([(-L1 * 0.5, 0), (0, -2.6), (L1 * 0.5, 0), (0, 2.6)], closed=True)
            glints.addPath(gfx.transformed(lens, gfx.mat(x0, y0, ang + math.pi / 2)))
        for path in paths:
            c.save()
            c.clipPath(path, SH.INTERSECT, True)
            c.drawPath(glints, gfx.paint(P.HAIR_HI, 0.5, blur=1.2))
            c.restore()

    def _strand_lines(self, c, g, s, px):
        R = g["R"]
        for k, (p2, z, w) in enumerate(self._bang_geo(g, s)):
            a, b, cc = p2
            for j in (-0.25, 0.2):
                pts = []
                for i in range(10):
                    t = 0.1 + 0.8 * i / 9
                    x = (1 - t) ** 2 * a[0] + 2 * (1 - t) * t * b[0] + t * t * cc[0]
                    y = (1 - t) ** 2 * a[1] + 2 * (1 - t) * t * b[1] + t * t * cc[1]
                    pts.append((x + j * w * (1 - t), y))
                SH.line(c, pts, 0.9 / px, 0.5 / px, color=P.HAIR_DEEP, alpha=0.55)
        for (au, tx, ty, w) in THIN:
            root = skull_point(au, hairline_elev(au) + 8, 1.06)
            tip = np.array([tx + s["hair_sway"][0], ty + s["hair_sway"][1], 104.0])
            ctrl = (root + tip) / 2 + np.array([0, -10, 26])
            p2, z = proj(R, [root, ctrl, tip])
            a, b, cc = p2
            pts, ws = [], []
            for i in range(12):
                t = i / 11
                pts.append(((1 - t) ** 2 * a[0] + 2 * (1 - t) * t * b[0] + t * t * cc[0],
                            (1 - t) ** 2 * a[1] + 2 * (1 - t) * t * b[1] + t * t * cc[1]))
                ws.append(max(0.3, w * (1 - t) ** 1.3))
            path = gfx.ribbon(pts, ws)
            c.drawPath(path, gfx.paint(P.HAIR))
            c.drawPath(path, gfx.paint(P.LINE_HAIR, 0.8, stroke=0.9 / px))
        for (au, av, tx, ty) in FLYAWAY:
            root = skull_point(au, av, 1.06)
            tip = np.array([tx + s["hair_sway"][0] * 1.5, ty + 10 * s["wind"] * math.sin(s["step"] * 0.7 + tx), 60.0])
            ctrl = (root + tip) / 2 + np.array([0, -30, 20])
            p2, z = proj(R, [root, ctrl, tip])
            SH.line(c, [tuple(p2[0]), tuple(p2[1]), tuple(p2[2])], 0.9 / px, 0.4 / px, color=P.LINE_HAIR, alpha=0.6)

    def _hairpin(self, c, g, s, px):
        R = g["R"]
        p = skull_point(78, 26, 1.08)
        q, z = proj(R, [p])
        if z[0] < -60:
            return
        x, y = q[0]
        draw_bud(c, x, y, 0.55, -0.4 + 0.5 * g["yaw"], s["bud_open"], px, self.light)
        sx = s["hair_sway"][0] * 0.4
        SH.line(c, [(x + 6, y + 16), (x + 10 + sx * 0.5, y + 40), (x + 9 + sx, y + 64)], 1.6 / px, 1.3 / px, color=P.THREAD)
        c.drawCircle(x + 9 + sx, y + 68, 3.6, gfx.paint(P.THREAD))

    def _ear(self, c, g, s):
        fy = g["fyaw"]
        a = abs(fy)
        if a < 0.55:
            return
        R = g["R"]
        side = -1 if fy > 0 else 1
        q, z = proj(R, [np.array([side * 96, 22, -8])])
        x, y = q[0]
        k = E.smooth((a - 0.55) / 0.3)
        ear = gfx.smooth_path([(x - 10, y - 26), (x + 8, y - 30), (x + 16, y - 6), (x + 8, y + 24), (x - 4, y + 22)], closed=True)
        SH.cel(c, ear, P.SKIN, self.light, d=4, feather=2, rim=False, shade=P.SKIN_SH)
        c.drawPath(ear, gfx.paint(P.LINE_SKIN, k, stroke=1.2 / s["px"]))

    # ------------------------------------------------------------------ face parts
    def _eye(self, c, e, s, near, px, vis):
        cx, cy, w, h, ev, turn = e
        shape = s["eye_shape"]
        o = max(0.0, min(1.0, s["eye_open"]))
        alpha = vis * min(1.0, ev * 1.5)
        out = -1 if (cx < 0 and abs(turn) <= 0.5) else 1
        if abs(turn) > 0.5:
            out = 1 if s["yaw"] >= 0 else -1

        def T(pts):
            return [(cx + out * x * w, cy + y * h) for x, y in pts]

        up = [(-0.48, 0.12), (-0.24, -0.32), (0.12, -0.44), (0.42, -0.30), (0.57, -0.13)]
        lo = [(-0.44, 0.26), (-0.05, 0.40), (0.34, 0.33), (0.52, 0.06)]
        closed = [(-0.48, 0.22), (-0.18, 0.34), (0.16, 0.34), (0.44, 0.20), (0.56, 0.08)]
        if shape == "sad":
            up = [(-0.48, 0.04), (-0.22, -0.40), (0.14, -0.44), (0.44, -0.16), (0.54, 0.02)]
        elif shape == "wide":
            up = [(-0.48, 0.06), (-0.24, -0.46), (0.12, -0.58), (0.44, -0.36), (0.58, -0.16)]
            lo = [(-0.44, 0.30), (-0.05, 0.48), (0.34, 0.40), (0.52, 0.10)]
        elif shape == "narrow":
            up = [(-0.48, 0.10), (-0.24, -0.22), (0.12, -0.30), (0.42, -0.18), (0.56, -0.06)]
        if shape in ("happy", "closed") or o < 0.06:
            arc = T([(-0.46, 0.16), (-0.18, -0.06), (0.14, -0.08), (0.42, 0.04), (0.56, 0.14)]) if shape == "happy" else T(closed)
            SH.line(c, arc, 2.8 / px, 2.0 / px, color=P.LASH, alpha=alpha)
            if shape != "happy":
                ex, ey = arc[-1]
                SH.line(c, [(ex - out * 6, ey - 1), (ex + out * 10, ey + 7)], 1.6 / px, 0.6 / px, color=P.LASH, alpha=alpha)
            return
        upper = [(L(a[0], b[0], o), L(a[1], b[1], o)) for a, b in zip(closed, up)]
        U = T(upper)
        Lw = T(lo)
        opening = gfx.smooth_path(U + Lw[::-1][1:], closed=True, tension=0.45)
        c.save()
        c.clipPath(opening, SH.INTERSECT, True)
        c.drawPath(opening, gfx.paint(P.SCLERA, alpha))
        shp = gfx.smooth_path(U + [(x, y + 0.30 * h) for x, y in U][::-1], closed=True)
        c.drawPath(shp, gfx.paint(P.SCLERA_SH, alpha, blur=2.0))
        lx, ly = s["look"]
        icx = cx + out * (0.03 + 0.10 * turn) * w + 0.16 * w * lx
        icy = cy + 0.05 * h + 0.10 * h * ly
        sq = 1 - 0.45 * abs(turn) * (1 if not near else 0.5)
        rx_ = 0.33 * w * sq * (0.9 if shape == "wide" else 1.0)
        ry_ = 0.47 * h * (0.86 if shape == "wide" else 1.0)
        dull = s["dull"]
        top = P.lerp(P.IRIS_TOP, (70, 68, 78), dull)
        mid = P.lerp(P.IRIS_MID, (120, 116, 126), dull)
        bot = P.lerp(P.IRIS_BOT, (176, 172, 180), dull)
        iris = gfx.ellipse(icx, icy, rx_, ry_)
        c.drawPath(iris, gfx.paint((255, 255, 255), alpha, shader=gfx.linear_grad(0, icy - ry_, 0, icy + ry_,
                   [top + (255,), mid + (255,), bot + (255,)], [0.0, 0.58, 1.0])))
        for k in range(14):
            a_ = math.pi * (0.15 + 0.7 * k / 13)
            c.drawLine(icx + math.cos(a_) * rx_ * 0.35, icy + math.sin(a_) * ry_ * 0.35,
                       icx + math.cos(a_) * rx_ * 0.92, icy + math.sin(a_) * ry_ * 0.92,
                       gfx.paint((255, 200, 170), 0.22 * alpha * (1 - dull), stroke=0.9 / px))
        c.drawPath(gfx.op(gfx.ellipse(icx, icy + ry_ * 0.12, rx_ * 0.86, ry_ * 0.86),
                          gfx.ellipse(icx, icy - ry_ * 0.05, rx_ * 0.86, ry_ * 0.86), "diff"),
                   gfx.paint((255, 190, 150), 0.45 * alpha * (1 - dull), blur=1.2))
        if dull < 0.95:
            pr = 0.12 * w * (0.75 if shape == "wide" else 1.0) * sq
            c.drawPath(gfx.ellipse(icx, icy + 0.01 * h, pr, pr * 1.55), gfx.paint(P.PUPIL, alpha * (1 - dull * 0.7)))
        c.drawPath(iris, gfx.paint(P.IRIS_RIM, alpha * 0.9, stroke=1.4 / px))
        c.drawPath(gfx.smooth_path(U + [(x, y + 0.34 * h) for x, y in U][::-1], closed=True),
                   gfx.paint((60, 16, 40), 0.42 * alpha, blend=gfx.MULTIPLY, blur=1.0))
        if dull < 0.7:
            k = 1 - dull
            c.drawPath(gfx.ellipse(icx - 0.11 * w * sq, icy - 0.17 * h, 0.075 * w, 0.10 * h), gfx.paint((255, 255, 255), alpha * k))
            c.drawPath(gfx.ellipse(icx + 0.12 * w * sq, icy + 0.20 * h, 0.03 * w, 0.035 * h), gfx.paint((255, 255, 255), alpha * 0.9 * k))
            c.drawPath(gfx.ellipse(icx + 0.02 * w, icy - 0.30 * h, 0.12 * w, 0.03 * h), gfx.paint((255, 240, 240), alpha * 0.5 * k, blur=1))
            if s["sparkle"] > 0:
                _star(c, icx - 0.05 * w, icy + 0.06 * h, 0.16 * w * s["sparkle"], alpha * s["sparkle"])
        c.restore()
        if s["tear_well"] > 0:
            SH.line(c, Lw, 3.4 / px, 3.4 / px, color=(206, 232, 255), alpha=0.75 * s["tear_well"] * alpha)
            SH.line(c, Lw, 1.2 / px, 1.2 / px, color=(255, 255, 255), alpha=0.95 * s["tear_well"] * alpha)
        SH.line(c, U, 1.2 / px, 3.6 / px, color=P.LASH, alpha=alpha, taper=False)
        ex, ey = U[-1]
        ex2, ey2 = U[-2]
        for k in range(3):
            c.drawPath(gfx.poly([(ex2 + out * k * 3, ey2 - 1), (ex + out * (9 + 4 * k), ey - 9 - 6 * k + 1.8 * k * k),
                                 (ex - out * 2 + out * k * 2, ey + 1)]), gfx.paint(P.LASH, alpha * (1 - 0.25 * k)))
        crease = [(x, y - 0.17 * h - 2) for x, y in U[1:5]]
        SH.line(c, crease, 0.9 / px, 0.5 / px, color=P.LINE_DEEP, alpha=0.5 * alpha)
        SH.line(c, Lw[1:], 0.6 / px, 1.1 / px, color=P.LINE_SKIN, alpha=0.9 * alpha)
        for k in range(2):
            bx, by = Lw[2 + k] if 2 + k < len(Lw) else Lw[-1]
            SH.line(c, [(bx, by), (bx + out * 4, by + 6)], 0.9 / px, 0.3 / px, color=P.LASH, alpha=0.7 * alpha)

    def _brow(self, c, e, s, px, alpha=1.0):
        cx, cy, w, h, ev, turn = e
        out = -1 if (cx < 0 and abs(turn) <= 0.5) else 1
        if abs(turn) > 0.5:
            out = 1 if s["yaw"] >= 0 else -1
        r = s["brow"] * 10
        sad = s["brow_sad"] * 12
        ang = s["brow_angry"] * 12
        inner = (cx - out * 0.30 * w, cy - 0.98 * h - r - sad + ang)
        midp = (cx + out * 0.06 * w, cy - 1.18 * h - r - sad * 0.3)
        outer = (cx + out * 0.46 * w, cy - 1.06 * h - r * 0.6 + sad * 0.5 - ang * 0.3)
        SH.line(c, [inner, midp, outer], 2.6 / px, 1.0 / px, color=P.HAIR_SH, alpha=alpha * min(1.0, ev * 1.5))

    def _nose(self, c, g, s, px, vis):
        nx, ny = g["nose"]
        fy = g["fyaw"]
        a = abs(fy)
        if a < 0.3:
            c.drawPath(gfx.ellipse(nx + 3, ny + 1, 5, 2.4), gfx.paint(P.SKIN_SH2, 0.8 * vis, blur=1.5))
            SH.line(c, [(nx + 1, ny - 7), (nx + 3, ny + 2)], 1.2 / px, 0.8 / px, color=P.LINE_SKIN, alpha=0.8 * vis)
        elif a < 0.85:
            sd = 1 if fy > 0 else -1
            SH.line(c, [(nx - sd * 6, ny - 18), (nx + sd * 4, ny), (nx - sd * 4, ny + 3)], 1.3 / px, 1.0 / px,
                    color=P.LINE_SKIN, alpha=0.9 * vis)
            c.drawPath(gfx.ellipse(nx - sd * 8, ny - 2, 6, 10), gfx.paint(P.SKIN_SH, 0.6 * vis, blur=3))
        else:
            sd = 1 if fy > 0 else -1
            SH.line(c, [(nx - sd * 14, ny + 6), (nx - sd * 8, ny + 9)], 1.0 / px, 0.6 / px, color=P.LINE_SKIN, alpha=0.8 * vis)

    def _mouth(self, c, g, s, px, vis):
        mx, my, mw = g["mouth"]
        k = mw / 30.0
        v = s["mouth"]
        o = max(0.0, min(1.0, s["mouth_open"]))
        smile = s["smile"]
        c.save()
        c.translate(mx, my)
        c.scale(k, k)
        lw = 1.3 / px / k
        if v in ("closed", "smile", "frown") or o < 0.07:
            curve = smile if v != "frown" else -0.7
            if v == "smile":
                curve = max(curve, 0.8)
            SH.line(c, [(-11, -1.2 * curve), (0, 1.4 + 2.2 * curve), (11, -1.2 * curve)], lw, lw * 0.8, color=P.LINE_SKIN, alpha=vis)
            c.drawPath(gfx.ellipse(0, 6, 7, 2.2), gfx.paint(P.LIP, 0.35 * vis, blur=1.5))
            c.restore()
            return
        shapes = {"a": (11, -4, 15), "o": (8, -6, 10), "u": (5.5, -4, 6), "e": (12, -3, 8), "i": (13, -2.5, 4.5),
                  "scream": (15, -7, 24)}
        hw, top, bot = shapes.get(v, shapes["a"])
        bot = top + (bot - top) * (0.3 + 0.7 * o)
        hw = hw * (0.7 + 0.3 * o)
        if v in ("o", "u"):
            pts = [(math.cos(a) * hw, (top + bot) / 2 + math.sin(a) * (bot - top) / 2) for a in np.linspace(0, 2 * math.pi, 12, endpoint=False)]
        else:
            pts = [(-hw, top + 1.5), (-hw * 0.5, top), (hw * 0.5, top), (hw, top + 1.5), (hw * 0.75, (top + bot) * 0.6),
                   (hw * 0.35, bot), (-hw * 0.35, bot), (-hw * 0.75, (top + bot) * 0.6)]
        mp = gfx.smooth_path(pts, closed=True, tension=0.45)
        c.drawPath(mp, gfx.paint((118, 40, 56), vis))
        c.save()
        c.clipPath(mp, SH.INTERSECT, True)
        c.drawPath(gfx.ellipse(0, bot + 1, hw * 0.8, (bot - top) * 0.45), gfx.paint((226, 120, 128), vis))
        if v in ("i", "e", "a", "scream"):
            c.drawRect(skia.Rect(-hw, top - 2, hw, top + 2.2), gfx.paint((255, 255, 255), vis))
        c.restore()
        c.drawPath(mp, gfx.paint(P.LINE_DEEP, vis, stroke=lw))
        c.restore()

    def _blush_lines(self, c, g, s, px, vis):
        b = s["blush"]
        if b < 0.4:
            return
        for (cx, cy, w, h, ev, turn) in g["eyes"]:
            if ev < 0.3:
                continue
            bx, by = cx, cy + 56
            for k in range(3):
                x = bx - w * 0.14 + k * w * 0.12
                SH.line(c, [(x + 3, by - 4), (x - 2, by + 4)], 1.0 / px, 0.5 / px, color=P.BLUSH, alpha=0.7 * (b - 0.3) * vis)

    def _tears(self, c, g, s, px, vis):
        t = s["tears"]
        if t <= 0:
            return
        for (cx, cy, w, h, ev, turn) in g["eyes"]:
            if ev < 0.3:
                continue
            x0, y0 = cx + 0.18 * w, cy + 0.36 * h
            Ln = 20 + 150 * t
            pts = [(x0 + 3 * math.sin(k * 0.7), y0 + k * Ln / 8) for k in range(9)]
            c.drawPath(gfx.ribbon(pts, [3, 4, 4.5, 4.5, 4.2, 4, 3.6, 3.4, 5]), gfx.paint((214, 236, 255), 0.6 * vis))
            SH.line(c, pts, 1.2 / px, 1.2 / px, color=(255, 255, 255), alpha=0.95 * vis)
            c.drawCircle(pts[-1][0], pts[-1][1] + 2, 3.6, gfx.paint((236, 248, 255), 0.9 * vis))


# ----------------------------------------------------------------------------- props

def draw_bud(c, x, y, sc, rot, openness, px=1.0, light=None):
    """Poppy-bud hairpin."""
    o = E.clamp(openness)
    Lt = light or SH.Light()
    c.save()
    c.translate(x, y)
    c.rotate(math.degrees(rot))
    c.scale(sc, sc)
    lw = 1.3 / px / sc
    if o < 0.45:
        q = o / 0.45
        cw, ch = 30 + 18 * q, 44 + 10 * q
        core = gfx.smooth_path([(0, 0), (cw * 0.5, -ch * 0.35), (cw * 0.42, -ch * 0.8), (0, -ch), (-cw * 0.42, -ch * 0.8),
                                (-cw * 0.5, -ch * 0.35)], closed=True)
        SH.cel(c, core, P.BUD, Lt, d=6, feather=3, rim_w=3, shade=P.BUD_DEEP)
        c.drawPath(core, gfx.paint(P.LINE_DEEP, 0.9, stroke=lw))
        for sgn in (-1, 1):
            c.save()
            c.rotate(sgn * (6 + 40 * q * q))
            sep = gfx.smooth_path([(0, 2), (sgn * 30, -14), (sgn * 26, -40), (sgn * 6, -50), (sgn * 8, -24)], closed=True)
            SH.cel(c, sep, P.BUD_GREEN, Lt, d=5, feather=2.5, rim_w=2.5, shade=P.BUD_GREEN_DEEP)
            c.drawPath(sep, gfx.paint(P.LINE_DEEP, 0.9, stroke=lw))
            c.restore()
    else:
        q = (o - 0.45) / 0.55
        R = 34 + 26 * q
        for k, (ang, rs, col) in enumerate(((-55, 1.0, P.BUD_DEEP), (55, 1.0, P.BUD_DEEP), (-18, 1.05, P.BUD),
                                             (18, 1.05, P.BUD), (0, 1.1, P.BUD))):
            c.save()
            c.rotate(ang * (0.5 + 0.5 * q))
            pet = gfx.smooth_path([(0, 0), (R * 0.55 * rs, -R * 0.5), (R * 0.45 * rs, -R * 1.05), (0, -R * 1.12 * rs),
                                   (-R * 0.45 * rs, -R * 1.05), (-R * 0.55 * rs, -R * 0.5)], closed=True)
            SH.cel(c, pet, col, Lt, d=6, feather=3, rim_w=3)
            c.drawPath(pet, gfx.paint(P.LINE_DEEP, 0.9, stroke=lw))
            c.restore()
        c.drawCircle(0, -R * 0.3, R * 0.2, gfx.paint((50, 30, 34)))
    c.restore()


def _star(c, x, y, r, alpha):
    p = gfx.poly([(x, y - r), (x + r * 0.16, y - r * 0.16), (x + r, y), (x + r * 0.16, y + r * 0.16), (x, y + r),
                  (x - r * 0.16, y + r * 0.16), (x - r, y), (x - r * 0.16, y - r * 0.16)])
    c.drawPath(p, gfx.paint((255, 255, 255), alpha))


def _convex_hull(pts):
    P_ = sorted(set((round(float(q[0]), 3), round(float(q[1]), 3)) for q in pts))
    if len(P_) < 3:
        return P_

    def cross(o, a, b):
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])
    lower, upper = [], []
    for p in P_:
        while len(lower) >= 2 and cross(lower[-2], lower[-1], p) <= 0:
            lower.pop()
        lower.append(p)
    for p in reversed(P_):
        while len(upper) >= 2 and cross(upper[-2], upper[-1], p) <= 0:
            upper.pop()
        upper.append(p)
    return lower[:-1] + upper[:-1]
