"""Audio tamper / synthetic-voice cues (training-free).

Cues
----
noise_floor_jump  : every real recording carries a room/line noise floor. Inserting
                    audio from another take changes that floor (level and colour)
                    abruptly. We track the floor in the pauses and look for steps.
splice_click      : hard cuts leave a sample-level discontinuity (a click) that
                    speech itself almost never produces.
digital_silence   : cloned / TTS voices are generated clean: pauses fall to near
                    digital zero, which a microphone or phone line never does.
pitch_regularity  : human voicing has cycle-to-cycle jitter; many voice-cloning
                    pipelines produce an unnaturally smooth pitch track.
bandwidth         : energy stops at 4 kHz although the file is 16 kHz+ (8 kHz vocoder
                    or phone). Weak on its own: genuine phone calls look the same.
"""
from __future__ import annotations

import subprocess
import tempfile

import numpy as np
from scipy import ndimage, signal
from scipy.io import wavfile

from .common import fuse, logistic, verdict

WEIGHTS = {"noise_floor_jump": 1.0, "splice_click": 0.7, "digital_silence": 0.9,
           "pitch_regularity": 0.6, "bandwidth": 0.35}
FRAME, HOP = 0.032, 0.010


def load_audio(path: str, sr: int = 16000):
    """Load any audio (or a video's audio track) as mono float at `sr` via ffmpeg."""
    if path.lower().endswith(".wav"):
        fs, x = wavfile.read(path)
        x = x.astype(np.float64)
        if x.ndim > 1:
            x = x.mean(1)
        x /= 32768.0 if np.abs(x).max() > 2 else 1.0
        if fs != sr:
            x = signal.resample_poly(x, sr, fs)
        return x, sr
    with tempfile.NamedTemporaryFile(suffix=".wav") as tf:
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", path, "-ac", "1", "-ar", str(sr), "-vn", tf.name], check=True)
        return load_audio(tf.name, sr)


def _frames(x, sr):
    n, h = int(FRAME * sr), int(HOP * sr)
    idx = np.arange(0, len(x) - n, h)
    win = np.hanning(n)
    fr = np.stack([x[i:i + n] * win for i in idx])
    return fr, idx / sr


def _pauses(rms_db, min_len=6, flat_db=4.0):
    """Runs of >= min_len frames that are quiet AND stationary (level spread < flat_db).

    Stationarity rejects reverb tails (which decay) so only true room/line tone is kept.
    """
    # quiet relative to the *local* speech level, so a louder-background insert still
    # exposes its pauses
    local = ndimage.median_filter(rms_db, int(1.5 / HOP), mode="nearest")
    quiet = rms_db < local - 10
    out, i, n = [], 0, len(rms_db)
    while i < n:
        if not quiet[i]:
            i += 1
            continue
        j = i
        while j < n and quiet[j]:
            j += 1
        # split the quiet run into stationary sub-runs
        k = i
        while k < j:
            m = k + 1
            while m < j and rms_db[k:m + 1].max() - rms_db[k:m + 1].min() < flat_db:
                m += 1
            if m - k >= min_len:
                out.append((k, m))
            k = m
        i = j
    return out


def noise_floor_cue(spec_db, rms_db, times):
    """Room/line tone measured in true pauses; look for pauses whose tone differs.

    In one continuous take every pause has the same background (level and colour).
    An insert from another take brings its own background, so a run of consecutive
    pauses departs from the clip's typical floor.
    """
    bands = [(5, 25), (25, 70), (70, 120), (120, 220)]  # FFT bins (31.25 Hz): ~0.15-0.8, 0.8-2.2, 2.2-3.75, 3.75-6.9 kHz
    feat = np.stack([spec_db[:, a:b].mean(1) for a, b in bands], 1)
    ps = _pauses(rms_db)
    if len(ps) < 3:
        return {"p": 0.0, "stat": 0.0, "note": "too few pauses to measure background"}
    fl = np.stack([np.median(feat[a:b], 0) for a, b in ps])
    dev = fl - np.median(fl, 0)
    mag = np.max(np.abs(dev), 1) * np.sign(dev[np.arange(len(dev)), np.argmax(np.abs(dev), 1)])
    lens = np.array([b - a for a, b in ps])
    best, at = 0.0, None
    for i in range(len(ps)):
        cand = abs(mag[i]) if lens[i] >= 20 else 0.0  # one long pause is enough evidence
        if i + 1 < len(ps) and np.sign(mag[i]) == np.sign(mag[i + 1]):
            cand = max(cand, min(abs(mag[i]), abs(mag[i + 1])))
        if cand > best:
            best, at = cand, float(times[ps[i][0]])
    p = logistic(best, 6.0, 1.0)
    return {"p": p, "stat": round(float(best), 2), "unit": "dB background change between pauses",
            "at_s": None if at is None else round(at, 2), "n_pauses": len(ps)}


