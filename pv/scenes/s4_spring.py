"""1:02.85 – 1:19.70  To die in spring.

SC16a tear     阿朵 bursts out through the paper screen (the screen tears open).
SC16b burst    spring explodes: grass, vines and red flowers erupt on the beats — the first green.
SC17  bed      top-down: she lies in the grass, flowers bloom over her like clothing; as the camera
               pulls away, the red drains from her arms.
SC18  roots    a cross-section of the spring mud: roots and seeds push through the dark, wildly.
SC19  silverfish  the mud that fed everything feeds her to the silverfish — they eat the paper image
               itself, hole by hole, until darkness.
"""
import math

import cv2
import numpy as np
import skia

from .. import config
from ..core import gfx, audio
from ..core import textures as TX
from ..core import easing as E
from ..core.camera import Cam
from ..core.noise import noise1, RNG, hash01
from ..elements import style as S
from ..elements.branch import BranchTree
from ..elements.puppet import Puppet, walk, run, breathe, merge, PoseTrack, blend_pose
from ..elements.flower import draw_poppy_side, draw_poppy_front
from ..elements.insects import draw_silverfish
from ..elements import fx, particles as PT
from ..timeline import Entry
from .common import Stage, ground, W, H

T16, T16B, T17, T18, T19, T20 = 62.85, 64.30, 66.85, 70.85, 74.85, 79.70

GREEN = (70, 150, 62)
GREEN_L = (150, 200, 90)
GREEN_D = (30, 90, 40)


class Sprout:
    """A grass blade / vine that grows from a base point."""

    def __init__(self, x, y, ang, L, w, t0, dur, curl=0.0, col=GREEN, seed=0, kind="blade"):
        self.x, self.y, self.ang, self.L, self.w = x, y, ang, L, w
        self.t0, self.dur, self.curl, self.col, self.seed, self.kind = t0, dur, curl, col, seed, kind

    def points(self, g, t=0.0):
        n = 14
        pts = []
        a = self.ang
        x, y = self.x, self.y
        for i in range(n + 1):
            u = i / n
            if u > g:
                break
            pts.append((x, y))
            a += self.curl / n + 0.02 * noise1(t * 0.8 + i * 0.3, self.seed)
            x += math.cos(a) * self.L / n
            y += math.sin(a) * self.L / n
        return pts

    def draw(self, c, t_local, t=0.0, alpha=1.0):
        g = E.out_cubic(E.clamp((t_local - self.t0) / self.dur))
        if g <= 0:
            return None
        pts = self.points(g, t)
        if len(pts) < 2:
            return None
        ws = [self.w * (1 - i / len(pts)) ** 0.8 + 0.6 for i in range(len(pts))]
        c.drawPath(gfx.ribbon(pts, ws), gfx.paint(self.col, 0.95 * alpha, blend=gfx.MULTIPLY))
        c.drawPath(gfx.ribbon(pts, ws), gfx.paint(S.INK, alpha * 0.9, stroke=1.4))
        if self.kind == "vine":
            for k in range(2, len(pts) - 1, 3):
                px, py = pts[k]
                side = 1 if k % 2 else -1
                a = self.ang + side * 1.2
                leaf = gfx.smooth_path([(px, py), (px + math.cos(a - 0.4) * 22, py + math.sin(a - 0.4) * 22),
                                        (px + math.cos(a) * 36, py + math.sin(a) * 36), (px + math.cos(a + 0.4) * 22, py + math.sin(a + 0.4) * 22)], closed=True)
                c.drawPath(leaf, gfx.paint(GREEN_L, 0.92 * alpha, blend=gfx.MULTIPLY))
                c.drawPath(leaf, gfx.paint(S.INK, alpha, stroke=1.2))
        return pts[-1]


