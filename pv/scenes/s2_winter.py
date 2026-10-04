"""0:30.90 – 0:46.90  Last winter.

SC08 winter branch  snow on a black branch; withered buds let go one by one on the beat.
SC09 no sunrise     the lamp itself becomes a pale sun that tries to rise and sinks back; frost creeps in.
SC10a alley         a deserted lane in perspective; fallen buds lie in the snow — only 阿朵 gets up.
SC10b lonely shadow she walks the lane; a second lamp throws a huge, blurred shadow of her on the wall.
"""
import math

import numpy as np
import skia

from .. import config
from ..core import gfx, audio
from ..core import easing as E
from ..core.camera import Cam
from ..core.noise import noise1, RNG, hash01
from ..elements import style as S
from ..elements.branch import BranchTree
from ..elements.puppet import Puppet, walk, breathe, merge, PoseTrack, blend_pose
from ..elements.flower import draw_poppy_side
from ..elements import fx, particles as PT
from ..elements.landscape import Mountains, draw_mist
from ..timeline import Entry
from .common import Stage, ground, W, H

T8, T9, T10, T10B, T11 = 30.90, 34.85, 38.90, 42.85, 46.90
COLD_INK = (14, 18, 26)


def snow_caps(c, tree, color=S.SNOW, alpha=0.95, growth=1.0):
    """White caps along the upper edge of every limb."""
    for limb in tree.limbs:
        if limb.t0 > growth:
            continue
        pts = limb.pts
        ws = limb.widths
        if len(pts) < 3 or ws[0] < 3:
            continue
        P = np.asarray(pts)
        top = [(x, y - w * 0.5) for (x, y), w in zip(pts, ws)]
        cap = [(x, y - w * 0.18 - 2) for (x, y), w in zip(top, ws)]
        poly = top + cap[::-1]
        c.drawPath(gfx.smooth_path(poly, closed=True), gfx.paint(color, alpha))


class WinterBranchScene(Stage):
    light = "cold"

    def setup(self):
        self.tree = BranchTree(seed=77, root=(2060, 240), angle=math.pi * 0.96, length=1700, width=96, depth=4,
                               spread=0.62, wander=0.14, children=(2, 4), droop=0.5, length_decay=0.66).normalize_time()
        tips = [tp for tp in self.tree.tip_list(1.0) if 60 < tp[0] < W - 60 and 60 < tp[1] < 860]
        rng = RNG(3)
        self.buds = []
        for tp in tips:
            if all((tp[0] - q[0]) ** 2 + (tp[1] - q[1]) ** 2 > 70 ** 2 for q in self.buds):
                self.buds.append(tp)
        self.buds = self.buds[:22]
        # each bud falls on a beat
        beats = [audio.beat_time(k) for k in range(audio.beat_index(self.start) + 1, audio.beat_index(self.end) + 1)]
        self.fall = []
        order = rng.r.permutation(len(self.buds))
        for j, i in enumerate(order):
            bt = beats[(j * 1) % len(beats)] if j < len(beats) else 1e9
            self.fall.append(bt - self.start if j % 2 == 0 or j < 3 else 1e9)
        self.ground_buds = [(rng.u(80, W - 80), rng.u(1010, 1150), rng.u(0, 6.28), rng.u(0.9, 1.3)) for _ in range(22)]

    def light_params(self, t, lt, u):
        return dict(boost=-0.05 + 0.04 * audio.beat_pulse(t, 0.2))

    def paint(self, fr, t, lt, u):
        c = fr.canvas
        tilt = E.in_out_sine(E.prog(lt, 1.0, 3.95))
        cam = Cam(W / 2, H / 2 + 120 * tilt, 1.0 + 0.06 * u, t=t, shake=0.0)
        c.save()
        cam.apply(c)
        # faint far hills
        c.drawPath(gfx.blob(500, 820, 520, 0.15, seed=4), gfx.paint((150, 160, 180), 0.25, blur=40))
        self.tree.draw(c, 1.0, style="cut", color=COLD_INK)
        snow_caps(c, self.tree)
        for i, (x, y, a, d) in enumerate(self.buds):
            tf = self.fall[i]
            if lt < tf:
                sway = 0.15 * noise1(t * 1.4 + i, 7)
                c.drawLine(x, y, x + 2, y + 26, gfx.paint(COLD_INK, 1.0, stroke=2.0))
                draw_poppy_side(c, x + 2, y + 26, 1.25, math.pi + sway, openness=0.0, seed=i, petal=(120, 96, 100),
                                sepal=(110, 120, 104), stem_len=4)
            else:
                k = lt - tf
                yy = y + 26 + 0.5 * 900 * k * k
                xx = x + 60 * k + 24 * math.sin(k * 5 + i)
                if yy < 1150:
                    draw_poppy_side(c, xx, yy, 1.25, math.pi + k * (4 + i % 3), openness=0.0, seed=i,
                                    petal=(120, 96, 100), sepal=(110, 120, 104), stem_len=4)
        # the snowy ground with fallen buds
        c.drawPath(gfx.poly([(-200, 1040), (W + 200, 1020), (W + 200, 1600), (-200, 1600)]),
                   gfx.paint((236, 240, 248), 1.0))
        for (x, y, a, s) in self.ground_buds:
            draw_poppy_side(c, x, y, s, a, openness=0.0, seed=int(x), petal=(110, 90, 96), sepal=(110, 116, 104),
                            stem_len=3, alpha=0.9)
        c.restore()

    def after_light(self, fr, t, lt, u):
        c = fr.canvas
        gust = 0.5 + 0.5 * math.sin(lt * 1.3)
        PT.draw_snow(c, t, n=420, seed=8, wind=120 + 160 * gust, fall=(80, 220), size=(1.2, 6.5), alpha=0.95)
        return {"grade": dict(sat=0.55, gain=(0.92, 0.97, 1.08), lift=(0.02, 0.03, 0.06)),
                "glow": {"thr": 0.9, "strength": 0.2}}


