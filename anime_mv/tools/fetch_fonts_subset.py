#!/usr/bin/env python3
"""fetch_fonts_subset.py -- download Google Fonts *subsets* that contain only the glyphs this film draws.

Why: the template's tools/fetch_fonts.py pulls ~260 MB of full TTFs; on a ~1 Mbit/s link that is most of an hour.
The Google Fonts CSS2 API returns a font cut down to the characters passed in `text=`, so each face is a few tens of
KB. The glyph set is collected locally from
  * the lyrics (analysis/lyrics_mv.lrc -- read here, never written anywhere in plain text),
  * engine/fonts/extra_glyphs.txt (titles, credits, solar terms, captions -- non-lyric strings, committed),
  * JIZURA's zh-Hans scramble / reel character sets (from jizura/app/jizura_engine.js), digits, Latin, punctuation.
Output (both git-ignored): engine/fonts/sub_*.woff2 and engine/fonts/fonts_subset.css (linked by engine/index.html
and engine/vertical.html). The faces are the ones JIZURA maps Chinese lyrics to (J.LANG_FACES['zh-Hans']) plus the
film's own display faces. The render tools abort requests to Google Fonts, so JIZURA's runtime loader falls back
to these local faces and every frame is deterministic.

  python tools/fetch_fonts_subset.py
"""
from __future__ import annotations

import concurrent.futures as cf
import re
import string
import sys
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FONTS = ROOT / "engine" / "fonts"
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
      "Chrome/140.0.0.0 Safari/537.36")

# family -> weights (Google Fonts axis values)
FACES = {
    "Noto Serif SC": [200, 300, 500, 700, 800, 900],
    "Noto Sans SC": [300, 500, 700, 900],
    "Ma Shan Zheng": [400],
    "Zhi Mang Xing": [400],
    "Long Cang": [400],
    "ZCOOL XiaoWei": [400],
    "ZCOOL QingKe HuangYou": [400],
    "ZCOOL KuaiLe": [400],
    "LXGW Marker Gothic": [400],
    "IBM Plex Mono": [500, 600],
}
LATIN_ONLY = {"IBM Plex Mono"}
CHUNK = 260          # characters per request (keeps the URL well under the API limit)


def lyric_chars() -> set[str]:
    p = ROOT / "analysis" / "lyrics_mv.lrc"
    if not p.exists():
        return set()
    txt = re.sub(r"\[[^\]]*\]", "", p.read_text(encoding="utf-8"))
    return set(txt) - set("\r\n\t")


def jizura_chars() -> set[str]:
    p = ROOT / "jizura" / "app" / "jizura_engine.js"
    if not p.exists():
        return set()
    js = p.read_text(encoding="utf-8")
    out: set[str] = set()
    for name in ("ZH_S", "SYM", "DIG"):
        m = re.search(r"const %s\s*=\s*'([^']*)'" % name, js)
        if m:
            out |= set(m.group(1))
    return out


def glyphs() -> str:
    s = lyric_chars() | jizura_chars()
    extra = FONTS / "extra_glyphs.txt"
    if extra.exists():
        s |= set(extra.read_text(encoding="utf-8"))
    s |= set(string.ascii_letters + string.digits + string.punctuation + " ")
    s |= set("、。，．・：；？！「」『』《》〈〉（）【】〔〕…—―～·“”‘’　〇")
    s -= set("\r\n\t")
    return "".join(sorted(s))


def get(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    for attempt in range(5):
        try:
            with urllib.request.urlopen(req, timeout=120) as r:
                return r.read()
        except Exception:  # noqa: BLE001 -- slow link: retry
            if attempt == 4:
                raise
    return b""


def css_for(family: str, weights: list[int], text: str) -> str:
    fam = family.replace(" ", "+")
    spec = f"{fam}:wght@{';'.join(map(str, weights))}" if weights != [400] else fam
    q = f"family={spec}&text={urllib.parse.quote(text, safe='')}&display=block"
    return get("https://fonts.googleapis.com/css2?" + q).decode("utf-8")


def unicode_range(chars: str) -> str:
    return ",".join(f"U+{ord(c):X}" for c in sorted(set(chars)))


def main() -> int:
    FONTS.mkdir(parents=True, exist_ok=True)
    text_all = glyphs()
    latin = "".join(c for c in text_all if ord(c) < 0x3000)
    print(f"glyph set: {len(text_all)} characters ({len(latin)} Latin/punctuation)")
    rules, downloads = [], []
    for family, weights in FACES.items():
        text = latin if family in LATIN_ONLY else text_all
        chunks = [text[i:i + CHUNK] for i in range(0, len(text), CHUNK)]
        for k, chunk in enumerate(chunks):
            css = css_for(family, weights, chunk)
            for block in re.findall(r"@font-face\s*{[^}]*}", css):
                w = re.search(r"font-weight:\s*(\d+)", block)
                u = re.search(r"url\((https://[^)]+)\)", block)
                if not (w and u):
                    continue
                weight = int(w.group(1))
                fname = f"sub_{family.replace(' ', '')}_{weight}_{k}.woff2"
                downloads.append((u.group(1), FONTS / fname))
                rules.append(f"@font-face{{font-family:'{family}';src:url('./{fname}') format('woff2');"
                             f"font-weight:{weight};font-style:normal;font-display:block;"
                             f"unicode-range:{unicode_range(chunk)};}}")
        print(f"  {family}: {len(weights)} weight(s) x {len(chunks)} chunk(s)")
    with cf.ThreadPoolExecutor(max_workers=12) as pool:
        sizes = list(pool.map(lambda d: d[1].write_bytes(get(d[0])), downloads))
    (FONTS / "fonts_subset.css").write_text(
        "/* Generated by tools/fetch_fonts_subset.py -- Google Fonts subsets (OFL) for the glyphs this film uses. "
        "Local only (git-ignored). */\n" + "\n".join(rules) + "\n", encoding="utf-8")
    print(f"wrote {len(downloads)} subset files, {sum(sizes) / 1e6:.2f} MB, and engine/fonts/fonts_subset.css")
    return 0


if __name__ == "__main__":
    sys.exit(main())
