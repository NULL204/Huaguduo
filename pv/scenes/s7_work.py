"""1:50.85 – 2:07.70  From the Waking of Insects to Frost's Descent.

SC29 run        she runs, clutching her bud, through streaking ink.
SC30 cage       furniture slams down around her on the beats until it walls her in.
SC31 seasons    sixteen solar-term seals stamp in on eighth notes, from 惊蛰 (on its sung syllable) to
                霜降 (on its sung syllable); sun and moon race overhead; she stands still and pales.
SC32 tower      at a desk, working; the camera pulls back: she is one lit window in a tower of identical
                windows, each with a working puppet — while day and night strobe past.
SC33 the youth  on her desk her red childhood self holds out the cat's-cradle thread; she never looks up;
                the child comes apart into red dust and the thread falls limp.
"""
import math

import numpy as np
import skia

from .. import config
from ..core import gfx, audio
from ..core import easing as E
from ..core import lyrics as LY
from ..core import text as TXT
from ..core.camera import Cam
from ..core.noise import noise1, RNG, hash01
from ..elements import style as S
from ..elements.puppet import Puppet, walk, run, breathe, merge, _cut_clouds
from ..elements.flower import draw_poppy_side
from ..elements import fx, particles as PT, thread as TH
from ..timeline import Entry
from .common import Stage, ground, W, H
from .s3_house import lattice

T29, T30, T31, T32, T33, T34 = 110.85, 112.85, 114.85, 118.85, 122.85, 127.70

TERMS = ["惊蛰", "春分", "清明", "谷雨", "立夏", "小满", "芒种", "夏至", "小暑", "大暑", "立秋", "处暑", "白露", "秋分", "寒露", "霜降"]

COVER = {"ua_f": 150, "fa_f": 120, "hand_f": "flat", "ua_b": 140, "fa_b": 130, "hand_b": "flat"}


class RunScene(Stage):
    light = "warm"

    def setup(self):
        self.duo = Puppet("woman", arm_red=0.5, seed=1)
        rng = RNG(3)
        self.streaks = [(rng.u(0, 1), rng.u(60, H - 60), rng.u(80, 420), rng.u(2, 10), rng.u(0.6, 1.6)) for _ in range(60)]

    def paint(self, fr, t, lt, u):
        c = fr.canvas
        sh = 0.25 + 0.2 * audio.beat_pulse(t, 0.2)
        cam = Cam(W / 2, H / 2, 1.0, rot=-0.03, t=t, shake=sh)
        c.save()
        cam.apply(c)
        for (x0, y, L, w, sp) in self.streaks:
            x = (x0 * (W + 800) - lt * 2600 * sp) % (W + 800) - 400
            c.drawPath(gfx.ribbon([(x, y), (x + L, y + 3)], [w, w * 0.2]), gfx.paint(S.INK, 0.35 + 0.3 * (sp - 0.6), blur=1.5))
        ground(c, 960, seed=8, t=t)
        pose = merge(run(lt * 2.4, 1.0), COVER, {"head": 6, "hair": 1.4, "sash": 1.4, "bud_open": 0.32})
        self.duo.draw(c, 900, 960, 0.8, pose=pose, t=t)
        c.restore()

    def after_light(self, fr, t, lt, u):
        return {"glow": {"thr": 0.82, "strength": 0.3, "red": 0.5}, "grade": dict(contrast=1.1)}


