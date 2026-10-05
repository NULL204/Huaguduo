#!/usr/bin/env python3
"""lock_grid.py -- replace the tracked beat grid in analysis/audio.json (+ envelope_30fps.json) by a steady grid.

Why: 《花骨朵》 is produced on a steady 120 BPM grid, but librosa's tracker drifts by up to one beat in the B4 /
refrain-3 region (116-146 s) and around the intro stops. Measured on the low band (< 150 Hz kick onsets, 8 s windows):
the steady grid t = 0.09 + 0.5 k s, with downbeats on k % 4 == 0, carries 2-4x the kick energy of the other beat phases
and beats the tracked downbeats in every window where they disagree (e.g. 128-136 s: 105.7 vs 13.6). Bar 81 then
starts at 160.09 s, right on the song's dead stop (160.19 s).

Rewrites: bpm, beats, beats_smooth, downbeats, bars (index 1..80), downbeat_info.winning_phase = 0, section starts /
ends snapped to bar starts (from analysis/sections.json bar ranges), and the per-frame beat / bar phase fields of
envelope_30fps.json. Re-run after every `tools/analyze_audio.py`.

  python tools/lock_grid.py [--t0 0.09] [--bpm 120]
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
AN = ROOT / "analysis"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--t0", type=float, default=0.09)
    ap.add_argument("--bpm", type=float, default=120.0)
    a = ap.parse_args()
    audio = json.loads((AN / "audio.json").read_text(encoding="utf-8"))
    cut = float(audio["music_cut"])
    spb = 60.0 / a.bpm
    beats = []
    k = 0
    while a.t0 + k * spb <= cut + 1e-6:
        beats.append(round(a.t0 + k * spb, 4))
        k += 1
    downbeats = beats[::4]
    bars = []
    for i, s in enumerate(downbeats):
        e = round(s + 4 * spb, 4)
        if e > cut + 0.25:          # only full bars before the dead stop
            break
        bars.append({"index": i + 1, "start": s, "end": e, "bpm": a.bpm})
    audio.update(bpm=a.bpm, beats=beats, beats_smooth=beats, downbeats=downbeats, bars=bars)
    audio.setdefault("downbeat_info", {})["winning_phase"] = 0
    audio["grid_lock"] = {"tool": "tools/lock_grid.py", "t0": a.t0, "bpm": a.bpm,
                          "why": "steady production grid; low-band kick onsets confirm it, tracker drifted 116-146 s"}
    # sections: keep labels, snap to bar starts from the curated bar ranges
    sec_path = AN / "sections.json"
    if sec_path.exists():
        rows = json.loads(sec_path.read_text(encoding="utf-8"))
        bstart = {b["index"]: b["start"] for b in bars}
        new_secs = []
        for r in rows:
            b0, b1 = int(r[0]), int(r[1])
            s = 0.0 if b0 == 1 else bstart.get(b0)
            e = bstart.get(b1 + 1, cut)
            old = next((x for x in audio["sections"] if x.get("name") == r[4] or x.get("label") == r[2]), {})
            sec = dict(old)
            sec.update(start=round(s, 4), end=round(e, 4), bar_start=b0, bar_end=b1, label=r[2], group=r[3], name=r[4])
            new_secs.append(sec)
        tail = [x for x in audio["sections"] if x.get("label") == "tail"]
        for x in tail:
            x["start"] = cut
        audio["sections"] = new_secs + tail
    (AN / "audio.json").write_text(json.dumps(audio, ensure_ascii=False, indent=1), encoding="utf-8")
    # envelope phases
    env_path = AN / "envelope_30fps.json"
    if env_path.exists():
        env = json.loads(env_path.read_text(encoding="utf-8"))
        fps = env.get("fps", 30)
        n = env.get("frames") or len(env.get("rms", []))
        bp, brp, bi, bri = [], [], [], []
        for f in range(n):
            t = f / fps
            x = (t - a.t0) / spb
            kb = int(x // 1) if x >= 0 else -1
            bp.append(round(x - kb if x >= 0 else 0.0, 4))
            bi.append(max(kb, -1))
            xb = x / 4.0
            kbar = int(xb // 1) if x >= 0 else -1
            brp.append(round(xb - kbar if x >= 0 else 0.0, 4))
            bri.append(kbar + 1 if x >= 0 else 0)
        env.update(beat_phase=bp, bar_phase=brp, beat=bi, bar=bri)
        env_path.write_text(json.dumps(env, separators=(",", ":")), encoding="utf-8")
    print(f"locked grid: {len(beats)} beats, {len(bars)} bars (bar 1 {bars[0]['start']}, bar {bars[-1]['index']} "
          f"{bars[-1]['start']}), music_cut {cut}; sections: " +
          ", ".join(f"{s['name']} {s['start']:.2f}" for s in audio["sections"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
