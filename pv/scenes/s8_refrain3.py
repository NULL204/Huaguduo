"""2:07.70 – 2:23.75  Refrain 3 — the question for the last time; the weight falls on the bud.

SC34 June snow  a summer garden in full leaf — and snow falling on it (六月飞雪: a sky that weeps for a
                wrong done).
SC35 the stem   back at the fork: she refuses both ways, grips the stem that grows from her back into the
                tree and tears it out; sap bursts red.
SC36 the fist   her hand closes on the cochineal by itself; red seeps between the fingers.
SC37 the bud    the bud forces itself open; she clutches it with both hands; petals push through her
                fingers in a blizzard of red and white.
"""
import math

import numpy as np
import skia

from .. import config
from ..core import gfx, audio
from ..core import easing as E
from ..core import lyrics as LY
from ..core.camera import Cam
from ..core.noise import noise1, RNG, hash01
from ..elements import style as S
from ..elements.branch import BranchTree
from ..elements.puppet import Puppet, walk, run, breathe, merge
from ..elements.flower import draw_poppy_side, draw_poppy_front
from ..elements.hand import draw_big_hand
from ..elements.insects import draw_cochineal
from ..elements import fx, particles as PT, thread as TH
from ..elements.landscape import Mountains, draw_mist
from ..timeline import Entry
from .common import Stage, ground, W, H
from .s1_refrain import fork_limb, draw_bark_limb

T34, T35, T36, T37, T38 = 127.70, 129.85, 134.85, 138.45, 143.75


class JuneSnowScene(Stage):
    light = "spring"

    def setup(self):
        self.duo = Puppet("woman", arm_red=0.3, seed=1)
        self.trees = [BranchTree(seed=110 + k, root=(x, 1000), angle=-math.pi / 2 + 0.1 * (k - 1), length=L, width=w, depth=4,
                                 spread=0.8, wander=0.2).normalize_time()
                      for k, (x, L, w) in enumerate(((260, 640, 44), (980, 520, 36), (1700, 700, 48)))]
        rng = RNG(7)
        self.leaves = []
        for tr in self.trees:
            for (x, y, a, d) in tr.tip_list(1.0):
                for j in range(5):
                    self.leaves.append((x + rng.n(0, 26), y + rng.n(0, 26), rng.u(0, 6.28), rng.u(16, 30)))

    def light_params(self, t, lt, u):
        return dict(radius=1.6, edge=0.6, paper=(1.0, 0.98, 0.90))

    def paint(self, fr, t, lt, u):
        c = fr.canvas
        cam = Cam(W / 2 + 60 * u, H / 2, 1.04, t=t)
        c.save()
        cam.apply(c)
        # summer sun high and bright
        c.drawCircle(1500, 200, 90, gfx.paint(S.LEATHER_GOLD, 0.5, blend=gfx.MULTIPLY))
        for tr in self.trees:
            tr.draw(c, 1.0, style="cut", color=S.INK)
        p = skia.Path()
        for (x, y, a, r) in self.leaves:
            sw = 3 * noise1(t * 1.2 + x * 0.01, 3)
            p.addPath(gfx.transformed(gfx.ellipse(0, 0, r, r * 0.45), gfx.mat(x + sw, y, a)))
        c.drawPath(p, gfx.paint((92, 160, 70), 0.9, blend=gfx.MULTIPLY))
        c.drawPath(p, gfx.paint(S.INK, 0.7, stroke=1.2))
        # summer flowers in bloom along the path
        for k in range(14):
            x = 80 + k * 140
            draw_poppy_side(c, x, 1000, 1.0, 0.1 * noise1(t + k, 4), openness=1.0, seed=k + 300, stem_len=60)
        ground(c, 1000, color=(30, 60, 30), seed=11, t=t)
        x = 520 + 760 * u
        self.duo.draw(c, x, 1000, 0.62, pose=merge(walk(lt * 0.9), {"head": -10, "bud_open": 0.36}), t=t)
        c.restore()

    def after_light(self, fr, t, lt, u):
        c = fr.canvas
        k = E.smooth(E.prog(lt, 0.0, 0.8))
        PT.draw_snow(c, t, n=380, seed=21, wind=30, fall=(50, 150), size=(1.5, 7.0), alpha=0.95, count=k, color=(255, 255, 255))
        return {"glow": {"thr": 0.8, "strength": 0.4, "red": 0.5}, "grade": dict(sat=1.05, gain=(0.98, 1.0, 1.04))}


