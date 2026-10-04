"""Shared palette for the 'rouge & ink shadow theatre' look."""

INK = (20, 16, 18)
INK_SOFT = (52, 44, 44)
INK_GRAY = (110, 102, 98)
PAPER = (248, 236, 212)
PAPER_DIM = (214, 198, 170)

ROUGE = (196, 22, 45)        # cochineal carmine
ROUGE_DEEP = (118, 8, 26)
ROUGE_HOT = (238, 52, 64)
ROUGE_PINK = (226, 120, 128)

# translucent leather colours as *transmittance* (drawn with multiply on white)
LEATHER_RED = (214, 44, 50)
LEATHER_RED_DEEP = (160, 20, 34)
LEATHER_PALE = (246, 238, 222)
LEATHER_GREEN = (116, 160, 84)
LEATHER_GREEN_DEEP = (64, 112, 60)
LEATHER_GOLD = (232, 182, 92)
LEATHER_BLUE = (92, 120, 160)

SPRING = (92, 160, 74)
SPRING_LIGHT = (172, 206, 98)
WINTER = (34, 46, 72)
WINTER_LIGHT = (150, 170, 198)
SNOW = (236, 240, 246)
GOLD = (255, 204, 128)
SILVER = (196, 204, 214)


def lerp3(a, b, t):
    return tuple(int(round(x + (y - x) * t)) for x, y in zip(a, b))


def arm_color(redness):
    return lerp3(LEATHER_PALE, LEATHER_RED, max(0.0, min(1.0, redness)))
