"""Pre-compute audio features used by the renderer.

Writes (numbers only — no lyric text is stored):
  data/audio_features.json : frame-rate envelopes (rms, onset, percussive, low band)
  data/char_timing.json    : estimated sung time of every character of every LRC line

Usage:  python tools/analyze_audio.py [song.mp3] [lyrics.lrc]
"""
import json
import os
import sys

import librosa
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from pv import config  # noqa: E402
from pv.core.lyrics import parse_lrc  # noqa: E402


def norm(a, pct=99):
    a = np.asarray(a, dtype=np.float64)
    a = a / (np.percentile(a, pct) + 1e-9)
    return np.clip(a, 0, 1.5)


def main():
    audio = sys.argv[1] if len(sys.argv) > 1 else config.AUDIO_PATH
    lrc = sys.argv[2] if len(sys.argv) > 2 else config.LRC_PATH
    y, sr = librosa.load(audio, sr=22050, mono=True)
    hop = 512
    ht = hop / sr
    S = np.abs(librosa.stft(y, n_fft=2048, hop_length=hop))
    freqs = librosa.fft_frequencies(sr=sr, n_fft=2048)
    rms = librosa.feature.rms(y=y, hop_length=hop)[0]
    onset = librosa.onset.onset_strength(S=librosa.amplitude_to_db(S, ref=np.max), sr=sr, hop_length=hop)
    _, yp = librosa.effects.hpss(y)
    perc = librosa.onset.onset_strength(y=yp, sr=sr, hop_length=hop)
    low = S[freqs < 150].mean(axis=0)
    high = S[freqs > 4000].mean(axis=0)
    feats = {
        "hop_time": ht,
        "duration": len(y) / sr,
        "rms": np.round(norm(rms), 4).tolist(),
        "onset": np.round(norm(onset), 4).tolist(),
        "perc": np.round(norm(perc), 4).tolist(),
        "low": np.round(norm(low), 4).tolist(),
        "high": np.round(norm(high), 4).tolist(),
    }
    os.makedirs(config.DATA, exist_ok=True)
    with open(os.path.join(config.DATA, "audio_features.json"), "w") as f:
        json.dump(feats, f)

    # --- per-character timing from the foreground (vocal) onset envelope ---
    S_filter = librosa.decompose.nn_filter(S, aggregate=np.median, metric="cosine",
                                           width=int(librosa.time_to_frames(2, sr=sr, hop_length=hop)))
    S_filter = np.minimum(S, S_filter)
    mask_v = librosa.util.softmask(S - S_filter, 10 * S_filter, power=2)
    S_fg = mask_v * S
    band = (freqs > 250) & (freqs < 3500)
    fg = S_fg[band].sum(axis=0)
    fg = fg / (np.percentile(fg, 99) + 1e-9)
    on = librosa.onset.onset_strength(S=librosa.amplitude_to_db(S_fg, ref=np.max), sr=sr, hop_length=hop)
    on = on / (np.percentile(on, 99) + 1e-9)

    lines = parse_lrc(lrc)
    timing = []
    for i, ln in enumerate(lines):
        t0 = ln["t"]
        t1 = lines[i + 1]["t"] if i + 1 < len(lines) else min(t0 + 5.0, config.MUSIC_END)
        chars = [c for c in ln["text"] if not c.isspace()]
        n = len(chars)
        a = max(0, int((t0 - 0.2) / ht))
        b = int(t1 / ht)
        e = fg[a:b]
        act = np.where(e > 0.2)[0]
        sung_end = (a + act[-1]) * ht if len(act) else t1
        sung_end = min(max(sung_end, t0 + 0.25 * n), t1)
        seg = on[a:b]
        pk = librosa.util.peak_pick(seg, pre_max=3, post_max=3, pre_avg=5, post_avg=5, delta=0.1, wait=3)
        cand = [((a + p) * ht, seg[p]) for p in pk if (a + p) * ht <= sung_end - 0.1]
        times = None
        if len(cand) >= n:
            # keep the n strongest onsets but always the first one, then sort
            first = min(cand, key=lambda c: c[0])
            rest = sorted([c for c in cand if c is not first], key=lambda c: -c[1])[: n - 1]
            times = sorted([first[0]] + [c[0] for c in rest])
            # sanity: monotone with min gap, starts near t0
            if abs(times[0] - t0) > 0.35 or min(np.diff(times), default=1) < 0.08:
                times = None
        if times is None:
            span = min(sung_end - t0, 0.36 * n)
            times = [t0 + span * k / max(n, 1) for k in range(n)]
        times[0] = max(min(times[0], t0 + 0.05), t0 - 0.12)
        for k in range(1, len(times)):
            times[k] = max(times[k], times[k - 1] + 0.06)
        timing.append({"line": i, "t": t0, "end": round(float(sung_end), 3),
                       "chars": [round(float(x), 3) for x in times]})
    with open(os.path.join(config.DATA, "char_timing.json"), "w") as f:
        json.dump(timing, f, indent=0)
    print("wrote features and timing for", len(lines), "lines")


if __name__ == "__main__":
    main()
