"""0:00 – 0:15.85  Intro.

SC01 旧画  an aged painting of a blossoming branch, seen like an old photograph.  The title is brushed
           on, a seal stamps on the beat, and the camera sinks into one closed bud.
SC02 翻花绳 two children play cat's cradle with a red thread; 阿朵 points out the next move.
SC03 交错  阿朵 and her red "ideal self" pass through each other; her bud cracks; a gust lifts her.
"""
import math

import numpy as np
import skia

from .. import config
from ..core import gfx, audio
from ..core import easing as E
from ..core import text as TXT
from ..core.camera import Cam
from ..core.noise import noise1, RNG
from ..elements import style as S
from ..elements.branch import BranchTree, draw_blossom_ink
from ..elements.puppet import Puppet, walk, breathe, merge, PoseTrack, blend_pose
from ..elements.flower import draw_poppy_side
from ..elements import fx, particles as PT, thread as TH
from ..elements.landscape import Mountains, draw_mist
from ..timeline import Entry
from .common import Stage, stage_light, ground, LIGHTS, W, H

T_SC02 = 8.08
T_SC03 = 12.08
T_END = 15.85

AGED = (0.94, 0.85, 0.68)


class PaintingScene(Stage):
    """The scroll painting.  Shared by the intro (aged) and the finale (crisp, present day)."""
    light = "paper"

    def setup(self):
        self.aged = self.kw.get("aged", True)
        self.tree = BranchTree(seed=21, root=(-140, 1180), angle=-0.72, length=980, width=58, depth=4,
                               spread=0.62, wander=0.16, children=(2, 3), length_decay=0.6).normalize_time()
        tips = self.tree.tip_list(1.0)
        rng = RNG(5)
        self.blooms = []
        for i, (x, y, a, d) in enumerate(tips):
            if x < 80 or y < 60 or x > 1560:
                continue
            r = rng.u()
            if r < 0.55:
                kind = "open" if rng.u() < 0.62 else "bud"
                self.blooms.append((x, y, a, kind, rng.u(22, 34), i))
        # the protagonist bud: the tip closest to a chosen spot
        target = (1010, 470)
        best = min(tips, key=lambda p: (p[0] - target[0]) ** 2 + (p[1] - target[1]) ** 2)
        self.hero = (best[0], best[1], best[2])
        self.blooms = [b for b in self.blooms if (b[0] - best[0]) ** 2 + (b[1] - best[1]) ** 2 > 60 ** 2]
        self.extra_bloom = self.kw.get("extra_bloom", 0.0)
        # growth timeline (aged intro paints itself; the finale is already complete)
        self.g_track = E.Track([(0.3, 0.0), (5.2, 1.0, "in_out_sine")]) if self.aged else (lambda lt: 1.0)
        tips_t = {}
        ts = np.linspace(0, 8, 801)
        gs = np.array([self.g_track(x) for x in ts])
        self.pop = []
        for (x, y, a, kind, r, i) in self.blooms:
            tb = [tb for (tx, ty, ta, d, tb) in self.tree.tips if abs(tx - x) < 1e-6 and abs(ty - y) < 1e-6]
            tb = tb[0] if tb else 1.0
            j = int(np.searchsorted(gs, min(tb, 0.999)))
            tl = ts[min(j, len(ts) - 1)]
            # snap to the next half beat
            gb = audio.beat_index(tl + self.start) + 0.5
            tpop = audio.beat_time(math.ceil((tl + self.start - config.BEAT0) / (config.BEAT / 2)) * 0.5 * 2 / 2) - self.start
            k = math.ceil((tl + self.start - config.BEAT0) / (config.BEAT / 2))
            tpop = config.BEAT0 + k * config.BEAT / 2 - self.start
            self.pop.append(tpop if self.aged else -10.0)

    def light_params(self, t, lt, u):
        if self.aged:
            return dict(paper=AGED, edge=0.62)
        return dict(paper=(0.98, 0.95, 0.89), edge=0.85, radius=2.2)

    def camera(self, t, lt):
        if self.aged:
            hx, hy = self.hero[0], self.hero[1]
            z = E.Track([(0.0, 1.0), (5.0, 1.1, "in_out_sine"), (8.08, 7.0, "in_expo")])(lt)
            k = E.in_out_cubic(E.prog(lt, 4.6, 7.6))
            cx = W / 2 + (hx - W / 2) * k
            cy = H / 2 + (hy - 40 - H / 2) * k
            return Cam(cx, cy, z, 0.0, t=t)
        k = self.kw.get("cam", None)
        return k(t, lt) if k else Cam(t=t)

    def paint(self, fr, t, lt, u):
        c = fr.canvas
        cam = self.camera(t, lt)
        c.save()
        cam.apply(c)
        # faint stains on the old paper
        if self.aged:
            for k, (sx, sy, sr) in enumerate(((320, 260, 260), (1500, 860, 300), (980, 120, 180))):
                c.drawPath(gfx.blob(sx, sy, sr, 0.3, seed=k + 40), gfx.paint((150, 120, 70), 0.10, blur=60))
        growth = self.g_track(lt)
        # pale distant wash for depth
        c.drawPath(gfx.blob(1180, 640, 420, 0.25, seed=71), gfx.paint((120, 108, 96), 0.10 * E.prog(lt, 0.5, 3.0) if self.aged else 0.10, blur=70))
        self.tree.draw(c, growth=growth, style="ink", color=(28, 22, 20), alpha=0.94, dry=0.7)
        for (x, y, a, kind, r, i), tp in zip(self.blooms, self.pop):
            k = E.prog(lt, tp, tp + 0.35)
            if k <= 0:
                continue
            sc = E.out_back(k, 2.2)
            op = (1.0 if kind == "open" else 0.15) * (0.4 + 0.6 * E.out_cubic(k))
            draw_blossom_ink(c, x, y, r * sc, openness=op if kind == "open" else 0.15, rot=a + math.pi / 2 + 0.3 * noise1(i, 3), seed=i,
                             alpha=0.93 * min(1.0, k * 3))
        hx, hy, ha = self.hero
        hero_open = self.kw.get("hero_open", 0.0)
        glow = 0.0
        if self.aged:
            glow = 0.45 * E.smooth(E.prog(lt, 4.0, 7.0)) + 0.35 * audio.beat_pulse(t, 0.25) * E.prog(lt, 4.0, 5.0)
        hk = E.prog(growth, 0.55, 0.7) if self.aged else 1.0
        if glow > 0:
            c.drawCircle(hx, hy - 34, 46, gfx.paint(S.ROUGE_HOT, glow * 0.55, blur=30))
        if hk > 0:
            draw_poppy_side(c, hx, hy, 0.95 * E.out_back(hk), ha + math.pi / 2 + 0.05 * noise1(lt * 0.6, 4),
                            openness=hero_open, seed=99, alpha=0.96, stem_len=14, stem_curve=0.3)
        # inscription + seals
        self.inscription(c, t, lt)
        c.restore()

    def inscription(self, c, t, lt):
        x, y0, size = 1700, 170, 118
        if self.aged:
            for k, ch in enumerate("花骨朵"):
                a0 = 1.4 + k * 0.62
                rv = E.prog(lt, a0, a0 + 0.55)
                if rv <= 0:
                    continue
                gp = TXT.glyph_path("running", ch)
                cy = y0 + k * size * 1.02
                c.save()
                c.clipRect(skia.Rect(x - size, cy - 10, x + size, cy + 10 + (size + 30) * E.in_out_sine(rv)))
                c.translate(x - size / 2, cy + size * 0.88)
                c.scale(size / 100, size / 100)
                c.drawPath(gp, gfx.paint((24, 18, 16), 0.25, blur=4))
                c.drawPath(gp, gfx.paint((24, 18, 16), 0.95, blur=0.6))
                c.restore()
            fx.draw_seal(c, x, y0 + 3 * size * 1.02 + 70, 96, "花骨朵", t_stamp=self.start + 4.08, t=t, style="bai", rot=-0.02)
            fx.draw_seal(c, 120, 980, 60, "影", t_stamp=self.start + 4.58, t=t, style="zhu", rot=0.04)
        else:
            # present day: the same marks, crisp
            TXT.draw_text(c, "花骨朵", x - size / 2 + size / 2, y0, size, face="running", color=(24, 18, 16, 245), vertical=True,
                          spacing=1.02)
            fx.draw_seal(c, x, y0 + 3 * size * 1.02 + 70, 96, "花骨朵", style="bai", rot=-0.02)
            fx.draw_seal(c, 120, 980, 60, "影", style="zhu", rot=0.04)

    def after_light(self, fr, t, lt, u):
        pp = {}
        if self.aged:
            pp["film"] = 1.0 - 0.85 * E.smooth(E.prog(lt, 5.5, 8.0))
            pp["fade"] = 1.0 - E.smooth(E.prog(lt, 0.0, 1.5))
            pp["grade"] = dict(contrast=1.05, sat=0.95)
            # seal stamp impact shake
            k = audio.beat_pulse(t, 0.12) if 4.0 < lt < 4.4 else 0.0
            if k > 0.05:
                pp["shake"] = (6 * k, 4 * k)
        else:
            pp["grade"] = dict(contrast=1.06, sat=1.05)
        return pp


