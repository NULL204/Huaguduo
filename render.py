"""Render the 花骨朵 fan PV.

    python render.py                      # full 1080p30 render -> out/huaguduo_pv.mp4
    python render.py --start 60 --end 80  # a time range
    python render.py --workers 4 --crf 17

Needs the user's own song + LRC in assets/ (see README) and data/*.json from tools/analyze_audio.py.
Frames are rendered in parallel worker processes; each pipes raw RGB into its own x264 encoder, then
the segments are concatenated and muxed with the song.
"""
import argparse
import concurrent.futures as cf
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


def frame_count(path):
    try:
        out = subprocess.run(["ffprobe", "-v", "error", "-count_packets", "-select_streams", "v:0", "-show_entries",
                              "stream=nb_read_packets", "-of", "csv=p=0", path], capture_output=True, text=True, timeout=120)
        return int(out.stdout.strip() or 0)
    except Exception:
        return 0


def final_encode(src, dst, bitrate, audio_start, audio_len):
    """Two-pass size-targeted delivery encode (light temporal denoise keeps film grain from eating the bitrate)."""
    vf = "hqdn3d=0.8:0.8:3.5:3.5"
    common = ["-vf", vf, "-c:v", "libx264", "-preset", "slow", "-tune", "film", "-b:v", bitrate, "-pix_fmt", "yuv420p",
              *COLOR_ARGS]
    logp = dst + ".2pass"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", src, *common, "-pass", "1", "-passlogfile", logp, "-an",
                    "-f", "mp4", os.devnull], check=True)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", src, "-ss", str(audio_start), "-t", str(audio_len),
                    "-i", config.AUDIO_PATH, "-map", "0:v", "-map", "1:a", *common, "-pass", "2", "-passlogfile", logp,
                    "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", "-shortest", dst], check=True)
    for ext in ("-0.log", "-0.log.mbtree"):
        try:
            os.remove(logp + ext)
        except OSError:
            pass


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--start", type=float, default=0.0)
    ap.add_argument("--end", type=float, default=config.DURATION)
    ap.add_argument("--workers", type=int, default=max(1, os.cpu_count() or 4))
    ap.add_argument("--crf", type=int, default=17)
    ap.add_argument("--preset", default="medium")
    ap.add_argument("--out", default=os.path.join(config.OUT, "huaguduo_pv.mp4"))
    ap.add_argument("--no-audio", action="store_true")
    ap.add_argument("--resume", action="store_true", help="skip segments that are already complete")
    ap.add_argument("--final-bitrate", default="4000k", help="2-pass delivery encode bitrate ('' to skip)")
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
    todo = jobs
    if a.resume:
        todo = [j for j in jobs if frame_count(j[3]) != j[2] - j[1]]
        print(f"resume: {len(jobs) - len(todo)} complete segments kept, {len(todo)} to render")
    t0 = time.time()
    # ProcessPoolExecutor raises BrokenProcessPool if a worker dies, instead of hanging forever
    with cf.ProcessPoolExecutor(max_workers=k, mp_context=mp.get_context("fork")) as ex:
        for path, el in ex.map(worker, todo):
            print(f"done {os.path.basename(path)} in {el:.0f}s", flush=True)
    for j in jobs:
        got = frame_count(j[3])
        if got != j[2] - j[1]:
            raise SystemExit(f"segment {j[3]} has {got} frames, expected {j[2] - j[1]}")
    print(f"rendered in {time.time() - t0:.0f}s")
    lst = os.path.join(segdir, "list.txt")
    with open(lst, "w") as f:
        for j in jobs:
            f.write(f"file '{os.path.abspath(j[3])}'\n")
    silent = os.path.join(config.OUT, "video_only.mp4")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", silent], check=True)
    master = a.out.replace(".mp4", "_master.mp4")
    if a.no_audio:
        os.replace(silent, master)
    else:
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", silent, "-ss", str(a.start), "-t", str(a.end - a.start),
                        "-i", config.AUDIO_PATH, "-map", "0:v", "-map", "1:a", "-c:v", "copy", "-c:a", "aac", "-b:a", "320k",
                        "-movflags", "+faststart", "-shortest", master], check=True)
    print("wrote", master)
    if a.final_bitrate and not a.no_audio:
        final_encode(silent, a.out, a.final_bitrate, a.start, a.end - a.start)
        print("wrote", a.out)


if __name__ == "__main__":
    main()
