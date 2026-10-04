"""Procedural branches in two looks: 'ink' (xieyi brushwork) and 'cut' (shadow-puppet silhouette)."""
import math

import numpy as np
import skia

from ..core import gfx
from ..core import easing as E
from ..core import textures as TX
from ..core.noise import noise1, RNG
from . import style as S


class Limb:
    __slots__ = ("pts", "widths", "t0", "dur", "depth", "parent_u")

    def __init__(self, pts, widths, t0, dur, depth):
        self.pts = pts
        self.widths = widths
        self.t0 = t0
        self.dur = dur
        self.depth = depth


class BranchTree:
    """A recursively generated branch.

    root: (x, y); angle: radians (0 = +x, -pi/2 = up); length/width in px.
    growth timing: limb i is drawn in [t0, t0+dur] of the growth parameter (0..1).
    """

    def __init__(self, seed=0, root=(0, 0), angle=-math.pi / 2, length=600, width=34, depth=4,
                 spread=0.55, child_prob=0.75, children=(2, 4), wander=0.22, gravity=0.0,
                 length_decay=0.62, width_decay=0.55, droop=0.0, twig_tips=True, min_width=1.2):
        self.rng = RNG(seed)
        self.seed = seed
        self.limbs = []
        self.tips = []   # (x, y, angle, depth, t_birth)
        self.nodes = []  # moss-dot positions (x, y, r, t)
        self.spread = spread
        self.child_prob = child_prob
        self.children = children
        self.wander = wander
        self.gravity = gravity
        self.length_decay = length_decay
        self.width_decay = width_decay
        self.droop = droop
        self.min_width = min_width
        self._grow(root, angle, length, width, depth, 0.0, 0.42)
        self.twig_tips = twig_tips

    def _grow(self, p, ang, length, width, depth, t0, dur):
        r = self.rng
        n = max(4, int(length / 18))
        pts = [p]
        widths = [width]
        a = ang
        x, y = p
        step = length / n
        for i in range(1, n + 1):
            a += r.n(0, self.wander) * 0.5 + noise1(i * 0.37, self.seed + depth * 13) * self.wander * 0.4
            # gravity/droop pulls toward +y
            a += self.droop * math.cos(a) * 0.03 * (i / n)
            x += math.cos(a) * step
            y += math.sin(a) * step
            pts.append((x, y))
            u = i / n
            widths.append(max(self.min_width, width * (1 - 0.72 * u) ** 1.05))
        limb = Limb(pts, widths, t0, dur, depth)
        self.limbs.append(limb)
        # moss dots
        for k in range(int(r.i(0, 3))):
            j = int(r.i(1, len(pts)))
            self.nodes.append((pts[j][0] + r.n(0, widths[j] * 0.4), pts[j][1] + r.n(0, widths[j] * 0.4),
                               max(1.5, widths[j] * r.u(0.18, 0.4)), t0 + dur * j / len(pts)))
        if depth <= 0 or length < 30:
            self.tips.append((x, y, a, depth, t0 + dur))
            return
        nc = int(r.i(self.children[0], self.children[1] + 1))
        for c in range(nc):
            if r.u() > self.child_prob and c > 0:
                continue
            u = r.u(0.35, 0.95) if c < nc - 1 else 1.0
            j = min(len(pts) - 1, max(1, int(u * (len(pts) - 1))))
            side = 1 if (c % 2 == 0) else -1
            if r.u() < 0.3:
                side = -side
            ca = a if u >= 1.0 else ang + side * r.u(0.35, 1.0) * self.spread * 1.6
            ca += r.n(0, 0.12)
            cl = length * self.length_decay * r.u(0.7, 1.1) * (1.0 if u >= 1 else 0.85)
            cw = widths[j] * (0.92 if u >= 1.0 else self.width_decay * r.u(0.8, 1.1) / max(widths[j] / width, 0.3))
            cw = min(cw, widths[j] * 0.95)
            ct0 = t0 + dur * (j / (len(pts) - 1))
            self._grow(pts[j], ca, cl, cw, depth - 1, ct0, dur * 0.8)
        # small twigs
        for k in range(int(r.i(0, 3))):
            j = int(r.i(2, len(pts)))
            ta = a + r.choice([-1, 1]) * r.u(0.6, 1.2)
            tl = r.u(14, 40)
            tx = pts[j][0] + math.cos(ta) * tl
            ty = pts[j][1] + math.sin(ta) * tl
            tw = max(1.2, widths[j] * 0.35)
            self.limbs.append(Limb([pts[j], ((pts[j][0] + tx) / 2 + r.n(0, 3), (pts[j][1] + ty) / 2 + r.n(0, 3)), (tx, ty)],
                                   [tw, tw * 0.7, self.min_width], t0 + dur * j / len(pts), dur * 0.3, -1))
            self.tips.append((tx, ty, ta, -1, t0 + dur * j / len(pts) + dur * 0.3))

    def normalize_time(self):
        """Rescale birth times so the whole tree finishes at growth=1."""
        end = max(l.t0 + l.dur for l in self.limbs)
        for l in self.limbs:
            l.t0 /= end
            l.dur /= end
        self.tips = [(x, y, a, d, tb / end) for x, y, a, d, tb in self.tips]
        self.nodes = [(x, y, r, tb / end) for x, y, r, tb in self.nodes]
        return self

    # ------------------------------------------------------------------ draw
    def draw(self, canvas, growth=1.0, style="ink", color=S.INK, alpha=1.0, dry=0.55, moss=True,
             blur=0.0, tex_scale=1.0, width_mul=1.0):
        for limb in self.limbs:
            g = E.clamp((growth - limb.t0) / max(1e-6, limb.dur))
            if g <= 0:
                continue
            pts = limb.pts
            ws = [w * width_mul for w in limb.widths]
            if g < 1:
                m = max(2, int(math.ceil(g * (len(pts) - 1))) + 1)
                pts = list(pts[:m])
                ws = list(ws[:m])
                # shrink last point toward growth fraction
                f = g * (len(limb.pts) - 1) - (m - 2)
                f = E.clamp(f)
                a, b = limb.pts[m - 2], limb.pts[m - 1]
                pts[-1] = (a[0] + (b[0] - a[0]) * f, a[1] + (b[1] - a[1]) * f)
                ws[-1] = max(self.min_width, ws[-1] * 0.6)
            if style == "cut":
                self._draw_cut(canvas, pts, ws, color, alpha)
            else:
                self._draw_ink(canvas, pts, ws, color, alpha, dry, blur, tex_scale, limb.depth)
        if moss and style == "ink":
            for x, y, r, tb in self.nodes:
                if growth >= tb:
                    canvas.drawCircle(x, y, r, gfx.paint(color, alpha * 0.92, blur=r * 0.25))

    def _draw_cut(self, canvas, pts, ws, color, alpha):
        if len(pts) < 2:
            return
        canvas.drawPath(gfx.ribbon(pts, ws), gfx.paint(color, alpha))

    def _draw_ink(self, canvas, pts, ws, color, alpha, dry, blur, tex_scale, depth):
        if len(pts) < 2:
            return
        body = gfx.ribbon(pts, ws)
        # wet halo
        canvas.drawPath(body, gfx.paint(color, alpha * 0.2, blur=max(1.5, ws[0] * 0.16) + blur))
        if ws[0] < 7 or dry <= 0:
            # thin limbs: textured solid stroke
            sh = TX.ink_shader(scale=tex_scale * 0.7, seed=11, lo=0.05, hi=0.35)
            cf = skia.ColorFilters.Blend(gfx.C(*color, 255), skia.BlendMode.kSrcIn)
            canvas.drawPath(body, gfx.paint(color, alpha * 0.95, blur=0.5 + blur, shader=sh, color_filter=cf))
            canvas.drawPath(gfx.ribbon(pts, [w * 0.5 for w in ws]), gfx.paint(color, alpha * 0.9, blur=0.3 + blur))
            return
        # thick limbs: bristles — parallel strokes broken by long/short gaps (飞白)
        P = np.asarray(pts, np.float64)
        d = np.gradient(P, axis=0)
        ln = np.linalg.norm(d, axis=1, keepdims=True) + 1e-9
        nrm = np.stack([-d[:, 1], d[:, 0]], axis=1) / ln
        Wd = np.asarray(ws)[:, None]
        canvas.drawPath(gfx.ribbon(pts, [w * 0.62 for w in ws]), gfx.paint(color, alpha * 0.92, blur=0.5 + blur))
        nb = 9
        rng = np.random.default_rng(int(abs(P[0, 0] * 7 + P[0, 1] * 13)) % 100000)
        for k in range(nb):
            off = (k / (nb - 1) - 0.5) * 0.92
            Q = P + nrm * Wd * off
            bw = [max(0.8, w / nb * 1.9) for w in ws]
            on1, off1 = rng.uniform(60, 220), rng.uniform(4, 16) * dry * (1.6 if abs(off) > 0.3 else 0.6)
            on2, off2 = rng.uniform(30, 120), rng.uniform(3, 10) * dry
            pe = skia.DashPathEffect.Make([on1, max(0.1, off1), on2, max(0.1, off2)], rng.uniform(0, 80))
            a = alpha * (0.85 if abs(off) < 0.35 else 0.7)
            canvas.drawPath(gfx.smooth_path(list(map(tuple, Q))),
                            gfx.paint(color, a, stroke=sum(bw) / len(bw), blur=0.35 + blur, path_effect=pe, cap="butt"))

    def tip_list(self, growth=1.0, min_depth=-1):
        return [(x, y, a, d) for x, y, a, d, tb in self.tips if growth >= tb and d >= min_depth]


