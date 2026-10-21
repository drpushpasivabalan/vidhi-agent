"""Synthetic 'official video statement' clips (H.264 + AAC via ffmpeg).

A presenter (stylised head with blinking eyes and a talking mouth) in front of an
office backdrop, filmed by a noisy camera. Manipulations:
  face_swap : the face region is replaced every frame by a re-rendered face that is
              smoother (generator-like), carries no camera noise, has a slightly
              different tone and a feathered, slightly jittering blend mask
  splice    : a 1-1.5 s segment from another take (different framing/lighting and a
              different audio background) is inserted mid-clip
Everything is fictitious and stylised; no real person is depicted.
"""
from __future__ import annotations

import os
import subprocess
import tempfile

import cv2
import numpy as np
from scipy.io import wavfile

from . import make_audio as MA

W, H, FPS, DUR = 480, 360, 25, 4.0


def _backdrop(rng, shift=0, light=1.0):
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    base = 150 + 25 * np.sin(xx / 37 + rng.uniform(0, 6)) * np.cos(yy / 53)
    img = np.stack([base * 0.9, base * 0.95, base * 1.05], -1)
    for k in range(6):  # bookshelf / panels
        x0 = int(20 + k * 75 + shift) % W
        cv2.rectangle(img, (x0, 30), (x0 + 50, 150), tuple(float(v) for v in rng.uniform(60, 200, 3)), -1)
    cv2.rectangle(img, (0, 290), (W, H), (90, 70, 55), -1)  # desk
    tex = cv2.GaussianBlur(rng.normal(0, 12, (H, W)).astype(np.float32), (0, 0), 1.2)
    return np.clip((img + tex[..., None]) * light, 0, 255)


def _face(img, cx, cy, mouth, blink, tone=(180, 140, 120), smooth=False):
    out = img.copy()
    cv2.rectangle(out, (cx - 80, cy + 60), (cx + 80, H), (60, 60, 90), -1)  # torso/suit
    cv2.ellipse(out, (cx, cy), (52, 68), 0, 0, 360, tone, -1)
    cv2.ellipse(out, (cx, cy - 55), (54, 25), 0, 180, 360, (40, 30, 25), -1)  # hair
    eh = 2 if blink else 7
    for dx in (-20, 20):
        cv2.ellipse(out, (cx + dx, cy - 12), (9, eh), 0, 0, 360, (40, 30, 30), -1)
    cv2.ellipse(out, (cx, cy + 30), (18, 3 + int(10 * mouth)), 0, 0, 360, (90, 40, 50), -1)
    cv2.line(out, (cx, cy - 5), (cx - 4, cy + 12), (150, 110, 95), 2)
    return out


def _face_mask(cx, cy, feather=7):
    m = np.zeros((H, W), np.float32)
    cv2.ellipse(m, (cx, cy + 4), (50, 64), 0, 0, 360, 1.0, -1)
    return cv2.GaussianBlur(m, (0, 0), feather)[..., None]


def _envelope(x, n_frames):
    sr = MA.SR
    hop = int(sr / FPS)
    e = np.array([np.sqrt(np.mean(x[i * hop:(i + 1) * hop].astype(float) ** 2)) for i in range(n_frames)])
    return np.clip(e / (e.max() + 1e-9) * 1.4, 0, 1)


def render(rng, kind="authentic", out_path="clip.mp4", crf=None):
    n = int(DUR * FPS)
    sigma = rng.uniform(3, 6)
    crf = crf or int(rng.integers(18, 25))
    audio_rng = np.random.default_rng(int(rng.integers(2**31)))
    x = MA.speech(audio_rng, dur=DUR, noise_dbfs=rng.uniform(-55, -42), noise_color="pink")
    bg = _backdrop(rng)
    env = _envelope(x, n)
    blinks = set(int(v) for v in rng.integers(0, n, 3))
    meta = {"kind": kind, "crf": crf, "noise_sigma": round(sigma, 2)}
    frames = []
    seg = None
    if kind == "splice":
        a0 = int(rng.uniform(1.2, 2.0) * FPS)
        seg = (a0, a0 + int(rng.uniform(1.0, 1.5) * FPS))
        bg2 = _backdrop(rng, shift=rng.uniform(15, 40), light=rng.uniform(0.85, 1.15))
        x2 = MA.speech(audio_rng, dur=DUR, noise_dbfs=rng.uniform(-60, -36), noise_color="white")
        s0, s1 = int(seg[0] / FPS * MA.SR), int(seg[1] / FPS * MA.SR)
        x = np.concatenate([x[:s0], x2[s0:s1], x[s1:]])
        meta["splice_s"] = [round(seg[0] / FPS, 2), round(seg[1] / FPS, 2)]
    tone2 = tuple(float(v) for v in np.array((180, 140, 120)) * rng.uniform(0.92, 1.08, 3))
    for i in range(n):
        insert = seg is not None and seg[0] <= i < seg[1]
        cx = int(W / 2 + 6 * np.sin(i / 17.0) + (18 if insert else 0))
        cy = int(150 + 3 * np.sin(i / 11.0))
        f = _face(bg2 if insert else bg, cx, cy, env[i], i in blinks)
        if kind == "face_swap":
            jx, jy = rng.integers(-2, 3, 2)
            fake = _face(bg, cx + jx, cy + jy, env[max(i - 1, 0)], i in blinks, tone=tone2)
            fake = cv2.GaussianBlur(fake.astype(np.float32), (0, 0), 1.6)  # generator smoothness
            m = _face_mask(cx + jx, cy + jy)
            noise = np.random.default_rng(i).normal(0, sigma, f.shape)
            noise *= (1 - m)  # swapped face carries no sensor noise
            f = f * (1 - m) + fake * m + noise
        else:
            f = f + rng.normal(0, sigma, f.shape)
        frames.append(np.clip(f, 0, 255).astype(np.uint8))
    with tempfile.TemporaryDirectory() as td:
        raw = os.path.join(td, "v.raw")
        np.stack(frames).tofile(raw)
        wav = os.path.join(td, "a.wav")
        wavfile.write(wav, MA.SR, MA.to_int16(x))
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                        "-r", str(FPS), "-i", raw, "-i", wav, "-c:v", "libx264", "-crf", str(crf),
                        "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "96k", "-shortest", out_path], check=True)
    return out_path, meta