class NoSunriseScene(Stage):
    light = "night"

    def setup(self):
        self.frost = fx.Frost(seed=5, n=34, length=(160, 420))
        self.m = Mountains(seed=31, base=820, height=170, freq=0.0022)
        self.horizon = 820

    def sun(self, lt):
        # rises a little, hesitates, sinks back below the ridge
        y = E.Track([(0.0, 900), (1.6, 700, "out_cubic"), (2.3, 690, "linear"), (4.05, 930, "in_cubic")])(lt)
        return 1120, y

    def light_params(self, t, lt, u):
        sx, sy = self.sun(lt)
        above = E.clamp((self.horizon - sy + 120) / 260)
        return dict(cx=sx / W, cy=sy / H, radius=0.7 + 0.35 * above, power=1.5, edge=0.16 + 0.1 * above,
                    paper=(0.76 + 0.2 * above, 0.82 + 0.14 * above, 0.95))

    def paint(self, fr, t, lt, u):
        c = fr.canvas
        sx, sy = self.sun(lt)
        # the sun disc: a pale paper circle (a hole in the scenery)
        c.drawCircle(sx, sy, 150, gfx.paint((205, 212, 228), 0.6, blur=40))
        # thin cloud bands across it
        for k in range(4):
            yy = 600 + k * 70 + 8 * noise1(t * 0.3 + k, 2)
            c.drawPath(gfx.ellipse(sx - 200 + 140 * noise1(k + t * 0.1, 5), yy, 420, 10 + 4 * k), gfx.paint((70, 78, 96), 0.45, blur=8))
        # cover the sky outside the disc with dusk tone
        sky = gfx.op(gfx.rect(-50, -50, W + 100, self.horizon + 60), gfx.circle(sx, sy, 92), "diff")
        c.drawPath(sky, gfx.paint((58, 66, 92), 0.88, blur=2.5, blend=gfx.MULTIPLY))
        # halo + faint banding inside the disc
        c.drawCircle(sx, sy, 92, gfx.paint((236, 240, 248), 0.25, stroke=6, blur=4))
        self.m.draw(c, tone=(26, 30, 42), alpha=0.95, blur=1.5, mist=0.1, snow=0.85)
        c.drawPath(gfx.poly([(-50, self.horizon), (W + 50, self.horizon - 10), (W + 50, H + 50), (-50, H + 50)]),
                   gfx.paint((214, 222, 236), 1.0))
        # a lone small figure hunched in the snow, far away
        Puppet("woman", arm_red=0.8, seed=1).draw(c, 520, 930, 0.32, pose={"torso": 18, "head": 20, "ua_f": 40, "fa_f": 120,
                                                                             "ua_b": 30, "fa_b": 120, "hair": 0.5}, t=t)

    def after_light(self, fr, t, lt, u):
        c = fr.canvas
        g = E.in_out_sine(E.prog(lt, 0.2, 3.9))
        self.frost.draw(c, g, alpha=0.8)
        PT.draw_snow(c, t, n=300, seed=9, wind=520, fall=(40, 120), size=(1.0, 4.5), alpha=0.85)
        return {"grade": dict(sat=0.5, gain=(0.9, 0.96, 1.1), lift=(0.02, 0.03, 0.07))}


