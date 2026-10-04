"""The PV timeline: scenes, transitions and lyric layout."""
import math

import numpy as np

from . import config
from .core import post, audio, gfx
from .core import lyrics as LY
from .core.frame import blend, FrameCtx, apply_post
from .core import easing as E

W, H = config.W, config.H

_TIMELINE = None


class Entry:
    def __init__(self, scene, trans=("cut", 0.0), params=None):
        self.scene = scene
        self.trans = trans            # transition INTO this scene: (kind, duration)
        self.params = params or {}


def build():
    from .scenes import s0_intro, s1_refrain, s2_winter, s3_house, s4_spring, s5_refrain2, s6_hide, \
        s7_work, s8_refrain3, s9_bloom
    entries = []
    for mod in (s0_intro, s1_refrain, s2_winter, s3_house, s4_spring, s5_refrain2, s6_hide, s7_work,
                s8_refrain3, s9_bloom):
        entries.extend(mod.entries())
    entries.sort(key=lambda e: e.scene.start)
    return entries


def timeline():
    global _TIMELINE
    if _TIMELINE is None:
        _TIMELINE = build()
    return _TIMELINE


def lyric_styles():
    from .scenes.lyric_layout import STYLES
    return STYLES


def render_frame(t):
    tl = timeline()
    # find current entry
    cur = None
    idx = -1
    for i, e in enumerate(tl):
        if e.scene.start <= t < e.scene.end:
            cur, idx = e, i
            break
    if cur is None:
        cur, idx = (tl[-1], len(tl) - 1) if t >= tl[-1].scene.start else (tl[0], 0)
    img = cur.scene.render(t)
    kind, dur = cur.trans
    if kind != "cut" and dur > 0 and idx > 0 and t < cur.scene.start + dur:
        prev = tl[idx - 1]
        k = (t - cur.scene.start) / dur
        a = prev.scene.render(t)
        img = blend(a, img, kind, k, seed=idx, params=cur.params)
    # lyrics overlay
    fr = FrameCtx(t)
    fr.put_rgb(img)
    styles = lyric_styles()
    for i, st in styles.items():
        if st is None:
            continue
        LY.draw_line(fr.canvas, i, t, st, seed=i)
    img = fr.rgb_copy()
    # global finishing
    img = post.grain(img, t, amount=6.0)
    return img
