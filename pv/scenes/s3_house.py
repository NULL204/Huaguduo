"""0:46.90 – 1:02.85  A house.

SC11 house      warmth returns; a hall slams together piece by piece on the beats around 阿朵.
SC12 curtain    her red hand lifts the door curtain: a veiled bride lies in a ring of flowers —
                red for a wedding, white for a funeral, and you cannot tell which.
SC13 white      strands of silver beads, white cloth: the bride is wrapped in plain white.
SC14 rouge      cochineal crushed in a mortar on each beat; the rouge is brushed onto a hollow face.
SC15 queue      the bride enthroned among clouds and flowers; an endless queue of identical brides
                waits behind her; 阿朵 peeks from the curtain as the veil lifts on an empty face.
"""
import math

import numpy as np
import skia

from .. import config
from ..core import gfx, audio
from ..core import easing as E
from ..core import text as TXT
from ..core.camera import Cam
from ..core.noise import noise1, RNG, hash01
from ..elements import style as S
from ..elements.puppet import Puppet, walk, breathe, merge, PoseTrack, blend_pose, _cut_clouds
from ..elements.flower import draw_poppy_side, draw_poppy_front, draw_chrysanthemum
from ..elements.hand import draw_big_hand
from ..elements.insects import draw_cochineal
from ..elements import fx, particles as PT, thread as TH
from ..timeline import Entry
from .common import Stage, ground, W, H

T11, T12, T13, T14, T15, T16 = 46.90, 50.85, 54.85, 56.85, 58.85, 62.85


# --------------------------------------------------------------------------- the hall

def lattice(c, x, y, w, h, ink=S.INK, alpha=1.0, kind="fret", bar=5.0):
    """Carved window lattice: solid frame with geometric openings (light passes through)."""
    frame = gfx.rect(x, y, w, h)
    holes = skia.Path()
    if kind == "fret":
        cell = w / 5
        for i in range(5):
            for j in range(int(h / cell)):
                cx, cy = x + i * cell, y + j * cell
                holes.addRect(skia.Rect(cx + bar, cy + bar, cx + cell / 2 - bar / 2, cy + cell / 2 - bar / 2))
                holes.addRect(skia.Rect(cx + cell / 2 + bar / 2, cy + cell / 2 + bar / 2, cx + cell - bar, cy + cell - bar))
                holes.addRect(skia.Rect(cx + cell / 2 + bar / 2, cy + bar, cx + cell - bar, cy + cell / 2 - bar / 2))
                holes.addRect(skia.Rect(cx + bar, cy + cell / 2 + bar / 2, cx + cell / 2 - bar / 2, cy + cell - bar))
    else:  # ice-crack
        rng = RNG(int(x + y))
        pts = [(x + rng.u(0, w), y + rng.u(0, h)) for _ in range(14)]
        for (px, py) in pts:
            holes.addPath(gfx.poly([(px + rng.u(-28, -8), py + rng.u(-24, -6)), (px + rng.u(8, 28), py + rng.u(-24, -6)),
                                    (px + rng.u(8, 28), py + rng.u(6, 24)), (px + rng.u(-28, -8), py + rng.u(6, 24))]))
        holes = gfx.op(holes, gfx.rect(x + bar, y + bar, w - 2 * bar, h - 2 * bar), "inter")
    c.drawPath(gfx.op(frame, holes, "diff"), gfx.paint(ink, alpha))