class TearScene(Stage):
    """She runs at the screen and tears out through the paper."""
    light = "warm"

    def setup(self):
        self.duo = Puppet("woman", arm_red=0.8, seed=1)
        self.t_tear = 0.95

    def paint(self, fr, t, lt, u):
        c = fr.canvas
        tt = self.t_tear
        k = E.prog(lt, 0.0, tt)
        # she runs toward the camera: grows huge (closer to the lamp the shadow enlarges)
        sc = 0.55 + 2.2 * E.in_cubic(k)
        blur = 0.5 + 10 * E.in_cubic(k)
        x = 760 + 240 * k
        with gfx.Layer(c, blur=blur, alpha=1.0) as lc:
            self.duo.draw(lc, x, 980 + 900 * E.in_cubic(k), sc, pose=merge(run(lt * 1.8), {"bud_open": 0.18}), t=t)
        ground(c, 980, seed=2, t=t)

    def after_light(self, fr, t, lt, u):
        c = fr.canvas
        tt = self.t_tear
        if lt >= tt:
            # torn screen: jagged hole that opens, revealing blinding spring light behind
            o = E.out_expo(E.prog(lt, tt, tt + 0.5))
            rng = RNG(3)
            pts = []
            n = 40
            for i in range(n):
                a = 2 * math.pi * i / n
                r = (120 + 1400 * o) * (1 + 0.35 * rng.u(-1, 1))
                pts.append((W / 2 + math.cos(a) * r, H / 2 + math.sin(a) * r * 0.8))
            hole = gfx.poly(pts)
            c.drawPath(hole, gfx.paint((255, 252, 230), 1.0))
            c.drawPath(hole, gfx.paint((255, 255, 255), 0.6, stroke=18, blur=10))
            PT.draw_burst(c, lt, tt, W / 2, H / 2, n=60, seed=5, speed=(500, 1600), size=(4, 12), color=(240, 226, 200),
                          gravity=500, life=0.8)
        flash = E.bump(lt, tt - 0.03, tt, tt + 0.05, tt + 0.5)
        return {"flash": 0.6 * flash, "flash_color": (255, 252, 236), "glow": {"thr": 0.8, "strength": 0.4}}


class SpringBurstScene(Stage):
    light = "spring"

    def setup(self):
        self.duo = Puppet("woman", arm_red=0.85, seed=1)
        rng = RNG(21)
        b0 = audio.beat_index(self.start)
        self.beats = [audio.beat_time(b0 + k) - self.start for k in range(1, 8)]
        self.sprouts = []
        for k in range(120):
            x = rng.u(-50, W + 50)
            bt = self.beats[k % len(self.beats)] + rng.u(-0.05, 0.1)
            L = rng.u(120, 420)
            self.sprouts.append(Sprout(x, 1000 + rng.u(0, 60), -math.pi / 2 + rng.n(0, 0.35), L, rng.u(8, 18), bt, rng.u(0.25, 0.6),
                                       curl=rng.n(0, 0.8), col=S.lerp3(GREEN_D, GREEN_L, rng.u()), seed=k,
                                       kind="vine" if rng.u() < 0.25 else "blade"))
        self.flowers = []
        for k in range(26):
            x = rng.u(40, W - 40)
            y = rng.u(560, 960)
            bt = self.beats[(k * 3) % len(self.beats)] + 0.1
            self.flowers.append((x, y, bt, rng.u(0.9, 1.6), rng.u(-0.4, 0.4)))

    def light_params(self, t, lt, u):
        return dict(boost=0.1 * audio.beat_pulse(t, 0.18))

    def paint(self, fr, t, lt, u):
        c = fr.canvas
        imp = max([E.pulse(lt, bt, 0.01, 0.12) for bt in self.beats] + [0])
        cam = Cam(W / 2, H / 2 + 40, 1.06 - 0.06 * u + 0.02 * imp, rot=0.01 * math.sin(lt * 2), t=t, shake=0.3 * imp)
        c.save()
        cam.apply(c)
        # sky gradient of spring
        c.drawRect(skia.Rect(-100, -100, W + 100, H + 100), gfx.paint((255, 255, 255), 1.0,
                   shader=gfx.linear_grad(0, 0, 0, H, [(250, 250, 236, 255), (236, 246, 222, 255)])))
        for sp in self.sprouts:
            sp.draw(c, lt, t)
        for (x, y, bt, s, a) in self.flowers:
            k = E.prog(lt, bt, bt + 0.4)
            if k <= 0:
                continue
            c.drawLine(x, 1040, x + 20 * a, y, gfx.paint(GREEN_D, 1.0, stroke=3))
            draw_poppy_side(c, x + 20 * a, y, s * E.out_back(min(1, k * 1.5)), a, openness=min(1.0, 0.3 + k), seed=int(x))
        # A-Duo spinning in the middle (a puppet twirl: flip on beats)
        spin = int(lt / (config.BEAT)) % 2 == 1
        pose = {"ua_f": 120 + 20 * math.sin(lt * 6), "fa_f": 20, "hand_f": "flat", "ua_b": -120 - 20 * math.sin(lt * 6),
                "fa_b": 20, "hand_b": "flat", "skirt": 8 * math.sin(lt * 6), "hair": 1.4 * math.sin(lt * 3), "sash": 1.4,
                "head": -14, "bud_open": 0.2, "bob": 10 * abs(math.sin(lt * 6))}
        self.duo.draw(c, W / 2, 1010, 0.72, pose=pose, t=t, flip=spin)
        ground(c, 1040, color=(24, 50, 26), seed=4, t=t)
        c.restore()

    def after_light(self, fr, t, lt, u):
        c = fr.canvas
        PT.draw_petals(c, t, n=80, seed=31, wind=200, fall=(-120, 60), size=(6, 16), alpha=0.9, color=S.ROUGE, rise=True)
        PT.draw_petals(c, t, n=40, seed=32, wind=150, fall=(-80, 40), size=(8, 14), alpha=0.85, color=(130, 190, 80),
                       color2=(80, 150, 60), rise=True)
        imp = max([E.pulse(lt, bt, 0.01, 0.1) for bt in self.beats] + [0])
        return {"glow": {"thr": 0.8, "strength": 0.4, "red": 0.5}, "grade": dict(sat=1.25, contrast=1.06),
                "flash": 0.12 * imp, "flash_color": (255, 255, 230)}


