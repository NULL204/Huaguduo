"""1:34.85 – 1:50.85  The hide (皮囊) — the quiet section.

SC24 alone      one dim lamp; 阿朵 sits by herself.
SC25 forgotten  bloomed flowers hang from a tree like lanterns and grey into ash; on a family register the
                women — recorded only as 'so-and-so 氏' — are washed out with ink one by one.
SC26 the hide   the lamp comes right up behind her: the light shows the carved leather, the rivets, and the
                rods fixed to her neck and wrists — held by a huge blurred pair of hands below.
SC27 one bed    a carved canopy bed; two heads on one pillow, turned away from each other.
SC28 two dreams above each sleeper a different dream rises (rank and coin / sky, insect, thread); they
                drift apart.  She wakes clutching her bud.
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
from ..elements.branch import BranchTree
from ..elements.puppet import Puppet, walk, run, breathe, merge, _cut_clouds
from ..elements.flower import draw_poppy_side, draw_poppy_front
from ..elements.hand import draw_big_hand
from ..elements.insects import draw_cochineal
from ..elements import fx, particles as PT, thread as TH
from ..timeline import Entry
from .common import Stage, ground, W, H
from .s3_house import lattice, lantern

T24, T25, T26, T27, T28, T29 = 94.85, 96.30, 98.85, 102.85, 106.85, 110.85

SURNAMES = "王李张刘陈杨黄赵周吴徐孙朱马胡郭林何高罗"


class AloneScene(Stage):
    light = "spot"

    def setup(self):
        self.duo = Puppet("woman", arm_red=0.6, seed=1)

    def light_params(self, t, lt, u):
        return dict(cx=0.5, cy=0.5, radius=0.55, power=1.8, edge=0.02, flick=2.0)

    def paint(self, fr, t, lt, u):
        c = fr.canvas
        z = 1.0 + 0.05 * u
        cam = Cam(W / 2, H / 2, z, t=t)
        c.save()
        cam.apply(c)
        ground(c, 860, seed=6, t=t)
        # a low stool
        c.drawPath(gfx.rect(880, 740, 160, 26), gfx.paint(S.INK, 0.97))
        for x in (892, 1012):
            c.drawPath(gfx.rect(x, 760, 16, 100), gfx.paint(S.INK, 0.97))
        pose = merge(breathe(lt, amt=0.6), {"torso": 14, "head": 22, "ua_f": 30, "fa_f": 100, "ua_b": 24, "fa_b": 104,
                                            "hand_f": "relax", "foot_f": (60, 0), "foot_b": (40, 0), "bud_open": 0.3})
        # sitting: draw the puppet lowered onto the stool
        self.duo.draw(c, 960, 1100, 0.78, pose=pose, t=t)
        c.restore()

    def after_light(self, fr, t, lt, u):
        PT.draw_dust(fr.canvas, t, n=60, alpha=0.35, speed=0.5)
        return {"grade": dict(sat=0.7, contrast=1.08), "glow": {"thr": 0.8, "strength": 0.3, "red": 0.4}}


class ForgottenScene(Stage):
    light = "warm"

    def setup(self):
        self.tree = BranchTree(seed=91, root=(1620, 1200), angle=-math.pi / 2 - 0.25, length=900, width=60, depth=4,
                               spread=0.8, wander=0.2).normalize_time()
        tips = sorted([tp for tp in self.tree.tip_list(1.0) if tp[1] < 700 and tp[0] > 900], key=lambda p: p[0])
        self.tips = []
        for tp in tips:
            if all((tp[0] - q[0]) ** 2 + (tp[1] - q[1]) ** 2 > 110 ** 2 for q in self.tips):
                self.tips.append(tp)
        self.tips = self.tips[:12]
        rng = RNG(5)
        self.names = []
        for k in range(14):
            sn = SURNAMES[int(rng.i(0, len(SURNAMES)))]
            self.names.append(sn + "氏")
        self.duo = Puppet("woman", arm_red=0.55, seed=1)

    def light_params(self, t, lt, u):
        return dict(radius=1.1, edge=0.22)

    def paint(self, fr, t, lt, u):
        c = fr.canvas
        cam = Cam(W / 2 + 40 * u, H / 2, 1.02 + 0.04 * u, t=t)
        c.save()
        cam.apply(c)
        # the family register: columns, right to left; the women's entries are washed out one by one
        x0, y0 = 760, 120
        c.drawPath(gfx.rect(60, 80, 760, 720), gfx.paint((236, 226, 204), 0.5, blend=gfx.MULTIPLY))
        for k, nm in enumerate(self.names):
            col = k % 7
            row = k // 7
            x = x0 - col * 100
            y = y0 + row * 330
            te = 0.15 + k * 0.16
            wash = E.smooth(E.prog(lt, te, te + 0.45))
            TXT.draw_text(c, nm, x, y, 64, face="serif", color=(30, 22, 18, int(230 * (1 - 0.85 * wash))), vertical=True,
                          align="start")
            if wash > 0:
                fx.ink_blot(c, x, y + 70, 40 + 30 * wash, color=(30, 24, 22), alpha=0.75 * wash, seed=k + 3, growth=wash)
        # ruled lines of the register
        for k in range(8):
            c.drawLine(x0 + 50 - k * 100, 100, x0 + 50 - k * 100, 790, gfx.paint((120, 40, 40), 0.35, stroke=1.5))
        # the tree of lanterns: bloomed flowers hanging, greying, dropping petals as ash
        self.tree.draw(c, 1.0, style="cut", color=S.INK)
        for i, (x, y, a, d) in enumerate(self.tips):
            fade = E.smooth(E.prog(lt, 0.3 + i * 0.1, 1.8 + i * 0.1))
            L = 50 + 40 * hash01(i, 3)
            sw = 6 * noise1(t * 0.9 + i, 4)
            c.drawLine(x, y, x + sw, y + L, gfx.paint(S.INK, 1.0, stroke=1.6))
            col = S.lerp3(S.LEATHER_RED, (150, 144, 140), fade)
            draw_poppy_side(c, x + sw, y + L, 1.1, math.pi, openness=1.0, seed=i, petal=col, sepal=S.lerp3(S.LEATHER_GREEN, (130, 130, 120), fade),
                            alpha=1.0 - 0.3 * fade, stem_len=4)
        # 阿朵, small, looking up at them
        self.duo.draw(c, 980, 1000, 0.5, pose=merge(breathe(lt), {"head": -18, "bud_open": 0.3}), t=t)
        ground(c, 1000, seed=7, t=t)
        c.restore()

    def after_light(self, fr, t, lt, u):
        c = fr.canvas
        PT.draw_petals(c, t, n=40, seed=91, wind=-20, fall=(40, 90), size=(5, 11), alpha=0.6, color=(150, 140, 136),
                       color2=(110, 104, 100))
        return {"grade": dict(sat=0.75), "glow": {"thr": 0.82, "strength": 0.3, "red": 0.4}}


class HideScene(Stage):
    light = "warm"

    def setup(self):
        self.duo = Puppet("woman", arm_red=0.55, seed=1)

    def light_params(self, t, lt, u):
        close = E.in_out_cubic(E.prog(lt, 0.2, 1.6))
        return dict(cx=0.47, cy=0.42, radius=1.0 - 0.45 * close, power=1.3 + 0.4 * close, edge=0.2 - 0.14 * close,
                    boost=0.25 * close)

    def paint(self, fr, t, lt, u):
        c = fr.canvas
        close = E.in_out_cubic(E.prog(lt, 0.2, 1.6))
        look = E.smooth(E.prog(lt, 1.6, 2.4))
        down = E.smooth(E.prog(lt, 2.8, 3.6))
        pose = merge(breathe(lt, amt=0.5), {"ua_f": 20 + 70 * look, "fa_f": 40 + 50 * look, "hand_f": "open",
                                            "head": -4 + 18 * look * (1 - down) + 30 * down, "bud_open": 0.3})
        z = 1.75 + 0.2 * E.in_out_sine(u)
        cam = Cam(930, 600 + 40 * u, z, t=t)
        c.save()
        cam.apply(c)
        # the backlit leather: draw slightly translucent so the light 'shines through the hide'
        alpha = 1.0 - 0.28 * close
        self.duo.draw(c, 900, 1060, 0.9, pose=pose, t=t, alpha=alpha, rods=E.smooth(E.prog(lt, 0.9, 1.8)))
        c.restore()
        # the puppeteer's hands far below, huge and blurred (close to the lamp)
        k = E.smooth(E.prog(lt, 1.2, 2.6))
        if k > 0:
            with gfx.Layer(c, blur=11, alpha=0.85 * k) as lc:
                for (x, rot) in ((640, 0.2), (1300, -0.25)):
                    draw_big_hand(lc, x, 1460 - 160 * k, 2.4, rot=rot, openness=0.3, redness=0.0, t=t, sleeve=True)

    def after_light(self, fr, t, lt, u):
        PT.draw_dust(fr.canvas, t, n=70, alpha=0.4)
        return {"glow": {"thr": 0.78, "strength": 0.45, "red": 0.5}, "grade": dict(contrast=1.08)}


class BedScene(Stage):
    light = "warm"

    def setup(self):
        self.duo = Puppet("woman", arm_red=0.5, seed=1)
        self.man = Puppet("man", arm_red=0.0, bud=False, hair_tail=False, seed=6)

    def light_params(self, t, lt, u):
        return dict(radius=1.05, power=1.3, edge=0.2, paper=(1.0, 0.82, 0.70))

    def bed(self, c, t):
        cx = W / 2
        # canopy frame with a labyrinth lattice
        c.drawPath(gfx.rect(cx - 760, 120, 1520, 60), gfx.paint(S.INK, 0.97))
        lattice(c, cx - 740, 180, 1480, 120, kind="fret", bar=6)
        for x in (-760, -720, 720, 760):
            c.drawPath(gfx.rect(cx + x - 18, 120, 36, 820), gfx.paint(S.INK, 0.97))
        # tied-back curtains
        for sgn in (-1, 1):
            cur = gfx.smooth_path([(cx + sgn * 700, 300), (cx + sgn * 560, 300), (cx + sgn * 620, 520), (cx + sgn * 690, 760),
                                   (cx + sgn * 700, 760)], closed=True)
            c.drawPath(cur, gfx.paint(S.LEATHER_RED, 0.92, blend=gfx.MULTIPLY))
            c.drawPath(cur, gfx.paint(S.INK, 1.0, stroke=2.5))
            c.drawCircle(cx + sgn * 640, 520, 14, gfx.paint(S.LEATHER_GOLD, 0.95, blend=gfx.MULTIPLY))
        # bed base
        c.drawPath(gfx.rect(cx - 740, 760, 1480, 180), gfx.paint(S.INK, 0.97))
        c.drawPath(_cut_clouds(cx - 400, 850, 3.0), gfx.paint((240, 200, 160), 0.6, blend=gfx.SCREEN))
        c.drawPath(_cut_clouds(cx + 400, 850, 3.0), gfx.paint((240, 200, 160), 0.6, blend=gfx.SCREEN))

    def sleepers(self, c, t, lt, wake=0.0):
        cx = W / 2
        # one long pillow
        c.drawPath(gfx.smooth_path([(cx - 420, 560), (cx + 420, 560), (cx + 440, 610), (cx - 440, 610)], closed=True),
                   gfx.paint(S.LEATHER_GOLD, 0.92, blend=gfx.MULTIPLY))
        # heads, back to back: him on the left facing left, her on the right facing right
        c.save()
        c.clipRect(skia.Rect(cx - 760, 0, cx + 760, 690))
        c.save()
        c.translate(cx - 200, 650)
        c.scale(1.6, 1.6)
        c.translate(0, 470)
        self.man.draw(c, 0, 0, 1.0, pose={"head": -50}, t=t, flip=True, rivets=False)
        c.restore()
        c.save()
        c.translate(cx + 200, 650 - 60 * wake)
        c.scale(1.6, 1.6)
        c.translate(0, 470)
        self.duo.draw(c, 0, 0, 1.0, pose={"head": -50 + 60 * wake, "bud_open": 0.3}, t=t, rivets=False)
        c.restore()
        c.restore()
        # the red quilt over both
        q = gfx.smooth_path([(cx - 700, 640), (cx - 300, 600), (cx, 630), (cx + 300, 600), (cx + 700, 640), (cx + 720, 780),
                             (cx - 720, 780)], closed=True)
        c.drawPath(q, gfx.paint(S.LEATHER_RED, 0.95, blend=gfx.MULTIPLY))
        cl = skia.Path()
        for k in range(5):
            cl.addPath(_cut_clouds(cx - 520 + k * 260, 700, 2.4))
        c.drawPath(cl, gfx.paint(S.INK, 0.8))
        c.drawPath(q, gfx.paint(S.INK, 1.0, stroke=3))

    def paint(self, fr, t, lt, u):
        c = fr.canvas
        cam = Cam(W / 2, H / 2 + 20, 1.0 + 0.08 * E.in_out_sine(u), t=t)
        c.save()
        cam.apply(c)
        self.bed(c, t)
        self.sleepers(c, t, lt)
        for k, lx in enumerate((-860, 860)):
            lantern(c, W / 2 + lx, 420, 40, lit=1.0, t=t, seed=k + 5, char="囍")
        c.restore()

    def after_light(self, fr, t, lt, u):
        return {"glow": {"thr": 0.8, "strength": 0.4, "red": 0.6}}


class DreamsScene(BedScene):
    def setup(self):
        super().setup()
        rng = RNG(13)
        self.coins = [(rng.u(-160, 160), rng.u(-90, 90), rng.u(0, 6.28)) for _ in range(9)]

    def paint(self, fr, t, lt, u):
        c = fr.canvas
        wake = E.smooth(E.prog(lt, 3.2, 3.9))
        cam = Cam(W / 2, H / 2 - 60 * E.in_out_sine(u), 1.08 - 0.05 * u, t=t)
        c.save()
        cam.apply(c)
        self.bed(c, t)
        self.sleepers(c, t, lt, wake=wake)
        rise = E.out_cubic(E.prog(lt, 0.1, 1.2))
        apart = E.in_out_cubic(E.prog(lt, 1.2, 3.4))
        # his dream (left): ingots, coins, an official seal
        mx, my = W / 2 - 330 - 260 * apart, 330 - 120 * rise
        self.dream_cloud(c, mx, my, 250 * rise, seed=1)
        if rise > 0.3:
            for (dx, dy, a) in self.coins:
                ang = a + lt * 2
                x, y = mx + dx * rise, my + dy * rise
                c.drawPath(gfx.ellipse(x, y, 26 * abs(math.cos(ang)) + 2, 26), gfx.paint(S.LEATHER_GOLD, 0.95, blend=gfx.MULTIPLY))
                c.drawPath(gfx.rect(x - 6, y - 6, 12, 12), gfx.paint((240, 220, 180), 0.9))
                c.drawPath(gfx.ellipse(x, y, 26 * abs(math.cos(ang)) + 2, 26), gfx.paint(S.INK, 1.0, stroke=2))
            fx.draw_seal(c, mx, my - 10, 90 * rise, "官", style="bai", rot=0.05)
        # her dream (right): open sky, the flying insect and the red thread of the cat's cradle
        hx, hy = W / 2 + 330 + 260 * apart, 330 - 120 * rise
        self.dream_cloud(c, hx, hy, 250 * rise, seed=2, sky=True)
        if rise > 0.3:
            pts = [(hx - 140 + 280 * j / 20, hy + 40 * math.sin(j * 0.6 + lt * 2)) for j in range(21)]
            TH.draw_thread(c, pts, width=3, glow=1.2)
            draw_cochineal(c, hx + 60 * math.sin(lt * 1.3), hy - 70 + 20 * math.cos(lt * 2), 0.8, -0.3, t=t, wings=1.0,
                           flap=lt * 9)
            Puppet("child", arm_red=1.0, robe_color=S.LEATHER_RED, bud=True, seed=4).draw(c, hx - 90, hy + 150, 0.5,
                                                                                            pose={"ua_f": 80, "fa_f": 10, "hand_f": "spread"}, t=t)
        c.restore()
        # a crack opening between the dreams
        if apart > 0.2:
            cr = fx.Cracks(W / 2, 320, seed=4, n=3, length=(200, 400))
            cr.draw(c, E.prog(apart, 0.2, 1.0), color=S.INK, width=4)

    def dream_cloud(self, c, x, y, r, seed=0, sky=False):
        if r < 4:
            return
        blob = skia.Path()
        rng = RNG(seed)
        for k in range(9):
            a = 2 * math.pi * k / 9
            blob = gfx.op(blob, gfx.circle(x + math.cos(a) * r * 0.75, y + math.sin(a) * r * 0.5, r * rng.u(0.35, 0.5)), "union")
        blob = gfx.op(blob, gfx.ellipse(x, y, r * 0.8, r * 0.55), "union")
        c.drawPath(blob, gfx.paint((250, 246, 236) if not sky else (226, 236, 250), 0.95))
        c.drawPath(blob, gfx.paint(S.INK, 0.9, stroke=3))
        # little bubbles trailing down to the sleeper
        for k in range(3):
            c.drawCircle(x + (W / 2 - x) * 0.15 * (k + 1), y + r * 0.6 + 40 * (k + 1), 14 - 4 * k, gfx.paint(S.INK, 0.9, stroke=2.5))

    def after_light(self, fr, t, lt, u):
        wake = E.bump(lt, 3.2, 3.3, 3.4, 3.9)
        return {"glow": {"thr": 0.8, "strength": 0.4, "red": 0.6}, "flash": 0.15 * wake}


def entries():
    return [
        Entry(AloneScene(T24, T25), trans=("black", 0.6)),
        Entry(ForgottenScene(T25, T26), trans=("fade", 0.5)),
        Entry(HideScene(T26, T27), trans=("fade", 0.4)),
        Entry(BedScene(T27, T28), trans=("black", 0.5)),
        Entry(DreamsScene(T28, T29), trans=("cut", 0.0)),
    ]