def furniture(c, kind, x, y, s=1.0, ink=S.INK):
    c.save()
    c.translate(x, y)
    c.scale(s, s)
    p = gfx.paint(ink, 0.97)
    if kind == "wardrobe":
        body = gfx.rect(-150, -620, 300, 600)
        c.drawPath(body, p)
        lattice(c, -130, -590, 120, 260, kind="fret", bar=4)
        lattice(c, 10, -590, 120, 260, kind="fret", bar=4)
        c.drawPath(gfx.rect(-160, -640, 320, 30), p)
        for lx in (-130, 110):
            c.drawPath(gfx.rect(lx, -30, 20, 30), p)
    elif kind == "table":
        c.drawPath(gfx.rect(-220, -260, 440, 34), p)
        for lx in (-200, 180):
            c.drawPath(gfx.rect(lx, -230, 22, 230), p)
        c.drawPath(gfx.rect(-200, -90, 400, 12), p)
    elif kind == "chair":
        c.drawPath(gfx.rect(-70, -220, 140, 20), p)
        c.drawPath(gfx.rect(-70, -480, 16, 480), p)
        c.drawPath(gfx.rect(54, -220, 16, 220), p)
        c.drawPath(gfx.smooth_path([(-80, -500), (-40, -520), (40, -510), (70, -490), (-70, -470)], closed=True), p)
        c.drawPath(_cut_clouds(-62, -360, 1.2), gfx.paint((240, 210, 170), 0.7, blend=gfx.SCREEN))
    elif kind == "mirror":
        c.drawPath(gfx.rect(-12, -420, 24, 420), p)
        c.drawPath(gfx.rect(-90, -30, 180, 30), p)
        ring = gfx.op(gfx.circle(0, -470, 110), gfx.circle(0, -470, 86), "diff")
        c.drawPath(ring, p)
        c.drawPath(gfx.circle(0, -470, 86), gfx.paint((200, 206, 214), 0.6, blend=gfx.MULTIPLY))
    elif kind == "chest":
        c.drawPath(gfx.rect(-170, -220, 340, 200), p)
        c.drawPath(gfx.rect(-20, -170, 40, 40), gfx.paint(S.LEATHER_GOLD, 0.95, blend=gfx.MULTIPLY))
        for lx in (-150, 130):
            c.drawPath(gfx.rect(lx, -20, 20, 20), p)
    elif kind == "screen":
        for k in range(4):
            c.drawPath(gfx.rect(-260 + k * 130, -560, 120, 540), p)
            lattice(c, -250 + k * 130, -540, 100, 240, kind="ice", bar=6)
    elif kind == "vase":
        c.drawPath(gfx.smooth_path([(-30, 0), (-60, -80), (-50, -170), (-20, -210), (-24, -260), (24, -260), (20, -210),
                                    (50, -170), (60, -80), (30, 0)], closed=True), p)
    elif kind == "loom":
        c.drawPath(gfx.rect(-200, -400, 20, 400), p)
        c.drawPath(gfx.rect(180, -400, 20, 400), p)
        c.drawPath(gfx.rect(-200, -400, 400, 20), p)
        for k in range(14):
            c.drawLine(-170 + k * 25, -380, -170 + k * 25, -120, gfx.paint(ink, 0.8, stroke=1.4))
        c.drawPath(gfx.rect(-200, -130, 400, 24), p)
    c.restore()


class CageScene(Stage):
    light = "warm"

    def setup(self):
        self.duo = Puppet("woman", arm_red=0.45, seed=1)
        b0 = audio.beat_index(self.start)
        self.beats = [audio.beat_time(b0 + k) - self.start for k in range(1, 5)]
        self.pieces = [("wardrobe", 340, 980, 1.2, 0), ("screen", 1560, 980, 1.1, 0), ("table", 760, 980, 1.0, 1),
                       ("chair", 1240, 980, 1.1, 1), ("mirror", 160, 980, 1.0, 2), ("chest", 1760, 1000, 1.0, 2),
                       ("loom", 560, 1000, 1.0, 3), ("vase", 1400, 1000, 1.2, 3)]

    def light_params(self, t, lt, u):
        close = E.smooth(E.prog(lt, 0.5, 2.0))
        return dict(radius=1.1 - 0.45 * close, power=1.3 + 0.4 * close, edge=0.25 - 0.2 * close)

    def paint(self, fr, t, lt, u):
        c = fr.canvas
        imp = max([E.pulse(lt, b, 0.01, 0.12) for b in self.beats] + [0])
        cam = Cam(W / 2, H / 2 + 20, 1.0 + 0.06 * u, t=t, shake=0.5 * imp)
        c.save()
        cam.apply(c)
        ground(c, 980, seed=9, t=t)
        stop = E.out_cubic(E.prog(lt, 0.0, 0.3))
        pose = merge(breathe(lt), COVER, {"head": 10, "bud_open": 0.32, "lean": -6 * (1 - stop)})
        self.duo.draw(c, 960, 980, 0.66, pose=pose, t=t)
        for (kind, x, y, s, b) in self.pieces:
            tb = self.beats[b]
            d = E.prog(lt, tb - 0.18, tb)
            if d <= 0:
                continue
            yy = y - 900 * (1 - E.in_quad(d))
            furniture(c, kind, x, yy, s)
        c.restore()

    def after_light(self, fr, t, lt, u):
        c = fr.canvas
        for k, tb in enumerate(self.beats):
            PT.draw_burst(c, lt, tb, W / 2 + (k - 1.5) * 420, 980, n=30, seed=k + 60, speed=(160, 500), size=(2, 6),
                          color=(220, 200, 170), gravity=300, life=0.8, alpha=0.6, blend=gfx.SCREEN, spread=(math.pi, 2 * math.pi))
        imp = max([E.pulse(lt, b, 0.01, 0.1) for b in self.beats] + [0])
        return {"glow": {"thr": 0.82, "strength": 0.3, "red": 0.5}, "flash": 0.1 * imp, "grade": dict(contrast=1.1, sat=0.85)}