def roof(c, cx, y, w, h, ink=S.INK, alpha=1.0):
    """Curved hip roof with upturned corners, tile rows, ridge and ornaments."""
    half = w / 2
    p = gfx.smooth_path([(cx - half - 70, y + h + 10), (cx - half - 40, y + h - 30), (cx - half + 30, y + h * 0.55),
                         (cx - half * 0.55, y + h * 0.2), (cx, y), (cx + half * 0.55, y + h * 0.2),
                         (cx + half - 30, y + h * 0.55), (cx + half + 40, y + h - 30), (cx + half + 70, y + h + 10),
                         (cx + half + 10, y + h), (cx - half - 10, y + h)], closed=True, tension=0.4)
    c.drawPath(p, gfx.paint(ink, alpha))
    tiles = skia.Path()
    for k in range(-14, 15):
        xx = cx + k * half / 14
        tiles.addPath(gfx.ribbon([(xx, y + h * 0.12 + abs(k) * 1.5), (xx * 1.0 + k * 3, y + h * 0.96)], [1.5, 3.0]))
    c.drawPath(tiles, gfx.paint((236, 214, 180), 0.45 * alpha, blend=gfx.SCREEN))
    ridge = gfx.rect(cx - half * 0.6, y - 18, half * 1.2, 22)
    c.drawPath(ridge, gfx.paint(ink, alpha))
    for sgn in (-1, 1):
        ox = cx + sgn * half * 0.6
        orn = gfx.smooth_path([(ox, y - 16), (ox + sgn * 30, y - 60), (ox + sgn * 10, y - 70), (ox - sgn * 10, y - 30)], closed=True)
        c.drawPath(orn, gfx.paint(ink, alpha))
    c.drawPath(gfx.ellipse(cx, y - 30, 22, 22), gfx.paint(S.LEATHER_RED, 0.9 * alpha, blend=gfx.MULTIPLY))
    c.drawPath(gfx.ellipse(cx, y - 30, 22, 22), gfx.paint(ink, alpha, stroke=3))


def lantern(c, x, y, r, lit=1.0, t=0.0, seed=0, alpha=1.0, char=None):
    sw = 3 * noise1(t * 1.3 + seed, 4)
    c.drawLine(x, y - r * 2.0, x + sw, y - r, gfx.paint(S.INK, alpha, stroke=2))
    col = S.lerp3((150, 120, 120), (232, 60, 52), lit)
    body = gfx.ellipse(x + sw, y, r * 0.9, r)
    c.drawPath(body, gfx.paint(col, 0.95 * alpha, blend=gfx.MULTIPLY))
    for j in (-2, -1, 0, 1, 2):
        c.drawPath(gfx.ellipse(x + sw, y, abs(j) * r * 0.2 + 0.1, r), gfx.paint(S.INK, alpha * 0.55, stroke=1.2))
    c.drawPath(body, gfx.paint(S.INK, alpha, stroke=2.2))
    c.drawPath(gfx.rect(x + sw - r * 0.5, y - r * 1.1, r, r * 0.2), gfx.paint(S.INK, alpha))
    c.drawPath(gfx.rect(x + sw - r * 0.5, y + r * 0.9, r, r * 0.2), gfx.paint(S.INK, alpha))
    for j in range(5):
        tx = x + sw - r * 0.4 + j * r * 0.2
        c.drawLine(tx, y + r * 1.1, tx + sw * 0.3, y + r * 1.8, gfx.paint(S.INK, alpha, stroke=1.2))
    if char:
        TXT.draw_text(c, char, x + sw, y - r * 0.55, r * 1.1, face="serif_black", color=(30, 16, 14, int(230 * alpha)),
                      align="center")


