"""Airy illustration palette for 阿朵 (original character).

High-key, low saturation; warm pink light, cool lavender-blue shadow; carmine is the only strong colour.
"""

# line art (coloured, never pure black)
LINE = (86, 66, 92)          # general
LINE_SKIN = (170, 108, 112)  # face/skin contours
LINE_DEEP = (64, 44, 66)     # eye lash line, deep folds
LINE_HAIR = (30, 26, 40)
LINE_CLOTH = (124, 122, 156)

SKIN = (255, 246, 241)
SKIN_SH = (240, 210, 216)
SKIN_SH2 = (222, 184, 198)
BLUSH = (255, 156, 168)
LIP = (226, 120, 130)

SCLERA = (255, 255, 255)
SCLERA_SH = (214, 214, 236)
IRIS_TOP = (62, 12, 26)
IRIS_MID = (160, 34, 48)
IRIS_BOT = (255, 160, 118)
IRIS_RIM = (40, 8, 20)
PUPIL = (36, 6, 16)
LASH = (40, 26, 40)

HAIR = (58, 56, 74)
HAIR_SH = (34, 32, 48)
HAIR_DEEP = (22, 20, 32)
HAIR_HI = (168, 176, 204)
HAIR_RIM = (255, 214, 214)
HAIR_RED = (196, 42, 64)
HAIR_RED_GLOW = (255, 120, 132)

BLOUSE = (252, 252, 255)
BLOUSE_SH = (216, 220, 240)
BLOUSE_SH2 = (192, 196, 226)
PIPING = (204, 34, 56)
SLEEVE_RED = (212, 40, 62)
SLEEVE_RED_SH = (150, 20, 44)

SKIRT = (52, 52, 66)
SKIRT_SH = (32, 32, 44)
SKIRT_HI = (128, 132, 160)
HEM_RED = (196, 30, 52)
TIGHTS = (46, 44, 58)
TIGHTS_SHEER = (126, 116, 136)
SHOE = (40, 36, 46)
SHOE_HI = (190, 190, 214)

THREAD = (222, 30, 52)
THREAD_GLOW = (255, 96, 110)
BUD = (214, 40, 56)
BUD_DEEP = (150, 18, 36)
BUD_GREEN = (126, 168, 112)
BUD_GREEN_DEEP = (78, 118, 80)

PAPER = (248, 248, 250)
INK = (34, 30, 42)
ROUGE = (204, 30, 52)
ROUGE_HOT = (255, 72, 88)
SKY_PINK = (255, 236, 240)
SKY_BLUE = (214, 224, 240)
SHADOW_BLUE = (188, 198, 224)


def lerp(a, b, t):
    t = max(0.0, min(1.0, t))
    return tuple(int(round(x + (y - x) * t)) for x, y in zip(a, b))


def sleeve_cols(redness):
    r = max(0.0, min(1.0, redness))
    return BLOUSE, lerp(BLOUSE, SLEEVE_RED, 0.35 * r), lerp(BLOUSE, SLEEVE_RED, r)