# ----------------------------------------------------------------- blossoms in brushwork

def draw_blossom_ink(canvas, x, y, r, openness=1.0, rot=0.0, seed=0, color=(196, 26, 44), alpha=1.0,
                     center=S.INK):
    """Xieyi-style red blossom: soft wet petals with darker pooled edges and ink stamens."""
    o = E.clamp(openness)
    rng = RNG(seed)
    canvas.save()
    canvas.translate(x, y)
    canvas.rotate(math.degrees(rot))
    if o < 0.3:
        # bud: red tear with dark calyx
        q = o / 0.3
        h = r * (0.7 + 0.5 * q)
        bud = gfx.smooth_path([(0, 0), (r * 0.42, -h * 0.4), (0, -h), (-r * 0.42, -h * 0.4)], closed=True)
        canvas.drawPath(bud, gfx.paint(color, alpha * 0.9, blur=r * 0.05))
        canvas.drawPath(bud, gfx.paint(S.ROUGE_DEEP, alpha * 0.6, stroke=r * 0.06, blur=r * 0.05))
        cal = gfx.smooth_path([(0, 2), (r * 0.35, -h * 0.2), (0, -h * 0.12), (-r * 0.35, -h * 0.2)], closed=True)
        canvas.drawPath(cal, gfx.paint(center, alpha * 0.9, blur=r * 0.03))
        canvas.restore()
        return
    q = (o - 0.3) / 0.7
    np_ = 5
    for k in range(np_):
        a = 2 * math.pi * k / np_ + rng.n(0, 0.12)
        pr = r * (0.55 + 0.45 * q) * rng.u(0.85, 1.1)
        cx = math.cos(a) * pr * 0.55
        cy = math.sin(a) * pr * 0.55
        petal = gfx.blob(cx, cy, pr * 0.52, 0.12, seed=seed + k, n=14)
        canvas.drawPath(petal, gfx.paint(color, alpha * 0.55, blur=r * 0.04))
        canvas.drawPath(petal, gfx.paint(S.ROUGE_DEEP, alpha * 0.5, stroke=max(1.0, r * 0.05), blur=r * 0.05))
    # pooled dark centre
    canvas.drawCircle(0, 0, r * 0.22, gfx.paint(S.ROUGE_DEEP, alpha * 0.7, blur=r * 0.08))
    for k in range(9):
        a = 2 * math.pi * k / 9 + rng.n(0, 0.2)
        L = r * rng.u(0.35, 0.55) * q
        canvas.drawLine(0, 0, math.cos(a) * L, math.sin(a) * L, gfx.paint(center, alpha * 0.8, stroke=max(0.8, r * 0.03)))
        canvas.drawCircle(math.cos(a) * L, math.sin(a) * L, max(1.0, r * 0.06), gfx.paint(center, alpha * 0.9))
    canvas.restore()