class StemScene(Stage):
    light = "warm"

    def setup(self):
        self.duo = Puppet("woman", arm_red=0.3, seed=1)
        trunk = [(990, 1420), (960, 1180), (930, 930), (952, 760), (960, 700)]
        left = [(960, 700), (850, 650), (700, 500), (560, 420), (400, 300), (210, 260), (-40, 200)]
        right = [(960, 700), (1090, 640), (1250, 560), (1420, 430), (1600, 380), (1780, 300), (2000, 250)]
        self.limbs = [fork_limb(trunk, 170, 112, 1), fork_limb(left, 104, 16, 2), fork_limb(right, 100, 12, 3)]
        self.t_left = LY.char_time(34, 6) - self.start
        self.t_right = LY.char_time(34, 9) - self.start
        self.t_grip = 0.55
        # snap on the first strong beat after the last syllable
        tb = audio.beat_time(audio.beat_index(self.start + self.t_right + 0.35) + 1) - self.start
        self.t_snap = min(4.4, tb)

    def light_params(self, t, lt, u):
        fl = E.bump(lt, self.t_snap - 0.05, self.t_snap, self.t_snap + 0.05, self.t_snap + 0.6)
        return dict(boost=0.35 * fl, paper=(1.0, 0.92, 0.86))

    def paint(self, fr, t, lt, u):
        c = fr.canvas
        tl, tr, tg, ts = self.t_left, self.t_right, self.t_grip, self.t_snap
        x = E.Track([(0.0, 930), (tl - 0.2, 930), (tl + 0.15, 760, "out_cubic"), (tr - 0.2, 760), (tr + 0.15, 1100, "out_cubic"),
                     (ts - 0.2, 930, "in_out_cubic")])(lt)
        z = E.Track([(0.0, 1.9), (tl + 0.15, 1.7, "out_cubic"), (tr + 0.15, 1.7), (ts - 0.1, 2.5, "in_cubic"), (5.0, 1.9, "out_cubic")])(lt)
        imp = E.pulse(lt, ts, 0.01, 0.25)
        cam = Cam(x, 540, z, t=t, shake=0.6 * imp + 0.12 * E.bump(lt, tg, tg + 0.3, ts - 0.1, ts))
        c.save()
        cam.apply(c)
        for k, (pts, ws) in enumerate(self.limbs):
            draw_bark_limb(c, pts, ws, seed=k)
        # the stem from her back into the trunk; she grips and tears it out
        grip = E.smooth(E.prog(lt, tg - 0.3, tg))
        strain = E.prog(lt, tg, ts)
        snapped = lt >= ts
        pose = merge(breathe(lt), {"head": -6, "bud_open": 0.38})
        if grip > 0 and not snapped:
            shake = math.sin(lt * 31) * (0.3 + 0.7 * strain)
            pose.update({"ua_f": -60 * grip - 14 * strain, "fa_f": 120 * grip, "hand_f": "fist",
                         "ua_b": -70 * grip - 10 * strain, "fa_b": 110 * grip, "hand_b": "fist", "torso": 10 * strain + 5 * shake,
                         "lean": 6 * strain, "head": -6 + 20 * strain})
        if snapped:
            k = E.out_cubic(E.prog(lt, ts, ts + 0.5))
            pose.update({"ua_f": 40 + 50 * k, "fa_f": 20, "hand_f": "spread", "ua_b": -50, "fa_b": 30, "lean": -10 * (1 - k),
                         "torso": -6 * (1 - k), "head": -20 * (1 - k)})
        dx, dy = 960, 704
        anchor = (-180, -560)  # where the stem meets the trunk, in puppet space (flip=False)
        stem_amt = 1.0 if not snapped else 0.0
        if not snapped:
            # the stem: a living twig from her back into the trunk, taut as she pulls
            bx, by = self.duo.joint(pose, "back")
            p0 = (dx + bx * 0.5, dy + by * 0.5)
            p3 = (dx - 230, dy + 120)
            tremor = 6 * strain * math.sin(lt * 40)
            pts = gfx.bezier_pts(p0, (p0[0] - 60, p0[1] - 40 + tremor), (p3[0] + 60, p3[1] - 120), p3, 24)
            c.drawPath(gfx.ribbon(pts, np.linspace(7, 16, len(pts))), gfx.paint(S.INK, 1.0))
            for j in range(3, len(pts) - 3, 5):
                px, py = pts[j]
                c.drawPath(gfx.ellipse(px - 6, py - 10, 11, 5), gfx.paint(S.LEATHER_GREEN, 0.95, blend=gfx.MULTIPLY))
                c.drawPath(gfx.ellipse(px - 6, py - 10, 11, 5), gfx.paint(S.INK, 1.0, stroke=1.2))
            # red sap glows at the joint as it tears
            c.drawCircle(p0[0], p0[1], 8 + 10 * strain, gfx.paint(S.ROUGE_HOT, 0.5 * strain, blur=8))
        self.duo.draw(c, dx, dy, 0.5, pose=pose, t=t)
        if snapped:
            # the torn stem whips away, leaving a red wound of sap
            k = E.prog(lt, ts, ts + 0.8)
            bx, by = self.duo.joint(pose, "back")
            px, py = dx + bx * 0.5, dy + by * 0.5
            seg = [(px - 40 - 260 * k, py - 30 - 160 * k + 200 * k * k), (px - 120 - 300 * k, py - 120 - 120 * k + 260 * k * k)]
            c.drawPath(gfx.ribbon(seg, [8, 4]), gfx.paint(S.INK, 1 - k))
        c.restore()

    def after_light(self, fr, t, lt, u):
        c = fr.canvas
        ts = self.t_snap
        z_center = (W / 2, H / 2 + 60)
        PT.draw_burst(c, lt, ts, z_center[0] - 120, z_center[1] - 40, n=70, seed=3, speed=(400, 1500), size=(3, 12),
                      color=S.ROUGE, gravity=900, life=1.3)
        PT.draw_snow(c, t, n=240, seed=22, wind=60, fall=(50, 140), size=(1.5, 6.0), alpha=0.9, color=(255, 255, 255))
        fl = E.bump(lt, ts - 0.04, ts, ts + 0.05, ts + 0.5)
        return {"glow": {"thr": 0.78, "strength": 0.4 + 0.5 * fl, "red": 0.7}, "flash": 0.45 * fl, "chroma": 8 * fl}


