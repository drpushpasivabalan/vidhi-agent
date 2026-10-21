"""Synthetic speech-like 'official call' audio: authentic recordings and manipulations.

There is no TTS engine in this sandbox, so speech is modelled with a source-filter
synthesiser (glottal pulses with natural jitter -> vowel formant resonators ->
syllable envelopes -> room reverb -> microphone/background noise). That is enough
to exercise the *forensic* cues; it is not a substitute for testing on real voices.

authentic        : one continuous take; 1/3 are telephone-band (300-3400 Hz) calls
splice           : 1-2.5 s inserted from a different take (other speaker, other room/noise)
synthetic_voice  : 'cloned' voice - over-regular pitch, no room tone (digital silence),
                   half of them band-limited by an 8 kHz vocoder
"""
from __future__ import annotations

import numpy as np
from scipy import signal

SR = 16000
VOWELS = [(730, 1090, 2440), (270, 2290, 3010), (300, 870, 2240), (530, 1840, 2480),
          (640, 1190, 2390), (490, 1350, 1690), (660, 1720, 2410)]


def _resonator(x, f, bw, sr=SR):
    r = np.exp(-np.pi * bw / sr)
    a = [1, -2 * r * np.cos(2 * np.pi * f / sr), r * r]
    return signal.lfilter([1 - r], a, x)


def _pink(n, rng):
    w = rng.normal(size=n)
    b, a = [0.049922035, -0.095993537, 0.050612699, -0.004408786], [1, -2.494956002, 2.017265875, -0.522189400]
    return signal.lfilter(b, a, w)


def speech(rng: np.random.Generator, dur=6.0, f0=None, jitter=0.012, room=True,
           noise_dbfs=None, noise_color="pink"):
    n = int(dur * SR)
    f0 = f0 or rng.uniform(105, 220)
    out = np.zeros(n)
    t = 0
    while t < n - SR // 5:
        syl = int(rng.uniform(0.12, 0.26) * SR)
        syl = min(syl, n - t)
        # F0 contour: declination + intonation, pulse-by-pulse jitter
        pos, src = 0, np.zeros(syl)
        base = f0 * (1 - 0.15 * t / n) * (1 + 0.08 * np.sin(2 * np.pi * rng.uniform(0.5, 2) * t / SR + rng.uniform(0, 6)))
        while pos < syl:
            per = SR / (base * (1 + rng.normal(0, jitter)))
            src[int(pos)] = 1.0 * (1 + rng.normal(0, 0.05))
            pos += per
        src = signal.lfilter([1], [1, -0.97], src) - signal.lfilter([1], [1, -0.9], src)  # glottal-ish shape
        src += 0.02 * rng.normal(size=syl)  # aspiration
        F = VOWELS[rng.integers(len(VOWELS))]
        y = sum(_resonator(src, f * rng.uniform(0.93, 1.07), 60 + 30 * k) * g for k, (f, g) in enumerate(zip(F, (1.0, 0.6, 0.3))))
        env = np.sin(np.linspace(0, np.pi, syl)) ** 0.7
        out[t:t + syl] += y * env
        if rng.random() < 0.35 and t > SR // 10:  # fricative (s/sh/f) before the vowel
            fl = int(rng.uniform(0.05, 0.11) * SR)
            lo_f = rng.uniform(2500, 4500)
            sos = signal.butter(4, [lo_f / (SR / 2), 7600 / (SR / 2)], "band", output="sos")
            fr = signal.sosfilt(sos, rng.normal(size=fl)) * np.hanning(fl) * rng.uniform(0.15, 0.4)
            a0 = max(0, t - fl // 2)
            out[a0:a0 + fl] += fr[: len(out[a0:a0 + fl])]
        t += syl + int((rng.uniform(0.04, 0.12) if rng.random() < 0.75 else rng.uniform(0.3, 0.6)) * SR)
    out /= np.abs(out).max() + 1e-9
    if room:
        ir_len = int(rng.uniform(0.15, 0.4) * SR)
        ir = rng.normal(size=ir_len) * np.exp(-6.9 * np.arange(ir_len) / ir_len)
        ir[0] = 1 / 0.25
        out = signal.fftconvolve(out, ir * 0.25, mode="full")[:n]
        out /= np.abs(out).max() + 1e-9
    out *= 10 ** (-3 / 20)
    if noise_dbfs is not None:
        nz = _pink(n, rng) if noise_color == "pink" else rng.normal(size=n)
        if noise_color == "hum":
            nz = rng.normal(size=n) * 0.5 + np.sin(2 * np.pi * 50 * np.arange(n) / SR) * 2
        nz /= np.sqrt(np.mean(nz ** 2))
        out += nz * 10 ** (noise_dbfs / 20)
    b, a = signal.butter(2, 80 / (SR / 2), "high")
    return signal.lfilter(b, a, out)


def phone_band(x):
    sos = signal.butter(6, [300 / (SR / 2), 3400 / (SR / 2)], "band", output="sos")
    return signal.sosfilt(sos, x)


def to_int16(x):
    x = x / max(1.0, np.abs(x).max() / 0.98)
    return (x * 32767).astype(np.int16)


def authentic(rng):
    x = speech(rng, noise_dbfs=rng.uniform(-58, -40), noise_color=rng.choice(["pink", "white", "hum"]))
    kind = "authentic"
    if rng.random() < 1 / 3:
        x = phone_band(x)
        kind = "authentic_phone"
    return to_int16(x), {"kind": kind}


def splice(rng):
    a = speech(rng, noise_dbfs=rng.uniform(-58, -45), noise_color="pink")
    nd = rng.uniform(-60, -36)
    b = speech(rng, f0=rng.uniform(105, 220), noise_dbfs=nd, noise_color=rng.choice(["white", "hum"]),
               room=bool(rng.random() < 0.5))
    L = int(rng.uniform(1.0, 2.5) * SR)
    t1 = int(rng.uniform(1.5, 3.0) * SR)
    s0 = int(rng.uniform(0.5, 3.0) * SR)
    ins = b[s0:s0 + L] * rng.uniform(0.7, 1.3)
    xf = rng.random() < 0.5  # half the edits use a 5 ms crossfade (no click)
    if xf:
        k = int(0.005 * SR)
        ramp = np.linspace(0, 1, k)
        ins[:k] = ins[:k] * ramp + a[t1:t1 + k] * (1 - ramp)
        ins[-k:] = ins[-k:] * (1 - ramp) + a[t1 + L - k:t1 + L] * ramp
    x = np.concatenate([a[:t1], ins, a[t1 + L:]])[: len(a)]
    return to_int16(x), {"kind": "splice", "splice_s": [round(t1 / SR, 2), round((t1 + L) / SR, 2)], "crossfade": xf}


def synthetic_voice(rng):
    x = speech(rng, jitter=0.0015, room=False, noise_dbfs=None)
    meta = {"kind": "synthetic_voice", "vocoder_8k": False}
    if rng.random() < 0.5:
        x8 = signal.resample_poly(x, 1, 2)
        x = signal.resample_poly(x8, 2, 1)
        meta["vocoder_8k"] = True
    x += rng.normal(size=len(x)) * 10 ** (-96 / 20)  # dither only
    return to_int16(x), meta