class HouseScene(Stage):
    light = "warm"

    def setup(self):
        self.duo = Puppet("woman", arm_red=0.9, seed=1)
        b0 = audio.beat_index(48.9) + 1
        # platform, pillars on the off-beat, lattice, roof, lanterns light — all inside the shot
        offs = (0.0, 0.5, 1.0, 2.0, 3.0)
        self.slam = [audio.beat_time(b0) + o * config.BEAT - self.start for o in offs]

    def light_params(self, t, lt, u):
        warm = E.smooth(E.prog(lt, 0.0, 1.6))
        pc = (0.80 + 0.2 * warm, 0.86 + 0.08 * warm, 0.96 - 0.12 * warm)
        lit = E.smooth(E.prog(lt, self.slam[4] - 0.05, self.slam[4] + 0.3))
        return dict(paper=pc, warm=0.2 + 0.8 * warm, boost=0.08 * lit + 0.05 * audio.beat_pulse(t, 0.15) * (lt > self.slam[0]))

    def piece(self, lt, k):
        """Drop-in offset and alpha for house piece k."""
        ts = self.slam[k]
        d = E.prog(lt, ts - 0.22, ts)
        if d <= 0:
            return None
        y = -700 * (1 - E.in_quad(d))
        bounce = 14 * E.bump(lt, ts, ts + 0.05, ts + 0.06, ts + 0.25)
        return y - bounce

    def paint(self, fr, t, lt, u):
        c = fr.canvas
        imp = sum(E.pulse(lt, ts, 0.01, 0.12) for ts in self.slam)
        cam = Cam(W / 2, H / 2 + 30, 1.0 + 0.04 * u, t=t, shake=0.35 * min(1.0, imp))
        c.save()
        cam.apply(c)
        cx = W / 2
        ground(c, 940, seed=3, style="stone", t=t)
        # platform
        oy = self.piece(lt, 0)
        if oy is not None:
            c.save(); c.translate(0, oy)
            c.drawPath(gfx.rect(cx - 640, 880, 1280, 60), gfx.paint(S.INK, 0.97))
            for k in range(5):
                c.drawPath(gfx.rect(cx - 160 + k * 8, 900 + k * 10, 320 - k * 16, 8), gfx.paint((236, 214, 180), 0.5, blend=gfx.SCREEN))
            c.restore()
        oy = self.piece(lt, 1)
        if oy is not None:
            c.save(); c.translate(0, oy)
            for px in (-520, -200, 200, 520):
                c.drawPath(gfx.rect(cx + px - 22, 430, 44, 452), gfx.paint(S.INK, 0.97))
                c.drawPath(gfx.rect(cx + px - 34, 860, 68, 22), gfx.paint(S.INK, 0.97))
            c.restore()
        oy = self.piece(lt, 2)
        if oy is not None:
            c.save(); c.translate(0, oy)
            c.drawPath(gfx.rect(cx - 600, 400, 1200, 40), gfx.paint(S.INK, 0.97))
            lattice(c, cx - 498, 470, 276, 330, kind="fret")
            lattice(c, cx + 222, 470, 276, 330, kind="fret")
            # doorway with the red curtain
            c.drawPath(gfx.rect(cx - 178, 440, 356, 26), gfx.paint(S.INK, 0.97))
            cur = gfx.rect(cx - 170, 466, 340, 300)
            c.drawPath(cur, gfx.paint(S.LEATHER_RED, 0.92, blend=gfx.MULTIPLY))
            cl = skia.Path()
            for k in range(3):
                cl.addPath(_cut_clouds(cx - 90 + k * 90, 560, 2.2))
            c.drawPath(cl, gfx.paint(S.INK, 0.9))
            c.drawPath(cur, gfx.paint(S.INK, 1.0, stroke=3))
            c.restore()
        oy = self.piece(lt, 3)
        if oy is not None:
            c.save(); c.translate(0, oy)
            roof(c, cx, 160, 1200, 250)
            c.restore()
        lit = E.smooth(E.prog(lt, self.slam[4] - 0.05, self.slam[4] + 0.3))
        if self.piece(lt, 4) is not None or lit > 0:
            for k, lx in enumerate((-668, 668)):
                lantern(c, cx + lx, 520 + (self.piece(lt, 4) or 0) * 0.3, 50, lit=lit, t=t, seed=k, char="囍")
        # A-Duo in front of the hall, looking up
        look = E.smooth(E.prog(lt, 0.0, 1.0))
        pose = merge(breathe(lt), {"head": -14 * look, "ua_f": 10 + 50 * E.bump(lt, 0.2, 0.8, 1.6, 2.2), "fa_f": 30,
                                   "hand_f": "open", "bud_open": 0.16})
        self.duo.draw(c, cx + 300, 1000, 0.62, pose=pose, t=t, flip=True)
        c.restore()

    def after_light(self, fr, t, lt, u):
        c = fr.canvas
        # dust puffs on each slam
        for k, ts in enumerate(self.slam[:4]):
            PT.draw_burst(c, lt, ts, W / 2 + (k - 1.5) * 300, 900, n=26, seed=k + 3, speed=(120, 420), size=(2, 6),
                          color=(220, 200, 170), gravity=200, life=0.8, alpha=0.6, blend=gfx.SCREEN, spread=(math.pi, 2 * math.pi))
        lit = E.smooth(E.prog(lt, self.slam[4] - 0.05, self.slam[4] + 0.3))
        PT.draw_snow(c, t, n=120, seed=13, alpha=0.7 * (1 - E.smooth(E.prog(lt, 0, 1.5))), count=1.0)
        flash = max(E.pulse(lt, ts, 0.01, 0.1) for ts in self.slam)
        return {"glow": {"thr": 0.82, "strength": 0.35 + 0.3 * lit, "red": 0.6}, "flash": 0.12 * flash,
                "grade": dict(sat=0.6 + 0.4 * E.smooth(E.prog(lt, 0, 1.6)))}


