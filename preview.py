"""Render preview stills / contact sheets / low-res clips.

  python preview.py still 12.5 30.2 ...           -> out/preview/t_012.50.png
  python preview.py sheet 0 30 2.0                -> contact sheet of frames every 2 s
  python preview.py clip 8 16 [scale]             -> out/preview/clip_8_16.mp4 (with audio)
"""
import os
import subprocess
import sys
import time

import cv2
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pv import config  # noqa: E402

OUTDIR = os.path.join(config.OUT, "preview")


def still(ts):
    from pv.timeline import render_frame
    os.makedirs(OUTDIR, exist_ok=True)
    paths = []
    for t in ts:
        t0 = time.time()
        img = render_frame(float(t))
        p = os.path.join(OUTDIR, f"t_{float(t):07.2f}.png")
        cv2.imwrite(p, cv2.cvtColor(img, cv2.COLOR_RGB2BGR))
        print(f"{p}  {1000 * (time.time() - t0):.0f} ms", flush=True)
        paths.append(p)
    return paths


def sheet(a, b, step, cols=4, name=None):
    from pv.timeline import render_frame
    os.makedirs(OUTDIR, exist_ok=True)
    ts = list(np.arange(a, b + 1e-6, step))
    tiles = []
    for t in ts:
        t0 = time.time()
        img = render_frame(float(t))
        sm = cv2.resize(img, (480, 270), interpolation=cv2.INTER_AREA)
        cv2.putText(sm, f"{t:.2f}", (8, 22), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2, cv2.LINE_AA)
        cv2.putText(sm, f"{t:.2f}", (8, 22), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 1, cv2.LINE_AA)
        tiles.append(sm)
        print(f"t={t:.2f} {1000 * (time.time() - t0):.0f} ms", flush=True)
    while len(tiles) % cols:
        tiles.append(np.zeros_like(tiles[0]))
    rows = [np.hstack(tiles[i:i + cols]) for i in range(0, len(tiles), cols)]
    out = np.vstack(rows)
    p = os.path.join(OUTDIR, name or f"sheet_{a:06.2f}_{b:06.2f}.png")
    cv2.imwrite(p, cv2.cvtColor(out, cv2.COLOR_RGB2BGR))
    print(p)
    return p


def clip(a, b, scale=0.5, fps=None):
    from pv.timeline import render_frame
    os.makedirs(OUTDIR, exist_ok=True)
    fps = fps or config.FPS
    w, h = int(config.W * scale) // 2 * 2, int(config.H * scale) // 2 * 2
    p = os.path.join(OUTDIR, f"clip_{a:06.2f}_{b:06.2f}.mp4")
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{w}x{h}",
           "-r", str(fps), "-i", "-", "-ss", str(a), "-t", str(b - a), "-i", config.AUDIO_PATH,
           "-map", "0:v", "-map", "1:a", "-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
           "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", "-shortest", p]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    n = int(round((b - a) * fps))
    t0 = time.time()
    for i in range(n):
        t = a + i / fps
        img = render_frame(t)
        if scale != 1.0:
            img = cv2.resize(img, (w, h), interpolation=cv2.INTER_AREA)
        proc.stdin.write(img.tobytes())
    proc.stdin.close()
    proc.wait()
    print(p, f"{(time.time() - t0) / max(1, n) * 1000:.0f} ms/frame")
    return p


if __name__ == "__main__":
    mode = sys.argv[1]
    if mode == "still":
        still([float(x) for x in sys.argv[2:]])
    elif mode == "sheet":
        a, b, st = float(sys.argv[2]), float(sys.argv[3]), float(sys.argv[4])
        sheet(a, b, st)
    elif mode == "clip":
        a, b = float(sys.argv[2]), float(sys.argv[3])
        sc = float(sys.argv[4]) if len(sys.argv) > 4 else 0.5
        clip(a, b, sc)
