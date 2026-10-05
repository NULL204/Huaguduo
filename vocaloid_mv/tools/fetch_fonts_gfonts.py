#!/usr/bin/env python3
"""fetch_fonts_gfonts.py -- fallback for tools/fetch_fonts.py when the GitHub API is unreachable.

Downloads every family listed in engine/fonts/manifest.json through the Google Fonts CSS2 API
(fonts.googleapis.com -> fonts.gstatic.com TTF) and saves each file under the name the manifest and
engine/fonts/fonts.css expect.  Variable "[wght]" files are requested as a weight range (the API then
serves the variable TTF).  Fonts are SIL OFL 1.1.

    python tools/fetch_fonts_gfonts.py [--force] [--jobs 6]
"""
import argparse
import concurrent.futures as cf
import json
import os
import re
import urllib.parse
import urllib.error
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FONTS = os.path.join(ROOT, "engine", "fonts")
WEIGHTS = {"thin": 100, "extralight": 200, "light": 300, "regular": 400, "medium": 500, "semibold": 600,
           "bold": 700, "extrabold": 800, "black": 900}
UA = {"User-Agent": "curl/8.5"}   # a non-browser agent makes the CSS API answer with TTF urls


def css_queries(entry):
    """Candidate CSS2 urls (variable fonts: try the usual weight-axis ranges)."""
    fam = urllib.parse.quote_plus(entry["family"])
    src = entry["src"]
    if "[wght]" in src:
        specs = ["wght@100..900", "wght@200..900", "wght@300..900", "wght@200..1000", "wght@400"]
    else:
        m = re.search(r"-([A-Za-z]+)\.ttf$", src)
        specs = [f"wght@{WEIGHTS.get(m.group(1).lower(), 400) if m else 400}"]
    return [f"https://fonts.googleapis.com/css2?family={fam}:{sp}" for sp in specs]


def fetch(entry, force=False):
    dst = os.path.join(FONTS, entry["file"])
    if os.path.exists(dst) and os.path.getsize(dst) > 10000 and not force:
        return entry["file"], "kept", os.path.getsize(dst)
    css, err = None, None
    for url in css_queries(entry):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60) as r:
                css = r.read().decode("utf-8")
            break
        except urllib.error.HTTPError as e:   # 400 = weight range not offered by this family
            err = e
    if css is None:
        raise RuntimeError(f"CSS API refused every weight spec for {entry['family']}: {err}")
    m = re.search(r"url\((https://[^)]+\.ttf)\)", css)
    if not m:
        raise RuntimeError(f"no ttf in CSS for {entry['family']} ({url})")
    tmp = dst + ".part"
    with urllib.request.urlopen(urllib.request.Request(m.group(1), headers=UA), timeout=600) as r, open(tmp, "wb") as f:
        while True:
            b = r.read(1 << 20)
            if not b:
                break
            f.write(b)
    os.replace(tmp, dst)
    return entry["file"], "downloaded", os.path.getsize(dst)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--jobs", type=int, default=6)
    a = ap.parse_args()
    with open(os.path.join(FONTS, "manifest.json"), encoding="utf-8") as f:
        manifest = json.load(f)
    ok = 0
    with cf.ThreadPoolExecutor(a.jobs) as ex:
        futs = {ex.submit(fetch, e, a.force): e for e in manifest}
        for fu in cf.as_completed(futs):
            e = futs[fu]
            try:
                name, how, size = fu.result()
                ok += 1
                print(f"  {how:10s} {name}  {size / 1e6:.1f} MB")
            except Exception as ex_:  # noqa: BLE001
                print(f"  FAILED     {e['file']}: {ex_}")
    print(f"{ok}/{len(manifest)} font files in {FONTS}")


if __name__ == "__main__":
    main()