class CurtainScene(Stage):
    light = "warm"

    def setup(self):
        self.bride = Puppet("bride", arm_red=0.0, veil=True, bloom=1.0, face="empty", seed=31, hair_tail=False)

    def light_params(self, t, lt, u):
        reveal = E.smooth(E.prog(lt, 0.8, 2.0))
        return dict(paper=(1.0 - 0.06 * reveal, 0.95, 0.88 + 0.1 * reveal), warm=1.0 - 0.7 * reveal, radius=1.2)

    def paint(self, fr, t, lt, u):
        c = fr.canvas
        z = 1.0 + 0.18 * E.in_out_sine(u)
        cam = Cam(W / 2, H / 2, z, t=t)
        c.save()
        cam.apply(c)
        cx, cy = W / 2, 600
        # interior: the wreath of flowers with the bride lying in it (top-down)
        R = 330
        rng = RNG(4)
        for k in range(46):
            a = 2 * math.pi * k / 46
            rr = R * (1 + 0.06 * noise1(k, 3))
            x, y = cx + math.cos(a) * rr * 1.25, cy + math.sin(a) * rr * 0.82
            if k % 2:
                draw_chrysanthemum(c, x, y, 60 + 10 * hash01(k, 2), rot=a + hash01(k, 5), seed=k, alpha=0.97)
            else:
                draw_poppy_front(c, x, y, 50 + 10 * hash01(k, 2), openness=0.9, rot=a + hash01(k, 5), seed=k, alpha=0.95,
                                 veins=False)
        # leaves between
        for k in range(30):
            a = 2 * math.pi * (k + 0.5) / 30
            x, y = cx + math.cos(a) * R * 1.05, cy + math.sin(a) * R * 0.7
            c.drawPath(gfx.ellipse(x, y, 30, 10), gfx.paint(S.LEATHER_GREEN_DEEP, 0.9, blend=gfx.MULTIPLY))
        # the bride lying (rotated puppet), hands crossed
        self.bride.draw(c, cx + 290, cy + 60, 0.86, pose={"lean": 90, "ua_f": 150, "fa_f": 60, "ua_b": 140, "fa_b": 70,
                                                          "hand_f": "flat", "hand_b": "flat"}, t=t)
        c.restore()
        # the curtain being lifted, and her hand
        lift = E.in_out_cubic(E.prog(lt, 0.4, 1.9))
        top = -40 - 1100 * lift
        cur = gfx.smooth_path([(-60, -200), (W + 60, -200), (W + 60, top + 1150), (W * 0.75, top + 1170 + 40 * lift),
                               (W * 0.5, top + 1150 + 80 * lift), (W * 0.25, top + 1170 + 40 * lift), (-60, top + 1150)], closed=True)
        c.drawPath(cur, gfx.paint(S.LEATHER_RED, 0.95, blend=gfx.MULTIPLY))
        cl = skia.Path()
        for i in range(5):
            for j in range(3):
                cl.addPath(_cut_clouds(200 + i * 380, top + 400 + j * 280, 3.0))
        c.drawPath(gfx.op(cl, cur, "inter"), gfx.paint(S.INK, 0.85))
        c.drawPath(cur, gfx.paint(S.INK, 1.0, stroke=4))
        # door frame
        c.drawPath(gfx.op(gfx.rect(-40, -40, W + 80, H + 80), gfx.rect(150, 40, W - 300, H - 40), "diff"), gfx.paint(S.INK, 0.97))
        hx = 1240 + 40 * lift
        hy = top + 1250
        if hy < H + 300:
            draw_big_hand(c, hx, hy + 300, 1.25, rot=math.pi * 0.98, openness=0.75, redness=0.9, t=t, sleeve=True)

    def after_light(self, fr, t, lt, u):
        reveal = E.smooth(E.prog(lt, 0.9, 2.2))
        PT.draw_dust(fr.canvas, t, n=60, alpha=0.3 + 0.2 * reveal, color=(255, 250, 240))
        return {"glow": {"thr": 0.82, "strength": 0.35, "red": 0.5}, "grade": dict(sat=1.0 - 0.35 * reveal)}


