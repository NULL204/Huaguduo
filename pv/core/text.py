"""Font loading and glyph-path caching (paths are authored at size 100)."""
import os

import skia

from .. import config

_TF = {}
_GP = {}


def typeface(face):
    if face not in _TF:
        path = os.path.join(config.FONT_DIR, config.FONTS[face])
        tf = skia.Typeface.MakeFromFile(path)
        if tf is None:
            tf = skia.Typeface.MakeFromFile("/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc")
        _TF[face] = tf
    return _TF[face]


def font(face, size):
    f = skia.Font(typeface(face), size)
    f.setEdging(skia.Font.Edging.kAntiAlias)
    f.setSubpixel(True)
    return f


def glyph_path(face, ch):
    """Path of a single character at size 100, origin at baseline-left.
    Glyph box is roughly x in [0,100], y in [-88, 12]."""
    key = (face, ch)
    if key not in _GP:
        f = skia.Font(typeface(face), 100)
        g = f.textToGlyphs(ch)
        if len(g) == 0 or g[0] == 0:
            # fall back to serif for missing glyphs
            if face != "serif":
                _GP[key] = glyph_path("serif", ch)
                return _GP[key]
            _GP[key] = None
            return None
        p = f.getPath(g[0])
        if p is None:
            _GP[key] = None
            return None
        # centre horizontally in a 100 box
        b = p.getBounds()
        adv = f.getWidths([g[0]])[0] if hasattr(f, "getWidths") else 100
        dx = (100 - adv) / 2.0
        m = skia.Matrix.Translate(dx, 0)
        p2 = skia.Path(p)
        p2.transform(m)
        _GP[key] = p2
    return _GP[key]


def text_path(face, s, size, vertical=False, spacing=1.0):
    """Combined path of string s; horizontal origin baseline-left; vertical origin top-centre."""
    out = skia.Path()
    for k, ch in enumerate(s):
        if ch.isspace():
            continue
        gp = glyph_path(face, ch)
        if gp is None:
            continue
        m = skia.Matrix()
        sc = size / 100.0
        if vertical:
            m.setScaleTranslate(sc, sc, -size / 2, (k * spacing + 0.88) * size)
        else:
            m.setScaleTranslate(sc, sc, k * spacing * size, 0)
        p = skia.Path(gp)
        p.transform(m)
        out.addPath(p)
    return out


def draw_text(canvas, s, x, y, size, face="serif", color=(20, 20, 20, 255), vertical=False,
              spacing=1.0, align="start", blur=0.0):
    p = text_path(face, s, size, vertical, spacing)
    n = len(s)
    total = n * spacing * size
    if align == "center":
        off = -total / 2
    elif align == "end":
        off = -total
    else:
        off = 0
    canvas.save()
    if vertical:
        canvas.translate(x, y + off)
    else:
        canvas.translate(x + off, y)
    paint = skia.Paint(AntiAlias=True, Color=skia.Color(*color))
    if blur > 0:
        paint.setMaskFilter(skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, blur))
    canvas.drawPath(p, paint)
    canvas.restore()
