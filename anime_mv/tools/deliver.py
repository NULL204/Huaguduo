#!/usr/bin/env python3
"""deliver.py -- make the repository copy of the film from the local high-quality master.

The master (render/<name>_master.mp4, x264 near-lossless, git-ignored) stays local. The repository copy must stay
under GitHub's 100 MB file limit, so it is a two-pass x264 encode at the bitrate that lands on --target-mb
(default 92 MB), tuned for animation, AAC 192 kb/s, +faststart.

  python tools/deliver.py render/huaguduo_anime_pv_master.mp4 ../videos/huaguduo_anime_pv_1080p.mp4
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

FFMPEG = os.environ.get("FFMPEG", "ffmpeg")
FFPROBE = os.environ.get("FFPROBE", "ffprobe")


def duration(p: str) -> float:
    out = subprocess.run([FFPROBE, "-v", "error", "-show_entries", "format=duration", "-of", "json", p],
                         capture_output=True, text=True, check=True).stdout
    return float(json.loads(out)["format"]["duration"])


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("master"); ap.add_argument("out")
    ap.add_argument("--target-mb", type=float, default=92.0)
    ap.add_argument("--audio-kbps", type=int, default=192)
    ap.add_argument("--preset", default="slow")
    a = ap.parse_args()
    dur = duration(a.master)
    total_kbps = a.target_mb * 8 * 1000 / dur            # MB here = 10^6 bytes
    vkbps = int(total_kbps - a.audio_kbps - 40)           # container overhead margin
    print(f"duration {dur:.2f} s -> video {vkbps} kb/s + audio {a.audio_kbps} kb/s (target {a.target_mb} MB)")
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as td:
        log = os.path.join(td, "x264")
        common = ["-c:v", "libx264", "-preset", a.preset, "-tune", "animation", "-b:v", f"{vkbps}k", "-maxrate", f"{int(vkbps * 2.2)}k",
                  "-bufsize", f"{int(vkbps * 4)}k", "-pix_fmt", "yuv420p", "-profile:v", "high", "-passlogfile", log]
        subprocess.run([FFMPEG, "-v", "error", "-y", "-i", a.master, *common, "-pass", "1", "-an", "-f", "mp4", os.devnull], check=True)
        subprocess.run([FFMPEG, "-v", "error", "-y", "-i", a.master, *common, "-pass", "2", "-c:a", "aac", "-b:a", f"{a.audio_kbps}k",
                        "-movflags", "+faststart", a.out], check=True)
    size = os.path.getsize(a.out) / 1e6
    print(f"wrote {a.out}: {size:.1f} MB")
    return 0 if size < 100 else 1


if __name__ == "__main__":
    sys.exit(main())
