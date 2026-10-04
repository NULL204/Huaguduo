"""Render the 花骨朵 fan PV.

    python render.py                      # full 1080p30 render -> out/huaguduo_pv.mp4
    python render.py --start 60 --end 80  # a time range
    python render.py --workers 4 --crf 17

Needs the user's own song + LRC in assets/ (see README) and data/*.json from tools/analyze_audio.py.
Frames are rendered in parallel worker processes; each pipes raw RGB into its own x264 encoder, then
the segments are concatenated and muxed with the song.
"""
import argparse
import math
import multiprocessing as mp
import os
import subprocess
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pv import config  # noqa: E402

COLOR_ARGS = ["-color_primaries", "bt709", "-color_trc", "bt709", "-colorspace", "bt709", "-color_range", "tv"]


def encoder_cmd(path, crf, preset, threads):
    return ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{config.W}x{config.H}",
            "-r", str(config.FPS), "-i", "-",
            "-vf", "scale=out_color_matrix=bt709:out_range=tv,format=yuv420p",
            "-c:v", "libx264", "-preset", preset, "-crf", str(crf), "-tune", "animation", "-g", str(config.FPS * 2),
            "-threads", str(threads), *COLOR_ARGS, path]


def worker(args):
    idx, f0, f1, path, crf, preset, threads = args
    from pv.timeline import render_frame
    proc = subprocess.Popen(encoder_cmd(path, crf, preset, threads), stdin=subprocess.PIPE)
    t0 = time.time()
    for f in range(f0, f1):
        t = f / config.FPS
        img = render_frame(t)
        proc.stdin.write(img.tobytes())
        if (f - f0) % 60 == 0:
            el = time.time() - t0
            done = f - f0 + 1
            print(f"[w{idx}] frame {f} ({done}/{f1 - f0})  {el / done:.2f}s/frame", flush=True)
    proc.stdin.close()
    proc.wait()
    return path, time.time() - t0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--start", type=float, default=0.0)
    ap.add_argument("--end", type=float, default=config.DURATION)
    ap.add_argument("--workers", type=int, default=max(1, os.cpu_count() or 4))
    ap.add_argument("--crf", type=int, default=17)
    ap.add_argument("--preset", default="medium")
    ap.add_argument("--out", default=os.path.join(config.OUT, "huaguduo_pv.mp4"))
    ap.add_argument("--no-audio", action="store_true")
    a = ap.parse_args()

    os.makedirs(config.OUT, exist_ok=True)
    segdir = os.path.join(config.OUT, "segments")
    os.makedirs(segdir, exist_ok=True)
    f_start = int(round(a.start * config.FPS))
    f_end = int(round(a.end * config.FPS))
    n = f_end - f_start
    k = a.workers
    # interleave-free contiguous chunks; more chunks than workers balances uneven scene costs
    nchunks = k * 3
    bounds = [f_start + (n * i) // nchunks for i in range(nchunks + 1)]
    jobs = [(i, bounds[i], bounds[i + 1], os.path.join(segdir, f"seg_{i:03d}.mp4"), a.crf, a.preset, 1)
            for i in range(nchunks) if bounds[i + 1] > bounds[i]]
    t0 = time.time()
    with mp.get_context("fork").Pool(k) as pool:
        results = pool.map(worker, jobs, chunksize=1)
    print(f"rendered {n} frames in {time.time() - t0:.0f}s")
    lst = os.path.join(segdir, "list.txt")
    with open(lst, "w") as f:
        for path, _ in results:
            f.write(f"file '{os.path.abspath(path)}'\n")
    silent = os.path.join(config.OUT, "video_only.mp4")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", silent], check=True)
    if a.no_audio:
        os.replace(silent, a.out)
    else:
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", silent, "-ss", str(a.start), "-t", str(a.end - a.start),
                        "-i", config.AUDIO_PATH, "-map", "0:v", "-map", "1:a", "-c:v", "copy", "-c:a", "aac", "-b:a", "320k",
                        "-movflags", "+faststart", "-shortest", a.out], check=True)
    print("wrote", a.out)


if __name__ == "__main__":
    main()
