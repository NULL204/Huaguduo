"""LRC parsing and brush-calligraphy lyric typography.

The lyric text is read at render time from the user's own LRC file (config.LRC_PATH);
nothing from the lyrics is stored in this repository.
"""
import json
import math
import os
import re

import skia

from .. import config
from . import easing as E
from .noise import noise1, hash01
from .text import font, glyph_path

_LINES = None
_TIMING = None


def parse_lrc(path):
    lines = []
    with open(path, encoding="utf-8") as f:
        for raw in f:
            for m in re.finditer(r"\[(\d+):(\d+(?:\.\d+)?)\]", raw):
                pass
            m = re.match(r"((?:\[\d+:\d+(?:\.\d+)?\])+)(.*)", raw.strip())
            if not m:
                continue
            text = m.group(2).strip()
            if not text:
                continue
            for tm in re.finditer(r"\[(\d+):(\d+(?:\.\d+)?)\]", m.group(1)):
                t = int(tm.group(1)) * 60 + float(tm.group(2))
                lines.append({"t": t, "text": text})
    lines.sort(key=lambda d: d["t"])
    return lines


def lines():
    global _LINES
    if _LINES is None:
        _LINES = parse_lrc(config.LRC_PATH)
    return _LINES


def timing():
    global _TIMING
    if _TIMING is None:
        p = os.path.join(config.DATA, "char_timing.json")
        if os.path.exists(p):
            with open(p) as f:
                _TIMING = {d["line"]: d for d in json.load(f)}
        else:
            _TIMING = {}
    return _TIMING


def line_chars(i):
    """Characters of line i as a list of (char, sung_time).  Spaces become gaps (None)."""
    ln = lines()[i]
    tm = timing().get(i)
    chars = list(ln["text"])
    out = []
    k = 0
    for c in chars:
        if c.isspace():
            out.append((None, None))
            continue
        if tm and k < len(tm["chars"]):
            t = tm["chars"][k]
        else:
            t = ln["t"] + 0.28 * k
        out.append((c, t))
        k += 1
    return out


def line_time(i):
    return lines()[i]["t"]


def line_end(i):
    ls = lines()
    if i + 1 < len(ls):
        return ls[i + 1]["t"]
    return config.MUSIC_END


# ---------------------------------------------------------------------------
# Typography
# ---------------------------------------------------------------------------

RED_CHARS = set("红胭脂春死花")  # characters that get a rouge accent


class LyricStyle:
    def __init__(self, x, y, size=64, vertical=True, color=(24, 18, 16), accent=(178, 20, 38),
                 face="brush", glow=None, align="start", spacing=1.06, halo=None,
                 hold=0.35, fade_out=0.55, accent_chars=True, scale_in=1.25, drift=(0, -10),
                 jitter=0.0, shadow=None):
        self.x, self.y = x, y
        self.size = size
        self.vertical = vertical
        self.color = color
        self.accent = accent
        self.face = face
        self.glow = glow          # (r,g,b) glow colour for dark scenes
        self.align = align        # "start" | "center" | "end"
        self.spacing = spacing
        self.halo = halo          # paper-coloured halo behind glyphs for legibility
        self.hold = hold          # seconds to keep after next line starts
        self.fade_out = fade_out
        self.accent_chars = accent_chars
        self.scale_in = scale_in
        self.drift = drift
        self.jitter = jitter
        self.shadow = shadow


def _char_layout(chars, style):
    n = len(chars)
    step = style.size * style.spacing
    total = step * n
    if style.align == "center":
        start = -total / 2
    elif style.align == "end":
        start = -total
    else:
        start = 0
    pos = []
    for k in range(n):
        off = start + k * step
        if style.vertical:
            pos.append((style.x - style.size / 2, style.y + off + style.size * 0.88))
        else:
            pos.append((style.x + off, style.y))
    return pos


def draw_line(canvas, i, t, style, alpha=1.0, end_override=None, seed=0):
    """Draw lyric line i at global time t using `style`."""
    chars = line_chars(i)
    t0 = line_time(i)
    t_end = end_override if end_override is not None else line_end(i) + style.hold
    if t < t0 - 0.4 or t > t_end + style.fade_out:
        return
    f = font(style.face, style.size)
    pos = _char_layout(chars, style)
    out_u = E.prog(t, t_end, t_end + style.fade_out)
    for k, ((c, tc), (px, py)) in enumerate(zip(chars, pos)):
        if c is None:
            continue
        # entry
        a_in = E.prog(t, tc - 0.12, tc + 0.30)
        if a_in <= 0:
            continue
        stag = k * 0.04
        a_out = E.prog(t, t_end + stag, t_end + stag + style.fade_out * 0.8)
        a = E.smooth(a_in) * (1 - E.smooth(a_out)) * alpha
        if a <= 0.003:
            continue
        sc = 1 + (style.scale_in - 1) * (1 - E.out_cubic(a_in))
        blur = 6.0 * (1 - E.out_cubic(a_in)) + 7.0 * E.in_quad(a_out)
        dx = style.drift[0] * E.in_quad(a_out) + style.jitter * noise1(t * 3 + k * 7.1, seed)
        dy = style.drift[1] * E.in_quad(a_out) + style.jitter * noise1(t * 3 + k * 3.3, seed + 5)
        gp = glyph_path(style.face, c)
        if gp is None:
            continue
        accent = style.accent_chars and c in RED_CHARS
        col = style.accent if accent else style.color
        canvas.save()
        cx = px + style.size / 2
        cy = py - style.size * 0.38
        canvas.translate(cx + dx, cy + dy)
        canvas.scale(sc * style.size / 100.0, sc * style.size / 100.0)
        canvas.translate(-50, 38)
        if style.halo is not None:
            hp = skia.Paint(AntiAlias=True, Color=skia.Color(*style.halo, int(150 * a)),
                            MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 9))
            canvas.drawPath(gp, hp)
        if style.glow is not None:
            gpaint = skia.Paint(AntiAlias=True, Color=skia.Color(*style.glow, int(170 * a)),
                                MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 7 + blur))
            canvas.drawPath(gp, gpaint)
        if style.shadow is not None:
            sp = skia.Paint(AntiAlias=True, Color=skia.Color(*style.shadow, int(120 * a)),
                            MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 4))
            canvas.save()
            canvas.translate(3, 4)
            canvas.drawPath(gp, sp)
            canvas.restore()
        # ink bleed halo on arrival
        if a_in < 1:
            bleed = skia.Paint(AntiAlias=True, Color=skia.Color(*col, int(90 * (1 - a_in) * a)),
                               MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 4 + 10 * (1 - a_in)))
            canvas.drawPath(gp, bleed)
        p = skia.Paint(AntiAlias=True, Color=skia.Color(*col, int(255 * a)))
        if blur > 0.4:
            p.setMaskFilter(skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, blur))
        canvas.drawPath(gp, p)
        canvas.restore()


def line_progress(i, t):
    """0..1 progress of singing through line i."""
    ch = [tc for c, tc in line_chars(i) if c is not None]
    if not ch:
        return 0.0
    if t <= ch[0]:
        return 0.0
    if t >= ch[-1]:
        return 1.0
    for k in range(1, len(ch)):
        if t < ch[k]:
            return (k - 1 + (t - ch[k - 1]) / (ch[k] - ch[k - 1])) / (len(ch) - 1)
    return 1.0


def char_count(i):
    return sum(1 for c, _ in line_chars(i) if c is not None)


def char_time(i, k):
    ch = [tc for c, tc in line_chars(i) if c is not None]
    k = max(0, min(k, len(ch) - 1))
    return ch[k]
