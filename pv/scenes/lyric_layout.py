"""Per-line lyric placement, keyed by LRC line index.

Only positions and styles live here — the lyric text itself is read at render time from the user's
own LRC file (see pv/core/lyrics.py), so no lyrics are stored in this repository.
"""
from .. import config
from ..core.lyrics import LyricStyle

W, H = config.W, config.H
INK = (26, 20, 18)
ROUGE = (176, 18, 36)
PAPER = (250, 240, 222)
LIGHT = (252, 242, 224)
LIGHT_ACC = (255, 110, 110)
GLOW = (255, 196, 150)
SHADOW = (12, 8, 8)


def ink(x, y, size=62, **kw):
    kw.setdefault("halo", PAPER)
    return LyricStyle(x, y, size=size, color=INK, accent=ROUGE, **kw)


def light(x, y, size=62, **kw):
    kw.setdefault("glow", GLOW)
    kw.setdefault("shadow", SHADOW)
    return LyricStyle(x, y, size=size, color=LIGHT, accent=LIGHT_ACC, **kw)


def ink_h(y, size=60, **kw):
    kw.setdefault("halo", PAPER)
    return LyricStyle(W / 2, y, size=size, vertical=False, align="center", color=INK, accent=ROUGE, **kw)


def light_h(y, size=60, **kw):
    kw.setdefault("glow", GLOW)
    kw.setdefault("shadow", SHADOW)
    return LyricStyle(W / 2, y, size=size, vertical=False, align="center", color=LIGHT, accent=LIGHT_ACC, **kw)


STYLES = {
    # refrain 1 — consecutive lines on the same side step one column to the left (traditional order)
    0: ink(1760, 150, size=66),
    1: ink(1662, 130, size=66),
    2: light(190, 150, size=66),
    3: ink(1780, 150, size=66),
    # winter
    4: ink(170, 150, size=66),
    5: light(1760, 170, size=66),
    6: light(200, 160, size=66),
    7: light(1790, 160, size=66),
    # the house
    8: ink(300, 200, size=96, spacing=1.1),
    9: ink(166, 230, size=96, spacing=1.1),
    10: light(1840, 150, size=60),
    11: ink(220, 200, size=86, spacing=1.12),
    12: ink(390, 230, size=108, spacing=1.12, accent_chars=False),
    13: ink(1560, 150, size=64),
    # spring
    14: ink(260, 210, size=96, spacing=1.1),
    15: ink(1770, 170, size=84, spacing=1.08),
    16: ink(1660, 150, size=66),
    17: ink_h(150, size=66),
    18: light(1790, 150, size=66),
    # refrain 2
    19: light(1760, 150, size=66),
    20: light(170, 130, size=66),
    21: light(1820, 130, size=66),
    22: ink(250, 130, size=68),
    # the hide
    23: light(400, 230, size=96, spacing=1.1),
    24: light_h(1046, size=58),
    25: light(300, 150, size=66),
    26: ink_h(992, size=58),
    27: ink_h(1050, size=58),
    # work
    28: ink(260, 230, size=100, spacing=1.1),
    29: ink(W / 2, 110, size=86, spacing=1.08),
    30: ink(620, 300, size=60),
    31: light(1820, 140, size=66),
    32: ink(1700, 150, size=66),
    # refrain 3
    33: ink(1840, 140, size=66),
    34: ink(180, 130, size=66),
    35: light(330, 140, size=66),
    36: light(200, 130, size=70),
    # the bloom
    37: light(330, 160, size=68),
    38: light_h(1010, size=68),
    39: light(220, 160, size=68),
    40: ink(1700, 260, size=82, spacing=1.1),
    41: ink(220, 150, size=66, hold=0.0, fade_out=1.2),
}