class FlowerBedScene(Stage):
    light = "spring"

    def setup(self):
        self.duo = Puppet("woman", arm_red=1.0, seed=1)
        rng = RNG(41)
        self.grass = [(rng.u(-200, W + 200), rng.u(-200, H + 200), rng.u(0, 6.28), rng.u(30, 80)) for _ in range(900)]
        self.blooms = [(rng.u(-50, 50), 0.25 + 0.75 * rng.u(0, 1), rng.u(0.7, 1.1), rng.u(0, 6.28)) for _ in range(13)]
        self.wild = [(rng.u(-100, W + 100), rng.u(-100, H + 100), rng.u(30, 70), rng.u(0, 6.28), rng.u(0, 1)) for _ in range(60)]

    def paint(self, fr, t, lt, u):
        c = fr.canvas
        pull = E.in_out_cubic(E.prog(lt, 1.6, 4.0))
        z = 1.55 - 1.0 * pull
        cam = Cam(W / 2, H / 2, z, rot=0.2 * pull, t=t)
        c.save()
        cam.apply(c)
        # green ground seen from above
        c.drawRect(skia.Rect(-2000, -2000, W + 2000, H + 2000), gfx.paint((150, 196, 110), 0.85, blend=gfx.MULTIPLY))
        p = skia.Path()
        for (x, y, a, L) in self.grass:
            p.moveTo(x, y)
            p.lineTo(x + math.cos(a) * L * 0.3, y + math.sin(a) * L * 0.3)
        c.drawPath(p, gfx.paint(GREEN_D, 0.5, stroke=3))
        for (x, y, r, a, ph) in self.wild:
            draw_poppy_front(c, x, y, r, openness=1.0, rot=a + 0.2 * math.sin(t * 0.5 + ph), seed=int(x * 7) % 997, alpha=0.9,
                             veins=False)
        # A-Duo lying on her back (top-down): a puppet laid flat, hands folded
        cx, cy = W / 2, H / 2
        red = 1.0 - 0.95 * E.smooth(E.prog(lt, 1.8, 3.8))
        self.duo.draw(c, cx + 300, cy + 20, 0.9, pose={"lean": 90, "ua_f": 150, "fa_f": 60, "ua_b": 140, "fa_b": 66,
                                                      "hand_f": "flat", "hand_b": "flat", "bud_open": 0.2, "head": -4},
                      t=t, arm_red=red)
        # flowers bloom over her body like a garment
        for k, (dx, v, s, a) in enumerate(self.blooms):
            bt = 0.2 + v * 1.4
            kk = E.prog(lt, bt, bt + 0.6)
            if kk <= 0:
                continue
            x = cx + 300 - 40 - v * 520
            y = cy + 20 + dx * 0.9
            draw_poppy_front(c, x, y, 34 * s * E.out_back(kk), openness=kk, rot=a, seed=k + 200, alpha=0.95)
        c.restore()

    def after_light(self, fr, t, lt, u):
        c = fr.canvas
        PT.draw_petals(c, t, n=50, seed=33, wind=40, fall=(20, 60), size=(6, 14), alpha=0.85)
        return {"glow": {"thr": 0.82, "strength": 0.35, "red": 0.5}, "grade": dict(sat=1.2)}