class FistScene(Stage):
    light = "warm"

    def setup(self):
        self.t_close = 1.2

    def light_params(self, t, lt, u):
        return dict(radius=1.0, power=1.4, edge=0.12)

    def paint(self, fr, t, lt, u):
        c = fr.canvas
        z = 1.0 + 0.15 * E.in_out_sine(u)
        c.save()
        c.translate(W / 2, H / 2)
        c.scale(z, z)
        c.translate(-W / 2, -H / 2)
        close = E.in_out_cubic(E.prog(lt, self.t_close, self.t_close + 1.3))
        hx, hy = 960, 1180
        if close < 0.55:
            draw_cochineal(c, hx, hy - 330, 3.0, -math.pi / 2 + 0.1 * math.sin(lt * 2), t=t, walk=lt * 2, seed=5,
                           crushed=E.prog(close, 0.4, 0.55))
        draw_big_hand(c, hx, hy, 2.1, rot=0.0, openness=1.0 - close, redness=0.35, t=t, tremble=1.0 + 2 * close,
                      curl_order=[0.0, 0.1, 0.2, 0.3])
        c.restore()

    def after_light(self, fr, t, lt, u):
        c = fr.canvas
        close = E.in_out_cubic(E.prog(lt, self.t_close, self.t_close + 1.3))
        if close > 0.7:
            # red seeping between the fingers and running down the wrist
            k = E.prog(lt, self.t_close + 1.0, 3.6)
            z = 1.0 + 0.15 * E.in_out_sine(u)
            for j in range(5):
                x = W / 2 + (-150 + j * 70) * z
                y0 = H / 2 + 70 * z
                L = 40 + 460 * k * (0.6 + 0.4 * hash01(j, 4))
                pts = [(x + 4 * math.sin(i * 0.5 + j), y0 + i * L / 8) for i in range(9)]
                c.drawPath(gfx.ribbon(pts, [16, 14, 13, 12, 12, 11, 11, 12, 18]), gfx.paint(S.ROUGE, 0.92, blur=1.2))
            fx.ink_blot(c, W / 2 - 20, H / 2 + 80, 90 * k + 20, color=S.ROUGE, alpha=0.7, seed=9, growth=min(1.0, k * 2))
        return {"glow": {"thr": 0.78, "strength": 0.4, "red": 0.8}, "grade": dict(contrast=1.1)}