class SeasonsScene(Stage):
    light = "warm"

    def setup(self):
        self.duo = Puppet("woman", arm_red=0.45, seed=1)
        ta = LY.char_time(30, 3) - self.start
        tb = LY.char_time(30, 7) - self.start
        self.stamps = [ta + (tb - ta) * k / 15 for k in range(16)]
        rng = RNG(17)
        cols, rows = 8, 2
        self.slots = []
        for k in range(16):
            col = k % 8
            row = k // 8
            x = 150 + col * 232 + rng.u(-20, 20)
            y = 190 + row * 700 + rng.u(-30, 30)
            self.slots.append((x, y, rng.u(-0.12, 0.12)))

    def light_params(self, t, lt, u):
        # day/night alternating with each stamp pair
        ph = 0.5 + 0.5 * math.cos(lt * math.pi * 2.0)
        return dict(paper=(0.80 + 0.2 * ph, 0.80 + 0.14 * ph, 0.84 + 0.04 * ph), boost=-0.12 * (1 - ph))

    def paint(self, fr, t, lt, u):
        c = fr.canvas
        # sun and moon racing across the sky
        for k in range(6):
            ph = (lt * 0.9 + k / 6) % 1.0
            a = math.pi * (1 - ph)
            x = W / 2 + math.cos(a) * 900
            y = 760 - math.sin(a) * 520
            if k % 2 == 0:
                c.drawCircle(x, y, 46, gfx.paint(S.LEATHER_RED, 0.85, blend=gfx.MULTIPLY))
            else:
                c.drawPath(gfx.op(gfx.circle(x, y, 40), gfx.circle(x + 16, y - 8, 36), "diff"), gfx.paint((60, 70, 100), 0.9))
        ground(c, 980, seed=10, t=t)
        # a plant that grows and withers, over and over
        g = (lt / 1.333) % 1.0
        stem_h = 260 * math.sin(g * math.pi)
        c.drawPath(gfx.ribbon([(1300, 980), (1305, 980 - stem_h * 0.5), (1296, 980 - stem_h)], [8, 6, 3]),
                   gfx.paint(S.LEATHER_GREEN_DEEP, 0.95, blend=gfx.MULTIPLY))
        if stem_h > 60:
            draw_poppy_side(c, 1296, 980 - stem_h, 0.9, 0.0, openness=min(1.0, g * 2.2) if g < 0.6 else 1.0,
                            petal=S.lerp3(S.LEATHER_RED, (140, 130, 120), max(0.0, (g - 0.6) / 0.4)), seed=int(lt / 1.333))
        # she stands still while everything turns; her red drains
        red = 0.45 - 0.3 * u
        self.duo.draw(c, 960, 980, 0.72, pose=merge(breathe(lt, amt=0.3), {"head": 4, "bud_open": 0.34}), t=t, arm_red=red)
        # the seals
        for k, (ts, (x, y, rot)) in enumerate(zip(self.stamps, self.slots)):
            fx.draw_seal(c, x, y, 150, TERMS[k], t_stamp=ts, t=lt, style="bai" if k % 2 == 0 else "zhu", rot=rot)

    def after_light(self, fr, t, lt, u):
        imp = max([E.pulse(lt, s, 0.005, 0.08) for s in self.stamps] + [0])
        return {"glow": {"thr": 0.8, "strength": 0.3, "red": 0.6}, "shake": (5 * imp, 3 * imp), "flash": 0.06 * imp}