class WhiteScene(Stage):
    light = "white"

    def setup(self):
        self.bride = Puppet("bride", arm_red=0.0, veil=True, bloom=1.0, face="empty", seed=31, hair_tail=False)

    def paint(self, fr, t, lt, u):
        c = fr.canvas
        # bride standing, being wrapped in white cloth (pale silhouette behind the beads)
        with gfx.Layer(c, blur=3, alpha=0.82) as lc:
            self.bride.draw(lc, W / 2, 1060, 1.35, pose={"ua_f": 10, "fa_f": 6, "ua_b": -4}, t=t)
        wrap = E.out_cubic(E.prog(lt, 0.1, 1.8))
        for k in range(4):
            y0 = 140 + k * 220
            cloth = gfx.smooth_path([(W / 2 - 260, y0 + 60 * math.sin(lt + k)), (W / 2, y0 - 30 + 20 * math.sin(lt * 1.3 + k)),
                                     (W / 2 + 260, y0 + 50 * math.sin(lt + k + 1)), (W / 2 + 270, y0 + 120), (W / 2, y0 + 90),
                                     (W / 2 - 270, y0 + 130)], closed=True)
            c.save()
            c.clipRect(skia.Rect(0, 0, W * wrap + 100, H))
            c.drawPath(cloth, gfx.paint((236, 236, 240), 0.55, blend=gfx.MULTIPLY))
            c.restore()
        # strands of silver beads swaying in front, in three depth layers
        rng = RNG(12)
        for layer, (n_str, rmin, rmax, blur, a) in enumerate(((9, 7, 10, 2.0, 0.55), (11, 11, 15, 0.0, 0.92), (6, 22, 30, 6.0, 0.75))):
            for i in range(n_str):
                x0 = (i + 0.5) * W / n_str + rng.u(-40, 40)
                amp = (14 + 10 * layer) * (0.7 + 0.6 * hash01(i, layer))
                sway = amp * math.sin(lt * (1.3 + 0.3 * layer) + i * 0.7 + layer)
                r = rng.u(rmin, rmax)
                gap = r * 2.5
                n = int(H / gap) + 3
                strand = skia.Path()
                hl = skia.Path()
                pts = []
                for j in range(n):
                    v = j / n
                    xx = x0 + sway * v * v + 6 * math.sin(lt * 2 + j * 0.5 + i)
                    yy = -30 + j * gap + 8 * math.sin(lt + i)
                    pts.append((xx, yy))
                    strand.addCircle(xx, yy, r)
                    hl.addCircle(xx - r * 0.32, yy - r * 0.32, r * 0.3)
                c.drawPath(gfx.poly(pts, closed=False), gfx.paint((110, 116, 130), a * 0.6, stroke=1.2, blur=blur))
                c.drawPath(strand, gfx.paint((150, 158, 172), a, blur=blur))
                c.drawPath(strand, gfx.paint((90, 96, 110), a * 0.6, stroke=1.2, blur=blur))
                c.drawPath(hl, gfx.paint((255, 255, 255), a, blur=blur * 0.5 + 0.5, blend=gfx.SCREEN))

    def after_light(self, fr, t, lt, u):
        c = fr.canvas
        PT.draw_snow(c, t, n=160, seed=14, wind=10, fall=(30, 70), size=(2, 6), alpha=0.8, color=(255, 255, 255))
        return {"grade": dict(sat=0.15, contrast=1.05, gain=(1.02, 1.02, 1.05)), "glow": {"thr": 0.8, "strength": 0.35}}