def click_cue(x, sr):
    d2 = np.diff(x, 2)
    loc = np.sqrt(ndimage.uniform_filter1d(d2 ** 2, int(0.02 * sr)) + 1e-12)
    z = np.abs(d2) / loc
    z[loc < 10 ** (-70 / 20)] = 0  # ignore near-silence, where the ratio is meaningless
    edge = int(0.05 * sr)  # stream start/end (codec priming, truncation) is not a splice
    z[:edge] = 0
    z[-edge:] = 0
    # an isolated spike well above its 20 ms neighbourhood
    k = int(np.argmax(z))
    stat = float(z[k])
    p = logistic(stat, 7.5, 0.6)
    return {"p": p, "stat": round(stat, 2), "at_s": round(k / sr, 3)}


def silence_cue(rms_db):
    floor = float(np.percentile(rms_db, 5))
    p = logistic(-floor, 78.0, 3.0)  # quieter than about -78 dBFS -> generated
    return {"p": p, "stat": round(floor, 1), "unit": "dBFS 5th-pct frame level"}


def pitch_cue(fr, rms_db, sr):
    voiced = rms_db > np.percentile(rms_db, 60)
    f0 = np.full(len(fr), np.nan)
    lo, hi = int(sr / 400), int(sr / 70)
    for i in np.where(voiced)[0]:
        f = fr[i] - fr[i].mean()
        ac = np.correlate(f, f, "full")[len(f) - 1:]
        if ac[0] <= 0:
            continue
        seg = ac[lo:hi]
        k = int(np.argmax(seg)) + lo
        if ac[k] / ac[0] < 0.45 or k <= lo or k >= hi - 1:
            continue
        a, b, c = ac[k - 1], ac[k], ac[k + 1]  # parabolic refinement -> sub-sample period
        den = a - 2 * b + c
        kk = k + (0.5 * (a - c) / den if den != 0 else 0)
        f0[i] = sr / kk
    # micro-variation: relative deviation of consecutive voiced frames from a smooth trend
    runs, cur = [], []
    for v in f0:
        if np.isnan(v):
            if len(cur) >= 5:
                runs.append(np.array(cur))
            cur = []
        else:
            cur.append(v)
    if len(cur) >= 5:
        runs.append(np.array(cur))
    dev = []
    for r in runs:
        tr = ndimage.median_filter(r, 5, mode="nearest")
        dev += list(np.abs(np.diff(r / tr)))
    if len(dev) < 20:
        return {"p": 0.0, "stat": None, "note": "too little voiced speech"}
    jit = float(np.median(dev) * 100)
    p = logistic(-jit, -0.30, 0.04)  # below ~0.3 % frame-to-frame -> over-regular
    return {"p": p, "stat": round(jit, 3), "unit": "% median F0 micro-variation"}


def bandwidth_cue(spec_db, rms_db, sr):
    if sr < 12000:
        return {"p": 0.0, "stat": None, "note": "file itself is narrow-band"}
    voiced = rms_db > np.percentile(rms_db, 60)
    p_lin = 10 ** (spec_db[voiced] / 10)
    nb = p_lin.shape[1]
    cut = int(4300 / (sr / 2) * nb)
    frac = float(p_lin[:, cut:].sum() / (p_lin.sum() + 1e-20))
    stat = 10 * np.log10(frac + 1e-12)
    p = logistic(-stat, 40.0, 3.0)  # < -40 dB of energy above 4.3 kHz -> band-limited
    return {"p": p, "stat": round(stat, 1), "unit": "dB energy above 4.3 kHz"}


def analyze_audio(path_or_array, sr: int = 16000) -> dict:
    if isinstance(path_or_array, str):
        x, sr = load_audio(path_or_array, sr)
    else:
        x = np.asarray(path_or_array, np.float64)
        if np.abs(x).max() > 2:
            x = x / 32768.0
    fr, times = _frames(x, sr)
    spec = np.abs(np.fft.rfft(fr, 512, axis=1)) ** 2
    spec_db = 10 * np.log10(spec + 1e-14)
    rms_db = 10 * np.log10(np.mean(fr ** 2, 1) + 1e-14)

    cues = {
        "noise_floor_jump": noise_floor_cue(spec_db, rms_db, times),
        "splice_click": click_cue(x, sr),
        "digital_silence": silence_cue(rms_db),
        "pitch_regularity": pitch_cue(fr, rms_db, sr),
        "bandwidth": bandwidth_cue(spec_db, rms_db, sr),
    }
    # a digitally silent clip has no real floor to compare; don't double count
    if cues["digital_silence"]["p"] > 0.5:
        cues["noise_floor_jump"]["p"] *= 0.3
    score = fuse(cues, WEIGHTS)
    return {"modality": "audio", "duration_s": round(len(x) / sr, 2),
            "confidence_manipulated": round(score, 4), "verdict": verdict(score),
            "cues": {k: {kk: (round(vv, 4) if isinstance(vv, float) else vv) for kk, vv in v.items()} for k, v in cues.items()}}