class TowerScene(Stage):
    light = "night"

    def setup(self):
        self.duo = Puppet("woman", arm_red=0.3, seed=1)
        self.worker = Puppet("woman", arm_red=0.0, seed=2, huadian=False, bead_strands=False, hair_tail=False)
        self.t_pull = 1.2

    def light_params(self, t, lt, u):
        day = 0.5 + 0.5 * math.cos(lt * math.pi * 4)
        return dict(paper=(0.55 + 0.4 * day, 0.62 + 0.3 * day, 0.80 + 0.12 * day), radius=1.4, edge=0.45)

    def window(self, c, x, y, w, h, t, k, detail=True, who=None):
        """One lit office window with a working puppet."""
        c.drawPath(gfx.rect(x, y, w, h), gfx.paint((255, 236, 190), 1.0, blend=gfx.SCREEN))
        if not detail:
            # tiny: just a hunched silhouette and a lamp
            c.drawPath(gfx.rect(x + w * 0.15, y + h * 0.62, w * 0.7, h * 0.08), gfx.paint(S.INK, 0.95))
            c.drawPath(gfx.ellipse(x + w * 0.42, y + h * 0.42, w * 0.13, h * 0.16), gfx.paint(S.INK, 0.95))
            c.drawPath(gfx.rect(x + w * 0.34, y + h * 0.5, w * 0.16, h * 0.14), gfx.paint(S.INK, 0.95))
            return
        sc = h / 900
        writing = 20 * math.sin(t * 14 + k)
        (who or self.worker).draw(c, x + w * 0.42, y + h * 1.08, sc, pose={"torso": 22, "head": 26, "ua_f": 60, "fa_f": 80 + writing,
                                                                          "hand_f": "point", "ua_b": 40, "fa_b": 90, "bud_open": 0.34},
                                  t=t, rivets=False)
        c.drawPath(gfx.rect(x + w * 0.5, y + h * 0.66, w * 0.45, h * 0.06), gfx.paint(S.INK, 0.97))
        c.drawPath(gfx.rect(x + w * 0.88, y + h * 0.72, w * 0.04, h * 0.3), gfx.paint(S.INK, 0.97))
        # desk lamp + paper stacks
        c.drawPath(gfx.rect(x + w * 0.8, y + h * 0.5, w * 0.02, h * 0.16), gfx.paint(S.INK, 0.97))
        c.drawPath(gfx.poly([(x + w * 0.74, y + h * 0.5), (x + w * 0.88, y + h * 0.5), (x + w * 0.84, y + h * 0.42), (x + w * 0.78, y + h * 0.42)]),
                   gfx.paint(S.INK, 0.97))
        for j in range(4):
            c.drawPath(gfx.rect(x + w * 0.58, y + h * (0.63 - j * 0.025), w * 0.16, h * 0.02), gfx.paint(S.INK, 0.9))

    def paint(self, fr, t, lt, u):
        c = fr.canvas
        pull = E.in_out_expo(E.prog(lt, self.t_pull, 3.6))
        z = 1.0 / (1.0 + 26.0 * pull)
        # grid of windows centred on hers
        ww, wh, gap = W * 0.92, H * 0.86, 160
        cx, cy = W / 2, H / 2
        m = skia.Matrix()
        m.setTranslate(cx, cy)
        m.preScale(z, z)
        m.preTranslate(-cx, -cy)
        c.save()
        c.concat(m)
        # tower facade
        c.drawRect(skia.Rect(cx - 40 * (ww + gap), cy - 40 * (wh + gap), cx + 40 * (ww + gap), cy + 60 * (wh + gap)), gfx.paint(S.INK, 0.97))
        n = 1 + int(14 * pull)
        for i in range(-n, n + 1):
            for j in range(-n, n + 1):
                x = cx - ww / 2 + i * (ww + gap)
                y = cy - wh / 2 + j * (wh + gap)
                if i == 0 and j == 0:
                    self.window(c, x, y, ww, wh, t, 0, detail=True, who=self.duo)
                else:
                    if hash01(i * 131 + j * 17, 3) < 0.06:
                        continue  # a few dark windows
                    self.window(c, x, y, ww, wh, t, i * 7 + j, detail=(z * wh > 140))
        c.restore()

    def after_light(self, fr, t, lt, u):
        return {"glow": {"thr": 0.75, "strength": 0.45}, "grade": dict(contrast=1.12)}