class RougeScene(Stage):
    light = "red"

    def setup(self):
        b0 = audio.beat_index(self.start)
        self.hits = [audio.beat_time(b0 + k) - self.start for k in range(1, 4)]
        self.face = Puppet("bride", arm_red=0.0, veil=False, bloom=1.0, face="empty", seed=33, hair_tail=False)
        self.t_face = 1.3

    def light_params(self, t, lt, u):
        h = max([E.pulse(lt, ts, 0.01, 0.15) for ts in self.hits] + [0])
        return dict(boost=0.2 * h)

    def paint(self, fr, t, lt, u):
        c = fr.canvas
        if lt < self.t_face:
            imp = max([E.pulse(lt, ts, 0.01, 0.15) for ts in self.hits] + [0])
            cam = Cam(W / 2, H / 2, 1.05 + 0.06 * imp, t=t, shake=0.8 * imp)
            c.save()
            cam.apply(c)
            # mortar (front view) full of cochineal
            mx, my = W / 2, 760
            bowl = gfx.smooth_path([(mx - 380, my - 160), (mx + 380, my - 160), (mx + 330, my + 80), (mx + 220, my + 200),
                                    (mx - 220, my + 200), (mx - 330, my + 80)], closed=True)
            # crushed carmine accumulating inside
            crushed = sum(1 for ts in self.hits if lt >= ts) / len(self.hits)
            for k in range(14):
                draw_cochineal(c, mx - 300 + k * 46, my - 170 + 10 * math.sin(k), 0.9, -math.pi / 2 + 0.4 * noise1(k, 3),
                               t=t, crushed=min(1.0, crushed * 1.5) if k % 3 != 1 else crushed, seed=k)
            c.drawPath(bowl, gfx.paint(S.INK, 0.97))
            cut = skia.Path()
            for k in range(6):
                cut.addPath(_cut_clouds(mx - 250 + k * 100, my + 40, 2.0))
            c.drawPath(cut, gfx.paint((240, 200, 180), 0.5, blend=gfx.SCREEN))
            # pestle
            ts_next = next((ts for ts in self.hits if ts >= lt - 0.12), self.hits[-1] + 1)
            k = E.prog(lt, ts_next - 0.4, ts_next)
            up = (1 - E.in_quad(k)) * 360 if lt < ts_next else 0
            px, py = mx + 40, my - 220 - up
            c.save()
            c.translate(px, py)
            c.rotate(-12)
            c.drawPath(gfx.smooth_path([(-30, 40), (30, 40), (22, -500), (-22, -500)], closed=True), gfx.paint(S.INK, 0.97))
            c.drawPath(gfx.ellipse(0, 40, 44, 26), gfx.paint(S.INK, 0.97))
            c.restore()
            for j, ts in enumerate(self.hits):
                fx.draw_splash(c, mx + 40 + 60 * (j - 1), my - 160, 160 + 60 * j, color=S.ROUGE, growth=E.prog(lt, ts, ts + 0.25),
                               seed=j + 7, alpha=E.prog(lt, ts, ts + 0.02) * (1 - 0.5 * E.prog(lt, ts + 0.4, self.t_face)))
                PT.draw_burst(c, lt, ts, mx + 40, my - 160, n=40, seed=j + 20, speed=(300, 1100), size=(4, 14),
                              color=S.ROUGE, gravity=1400, life=1.0)
            c.restore()
        else:
            # profile of a bride's face receiving rouge
            k = E.prog(lt, self.t_face, self.t_face + 0.6)
            cam = Cam(W / 2 + 40, H / 2, 1.0, t=t)
            c.save()
            c.translate(843, 3061)
            c.scale(4.6, 4.6)
            self.face.draw(c, 0, 0, 1.0, pose={"head": 0}, t=t)
            c.restore()
            # blush, then the rouge stroke across the lips
            c.drawCircle(880, 600, 60 * E.smooth(k), gfx.paint(S.ROUGE, 0.5, blur=30, blend=gfx.MULTIPLY))
            pts = gfx.bezier_pts((926, 676), (944, 664), (968, 662), (992, 668), 20)
            seg = gfx.polyline_cut(pts, E.out_cubic(k))
            if len(seg) > 1:
                c.drawPath(gfx.ribbon(seg, np.linspace(26, 10, len(seg))), gfx.paint(S.ROUGE, 0.95, blur=2, blend=gfx.MULTIPLY))
            # brush
            bx, by = seg[-1]
            c.save()
            c.translate(bx, by)
            c.rotate(35)
            c.drawPath(gfx.smooth_path([(0, 0), (16, -40), (10, -80), (-10, -80), (-16, -40)], closed=True), gfx.paint(S.ROUGE_DEEP, 0.95))
            c.drawPath(gfx.rect(-8, -500, 16, 420), gfx.paint(S.INK, 0.97))
            c.restore()

    def after_light(self, fr, t, lt, u):
        h = max([E.pulse(lt, ts, 0.01, 0.12) for ts in self.hits] + [0])
        return {"glow": {"thr": 0.8, "strength": 0.4 + 0.4 * h, "red": 0.8}, "flash": 0.25 * h, "flash_color": (255, 60, 60),
                "chroma": 6 * h, "grade": dict(contrast=1.12, sat=1.15)}