def alley_geometry(vx=960, vy=470):
    return vx, vy


class AlleyScene(Stage):
    light = "cold"

    def setup(self):
        self.duo = Puppet("woman", arm_red=0.95, seed=1)
        self.fallen = [Puppet("woman", arm_red=0.85 - 0.1 * (k % 3), seed=20 + k, huadian=False) for k in range(6)]
        rng = RNG(9)
        self.fallen_pos = [(260, 1010, 0.62, 1), (650, 1060, 0.7, -1), (1420, 1040, 0.66, 1), (1700, 990, 0.55, -1),
                           (420, 930, 0.45, 1), (1240, 925, 0.42, -1)]
        self.t_rise = 1.4

    def light_params(self, t, lt, u):
        return dict(cy=0.36, radius=1.1, power=1.3, edge=0.25)

    def draw_alley(self, c, t):
        vx, vy = alley_geometry()
        ink = COLD_INK
        # walls: left and right planes
        for side in (-1, 1):
            x_edge = -60 if side < 0 else W + 60
            wall = gfx.poly([(x_edge, 150), (vx + side * 60, vy - 40), (vx + side * 60, vy + 40), (x_edge, H + 60)])
            c.drawPath(wall, gfx.paint(ink, 0.96))
            # doors / windows in perspective (carved, light passes through)
            for k in range(7):
                d0 = 0.08 + k * 0.13
                d1 = d0 + 0.07
                if d1 > 0.95:
                    break

                def P(d, h):
                    # d: 0 at the near edge, 1 at the vanishing point; h: 0 floor .. 1 top
                    x = x_edge + (vx + side * 60 - x_edge) * d
                    ytop = 150 + (vy - 40 - 150) * d
                    ybot = H + 60 + (vy + 40 - H - 60) * d
                    return x, ybot + (ytop - ybot) * h
                win = gfx.poly([P(d0, 0.42), P(d1, 0.42), P(d1, 0.62), P(d0, 0.62)])
                lat = gfx.poly([P(d0 + 0.01, 0.44), P(d1 - 0.01, 0.44), P(d1 - 0.01, 0.6), P(d0 + 0.01, 0.6)])
                c.drawPath(lat, gfx.paint((150, 160, 180), 0.55, blend=gfx.SCREEN))
                # lattice bars
                for j in range(1, 4):
                    q = j / 4
                    a = P(d0 + (d1 - d0) * q, 0.44)
                    b = P(d0 + (d1 - d0) * q, 0.6)
                    c.drawLine(a[0], a[1], b[0], b[1], gfx.paint(ink, 1.0, stroke=max(1.0, 4 * (1 - d0))))
                # faded couplet strips beside each door
                cp = gfx.poly([P(d1 + 0.005, 0.18), P(d1 + 0.018, 0.18), P(d1 + 0.018, 0.66), P(d1 + 0.005, 0.66)])
                c.drawPath(cp, gfx.paint((214, 206, 200), 0.7, blend=gfx.SCREEN))
                # eave: an overhanging roof edge against the sky, upturned at the corner
                e0 = P(d0 - 0.03, 1.0)
                e1 = P(d1 + 0.05, 1.0)
                th = max(3.0, 26 * (1 - d0))
                eave = gfx.poly([(e0[0], e0[1] - th * 0.2), (e1[0], e1[1] - th * 0.2), (e1[0] + side * th * 0.4, e1[1] - th * 1.4),
                                 (e1[0], e1[1] + th * 0.6), (e0[0], e0[1] + th * 0.6)])
                c.drawPath(eave, gfx.paint(ink, 1.0))
                c.drawPath(gfx.poly([(e0[0], e0[1] - th * 0.2), (e1[0], e1[1] - th * 0.2), (e1[0], e1[1] - th * 0.45), (e0[0], e0[1] - th * 0.45)]),
                           gfx.paint(S.SNOW, 0.9))
                # an unlit paper lantern hanging below the eave
                lx, ly = P((d0 + d1) / 2, 0.84)
                sw = 4 * (1 - d0) * noise1(t * 1.2 + k + side, 3)
                lr = 30 * (1 - d0 * 0.9)
                c.drawLine(lx, P((d0 + d1) / 2, 1.0)[1], lx + sw, ly - lr, gfx.paint(ink, 1.0, stroke=1.5))
                c.drawPath(gfx.ellipse(lx + sw, ly, lr * 0.8, lr), gfx.paint((196, 176, 176), 0.95))
                c.drawPath(gfx.ellipse(lx + sw, ly, lr * 0.8, lr), gfx.paint(ink, 1.0, stroke=1.6))
                for j in (-1, 0, 1):
                    c.drawLine(lx + sw + j * lr * 0.4, ly - lr * 0.9, lx + sw + j * lr * 0.4, ly + lr * 0.9, gfx.paint(ink, 0.7, stroke=1.0))
        # night sky above the lane
        c.drawPath(gfx.poly([(-60, -60), (W + 60, -60), (W + 60, 150), (vx + 60, vy - 40), (vx - 60, vy - 40), (-60, 150)]),
                   gfx.paint((150, 162, 190), 0.55, blend=gfx.MULTIPLY))
        # snowy ground
        c.drawPath(gfx.poly([(-60, H + 60), (vx - 60, vy + 40), (vx + 60, vy + 40), (W + 60, H + 60)]),
                   gfx.paint((232, 236, 246), 1.0))
        # footprints
        for k in range(10):
            d = 0.1 + k * 0.08
            x = vx + (-1 if k % 2 else 1) * 30 * (1 - d)
            y = H + 60 + (vy + 40 - H - 60) * d
            c.drawPath(gfx.ellipse(x, y, 14 * (1 - d), 5 * (1 - d)), gfx.paint((150, 160, 180), 0.5))

    def paint(self, fr, t, lt, u):
        c = fr.canvas
        z = 1.0 + 0.1 * E.in_out_sine(u)
        cam = Cam(W / 2, H / 2 + 20, z, t=t)
        c.save()
        cam.apply(c)
        self.draw_alley(c, t)
        for p, (x, y, s, fl) in zip(self.fallen, self.fallen_pos):
            p.draw(c, x, y, s, pose={"lean": 88 * fl, "ua_f": 30, "fa_f": 20, "ua_b": 10, "head": 10}, t=0.0, flip=fl < 0)
        # A-Duo rises among them (stiffly, as a puppeteer lifts a puppet)
        k = E.in_out_cubic(E.prog(lt, self.t_rise, self.t_rise + 1.3))
        pose = {"lean": 88 * (1 - k), "ua_f": 30 - 20 * k, "fa_f": 20 + 10 * k, "head": 10 - 18 * k,
                "hair": 0.3, "bud_open": 0.16}
        self.duo.draw(c, 960, 1030, 0.72, pose=merge(breathe(lt, amt=k), pose), t=t)
        c.restore()

    def after_light(self, fr, t, lt, u):
        c = fr.canvas
        PT.draw_snow(c, t, n=320, seed=10, wind=60, fall=(60, 160), size=(1.0, 5.5), alpha=0.9)
        return {"grade": dict(sat=0.6, gain=(0.92, 0.97, 1.08), lift=(0.02, 0.03, 0.06)),
                "glow": {"thr": 0.86, "strength": 0.25, "red": 0.5}}


