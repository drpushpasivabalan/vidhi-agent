"""Video tamper / face-swap cues (training-free).

Cues
----
region_sharpness_inconsistency : a swapped face (or pasted overlay) is softer than
        the rest of the frame; edge sharpness per block is averaged over many frames
        so a *persistent* soft region stands out while per-frame variation cancels.
temporal_discontinuity : inserted/removed segments cause an abrupt jump in
        frame-to-frame change that a single continuous take does not have.
audio_track : the soundtrack analysed with the audio detector (splices, synthetic voice).
"""
from __future__ import annotations

import subprocess

import cv2
import numpy as np

from .common import fuse, logistic, region_anomaly, robust_z, verdict

WEIGHTS = {"region_sharpness_inconsistency": 1.0, "temporal_discontinuity": 0.8, "audio_track": 0.8}
BS = 16


def _read_frames(path, max_side=640):
    cap = cv2.VideoCapture(path)
    fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
    frames = []
    while True:
        ok, f = cap.read()
        if not ok:
            break
        g = cv2.cvtColor(f, cv2.COLOR_BGR2GRAY).astype(np.float32)
        if max(g.shape) > max_side:
            s = max_side / max(g.shape)
            g = cv2.resize(g, None, fx=s, fy=s, interpolation=cv2.INTER_AREA)
        frames.append(g)
    cap.release()
    return frames, fps


def region_sharpness_cue(frames, step=3):
    """Persistent local loss of edge sharpness (face-swap / pasted-overlay cue).

    Face-swap generators typically work at a lower resolution and are blended back
    with smoothing, so edges inside the swapped region (eyes, mouth, hairline) are
    softer than edges elsewhere in the same frame. Sharpness is measured as
    mean|Laplacian| / mean|gradient| - a contrast-independent edge-width proxy -
    only in edge-bearing blocks, so flat areas (walls, clothing) never enter. Codec
    smoothing affects the whole frame alike, which the per-clip robust z removes.
    (Sensor-noise analysis is not used here: H.264/H.265 erase most of it.)
    """
    acc = cnt = None
    sel = frames[::step]
    for g in sel:
        gx = cv2.Sobel(g, cv2.CV_32F, 1, 0)
        gy = cv2.Sobel(g, cv2.CV_32F, 0, 1)
        G = np.hypot(gx, gy)
        L = np.abs(cv2.Laplacian(g, cv2.CV_32F, ksize=3))
        h, w = g.shape
        hb, wb = h // BS, w // BS
        Gb = G[: hb * BS, : wb * BS].reshape(hb, BS, wb, BS).mean((1, 3))
        Lb = L[: hb * BS, : wb * BS].reshape(hb, BS, wb, BS).mean((1, 3))
        ok = Gb > max(np.percentile(Gb, 60), 20)
        if acc is None:
            acc, cnt = np.zeros((hb, wb)), np.zeros((hb, wb))
        acc[ok] += np.log(Lb[ok] / Gb[ok])
        cnt[ok] += 1
    valid = cnt >= max(2, 0.3 * len(sel))
    if valid.sum() < 10:
        return {"p": 0.0, "stat": 0.0, "note": "too few edge regions"}
    m = np.where(valid, acc / np.maximum(cnt, 1), 0)
    z = np.zeros_like(m)
    z[valid] = robust_z(m[valid], min_scale=0.05)
    strength, area, bbox = region_anomaly(np.minimum(z, 0), 2.5, valid)  # only *softer* regions
    p = logistic(strength, 2.0, 0.4)
    cue = {"p": p, "stat": round(strength, 3), "area_frac": round(area, 4)}
    if bbox:
        cue["bbox_xyxy"] = [bbox[1] * BS, bbox[0] * BS, (bbox[3] + 1) * BS, (bbox[2] + 1) * BS]
    return cue


def temporal_cue(frames, fps):
    small = [cv2.resize(f, (160, 120), interpolation=cv2.INTER_AREA) for f in frames]
    d = np.array([np.mean(np.abs(small[i + 1] - small[i])) for i in range(len(small) - 1)])
    if len(d) < 10:
        return {"p": 0.0, "stat": 0.0, "note": "clip too short"}
    z = robust_z(np.log(d + 0.5), min_scale=0.05)
    k = np.argsort(z)[::-1][:2]
    stat = float(z[k[0]])
    p = logistic(stat, 8.0, 1.2)
    return {"p": p, "stat": round(stat, 2), "jumps_at_s": sorted(round(float(i + 1) / fps, 2) for i in k if z[i] > 6)}


def _has_audio(path):
    r = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "a", "-show_entries", "stream=index",
                        "-of", "csv=p=0", path], capture_output=True, text=True)
    return bool(r.stdout.strip())


def analyze_video(path: str) -> dict:
    from .audio import analyze_audio

    frames, fps = _read_frames(path)
    if len(frames) < 5:
        raise ValueError("could not decode enough frames")
    cues = {
        "region_sharpness_inconsistency": region_sharpness_cue(frames),
        "temporal_discontinuity": temporal_cue(frames, fps),
    }
    if _has_audio(path):
        a = analyze_audio(path)
        cues["audio_track"] = {"p": a["confidence_manipulated"], "stat": a["verdict"],
                               "top_cue": max(a["cues"].items(), key=lambda kv: kv[1]["p"])[0]}
    score = fuse(cues, WEIGHTS)
    return {"modality": "video", "frames": len(frames), "fps": round(fps, 2),
            "confidence_manipulated": round(score, 4), "verdict": verdict(score),
            "cues": {k: {kk: (round(vv, 4) if isinstance(vv, float) else vv) for kk, vv in v.items()} for k, v in cues.items()}}