class QueueScene(Stage):
    light = "warm"

    def setup(self):
        self.bride = Puppet("bride", arm_red=0.0, veil=True, bloom=1.0, face="empty", seed=31, hair_tail=False)
        self.unveiled = Puppet("bride", arm_red=0.0, veil=False, bloom=1.0, face="empty", seed=31, hair_tail=False)
        self.duo = Puppet("woman", arm_red=0.85, seed=1)
        self.t_veil = 2.0
        self.t_close = 2.6
        self.t_duo = 3.3

    def light_params(self, t, lt, u):
        return dict(radius=1.25, edge=0.3)

    def paint(self, fr, t, lt, u):
        c = fr.canvas
        tv, tc, td = self.t_veil, self.t_close, self.t_duo
        if lt < tc:
            z = 1.0 + 0.1 * E.in_out_sine(lt / tc)
            cam = Cam(W / 2, H / 2, z, t=t)
            c.save()
            cam.apply(c)
            # ghostly calligraphy of Li Bai's line (public domain) behind everything
            TXT.draw_text(c, "云想衣裳花想容", W / 2, 110, 120, face="running", color=(120, 90, 70, 60), align="center")
            # drifting ruyi clouds
            cl = skia.Path()
            for k in range(9):
                x = (k * 260 + lt * 40) % (W + 300) - 150
                cl.addPath(_cut_clouds(x, 300 + 40 * math.sin(k), 4.0))
            c.drawPath(cl, gfx.paint((90, 70, 60), 0.35))
            # the queue: identical brides receding to the left
            for k in range(8, 0, -1):
                s = 0.9 * (0.82 ** k)
                x = 840 - 150 * (1 - 0.82 ** k) / 0.18
                y = 990 - 260 * (1 - 0.82 ** k) / 0.18 * 0.3
                self.bride.draw(c, x, y, s, pose={"ua_f": 12, "fa_f": 70, "ua_b": 8, "fa_b": 70, "hand_f": "flat", "hand_b": "flat"},
                                t=t + k * 0.3)
            # throne with flowers
            tx = 1080
            back = gfx.smooth_path([(tx - 220, 1000), (tx - 240, 520), (tx - 160, 470), (tx + 160, 470), (tx + 240, 520),
                                    (tx + 220, 1000)], closed=True)
            c.drawPath(back, gfx.paint(S.LEATHER_RED_DEEP, 0.85, blend=gfx.MULTIPLY))
            cl2 = skia.Path()
            for j in range(3):
                for i in range(2):
                    cl2.addPath(_cut_clouds(tx - 110 + i * 220, 580 + j * 140, 2.4))
            c.drawPath(cl2, gfx.paint(S.INK, 0.85))
            c.drawPath(back, gfx.paint(S.INK, 1.0, stroke=6))
            for k in range(9):
                a = math.pi * (1.05 + 0.9 * k / 8)
                draw_poppy_front(c, tx + math.cos(a) * 280, 560 + math.sin(a) * 200, 60, openness=1.0, rot=a, seed=k + 50, alpha=0.95)
            veil_up = E.in_out_cubic(E.prog(lt, tv, tv + 0.5))
            pz = self.unveiled if veil_up > 0.5 else self.bride
            pz.draw(c, tx, 960, 0.9, pose={"ua_f": 30, "fa_f": 70, "ua_b": 24, "fa_b": 74, "hand_f": "flat", "hand_b": "flat", "head": -2},
                    t=t)
            if 0 < veil_up <= 0.5:
                pass
            c.restore()
            # A-Duo peeking from behind the curtain at the right edge
            c.drawPath(gfx.rect(W - 230, -20, 260, H + 40), gfx.paint(S.LEATHER_RED, 0.95, blend=gfx.MULTIPLY))
            c.drawPath(_cut_clouds(W - 110, 300, 3.0), gfx.paint(S.INK, 0.8))
            c.drawPath(_cut_clouds(W - 110, 700, 3.0), gfx.paint(S.INK, 0.8))
            self.duo.draw(c, W - 70, 1180, 1.05, pose={"head": 6, "lean": -8, "ua_f": 60, "fa_f": 100, "hand_f": "relax", "bud_open": 0.16},
                          t=t, flip=True)
            c.drawPath(gfx.rect(W - 120, -20, 160, H + 40), gfx.paint(S.LEATHER_RED, 0.95, blend=gfx.MULTIPLY))
            c.drawPath(gfx.rect(W - 120, -20, 160, H + 40), gfx.paint(S.INK, 1.0, stroke=3))
        elif lt < td:
            # push in on the emptied face
            k = E.out_cubic(E.prog(lt, tc, td))
            c.save()
            c.translate(W / 2 - 40, H / 2 + 40)
            sc = 5.0 + 1.2 * k
            c.scale(sc, sc)
            c.translate(-20, 552)
            self.unveiled.draw(c, 0, 0, 1.0, pose={"head": -2}, t=t)
            c.restore()
        else:
            # cut to 阿朵's living eye
            k = E.out_cubic(E.prog(lt, td, self.end - self.start))
            c.save()
            c.translate(W / 2 + 40, H / 2 + 40)
            sc = 5.0 + 0.8 * k
            c.scale(-sc, sc)
            c.translate(-20, 552)
            Puppet("woman", arm_red=0.85, seed=1).draw(c, 0, 0, 1.0, pose={"head": -6, "bud_open": 0.16}, t=t)
            c.restore()

    def after_light(self, fr, t, lt, u):
        k = E.bump(lt, self.t_close - 0.05, self.t_close, self.t_close + 0.05, self.t_close + 0.3)
        k2 = E.bump(lt, self.t_duo - 0.05, self.t_duo, self.t_duo + 0.05, self.t_duo + 0.3)
        return {"glow": {"thr": 0.84, "strength": 0.35, "red": 0.6}, "flash": 0.3 * max(k, k2), "chroma": 4 * max(k, k2)}


def entries():
    return [
        Entry(HouseScene(T11, T12), trans=("fade", 0.6)),
        Entry(CurtainScene(T12, T13), trans=("fade", 0.3)),
        Entry(WhiteScene(T13, T14), trans=("white", 0.4)),
        Entry(RougeScene(T14, T15)),
        Entry(QueueScene(T15, T16), trans=("fade", 0.25)),
    ]