class LonelyShadowScene(Stage):
    light = "cold"

    def setup(self):
        self.duo = Puppet("woman", arm_red=0.9, seed=1)
        self.shadow = Puppet("woman", leather=(20, 22, 34), arm_red=0.0, seed=1)

    def light_params(self, t, lt, u):
        return dict(cx=0.2 + 0.25 * u, cy=0.55, radius=1.0, power=1.4, edge=0.18)

    def paint(self, fr, t, lt, u):
        c = fr.canvas
        span = self.end - self.start
        x = 260 + 1300 * (lt / span)
        ph = lt * 0.85
        pose = merge(walk(ph, 0.9, 0.6), {"head": 6, "hair": 0.4, "bud_open": 0.16, "torso": 6})
        # the wall: a long row of shut doors (carved) and a bare plum branch over it
        c.drawPath(gfx.rect(-50, 40, W + 100, 840), gfx.paint((172, 180, 196), 0.55, blend=gfx.MULTIPLY))
        for k in range(9):
            dx = 40 + k * 230 - (lt * 30) % 230
            door = gfx.op(gfx.rect(dx, 420, 150, 450), gfx.rect(dx + 14, 440, 122, 410), "diff")
            c.drawPath(door, gfx.paint(COLD_INK, 0.85))
            c.drawLine(dx + 75, 440, dx + 75, 850, gfx.paint(COLD_INK, 0.85, stroke=4))
            c.drawCircle(dx + 64, 650, 6, gfx.paint(COLD_INK, 0.9))
            c.drawCircle(dx + 86, 650, 6, gfx.paint(COLD_INK, 0.9))
        # eaves
        c.drawPath(gfx.poly([(-50, 40), (W + 50, 40), (W + 50, 96), (-50, 104)]), gfx.paint(COLD_INK, 0.96))
        for k in range(30):
            xx = k * 70 - (lt * 30) % 70
            c.drawPath(gfx.ellipse(xx, 100, 30, 10), gfx.paint(COLD_INK, 0.96))
        c.drawPath(gfx.poly([(-50, 34), (W + 50, 34), (W + 50, 44), (-50, 46)]), gfx.paint(S.SNOW, 0.95))
        # faded couplets on a few doors
        for k in range(9):
            dx = 40 + k * 230 - (lt * 30) % 230
            if k % 3 == 1:
                c.drawPath(gfx.rect(dx - 26, 470, 18, 300), gfx.paint((200, 120, 120), 0.6, blend=gfx.MULTIPLY))
                c.drawPath(gfx.rect(dx + 158, 470, 18, 300), gfx.paint((200, 120, 120), 0.6, blend=gfx.MULTIPLY))
        # the huge blurred shadow (her puppet held close to a second lamp): lags, wavers
        lag = 0.35
        sx = 260 + 1300 * ((lt - lag) / span) - 120
        with gfx.Layer(c, blur=10, alpha=0.78) as lc:
            self.shadow.draw(lc, sx, 980, 1.32 + 0.04 * math.sin(lt * 1.3), pose=merge(walk(ph - 0.3, 0.9, 0.6), {"hair": 0.6}),
                             t=t - lag)
        # snow street
        c.drawPath(gfx.poly([(-50, 880), (W + 50, 870), (W + 50, H + 50), (-50, H + 50)]), gfx.paint((232, 236, 246), 1.0))
        self.duo.draw(c, x, 900, 0.62, pose=pose, t=t)

    def after_light(self, fr, t, lt, u):
        c = fr.canvas
        PT.draw_snow(c, t, n=260, seed=12, wind=-40, fall=(40, 120), size=(1.0, 5.0), alpha=0.85)
        return {"grade": dict(sat=0.6, gain=(0.92, 0.97, 1.08), lift=(0.02, 0.03, 0.06)),
                "glow": {"thr": 0.86, "strength": 0.25, "red": 0.5}}


def entries():
    return [
        Entry(WinterBranchScene(T8, T9), trans=("fade", 0.5)),
        Entry(NoSunriseScene(T9, T10), trans=("wipe_d", 0.6)),
        Entry(AlleyScene(T10, T10B), trans=("black", 0.6)),
        Entry(LonelyShadowScene(T10B, T11), trans=("fade", 0.5)),
    ]