class RootsScene(Stage):
    light = "spring"

    def setup(self):
        rng = RNG(51)
        b0 = audio.beat_index(self.start)
        self.beats = [audio.beat_time(b0 + k) - self.start for k in range(1, 9)]
        self.roots = []
        for k in range(10):
            x = 120 + k * 190 + rng.u(-40, 40)
            tr = BranchTree(seed=300 + k, root=(x, 420), angle=math.pi / 2 + rng.n(0, 0.2), length=rng.u(500, 800),
                            width=rng.u(14, 26), depth=4, spread=0.75, wander=0.35, children=(2, 3)).normalize_time()
            self.roots.append((tr, self.beats[k % len(self.beats)] - 0.2, rng.u(1.6, 2.6)))
        self.stems = [Sprout(120 + k * 190 + rng.u(-40, 40), 420, -math.pi / 2 + rng.n(0, 0.2), rng.u(220, 380), rng.u(10, 18),
                             self.beats[k % len(self.beats)], 1.2, curl=rng.n(0, 0.6), col=GREEN, seed=k, kind="vine")
                      for k in range(10)]
        self.seeds = [(rng.u(0, W), rng.u(500, 1050), rng.u(6, 12), self.beats[k % len(self.beats)]) for k in range(40)]
        self.worms = [(rng.u(0, W), rng.u(560, 1040), rng.u(0, 6.28)) for _ in range(5)]

    def paint(self, fr, t, lt, u):
        c = fr.canvas
        imp = max([E.pulse(lt, bt, 0.01, 0.12) for bt in self.beats] + [0])
        cam = Cam(W / 2, H / 2 + 60 - 120 * E.in_out_sine(u), 1.05, t=t, shake=0.25 * imp)
        c.save()
        cam.apply(c)
        # earth: dark spring mud below the surface line
        c.drawPath(gfx.poly([(-200, 420), (W + 200, 410), (W + 200, H + 400), (-200, H + 400)]), gfx.paint((58, 40, 30), 0.92))
        rng = RNG(9)
        stones = skia.Path()
        for k in range(70):
            stones.addPath(gfx.blob(rng.u(0, W), rng.u(460, 1300), rng.u(6, 22), 0.25, seed=k))
        c.drawPath(stones, gfx.paint((110, 90, 70), 0.6, blend=gfx.SCREEN))
        for tr, t0, dur in self.roots:
            g = E.out_cubic(E.prog(lt, t0, t0 + dur))
            if g > 0:
                tr.draw(c, g, style="cut", color=(232, 214, 180), alpha=0.85, width_mul=0.9)
        for (x, y, r, bt) in self.seeds:
            k = E.prog(lt, bt, bt + 0.4)
            c.drawPath(gfx.ellipse(x, y, r, r * 0.65), gfx.paint((200, 170, 120), 0.9, blend=gfx.SCREEN))
            if k > 0:
                c.drawPath(gfx.smooth_path([(x, y - r * 0.5), (x + 8 * k, y - 30 * k), (x + 2, y - 60 * k)]),
                           gfx.paint(GREEN_L, 1.0, stroke=3))
        for (x, y, a) in self.worms:
            pts = [(x + math.cos(a) * i * 9 + 6 * math.sin(lt * 4 + i * 0.6), y + math.sin(a) * i * 9 + 6 * math.cos(lt * 4 + i * 0.6))
                   for i in range(10)]
            c.drawPath(gfx.smooth_path(pts), gfx.paint((200, 120, 110), 0.9, stroke=8))
        # above ground: stems shooting up
        for sp in self.stems:
            tip = sp.draw(c, lt, t)
            if tip and lt > sp.t0 + 0.6:
                draw_poppy_side(c, tip[0], tip[1], 1.0, 0.0, openness=min(1, (lt - sp.t0 - 0.6) * 1.5), seed=int(tip[0]))
        c.restore()

    def after_light(self, fr, t, lt, u):
        imp = max([E.pulse(lt, bt, 0.01, 0.1) for bt in self.beats] + [0])
        return {"glow": {"thr": 0.8, "strength": 0.35, "red": 0.5}, "grade": dict(sat=1.15, contrast=1.08),
                "flash": 0.1 * imp, "flash_color": (240, 255, 220)}


