"""Access to pre-computed audio envelopes and the musical beat grid."""
import json
import math
import os

import numpy as np

from .. import config

_FEATS = None


def feats():
    global _FEATS
    if _FEATS is None:
        p = os.path.join(config.DATA, "audio_features.json")
        with open(p) as f:
            d = json.load(f)
        for k in ("rms", "onset", "perc", "low", "high"):
            d[k] = np.asarray(d[k], dtype=np.float32)
        # smoothed copies
        for k in ("rms", "low", "perc", "onset"):
            a = d[k]
            ker = np.exp(-np.arange(0, 12) / 3.0)
            ker /= ker.sum()
            # causal-ish exponential smoothing (attack fast, release slow)
            sm = np.convolve(a, ker, mode="full")[: len(a)]
            d[k + "_s"] = sm.astype(np.float32)
        _FEATS = d
    return _FEATS


def env(name, t):
    d = feats()
    a = d[name]
    x = t / d["hop_time"]
    i = int(x)
    if i < 0:
        return float(a[0])
    if i >= len(a) - 1:
        return float(a[-1])
    f = x - i
    return float(a[i] * (1 - f) + a[i + 1] * f)


def env_max(name, t, window=0.1):
    d = feats()
    a = d[name]
    i0 = max(0, int((t - window) / d["hop_time"]))
    i1 = max(i0 + 1, int(t / d["hop_time"]) + 1)
    return float(a[i0:i1].max()) if i1 <= len(a) else 0.0


def beat_index(t):
    return math.floor((t - config.BEAT0) / config.BEAT)


def beat_time(k):
    return config.BEAT0 + k * config.BEAT


def beat_phase(t):
    x = (t - config.BEAT0) / config.BEAT
    return x - math.floor(x)


def nearest_beat(t):
    k = round((t - config.BEAT0) / config.BEAT)
    return beat_time(k)


def beat_pulse(t, decay=0.18, every=1, offset=0):
    """Exponential pulse on every `every`-th beat (in beats from BEAT0)."""
    if t < config.BEAT0:
        return 0.0
    x = (t - config.BEAT0) / config.BEAT - offset
    k = math.floor(x / every) * every
    dt = (x - k) * config.BEAT
    return math.exp(-dt / decay)


def kick(t):
    """Low-band transient strength (0..~1.2)."""
    return env("low_s", t)


def music_on(t):
    return 1.0 if t < config.MUSIC_END else 0.0
