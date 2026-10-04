"""0:15.85 – 0:30.90  Refrain 1 — the question, asked for the first time (bewildered).

SC04 drift     阿朵 drifts over ink mountains like a seed on the wind.
SC05 fork      she lands in the crotch of a giant branch; the camera looks left (blossoms hung like
               lanterns) then right (bare twigs into fog) on the sung syllables.
SC06 palm      her red hand opens: a cochineal crawls in the lamp-light.
SC07 release   the insect curls into an oval that becomes her bud — 'doesn't it look like…' — then
               it unfolds wings and flies off, trailing a thread of red.  The world chills.
"""
import math

import numpy as np
import skia

from .. import config
from ..core import gfx, audio
from ..core import easing as E
from ..core import lyrics as LY
from ..core.camera import Cam
from ..core.noise import noise1, RNG
from ..elements import style as S
from ..elements.branch import BranchTree
from ..elements.puppet import Puppet, walk, breathe, merge, PoseTrack, blend_pose
from ..elements.flower import draw_poppy_side
from ..elements.hand import draw_big_hand
from ..elements.insects import draw_cochineal
from ..elements import fx, particles as PT, thread as TH
from ..elements.landscape import Mountains, draw_mist
from ..timeline import Entry
from .common import Stage, ground, W, H

T4, T5, T6, T7, T8 = 15.85, 17.90, 22.85, 26.45, 30.90


def clouds(c, t, seed=0, y=200, alpha=0.5, color=(255, 250, 240), speed=10):
    rng = RNG(seed)
    for k in range(6):
        x = (rng.u(0, W + 600) + t * speed * rng.u(0.6, 1.4)) % (W + 800) - 400
        yy = y + rng.n(0, 60)
        for j in range(4):
            c.drawPath(gfx.ellipse(x + j * 90 - 135, yy + rng.n(0, 12), rng.u(80, 150), rng.u(26, 44)),
                       gfx.paint(color, alpha * 0.4, blur=22))


class DriftScene(Stage):
    light = "soft"

    def setup(self):
        self.duo = Puppet("woman", arm_red=1.0, seed=1)
        self.m_far = Mountains(seed=11, base=700, height=300, freq=0.0018)
        self.m_mid = Mountains(seed=12, base=860, height=320, freq=0.0024)
        self.m_near = Mountains(seed=13, base=1040, height=300, freq=0.0032)

    def paint(self, fr, t, lt, u):
        c = fr.canvas
        span = self.end - self.start
        # sky wash
        c.drawRect(skia.Rect(0, 0, W, H), gfx.paint((255, 255, 255), 1.0,
                   shader=gfx.linear_grad(0, 0, 0, H, [(226, 222, 214, 255), (255, 255, 255, 255)])))
        clouds(c, t, seed=3, y=180, alpha=0.9, color=(196, 188, 176), speed=30)
        sx = -260 * lt
        self.m_far.draw(c, dx=sx * 0.25 % 400 - 200, tone=(140, 132, 126), alpha=0.45, blur=6, mist=0.85, cun=False)
        draw_mist(c, 720, 200, t, alpha=0.6)
        self.m_mid.draw(c, dx=(sx * 0.55) % 600 - 300, tone=(80, 72, 70), alpha=0.65, blur=3, mist=0.75)
        draw_mist(c, 900, 220, t + 3, alpha=0.7)
        self.m_near.draw(c, dx=(sx * 1.0) % 800 - 400, tone=(30, 26, 26), alpha=0.9, blur=1.2, mist=0.5)
        # A-Duo drifting: bob and a slow roll
        x = 820 + 120 * E.in_out_sine(u)
        y = 690 + 30 * math.sin(lt * 2.2) - 40 * u
        pose = {"lean": -12 + 6 * math.sin(lt * 1.3), "ua_f": 70 + 8 * math.sin(lt * 2), "fa_f": 20, "hand_f": "flat",
                "ua_b": -40, "fa_b": 20, "hand_b": "flat", "skirt": 10 + 4 * math.sin(lt * 3), "hair": -1.6,
                "sash": -1.8, "head": 10, "torso": -6, "foot_f": (24, -10), "foot_b": (-14, 6), "bud_open": 0.16}
        self.duo.draw(c, x, y, 0.85, pose=pose, t=t, flip=False)

    def after_light(self, fr, t, lt, u):
        c = fr.canvas
        PT.draw_petals(c, t, n=50, seed=21, wind=420, fall=(-30, 40), size=(5, 12), alpha=0.85)
        return {"glow": {"thr": 0.85, "strength": 0.3, "red": 0.4}}