class YouthScene(Stage):
    light = "warm"

    def setup(self):
        self.duo = Puppet("woman", arm_red=0.25, seed=1)
        self.kid = Puppet("child", arm_red=1.0, robe_color=S.LEATHER_RED, bud=True, seed=4)
        self.t_fade = 2.6
        self.t_look = 4.0

    def light_params(self, t, lt, u):
        return dict(radius=1.0, power=1.4, edge=0.15, cx=0.55)

    def paint(self, fr, t, lt, u):
        c = fr.canvas
        z = 1.08 + 0.1 * E.in_out_sine(u)
        cam = Cam(W / 2 + 80, H / 2 + 40, z, t=t)
        c.save()
        cam.apply(c)
        # desk
        c.drawPath(gfx.rect(260, 760, 1500, 40), gfx.paint(S.INK, 0.97))
        c.drawPath(gfx.rect(300, 800, 30, 400), gfx.paint(S.INK, 0.97))
        c.drawPath(gfx.rect(1700, 800, 30, 400), gfx.paint(S.INK, 0.97))
        for j in range(9):
            c.drawPath(gfx.rect(860 + 10 * math.sin(j), 744 - j * 18, 200, 14), gfx.paint(S.INK, 0.92))
        look = E.smooth(E.prog(lt, self.t_look, self.t_look + 0.6))
        writing = 22 * math.sin(lt * 15) * (1 - look)
        pose = {"torso": 22 - 18 * look, "head": 30 - 36 * look, "ua_f": 60, "fa_f": 84 + writing, "hand_f": "point",
                "ua_b": 40, "fa_b": 92, "bud_open": 0.34}
        self.duo.draw(c, 700, 1150, 0.95, pose=pose, t=t, flip=False)
        # the child on the desk, holding out the thread
        fade = E.smooth(E.prog(lt, self.t_fade, self.t_fade + 1.2))
        kx, ky = 1250, 760
        kp = {"ua_f": 70 + 6 * math.sin(lt * 3), "fa_f": 10, "hand_f": "spread", "ua_b": 60, "fa_b": 20, "hand_b": "spread",
              "head": 6 * math.sin(lt * 1.5), "bob": 6 * abs(math.sin(lt * 3)) * (1 - fade)}
        if fade < 1:
            with gfx.Layer(c, blur=8 * fade, alpha=1 - fade, matrix=cam.matrix()) as lc:
                self.kid.draw(lc, kx, ky, 0.95, pose=kp, t=t, flip=True)
        hf = self.kid.joint(kp, "hand_f")
        hb = self.kid.joint(kp, "hand_b")
        a = (kx - hf[0] * 0.95, ky + hf[1] * 0.95)
        b = (kx - hb[0] * 0.95, ky + hb[1] * 0.95)
        if fade < 0.7:
            anchors = {"Lt": (a[0] - 90, a[1] - 40), "Li": (a[0] - 100, a[1]), "Lp": (a[0] - 90, a[1] + 40),
                       "Rt": (b[0] + 0, b[1] - 40), "Ri": (b[0] - 10, b[1]), "Rp": (b[0], b[1] + 40)}
            pts = TH.cradle_points(anchors, "cradle", t, 1.5, 3)
            TH.draw_thread(c, pts, width=2.6, glow=1.0 * (1 - fade), alpha=1 - fade, smooth=False)
        # the thread falls limp on the desk
        if fade > 0.4:
            k = E.out_cubic(E.prog(fade, 0.4, 1.0))
            pts = [(1050 + j * 30, 756 - 30 * (1 - k) * math.sin(j * 0.9)) for j in range(12)]
            TH.draw_thread(c, pts, width=2.4, glow=0.5, alpha=k)
        c.restore()

    def after_light(self, fr, t, lt, u):
        c = fr.canvas
        fade = E.smooth(E.prog(lt, self.t_fade, self.t_fade + 1.6))
        if 0 < fade < 1:
            PT.draw_embers(c, t, n=80, seed=44, area=(1150, 300, 1600, 900), rise=80, color=(255, 70, 60), alpha=0.9 * (1 - fade) + 0.3,
                           count=min(1.0, fade * 2))
        return {"glow": {"thr": 0.8, "strength": 0.35, "red": 0.6}, "grade": dict(sat=0.9 - 0.3 * fade)}


def entries():
    return [
        Entry(RunScene(T29, T30), trans=("wipe_r", 0.35)),
        Entry(CageScene(T30, T31)),
        Entry(SeasonsScene(T31, T32), trans=("black", 0.3)),
        Entry(TowerScene(T32, T33), trans=("fade", 0.3)),
        Entry(YouthScene(T33, T34), trans=("iris", 0.6), params={"center": (0.5, 0.5)}),
    ]