# ------------------------------------------------------------------------- SC02 cat's cradle

def stage_backdrop(c, t, seed=0, hills=True, tree=True, alpha=1.0):
    if hills:
        m = _hills.setdefault(seed, Mountains(seed=seed + 2, base=760, height=260, freq=0.002))
        m.draw(c, tone=(150, 136, 124), alpha=0.35 * alpha, blur=5, mist=0.9, cun=False)
    if tree:
        tr = _trees.setdefault(seed, BranchTree(seed=seed + 31, root=(-60, 900), angle=-1.2, length=520, width=46,
                                                depth=4, spread=0.7, wander=0.2).normalize_time())
        tr.draw(c, growth=1.0, style="cut", color=S.INK, alpha=0.92 * alpha)
        for i, (x, y, a, d) in enumerate(tr.tip_list(1.0)):
            if i % 2 == 0:
                draw_poppy_side(c, x, y, 0.7, a + math.pi / 2, openness=1.0 if i % 4 == 0 else 0.0, seed=i,
                                alpha=0.95 * alpha, stem_len=8)


_hills = {}
_trees = {}


class CradleScene(Stage):
    light = "warm"

    def setup(self):
        self.duo = Puppet("woman", arm_red=1.0, seed=1)
        self.kid_red = Puppet("child", arm_red=1.0, robe_color=S.LEATHER_RED, bud=True, seed=4)
        self.kid_ink = Puppet("child", arm_red=0.4, bud=False, seed=5)
        self.duo_pose = PoseTrack([
            (0.0, merge(breathe(0), {"ua_f": 6, "fa_f": 14, "head": -4})),
            (1.2, {"ua_f": 6, "fa_f": 14, "head": -10, "torso": 4}),
            (1.75, {"ua_f": 62, "fa_f": 18, "hand_f": "point", "torso": 10, "head": -12, "lean": 3}, "out_back"),
            (2.8, {"ua_f": 58, "fa_f": 20, "hand_f": "point", "torso": 8, "head": -8, "lean": 2}),
            (3.6, {"ua_f": 10, "fa_f": 16, "hand_f": "relax", "torso": 3, "head": -4, "lean": 0}),
        ])

    def light_params(self, t, lt, u):
        return dict(boost=0.06 * audio.beat_pulse(t, 0.2))

    def kids(self, c, t, lt, xoff=0.0, alpha=1.0):
        gy = 900
        # holder (ink kid) on the right facing left, red kid on the left facing right
        hop = 18 * E.bump(lt, 2.0, 2.15, 2.25, 2.6)  # red kid's little jump of joy
        hes = 1.0 - E.smooth(E.prog(lt, 1.9, 2.1))   # hesitation tremble before the hint
        pr = {"ua_f": 78, "fa_f": 8 + 4 * hes * math.sin(lt * 23), "hand_f": "spread", "ua_b": 64, "fa_b": 30,
              "hand_b": "spread", "head": -6 + 3 * hes * math.sin(lt * 9), "bob": hop, "torso": 4}
        pi = {"ua_f": 76, "fa_f": 10, "hand_f": "spread", "ua_b": 62, "fa_b": 32, "hand_b": "spread", "head": -4,
              "torso": 3}
        xr, xi = 700 + xoff, 1080 + xoff
        self.kid_red.draw(c, xr, gy, 1.3, pose=pr, t=t, alpha=alpha)
        self.kid_ink.draw(c, xi, gy, 1.3, pose=pi, t=t, flip=True, alpha=alpha)
        # string anchors (hands of both kids)
        rf = self.kid_red.joint(pr, "hand_f")
        rb = self.kid_red.joint(pr, "hand_b")
        jf = self.kid_ink.joint(pi, "hand_f")
        jb = self.kid_ink.joint(pi, "hand_b")
        P = lambda x0, j: (x0 + j[0] * 1.3, gy + j[1] * 1.3)
        Pf = lambda x0, j: (x0 - j[0] * 1.3, gy + j[1] * 1.3)
        L1, L2 = P(xr, rf), P(xr, rb)
        R1, R2 = Pf(xi, jf), Pf(xi, jb)
        anchors = {"Lt": (L1[0] + 6, L1[1] - 44), "Li": (L1[0] + 12, L1[1] + 4), "Lp": (L2[0] + 8, L2[1] + 46),
                   "Rt": (R1[0] - 6, R1[1] - 44), "Ri": (R1[0] - 12, R1[1] + 4), "Rp": (R2[0] - 8, R2[1] + 46)}
        return anchors

    def paint(self, fr, t, lt, u):
        c = fr.canvas
        k = E.in_out_cubic(E.prog(lt, 0.5, 1.6))
        z = 2.3 + (1.08 - 2.3) * k + 0.04 * E.in_out_sine(u)
        cx = 880 + (W / 2 + 30 - 880) * k
        cy = 660 + (H / 2 + 40 - 660) * k
        cam = Cam(cx, cy, z, t=t)
        c.save()
        cam.apply(c)
        stage_backdrop(c, t, seed=0)
        ground(c, 900, seed=2, t=t)
        anchors = self.kids(c, t, lt)
        k = E.out_cubic(E.prog(lt, 2.0, 2.45))
        pa = TH.cradle_points(anchors, "cradle", t, 1.2, 1)
        pb = TH.cradle_points(anchors, "diamond", t, 1.2, 2)
        pts = TH.morph_points(pa, pb, k)
        flash = audio.beat_pulse(t, 0.3) if lt > 1.95 else 0.0
        TH.draw_thread(c, pts, width=2.6, glow=0.8 + 1.6 * E.bump(lt, 1.95, 2.05, 2.2, 2.9), smooth=False)
        # A-Duo watching from the right
        pose = self.duo_pose(lt)
        self.duo.draw(c, 1450, 900, 1.0, pose=merge(pose, {"hair": 0.1}), t=t, flip=True)
        c.restore()

    def after_light(self, fr, t, lt, u):
        c = fr.canvas
        PT.draw_dust(c, t, n=70, alpha=0.35)
        return {"glow": {"thr": 0.86, "strength": 0.35, "red": 0.55}, "grade": dict(contrast=1.04)}


