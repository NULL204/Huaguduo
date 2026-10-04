"""2:23.75 – 2:50.38  The bloom, and the silence after.

SC38 headwind   she runs into the blizzard toward the lamp; red threads tied to her neck and wrists drag
                her back.
SC39 the cry    head thrown back, a silent scream: the threads snap one by one on the beat and the paper
                screen cracks, the lamp's light bursting through the cracks.
SC40 the bloom  extreme close-up: the poppy opens, translucent, glowing — her forehead mark on one petal.
SC41 nobody     pull back: the flower alone at the tip of a bare branch.
SC42 the painting  …which is the painting from the opening — no longer an old photograph but crisp and
                present.  The music stops dead.
SC43 epilogue   silence; the lamp dims; next year's bud appears; end card.
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
from ..elements.puppet import Puppet, walk, run, breathe, merge
from ..elements.flower import draw_poppy_side, draw_poppy_front
from ..elements import fx, particles as PT, thread as TH
from ..timeline import Entry
from .common import Stage, ground, W, H
from .s0_intro import PaintingScene

T38, T39, T40, T41, T42, T43, TEND = 143.75, 146.10, 150.85, 154.00, 155.35, config.MUSIC_END, config.DURATION


class Threads:
    """Red threads from off-screen anchors to puppet joints; each may snap at a given time."""

    def __init__(self, joints, anchors, snaps, seed=0):
        self.joints = joints
        self.anchors = anchors
        self.snaps = snaps
        self.seed = seed

    def draw(self, c, puppet, pose, px, py, sc, lt, flip=False, alpha=1.0):
        out = []
        for k, (jn, anc, ts) in enumerate(zip(self.joints, self.anchors, self.snaps)):
            jx, jy = puppet.joint(pose, jn)
            jx = px + (-jx if flip else jx) * sc
            jy = py + jy * sc
            ax, ay = anc
            vib = 3 * math.sin(lt * 37 + k * 2)
            if ts is None or lt < ts:
                pts = [(ax, ay), ((ax + jx) / 2 + vib, (ay + jy) / 2 - vib), (jx, jy)]
                TH.draw_thread(c, pts, width=3.2, glow=1.1, alpha=alpha, smooth=True)
            else:
                k2 = E.out_cubic(E.prog(lt, ts, ts + 0.6))
                brk = 0.55 + 0.1 * math.sin(k * 3)
                bx = ax + (jx - ax) * brk
                by = ay + (jy - ay) * brk
                # upper half recoils toward the anchor, lower half falls slack
                up = [(ax, ay), (bx + (ax - bx) * 0.7 * k2, by + (ay - by) * 0.7 * k2 - 30 * k2)]
                lo_end = (jx, jy)
                lo = [(bx - 40 * k2, by + 260 * k2), ((bx + jx) / 2, (by + jy) / 2 + 180 * k2), lo_end]
                TH.draw_thread(c, up, width=3.0, glow=0.8 * (1 - k2), alpha=alpha * (1 - 0.6 * k2), smooth=False)
                TH.draw_thread(c, lo, width=2.6, glow=0.5 * (1 - k2), alpha=alpha * (1 - 0.5 * k2), smooth=True)
                out.append((bx, by, ts))
        return out


class HeadwindScene(Stage):
    light = "warm"

    def setup(self):
        self.duo = Puppet("woman", arm_red=0.35, seed=1)
        self.threads = Threads(["neck", "hand_f", "hand_b", "waist"],
                               [(-300, -200), (-200, -300), (200, -320), (-400, 300)], [None] * 4)

    def light_params(self, t, lt, u):
        return dict(cx=0.66, cy=0.42, radius=1.3, power=1.4, edge=0.28, boost=0.1 * audio.beat_pulse(t, 0.2))

    def paint(self, fr, t, lt, u):
        c = fr.canvas
        sh = 0.25 + 0.25 * audio.beat_pulse(t, 0.2)
        cam = Cam(W / 2, H / 2 + 20, 1.05, rot=-0.02, t=t, shake=sh)
        c.save()
        cam.apply(c)
        ground(c, 980, seed=12, t=t)
        strain = 0.5 + 0.5 * math.sin(lt * 2.0)
        x = 820 + 120 * E.in_out_sine(u) - 40 * strain
        pose = merge(run(lt * 1.6, 0.7), {"lean": 14 + 6 * strain, "torso": 14, "ua_f": 70, "fa_f": 10, "hand_f": "spread",
                                          "ua_b": -60, "fa_b": 30, "hand_b": "spread", "head": 10, "hair": -1.6, "sash": -1.8,
                                          "skirt": -10, "bud_open": 0.62})
        self.duo.draw(c, x, 980, 0.75, pose=pose, t=t)
        self.threads.draw(c, self.duo, pose, x, 980, 0.75, lt)
        c.restore()

    def after_light(self, fr, t, lt, u):
        c = fr.canvas
        PT.draw_snow(c, t, n=460, seed=31, wind=-900, fall=(60, 200), size=(1.5, 7.5), alpha=0.95, color=(255, 255, 255))
        PT.draw_petals(c, t, n=120, seed=32, wind=-1100, fall=(-40, 80), size=(6, 18), alpha=0.95)
        return {"glow": {"thr": 0.74, "strength": 0.5, "red": 0.8}, "grade": dict(contrast=1.1)}


class CryScene(Stage):
    light = "warm"

    def setup(self):
        self.duo = Puppet("woman", arm_red=0.35, seed=1)
        b0 = audio.beat_index(self.start)
        snaps = [audio.beat_time(b0 + k) - self.start for k in (2, 3, 5, 6)]
        self.snaps = snaps
        self.threads = Threads(["neck", "hand_f", "hand_b", "waist"],
                               [(-200, -260), (-160, -300), (W + 260, -300), (-300, 420)], snaps)
        self.cracks = fx.Cracks(W / 2 + 20, H / 2 + 20, seed=9, n=11, length=(500, 1300))
        self.t_white = 4.45

    def light_params(self, t, lt, u):
        imp = max([E.pulse(lt, s, 0.01, 0.15) for s in self.snaps] + [0])
        return dict(boost=0.15 * imp + 0.25 * E.prog(lt, 3.6, 4.7), radius=1.0 + 0.4 * E.prog(lt, 3.0, 4.7))

    def pose(self, lt):
        scream = E.out_cubic(E.prog(lt, 0.0, 0.6))
        return {"head": -38 * scream, "torso": -10 * scream, "ua_f": 120 * scream + 10 * math.sin(lt * 20) * scream,
                "fa_f": 20, "hand_f": "spread", "ua_b": -120 * scream, "fa_b": 20, "hand_b": "spread", "bud_open": 0.75,
                "hair": -1.0, "sash": -1.2}

    def paint(self, fr, t, lt, u):
        c = fr.canvas
        imp = max([E.pulse(lt, s, 0.01, 0.15) for s in self.snaps] + [0])
        z = 1.25 + 0.15 * E.in_cubic(u)
        cam = Cam(W / 2, H / 2 + 60, z, t=t, shake=0.25 + 0.7 * imp)
        c.save()
        cam.apply(c)
        pose = self.pose(lt)
        self.duo.draw(c, W / 2, 1000, 0.8, pose=pose, t=t)
        self.threads.draw(c, self.duo, pose, W / 2, 1000, 0.8, lt)
        c.restore()

    def after_light(self, fr, t, lt, u):
        c = fr.canvas
        # sparks where each thread breaks
        for k, s in enumerate(self.snaps):
            PT.draw_burst(c, lt, s, W / 2 + (k - 1.5) * 260, H / 2 - 150 + 60 * k, n=40, seed=k + 70, speed=(300, 1200),
                          size=(2, 7), color=(255, 120, 80), gravity=600, life=0.9, blend=gfx.SCREEN)
        # the screen cracks: light bursts through
        g = E.out_cubic(E.prog(lt, self.snaps[0], 4.6))
        self.cracks.draw(c, g, color=(255, 236, 200), width=4.0, glow=(255, 200, 140))
        PT.draw_petals(c, t, n=90, seed=35, wind=-600, fall=(-60, 80), size=(6, 16), alpha=0.9)
        white = E.in_expo(E.prog(lt, self.t_white - 0.3, self.t_white + 0.3))
        imp = max([E.pulse(lt, s, 0.01, 0.12) for s in self.snaps] + [0])
        return {"glow": {"thr": 0.7, "strength": 0.55 + 0.3 * imp, "red": 0.8}, "chroma": 8 * imp, "flash": max(0.2 * imp, white),
                "flash_color": (255, 250, 238)}


class BloomScene(Stage):
    light = "warm"

    def light_params(self, t, lt, u):
        return dict(cx=0.5, cy=0.5, radius=0.9, power=1.3, edge=0.1, boost=0.15)

    def paint(self, fr, t, lt, u):
        c = fr.canvas
        # bokeh in the dark around the flower
        rng = RNG(77)
        for k in range(18):
            x, y, r = rng.u(0, W), rng.u(0, H), rng.u(30, 110)
            c.drawCircle(x + 15 * math.sin(t * 0.4 + k), y, r, gfx.paint(S.ROUGE_DEEP, 0.3, blur=r * 0.5, blend=gfx.MULTIPLY))
        o = E.in_out_sine(E.prog(lt, 0.15, 2.7))
        R = 420 + 120 * E.in_out_sine(u)
        rot = 0.25 * u + 0.1
        draw_poppy_front(c, W / 2, H / 2, R, openness=0.12 + 0.88 * o, rot=rot, seed=7, alpha=1.0, veins=True)
        # her forehead mark (花钿) on one petal: the flower is her
        if o > 0.55:
            a = E.smooth((o - 0.55) / 0.3)
            mx = W / 2 + math.cos(rot + 0.9) * R * 0.62
            my = H / 2 + math.sin(rot + 0.9) * R * 0.62
            for k in range(3):
                aa = -math.pi / 2 + (k - 1) * 0.9 + rot
                c.save()
                c.translate(mx + math.cos(aa) * 13, my + math.sin(aa) * 13)
                c.rotate(math.degrees(aa + math.pi / 2))
                c.drawPath(gfx.ellipse(0, 0, 8, 15), gfx.paint(S.INK, 0.72 * a))
                c.restore()

    def after_light(self, fr, t, lt, u):
        c = fr.canvas
        PT.draw_dust(c, t, n=120, alpha=0.6, color=(255, 230, 190), size=(1.0, 3.2))
        white = 1.0 - E.out_cubic(E.prog(lt, 0.0, 0.8))
        return {"glow": {"thr": 0.62, "strength": 0.6, "red": 0.9, "sigma": 26}, "flash": white, "flash_color": (255, 250, 238),
                "grade": dict(contrast=1.08, sat=1.1)}


class FinaleScene(PaintingScene):
    """The lone flower on its branch, pulling back into the (now crisp) painting."""

    def setup(self):
        self.kw["aged"] = False
        self.kw["hero_open"] = 1.0
        super().setup()

    def camera(self, t, lt):
        hx, hy = self.hero[0], self.hero[1]
        k = E.in_out_cubic(E.prog(lt, 0.0, 4.6))
        z = 7.0 ** (1 - k)
        cx = hx + (W / 2 - hx) * k
        cy = hy - 40 + (H / 2 - (hy - 40)) * k
        return Cam(cx, cy, z, t=t)

    def paint(self, fr, t, lt, u):
        c = fr.canvas
        cam = self.camera(t, lt)
        others = E.smooth(E.prog(lt, 1.6, 3.6))   # nobody — then the world of the painting returns
        c.save()
        cam.apply(c)
        if others > 0:
            # draw the full painting faintly growing in
            with gfx.Layer(c, alpha=others, matrix=cam.matrix()) as lc:
                self.tree.draw(lc, growth=1.0, style="ink", color=(28, 22, 20), alpha=0.94, dry=0.7)
                for (x, y, a, kind, r, i) in self.blooms:
                    from ..elements.branch import draw_blossom_ink
                    draw_blossom_ink(lc, x, y, r, openness=1.0 if kind == "open" else 0.15, rot=a + math.pi / 2 + 0.3 * noise1(i, 3),
                                     seed=i, alpha=0.93)
                self.inscription(lc, t, lt)
        # the hero limb alone, always visible
        hx, hy, ha = self.hero
        limb = self._hero_limb()
        if limb is not None:
            pts, ws = limb
            c.drawPath(gfx.ribbon(pts, ws), gfx.paint((28, 22, 20), 0.94))
        draw_poppy_side(c, hx, hy, 0.95, ha + math.pi / 2 + 0.03 * noise1(lt * 0.6, 4), openness=1.0, seed=99, alpha=0.97,
                        stem_len=14, stem_curve=0.3)
        c.restore()

    def _hero_limb(self):
        hx, hy, _ = self.hero
        best = None
        for limb in self.tree.limbs:
            px, py = limb.pts[-1]
            d = (px - hx) ** 2 + (py - hy) ** 2
            if best is None or d < best[0]:
                best = (d, limb)
        if best is None:
            return None
        limb = best[1]
        return limb.pts, [max(1.2, w) for w in limb.widths]

    def after_light(self, fr, t, lt, u):
        pp = super().after_light(fr, t, lt, u) or {}
        pp["glow"] = {"thr": 0.86, "strength": 0.25, "red": 0.5}
        return pp


class EpilogueScene(PaintingScene):
    def setup(self):
        self.kw["aged"] = False
        self.kw["hero_open"] = 1.0
        super().setup()
        tips = self.tree.tip_list(1.0)
        target = (560, 820)
        self.newbud = min(tips, key=lambda p: (p[0] - target[0]) ** 2 + (p[1] - target[1]) ** 2)

    def light_params(self, t, lt, u):
        dim = E.smooth(E.prog(lt, 3.0, 6.0))
        p = super().light_params(t, lt, u)
        p["boost"] = -0.55 * dim
        return p

    def paint(self, fr, t, lt, u):
        super().paint(fr, t, lt, u)
        c = fr.canvas
        # next year's bud: a small new bud forms and glows faintly
        k = E.out_back(E.prog(lt, 3.6, 4.6))
        if k > 0:
            x, y, a, d = self.newbud
            glow = 0.3 + 0.2 * math.sin(lt * 3)
            c.drawCircle(x, y - 20, 26, gfx.paint(S.ROUGE_HOT, glow * k, blur=18))
            draw_poppy_side(c, x, y, 0.6 * k, a + math.pi / 2, openness=0.0, seed=123, stem_len=8)

    def after_light(self, fr, t, lt, u):
        c = fr.canvas
        pp = super().after_light(fr, t, lt, u) or {}
        # end card
        card = E.smooth(E.prog(lt, 6.0, 7.0))
        out = E.smooth(E.prog(lt, 9.4, 10.3))
        if card > 0:
            c.drawRect(skia.Rect(0, 0, W, H), gfx.paint((14, 10, 10), card * 0.92))
            a = card * (1 - out)
            TXT.draw_text(c, "花骨朵", W / 2, 330, 150, face="running", color=(240, 226, 204, int(255 * a)), align="center")
            fx.draw_seal(c, W / 2 + 290, 330 - 50, 80, "朵", style="bai", alpha=a)
            TXT.draw_text(c, "献给每一个曾经的花骨朵", W / 2, 560, 44, face="brush", color=(226, 206, 180, int(235 * a)), align="center")
            TXT.draw_text(c, "演唱  洛天依", W / 2, 700, 36, face="serif", color=(196, 178, 156, int(230 * a)), align="center")
            TXT.draw_text(c, "非官方同人动画 PV  ·  fan-made", W / 2, 770, 32, face="serif", color=(176, 158, 138, int(210 * a)), align="center")
        pp["fade"] = out
        return pp


def entries():
    return [
        Entry(HeadwindScene(T38, T39), trans=("fade", 0.3)),
        Entry(CryScene(T39, T40), trans=("cut", 0.0)),
        Entry(BloomScene(T40, T41), trans=("cut", 0.0)),
        Entry(FinaleScene(T41, T43), trans=("fade", 0.35)),
        Entry(EpilogueScene(T43, TEND), trans=("cut", 0.0)),
    ]