def fork_limb(points, w0, w1, seed=0):
    path = gfx.smooth_path(points)
    dense = TH._resample(points, 8)
    dense = TH._resample([(x, y) for x, y in _spline(points, 90)], 90)
    n = len(dense)
    u = np.linspace(0, 1, n)
    widths = w0 + (w1 - w0) * u ** 0.8
    widths = widths * (1 + 0.12 * np.array([noise1(i * 0.21, seed) for i in range(n)]))
    return dense, widths


def _spline(points, n):
    out = []
    P = points
    for i in range(len(P) - 1):
        p0 = P[max(i - 1, 0)]
        p1, p2 = P[i], P[i + 1]
        p3 = P[min(i + 2, len(P) - 1)]
        for k in range(n // (len(P) - 1)):
            t = k / (n // (len(P) - 1))
            t2, t3 = t * t, t * t * t
            x = 0.5 * ((2 * p1[0]) + (-p0[0] + p2[0]) * t + (2 * p0[0] - 5 * p1[0] + 4 * p2[0] - p3[0]) * t2 + (-p0[0] + 3 * p1[0] - 3 * p2[0] + p3[0]) * t3)
            y = 0.5 * ((2 * p1[1]) + (-p0[1] + p2[1]) * t + (2 * p0[1] - 5 * p1[1] + 4 * p2[1] - p3[1]) * t2 + (-p0[1] + 3 * p1[1] - 3 * p2[1] + p3[1]) * t3)
            out.append((x, y))
    out.append(P[-1])
    return out


def draw_bark_limb(c, pts, ws, seed=0, color=S.INK):
    body = gfx.ribbon(pts, ws)
    c.drawPath(body, gfx.paint(color, 0.97))
    rng = RNG(seed)
    P = np.asarray(pts)
    d = np.gradient(P, axis=0)
    ln = np.linalg.norm(d, axis=1, keepdims=True) + 1e-9
    nrm = np.stack([-d[:, 1], d[:, 0]], axis=1) / ln
    cut = skia.Path()
    # long carved bark slits following the limb
    for k in range(int(len(pts) * 0.5)):
        j = int(rng.i(2, len(pts) - 6))
        off = rng.u(-0.32, 0.32)
        L = int(rng.i(3, 7))
        seg = [tuple(P[j + m] + nrm[j + m] * ws[j + m] * (off + 0.04 * noise1(m + k, seed))) for m in range(L)]
        wid = [0.4] + [max(1.0, ws[j] * 0.035)] * (L - 2) + [0.4]
        cut.addPath(gfx.ribbon(seg, wid))
    # knots
    for k in range(3):
        j = int(rng.i(8, len(pts) - 8))
        x, y = P[j] + nrm[j] * ws[j] * rng.u(-0.2, 0.2)
        r = ws[j] * 0.16
        cut.addPath(gfx.op(gfx.ellipse(x, y, r * 1.4, r), gfx.ellipse(x, y, r * 0.8, r * 0.45), "diff"))
    c.drawPath(cut, gfx.paint((246, 226, 192), 0.62, blend=gfx.SCREEN))


class ForkScene(Stage):
    light = "warm"

    def setup(self):
        self.duo = Puppet("woman", arm_red=1.0, seed=1)
        trunk = [(990, 1420), (960, 1180), (930, 930), (952, 760), (960, 700)]
        left = [(960, 700), (850, 650), (700, 500), (560, 420), (400, 300), (210, 260), (-40, 200)]
        right = [(960, 700), (1090, 640), (1250, 560), (1420, 430), (1600, 380), (1780, 300), (2000, 250)]
        self.limbs = [fork_limb(trunk, 170, 112, 1), fork_limb(left, 104, 16, 2), fork_limb(right, 100, 12, 3)]
        self.twigs = [BranchTree(seed=60 + k, root=r, angle=a, length=L, width=w, depth=2, spread=0.6).normalize_time()
                      for k, (r, a, L, w) in enumerate((((700, 500), -1.9, 200, 16), ((560, 420), -1.2, 180, 14),
                                                      ((1250, 560), -1.4, 200, 15), ((1600, 380), -0.9, 160, 12),
                                                      ((930, 1000), -2.6, 160, 18), ((960, 1150), -0.4, 150, 16)))]
        self.left_tree = BranchTree(seed=41, root=(420, 330), angle=-2.4, length=360, width=26, depth=3, spread=0.7).normalize_time()
        self.right_tree = BranchTree(seed=43, root=(1520, 420), angle=-0.6, length=380, width=24, depth=3, spread=0.6,
                                     wander=0.3).normalize_time()
        self.mtn = Mountains(seed=17, base=900, height=280, freq=0.002)
        self.t_left = LY.char_time(1, 6) - self.start
        self.t_right = LY.char_time(1, 9) - self.start

    def camera(self, t, lt):
        tl, tr = self.t_left, self.t_right
        x = E.Track([(0.0, 960), (tl - 0.3, 960), (tl + 0.3, 640, "out_cubic"), (tr - 0.3, 640),
                     (tr + 0.3, 1290, "out_cubic"), (4.0, 1290), (4.95, 960, "in_out_cubic")])(lt)
        y = E.Track([(0.0, 520), (1.0, 600), (tl + 0.3, 520, "out_cubic"), (tr + 0.3, 520), (4.95, 560)])(lt)
        z = E.Track([(0.0, 1.0), (1.0, 1.25, "out_cubic"), (tl + 0.3, 1.55, "out_cubic"), (tr + 0.3, 1.55),
                     (4.0, 1.55), (4.95, 1.0, "in_out_cubic")])(lt)
        return Cam(x, y, z, t=t)

    def paint(self, fr, t, lt, u):
        c = fr.canvas
        cam = self.camera(t, lt)
        c.save()
        cam.apply(c, depth=0.4)
        self.mtn.draw(c, tone=(150, 138, 128), alpha=0.35, blur=5, mist=0.9, cun=False)
        c.restore()
        c.save()
        cam.apply(c)
        # left: blossoms hung like lanterns (what blooming leads to)
        self.left_tree.draw(c, 1.0, style="cut", color=S.INK)
        for i, (x, y, a, d) in enumerate(self.left_tree.tip_list(1.0)):
            sway = 3 * noise1(t * 0.8 + i, 5)
            if i % 2 == 0:
                c.drawLine(x, y, x + sway, y + 40, gfx.paint(S.INK, 1.0, stroke=1.5))
                draw_poppy_side(c, x + sway, y + 40, 0.8, math.pi + 0.1 * noise1(t + i, 2), openness=1.0, seed=i,
                                stem_len=6)
        # right: bare twigs into the fog
        self.right_tree.draw(c, 1.0, style="cut", color=S.INK)
        for tw in self.twigs:
            tw.draw(c, 1.0, style="cut", color=S.INK)
        for k, (pts, ws) in enumerate(self.limbs):
            draw_bark_limb(c, pts, ws, seed=k)
        # A-Duo landing in the fork
        land = E.out_cubic(E.prog(lt, 0.0, 0.8))
        y = 700 - 300 * (1 - land) + 4
        tl, tr = self.t_left, self.t_right
        head = E.Track([(0, 0), (tl - 0.2, 0), (tl + 0.2, 0), (tr - 0.2, 0), (4.9, 0)])(lt)
        face_left = lt > tl - 0.1 and lt < tr - 0.1
        pose = merge(breathe(lt), {"head": -6 if not face_left else -8, "hair": 0.6 * (1 - land) + 0.2,
                                   "bud_open": 0.16, "ua_f": 18 + 30 * E.bump(lt, tl - 0.1, tl + 0.2, tr - 0.4, tr),
                                   "fa_f": 26, "hand_f": "flat"})
        self.duo.draw(c, 960, y, 0.62, pose=pose, t=t, flip=face_left)
        c.restore()

    def after_light(self, fr, t, lt, u):
        c = fr.canvas
        draw_mist(c, 980, 260, t, color=(250, 238, 214), alpha=0.5)
        PT.draw_dust(c, t, n=60, alpha=0.3)
        return {"glow": {"thr": 0.86, "strength": 0.3, "red": 0.5}}


class PalmScene(Stage):
    light = "warm"

    def light_params(self, t, lt, u):
        return dict(radius=1.25, power=1.3, edge=0.22, cy=0.38)

    def paint(self, fr, t, lt, u):
        c = fr.canvas
        rng = RNG(5)
        # bokeh blossoms (far from the screen: big and soft)
        for k in range(14):
            x = rng.u(0, W)
            y = rng.u(0, H * 0.8)
            r = rng.u(40, 120)
            col = S.ROUGE if k % 3 else (90, 70, 60)
            c.drawCircle(x + 20 * math.sin(t * 0.3 + k), y, r, gfx.paint(col, 0.25, blur=r * 0.5, blend=gfx.MULTIPLY))
        z = 1.0 + 0.12 * E.in_out_sine(u)
        rise = E.out_cubic(E.prog(lt, 0.0, 0.9))
        op = E.in_out_cubic(E.prog(lt, 0.5, 1.9))
        c.save()
        c.translate(W / 2, H / 2)
        c.scale(z, z)
        c.translate(-W / 2, -H / 2)
        hx, hy = 940, 1220 + 300 * (1 - rise)
        draw_big_hand(c, hx, hy, 2.15, rot=-0.06 + 0.02 * math.sin(lt), openness=0.15 + 0.85 * op, spread=0.7,
                      redness=1.0, t=t)
        # the cochineal crawls across the palm once it is open
        if op > 0.6:
            k = E.prog(lt, 1.6, 3.6)
            px = hx - 60 + 120 * k + 10 * math.sin(lt * 2)
            py = hy - 330 - 60 * math.sin(k * math.pi)
            ang = -0.3 + 0.6 * k + 0.3 * math.cos(lt * 2)
            draw_cochineal(c, px, py, 3.4, ang, t=t, walk=lt * 2.2, alpha=E.prog(op, 0.6, 0.8))
        c.restore()

    def after_light(self, fr, t, lt, u):
        PT.draw_dust(fr.canvas, t, n=90, alpha=0.45)
        return {"glow": {"thr": 0.84, "strength": 0.35, "red": 0.6}, "grade": dict(contrast=1.05)}


class ReleaseScene(Stage):
    light = "warm"

    def setup(self):
        self.duo = Puppet("woman", arm_red=1.0, seed=1)
        self.t_morph = 1.2   # local: insect curls & becomes the bud
        self.t_fly = 2.4

    def light_params(self, t, lt, u):
        cold = E.smooth(E.prog(lt, 3.6, 4.45))
        if cold > 0:
            p = (1.0 - 0.2 * cold, 1.0 - 0.12 * cold, 1.0 - 0.0 * cold)
            pc = (0.97 * p[0], 0.93 * p[1], 0.85 + 0.1 * cold)
            return dict(paper=pc, warm=1.0 - 0.8 * cold)
        return {}

    def paint(self, fr, t, lt, u):
        c = fr.canvas
        tm, tf = self.t_morph, self.t_fly
        # macro phase: the curled insect becomes the bud, then pull back to reveal her
        pull = E.in_out_cubic(E.prog(lt, tm + 0.1, tm + 1.0))
        z = 3.6 + (1.0 - 3.6) * pull
        # world positions (medium shot)
        dx, dy = 1180, 900
        pose = merge(breathe(lt), {"ua_f": 70, "fa_f": 40, "hand_f": "open", "head": -8 - 14 * E.smooth(E.prog(lt, tf, tf + 1.0)),
                                   "bud_open": 0.16})
        bud_w = self.duo.joint(pose, "bud")
        hand_w = self.duo.joint(pose, "hand_f")
        sc = 1.0
        bud = (dx - bud_w[0] * sc, dy + bud_w[1] * sc)
        hand = (dx - hand_w[0] * sc - 6, dy + hand_w[1] * sc - 14)
        focus = (bud[0] + (W / 2 - bud[0]) * pull, bud[1] + 20 + (H / 2 + 60 - bud[1] - 20) * pull)
        cam = Cam(focus[0], focus[1], z, t=t)
        c.save()
        cam.apply(c)
        ground(c, 900, seed=2, t=t)
        if lt < tm:
            # extreme close-up: the insect curls up in the place where the bud will appear
            k = E.prog(lt, 0.0, tm)
            draw_cochineal(c, bud[0], bud[1] + 10, 1.5 * (1 - 0.35 * k), -math.pi / 2 + 0.2 * math.sin(lt * 3), t=t,
                           walk=lt * 2 * (1 - k), alpha=1.0)
            if k > 0.6:
                a = E.smooth((k - 0.6) / 0.4)
                c.drawPath(gfx.ellipse(bud[0], bud[1] + 10, 22 * a, 30 * a), gfx.paint(S.LEATHER_RED, 0.6 * a, blend=gfx.MULTIPLY))
        else:
            self.duo.draw(c, dx, dy, sc, pose=pose, t=t, flip=True)
            # the insect, back in her palm, then flying away
            if lt < tf:
                draw_cochineal(c, hand[0], hand[1], 0.32, -math.pi / 2, t=t, walk=lt, alpha=E.prog(lt, tm + 0.4, tm + 0.8))
            else:
                k = E.prog(lt, tf, tf + 2.0)
                path = gfx.bezier_pts(hand, (hand[0] - 160, hand[1] - 260), (hand[0] - 520, hand[1] - 380), (220, -120), 40)
                pos = gfx.polyline_cut(path, E.in_sine(k))
                trail = gfx.polyline_cut(path, max(0.0, E.in_sine(k)))
                TH.draw_thread(c, trail, width=2.2, glow=1.4, alpha=0.9, smooth=True)
                px, py = pos[-1]
                ang = math.atan2(pos[-1][1] - pos[-2][1], pos[-1][0] - pos[-2][0]) if len(pos) > 1 else -math.pi / 2
                wings = E.out_cubic(E.prog(lt, tf, tf + 0.3))
                draw_cochineal(c, px, py, 0.34 + 0.2 * k, ang, t=t, wings=wings, flap=lt * 9, alpha=1.0)
        c.restore()

    def after_light(self, fr, t, lt, u):
        c = fr.canvas
        cold = E.smooth(E.prog(lt, 3.6, 4.45))
        if cold > 0:
            PT.draw_snow(c, t, n=160, seed=3, alpha=0.8 * cold, count=cold, wind=20)
        PT.draw_dust(c, t, n=50, alpha=0.3 * (1 - cold))
        flash = E.bump(lt, self.t_morph - 0.05, self.t_morph, self.t_morph + 0.05, self.t_morph + 0.4)
        return {"glow": {"thr": 0.84, "strength": 0.35 + 0.4 * flash, "red": 0.6}, "flash": 0.3 * flash,
                "grade": dict(sat=1.0 - 0.45 * cold, gain=(1 - 0.1 * cold, 1 - 0.04 * cold, 1 + 0.06 * cold))}


def entries():
    return [
        Entry(DriftScene(T4, T5), trans=("fade", 0.4)),
        Entry(ForkScene(T5, T6), trans=("ink", 0.6), params={"center": (0.5, 0.2)}),
        Entry(PalmScene(T6, T7), trans=("fade", 0.35)),
        Entry(ReleaseScene(T7, T8), trans=("white", 0.3)),
    ]