class BudFightScene(Stage):
    light = "warm"

    def setup(self):
        self.duo = Puppet("woman", arm_red=0.3, seed=1)
        b0 = audio.beat_index(self.start)
        self.pulses = [audio.beat_time(b0 + k) - self.start for k in range(1, 11)]

    def light_params(self, t, lt, u):
        return dict(radius=1.0, edge=0.15, boost=0.08 * audio.beat_pulse(t, 0.2))

    def paint(self, fr, t, lt, u):
        c = fr.canvas
        k = sum(E.out_back(E.prog(lt, p, p + 0.25)) for p in self.pulses) / len(self.pulses)
        bud = 0.38 + 0.3 * k
        rot = 0.25 * math.sin(lt * 0.9) * E.prog(lt, 0, 2)
        cam = Cam(W / 2, H / 2, 1.0, rot=rot, t=t, shake=0.2 + 0.25 * audio.beat_pulse(t, 0.2))
        c.save()
        cam.apply(c)
        c.translate(W / 2 + 60, H / 2 + 260)
        sc = 2.6 + 0.4 * E.in_out_sine(lt / 5.3)
        c.scale(-sc, sc)
        c.translate(-10, 560)
        pose = {"head": -20, "bud_open": bud, "ua_f": 160, "fa_f": 150, "hand_f": "spread", "ua_b": 150, "fa_b": 160,
                "hand_b": "spread", "hair": 1.2 * math.sin(lt * 2), "sash": 1.0}
        self.duo.draw(c, 0, 0, 1.0, pose=pose, t=t)
        c.restore()

    def after_light(self, fr, t, lt, u):
        c = fr.canvas
        g = E.prog(lt, 0.0, 3.0)
        PT.draw_snow(c, t, n=420, seed=23, wind=420 + 300 * g, fall=(80, 260), size=(1.5, 7.0), alpha=0.95, color=(255, 255, 255),
                     gust=1.0)
        PT.draw_petals(c, t, n=110, seed=24, wind=520 + 300 * g, fall=(-40, 120), size=(6, 18), alpha=0.95, count=0.3 + 0.7 * g)
        imp = max([E.pulse(lt, p, 0.01, 0.12) for p in self.pulses] + [0])
        return {"glow": {"thr": 0.78, "strength": 0.45, "red": 0.8}, "chroma": 4 * imp, "flash": 0.06 * imp,
                "flash_color": (255, 120, 120)}


def entries():
    return [
        Entry(JuneSnowScene(T34, T35), trans=("white", 0.5)),
        Entry(StemScene(T35, T36), trans=("fade", 0.35)),
        Entry(FistScene(T36, T37), trans=("fade", 0.3)),
        Entry(BudFightScene(T37, T38), trans=("fade", 0.3)),
    ]
