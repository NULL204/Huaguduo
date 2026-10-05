#!/usr/bin/env python3
"""build_lyrics_mv.py -- build analysis/lyrics_mv.lrc (what the film shows) from the user's own LRC plus the
JIZURA markup overlay in analysis/lyrics_markup.json.

The overlay stores only character positions (cuts '/', *emphasis*, trailing '!' キメ lines, [間奏] gaps), so
the repository never contains the song's lyrics: put your LRC at analysis/lyrics_source.lrc (new_project.py
--lyrics does that) or pass --lrc.

    python tools/build_lyrics_mv.py [--lrc analysis/lyrics_source.lrc] [--out analysis/lyrics_mv.lrc] [--print]
"""
import argparse
import json
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TAG = re.compile(r"^\[(\d+):(\d+(?:\.\d+)?)\](.*)$")


def fmt(t):
    m, s = divmod(max(0.0, t), 60)
    return f"[{int(m):02d}:{s:05.2f}]"


def mark(text, spec):
    chars = list(text)
    n = len(chars)
    cuts = set(spec.get("cut", []))
    starts, ends = {}, {}
    for a, b in spec.get("emph", []):
        if 0 <= a < b <= n:
            starts[a] = starts.get(a, 0) + 1
            ends[b] = ends.get(b, 0) + 1
    out = []
    for i in range(n + 1):
        out.append("*" * ends.get(i, 0))
        if i in cuts and 0 < i < n:
            out.append("/")
        if i == n:
            break
        out.append("*" * starts.get(i, 0))
        if chars[i] == " " and (i in cuts or i + 1 in cuts):
            continue
        if chars[i] == " ":
            out.append("/")          # any remaining phrase space becomes a JIZURA cut
            continue
        out.append(chars[i])
    s = "".join(out).replace("//", "/").strip("/")
    if spec.get("kime"):
        s += "!"
    return s


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--lrc", default=os.path.join(ROOT, "analysis", "lyrics_source.lrc"))
    ap.add_argument("--markup", default=os.path.join(ROOT, "analysis", "lyrics_markup.json"))
    ap.add_argument("--out", default=os.path.join(ROOT, "analysis", "lyrics_mv.lrc"))
    ap.add_argument("--print", action="store_true", help="print the result instead of only writing it")
    a = ap.parse_args()
    with open(a.markup, encoding="utf-8") as f:
        mk = json.load(f)
    rows = []
    with open(a.lrc, encoding="utf-8-sig") as f:
        for raw in f:
            m = TAG.match(raw.strip())
            if not m:
                continue
            text = m.group(3).strip()
            if not text:
                continue
            rows.append((int(m.group(1)) * 60 + float(m.group(2)), text))
    rows.sort(key=lambda r: r[0])
    lines = mk.get("lines", {})
    out = []
    hdr = mk.get("header", {})
    out.append(f"[ar:{hdr.get('ar', '')}]")
    out.append(f"[by:{hdr.get('by', '')}]")
    out.append("[offset:0]")
    body = [(t, mark(text, lines.get(str(i), {}))) for i, (t, text) in enumerate(rows)]
    body += [(g, "[間奏]") for g in mk.get("gaps", [])]
    body.sort(key=lambda r: r[0])
    for t, s in body:
        out.append(f"{fmt(t)}{s}")
    with open(a.out, "w", encoding="utf-8") as f:
        f.write("\n".join(out) + "\n")
    print(f"wrote {a.out}: {len(rows)} lyric rows + {len(mk.get('gaps', []))} gap rows")
    if a.print:
        print("\n".join(out))


if __name__ == "__main__":
    main()