class SilverfishScene(Stage):
    light = "spring"

    def setup(self):
        self.bed = FlowerBedScene(self.start - 4.0, self.start)
        self.holes = fx.Holes(seed=7, n=16, t_start=0.3, t_end=3.6, speed=(160, 300))

    def paint(self, fr, t, lt, u):
        c = fr.canvas
        # the spring image (same flower bed, now wide and pale-armed) ...
        self.bed.paint(fr, t, lt + 4.0, 1.0)

    def after_light(self, fr, t, lt, u):
        c = fr.canvas
        # ... eaten away: rasterise the eaten area, roughen its edge with noise, and cut it out of the paper
        ms = gfx.pooled("holes", W // 2, H // 2)
        ms.clear()
        ms.canvas.save()
        ms.canvas.scale(0.5, 0.5)
        ms.canvas.drawPath(self.holes.mask_path(lt), gfx.paint((255, 255, 255), 1.0))
        ms.canvas.restore()
        m = ms.arr[..., 3].astype(np.float32) / 255.0
        m = cv2.GaussianBlur(m, (0, 0), 2.5)
        m = cv2.resize(m, (W, H), interpolation=cv2.INTER_LINEAR)
        nz = 0.55 * TX.noise_field(40, seed=17, octaves=4) + 0.45 * TX.noise_field(14, seed=23, octaves=3)
        hole = np.clip((m + (nz - 0.5) * 0.75 - 0.45) * 14, 0, 1)
        dark = E.in_cubic(E.prog(lt, 3.5, 4.85))
        rim = np.clip((m + (nz - 0.5) * 0.75 - 0.36) * 9, 0, 1) - hole
        rim = np.clip(rim, 0, 1)
        a = fr.arr
        rgb = a[..., :3].astype(np.float32)
        paper = np.array([244, 232, 206], np.float32)
        rgb = rgb * (1 - rim[..., None] * 0.85) + paper * rim[..., None] * 0.85
        void = np.array([10, 8, 10], np.float32)
        hole_d = np.maximum(hole, dark)
        rgb = rgb * (1 - hole_d[..., None]) + void * hole_d[..., None]
        a[..., :3] = np.clip(rgb, 0, 255).astype(np.uint8)
        for path, r, head, ang, sd in self.holes.state(lt):
            hx, hy = head
            draw_silverfish(c, hx, hy, 2.1, ang, t=t, seed=sd, alpha=1.0 - dark)
        return {"glow": {"thr": 0.82, "strength": 0.3, "red": 0.4}, "grade": dict(sat=1.1 - 0.5 * E.prog(lt, 0, 4.8))}


def entries():
    return [
        Entry(TearScene(T16, T16B), trans=("cut", 0.0)),
        Entry(SpringBurstScene(T16B, T17), trans=("white", 0.25)),
        Entry(FlowerBedScene(T17, T18), trans=("fade", 0.4)),
        Entry(RootsScene(T18, T19), trans=("wipe_d", 0.45)),
        Entry(SilverfishScene(T19, T20), trans=("fade", 0.5)),
    ]