class CrossingScene(Stage):
    light = "warm"

    def setup(self):
        self.duo = Puppet("woman", arm_red=1.0, seed=1)
        self.red = Puppet("woman", leather=S.LEATHER_RED, arm_red=1.0, seed=8, huadian=False)
        self.cradle = CradleScene(self.start, self.end)
        self.t_cross = 1.42  # local time of the crossing

    def light_params(self, t, lt, u):
        fl = E.bump(lt, self.t_cross - 0.1, self.t_cross, self.t_cross + 0.1, self.t_cross + 0.6)
        return dict(boost=0.25 * fl)

    def paint(self, fr, t, lt, u):
        c = fr.canvas
        tc = self.t_cross
        rise = E.in_cubic(E.prog(lt, 2.75, 3.77))
        cam = Cam(W / 2, H / 2 - 260 * rise, 1.0 + 0.06 * u, t=t, shake=0.15 * E.bump(lt, tc - 0.1, tc, tc + 0.1, tc + 0.5))
        c.save()
        cam.apply(c)
        stage_backdrop(c, t, seed=0)
        ground(c, 900, seed=2, t=t)
        # children continue in the background, blurred (moved away from the screen)
        ka = 0.55 * (1 - E.smooth(E.prog(lt, 0.0, 0.9)))
        if ka > 0.01:
            with gfx.Layer(c, blur=7, alpha=ka, matrix=cam.matrix()) as lc:
                anchors = self.cradle.kids(lc, t, lt + 4, xoff=-80)
                pts = TH.cradle_points(anchors, "diamond", t, 1.0, 2)
                TH.draw_thread(lc, pts, width=2.4, glow=0.6, smooth=False)
        # walkers
        wk = E.prog(lt, 0.0, 2.4)
        x_duo = 1460 - 560 * E.out_sine(wk)
        x_red = 300 + 1100 * E.in_out_sine(E.prog(lt, 0.0, 3.0))
        stop = E.smooth(E.prog(lt, 2.3, 2.8))
        ph = lt * 0.9
        pose_d = blend_pose(merge(walk(ph), {"hair": 0.0}), merge(breathe(lt), {"head": 14, "ua_f": 20, "fa_f": 30, "hair": 1.0, "sash": 1.0}), stop)
        crack = E.out_back(E.prog(lt, tc, tc + 0.35))
        pose_d["bud_open"] = 0.0 + 0.16 * crack
        gust = E.smooth(E.prog(lt, 2.0, 2.6))
        pose_d["hair"] = pose_d.get("hair", 0) + 1.2 * gust
        pose_d["sash"] = pose_d.get("sash", 0) + 1.2 * gust
        y_duo = 900 - 420 * rise
        # red self, larger and blurred: further from the screen, closer to the lamp
        with gfx.Layer(c, blur=5.0, alpha=0.75 * (1 - E.smooth(E.prog(lt, tc + 0.4, tc + 1.4))), matrix=cam.matrix()) as lc:
            self.red.draw(lc, x_red, 905, 1.12, pose=merge(walk(ph + 0.5), {"hair": 0.4}), t=t)
        self.duo.draw(c, x_duo, y_duo, 1.0, pose=pose_d, t=t, flip=True)
        c.restore()

    def after_light(self, fr, t, lt, u):
        c = fr.canvas
        gust = E.smooth(E.prog(lt, 2.0, 2.8))
        if gust > 0:
            PT.draw_petals(c, t, n=70, seed=11, wind=-900 * gust, fall=(-40, 60), size=(6, 14), alpha=0.9 * gust,
                           color=S.ROUGE, color2=S.ROUGE_DEEP, count=gust)
        PT.draw_dust(c, t, n=70, alpha=0.3)
        tc = self.t_cross
        fl = E.bump(lt, tc - 0.06, tc, tc + 0.05, tc + 0.5)
        return {"glow": {"thr": 0.84, "strength": 0.4 + 0.5 * fl, "red": 0.6}, "flash": 0.35 * fl,
                "chroma": 4 * fl}


def entries():
    return [
        Entry(PaintingScene(0.0, T_SC02, aged=True)),
        Entry(CradleScene(T_SC02, T_SC03), trans=("ink", 0.7), params={"center": (0.5, 0.45), "color": (150, 20, 30)}),
        Entry(CrossingScene(T_SC03, T_END)),
    ]
