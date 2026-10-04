"""1:19.70 – 1:34.85  Refrain 2 — the same question, now an accusation.

SC20 void       out of the eaten darkness: torn scraps of the earlier scenes drift; 阿朵 stands in a
                red backlight.
SC21 labyrinth  an endless binary tree of forks; the camera dives along it, turning left/right at every
                beat while the whole world rolls.
SC22 hands      white hands close in from every side and crush their cochineal into rouge on the beat;
                only her red hand stays open, trembling.
SC23 cracking   her bud splits under the pressure; rouge runs down the screen like tears.
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
from ..elements.puppet import Puppet, walk, run, breathe, merge
from ..elements.flower import draw_poppy_side, draw_poppy_front
from ..elements.hand import draw_big_hand
from ..elements.insects import draw_cochineal
from ..elements import fx, particles as PT, thread as TH
from ..timeline import Entry
from .common import Stage, ground, W, H

T20, T21, T22, T23, T24 = 79.70, 81.85, 86.85, 90.45, 94.85


class VoidScene(Stage):
    light = "red"

    def setup(self):
        self.duo = Puppet("woman", arm_red=0.8, seed=1)
        rng = RNG(61)
        self.scraps = [(rng.u(0, W), rng.u(0, H), rng.u(60, 180), rng.u(0, 6.28), rng.u(-0.4, 0.4), k) for k in range(16)]

    def light_params(self, t, lt, u):
        return dict(cx=0.5, cy=0.5, radius=0.55 + 0.25 * E.out_cubic(E.prog(lt, 0, 1.2)), power=1.6, edge=0.0)

    def paint(self, fr, t, lt, u):
        c = fr.canvas
        rot = 0.04 * math.sin(lt * 0.8)
        cam = Cam(W / 2, H / 2, 1.0 + 0.06 * u, rot=rot, t=t)
        c.save()
        cam.apply(c)
        self.duo.draw(c, W / 2, 900, 0.8, pose=merge(breathe(lt), {"head": -16, "hair": 0.6, "sash": 0.6, "bud_open": 0.2,
                                                                  "ua_f": 14, "fa_f": 20}), t=t)
        c.restore()

    def after_light(self, fr, t, lt, u):
        c = fr.canvas
        # torn scraps of paper with fragments of earlier scenes, tumbling in the dark
        for (x, y, r, a, spin, k) in self.scraps:
            xx = x + 30 * math.sin(lt * 0.5 + k)
            yy = y - 40 * lt + 20 * math.cos(lt * 0.7 + k)
            c.save()
            c.translate(xx, yy)
            c.rotate(math.degrees(a + spin * lt))
            p = gfx.rough(gfx.rect(-r / 2, -r * 0.35, r, r * 0.7), seg=8, dev=5, seed=k)
            c.drawPath(p, gfx.paint((236, 222, 196), 0.75))
            if k % 3 == 0:
                draw_poppy_side(c, 0, r * 0.25, 0.5, 0.0, openness=1.0 if k % 2 else 0.0, seed=k, stem_len=8)
            elif k % 3 == 1:
                c.drawPath(gfx.ribbon([(-r * 0.4, r * 0.1), (0, -r * 0.1), (r * 0.4, r * 0.05)], [6, 4, 1]), gfx.paint(S.INK, 0.9))
            else:
                c.drawCircle(0, 0, r * 0.12, gfx.paint(S.ROUGE, 0.9))
            c.restore()
        PT.draw_embers(c, t, n=40, alpha=0.6, rise=60)
        return {"glow": {"thr": 0.7, "strength": 0.5, "red": 0.8}, "grade": dict(contrast=1.15)}


class Labyrinth:
    def __init__(self, depth=12, seed=0):
        self.segs = []
        rng = RNG(seed)
        self.root_len = 520.0
        self._grow((0.0, 0.0), -math.pi / 2, self.root_len, 70.0, 0, "", rng, depth)
        self.by_code = {s[5]: s for s in self.segs}

    def _grow(self, p, a, L, w, lvl, code, rng, depth):
        q = (p[0] + math.cos(a) * L, p[1] + math.sin(a) * L)
        self.segs.append((p, q, a, L, w, code, lvl))
        if lvl >= depth:
            return
        spread = 0.5 + 0.08 * rng.n()
        for side, ch in ((-1, "L"), (1, "R")):
            self._grow(q, a + side * spread, L * 0.72, w * 0.7, lvl + 1, code + ch, rng, depth)


class LabyrinthScene(Stage):
    light = "red"

    def setup(self):
        self.lab = Labyrinth(depth=13, seed=4)
        b0 = audio.beat_index(self.start)
        self.forks = [audio.beat_time(b0 + k) - self.start for k in range(1, 11)]
        self.code = "LRLRRLRLLR"
        self.duo = Puppet("woman", arm_red=0.75, seed=1)

    def cam_state(self, lt):
        # level index advances by one at each fork beat
        fk = self.forks
        k = 0
        while k < len(fk) and lt >= fk[k]:
            k += 1
        t0 = fk[k - 1] if k > 0 else 0.0
        t1 = fk[k] if k < len(fk) else t0 + config.BEAT
        f = E.in_out_sine(E.clamp((lt - t0) / (t1 - t0)))
        code = self.code[:k]
        seg = self.lab.by_code.get(code)
        nxt = self.lab.by_code.get(self.code[:k + 1])
        p, q, a, L, w, _, lvl = seg
        x = p[0] + (q[0] - p[0]) * f
        y = p[1] + (q[1] - p[1]) * f
        scale = 0.72 ** (lvl + f)
        ang = a
        if nxt is not None and f > 0.7:
            g = E.smooth((f - 0.7) / 0.3)
            ang = a + (nxt[2] - a) * g
        return x, y, scale, ang

    def paint(self, fr, t, lt, u):
        c = fr.canvas
        x, y, scale, ang = self.cam_state(lt)
        z = 1.25 / scale
        rot = -(ang + math.pi / 2)
        m = skia.Matrix()
        m.setTranslate(W / 2, H * 0.62)
        m.preRotate(math.degrees(rot))
        m.preScale(z, z)
        m.preTranslate(-x, -y)
        c.save()
        c.concat(m)
        for (p, q, a, L, w, code, lvl) in self.lab.segs:
            sw = w * z
            if sw < 0.6:
                continue
            sp = m.mapXY(*p)
            sq = m.mapXY(*q)
            minx, maxx = min(sp.x(), sq.x()), max(sp.x(), sq.x())
            miny, maxy = min(sp.y(), sq.y()), max(sp.y(), sq.y())
            pad = sw * 2 + 50
            if maxx < -pad or minx > W + pad or maxy < -pad or miny > H + pad:
                continue
            mid = ((p[0] + q[0]) / 2 + 0.06 * L * math.sin(lvl + len(code)), (p[1] + q[1]) / 2)
            c.drawPath(gfx.ribbon([p, mid, q], [w, w * 0.86, w * 0.72]), gfx.paint(S.INK, 0.97))
            if lvl >= 13 and hash01(len(code) * 7 + lvl, 3) < 0.5:
                draw_poppy_side(c, q[0], q[1], w * 0.05, a + math.pi / 2, openness=1.0, seed=len(code) + lvl)
        # her path through the labyrinth, marked by the red thread
        k = sum(1 for f in self.forks if lt >= f)
        path_pts = []
        for j in range(0, min(len(self.code), k + 1) + 1):
            sg = self.lab.by_code.get(self.code[:j])
            if sg is None:
                break
            path_pts.append(sg[0])
            path_pts.append(sg[1])
        if len(path_pts) > 1:
            TH.draw_thread(c, path_pts, width=3.0 / z, glow=1.2, smooth=False, alpha=0.95)
        c.restore()
        # a pool of light around her so her silhouette reads against the branches
        c.drawCircle(W / 2, H * 0.62 - 90, 170, gfx.paint((255, 255, 255), 0.85, blur=60))
        # 阿朵 running, always upright at the centre of the dive
        self.duo.draw(c, W / 2, H * 0.62 + 6, 0.30, pose=merge(run(lt * 2.2, 0.9), {"bud_open": 0.22}), t=t,
                      flip=self.code[min(len(self.code) - 1, int(sum(1 for f in self.forks if lt >= f)))] == "L")

    def after_light(self, fr, t, lt, u):
        imp = max([E.pulse(lt, f, 0.01, 0.12) for f in self.forks] + [0])
        PT.draw_embers(fr.canvas, t, n=50, alpha=0.5, rise=90)
        return {"glow": {"thr": 0.72, "strength": 0.45, "red": 0.8}, "grade": dict(contrast=1.12),
                "chroma": 3 * imp, "flash": 0.08 * imp, "flash_color": (255, 120, 100)}


class HandsScene(Stage):
    light = "warm"

    def setup(self):
        b0 = audio.beat_index(self.start)
        self.crush = [audio.beat_time(b0 + k) - self.start for k in range(2, 8)]
        rng = RNG(71)
        self.hands = []
        for k in range(8):
            a = 2 * math.pi * k / 8 + 0.2
            r = 820
            self.hands.append((W / 2 + math.cos(a) * r * 1.1, H / 2 + math.sin(a) * r * 0.75, a + math.pi / 2 + math.pi,
                               self.crush[k % len(self.crush)], rng.u(0.9, 1.1), k))

    def light_params(self, t, lt, u):
        imp = max([E.pulse(lt, c, 0.01, 0.12) for c in self.crush] + [0])
        return dict(radius=0.95, power=1.5, edge=0.08, boost=0.12 * imp)

    def paint(self, fr, t, lt, u):
        c = fr.canvas
        imp = max([E.pulse(lt, cc, 0.01, 0.12) for cc in self.crush] + [0])
        cam = Cam(W / 2, H / 2, 1.0 + 0.05 * u, t=t, shake=0.5 * imp)
        c.save()
        cam.apply(c)
        inn = E.out_cubic(E.prog(lt, 0.0, 0.9))
        for (x, y, rot, tc, s, k) in self.hands:
            # reach in toward the centre
            hx = x + (W / 2 - x) * 0.42 * inn
            hy = y + (H / 2 - y) * 0.42 * inn
            closed = E.out_cubic(E.prog(lt, tc - 0.08, tc + 0.06))
            draw_big_hand(c, hx, hy, 1.0 * s, rot=rot, openness=1.0 - closed, redness=0.0, t=t, seed=k)
            if closed < 0.6:
                # the insect sits in the palm (palm is ~ (0,-150) in hand space)
                px = hx + math.sin(rot) * 150 * s
                py = hy - math.cos(rot) * 150 * s
                draw_cochineal(c, px, py, 1.1 * s, rot - math.pi / 2, t=t, walk=lt * 2, seed=k)
        # her red hand at the centre, open, trembling
        draw_big_hand(c, W / 2, H / 2 + 330, 1.15, rot=0.0, openness=1.0, redness=1.0, t=t, tremble=1.0 + 2 * imp)
        draw_cochineal(c, W / 2, H / 2 + 330 - 170, 1.4, -math.pi / 2, t=t, walk=lt * 2, seed=99)
        c.restore()

    def after_light(self, fr, t, lt, u):
        c = fr.canvas
        inn = E.out_cubic(E.prog(lt, 0.0, 0.9))
        for (x, y, rot, tc, s, k) in self.hands:
            hx = x + (W / 2 - x) * 0.42 * inn
            hy = y + (H / 2 - y) * 0.42 * inn
            px = hx + math.sin(rot) * 150 * s
            py = hy - math.cos(rot) * 150 * s
            g = E.prog(lt, tc, tc + 0.3)
            if g > 0:
                fade = 1.0 - 0.55 * E.smooth(E.prog(lt, tc + 0.4, tc + 1.4))
                fx.draw_splash(c, px, py, 95 * s, color=S.ROUGE, growth=g, seed=k + 30, alpha=0.88 * fade, spikes=11)
            PT.draw_burst(c, lt, tc, px, py, n=36, seed=k + 40, speed=(400, 1400), size=(4, 12), color=S.ROUGE,
                          gravity=1200, life=1.1)
        imp = max([E.pulse(lt, cc, 0.01, 0.1) for cc in self.crush] + [0])
        return {"glow": {"thr": 0.78, "strength": 0.4, "red": 0.8}, "flash": 0.18 * imp, "flash_color": (255, 70, 70),
                "chroma": 6 * imp, "grade": dict(contrast=1.1, sat=1.1)}


class CrackingScene(Stage):
    light = "warm"

    def setup(self):
        self.duo = Puppet("woman", arm_red=0.75, seed=1)
        rng = RNG(81)
        self.drips = [(rng.u(0, W), rng.u(-200, 300), rng.u(8, 26), rng.u(0.0, 1.6), rng.u(120, 360)) for _ in range(26)]
        b0 = audio.beat_index(self.start)
        self.pulses = [audio.beat_time(b0 + k) - self.start for k in range(1, 9)]

    def light_params(self, t, lt, u):
        fade = E.smooth(E.prog(lt, 3.2, 4.4))
        return dict(radius=1.0 - 0.3 * fade, boost=-0.15 * fade + 0.06 * audio.beat_pulse(t, 0.2))

    def paint(self, fr, t, lt, u):
        c = fr.canvas
        # close-up on her head; the bud splits a little more on every beat
        k = sum(E.out_back(E.prog(lt, p, p + 0.2)) for p in self.pulses) / len(self.pulses)
        bud = 0.18 + 0.16 * k
        droop = E.smooth(E.prog(lt, 2.6, 4.2))
        c.save()
        c.translate(W / 2 + 80, H / 2 + 160)
        sc = 3.4 + 0.3 * E.in_out_sine(lt / 4.4)
        c.scale(-sc, sc)
        c.translate(-10, 560)
        self.duo.draw(c, 0, 0, 1.0, pose={"head": -10 + 26 * droop, "bud_open": bud, "hair": 0.3}, t=t)
        c.restore()

    def after_light(self, fr, t, lt, u):
        c = fr.canvas
        # rouge runs down the screen
        for i, (x, y0, w, t0, sp) in enumerate(self.drips):
            if lt < t0:
                continue
            L = (lt - t0) * sp
            pts = [(x + 3 * math.sin(j * 0.4 + i), y0 + j * L / 10) for j in range(11)]
            wid = [w * (0.6 + 0.4 * math.sin(j * 0.7 + i)) for j in range(11)]
            wid[-1] = w * 1.15
            c.drawPath(gfx.ribbon(pts, wid), gfx.paint(S.ROUGE, 0.9, blur=1.2))
            c.drawCircle(pts[-1][0], pts[-1][1] + w * 0.3, w * 0.62, gfx.paint(S.ROUGE, 0.95, blur=1.0))
            c.drawPath(gfx.ribbon(pts, [x * 0.25 for x in wid]), gfx.paint((255, 140, 140), 0.35, blur=1.0, blend=gfx.SCREEN))
        imp = max([E.pulse(lt, p, 0.01, 0.12) for p in self.pulses] + [0])
        return {"glow": {"thr": 0.78, "strength": 0.4, "red": 0.7}, "flash": 0.08 * imp, "flash_color": (255, 90, 90)}


def entries():
    return [
        Entry(VoidScene(T20, T21), trans=("fade", 0.4)),
        Entry(LabyrinthScene(T21, T22), trans=("burn", 0.5), params={"center": (0.5, 0.6), "color": (255, 70, 40)}),
        Entry(HandsScene(T22, T23), trans=("white", 0.3)),
        Entry(CrackingScene(T23, T24), trans=("fade", 0.3)),
    ]
