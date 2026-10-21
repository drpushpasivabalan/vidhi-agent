"""Image tamper cues (training-free).

Cues
----
noise_inconsistency : pasted/edited regions rarely share the sensor/scan noise of the
                      rest of the image. Block-wise robust noise sigma, then look for a
                      coherent cluster of blocks whose noise deviates.
compression_inconsistency : JPEG 8x8 grid analysis; a region with a different
                      compression history (pasted from another JPEG, often off-grid)
                      carries grid energy at a shifted phase or a different strength.
copy_move           : duplicated regions (a cloned seal, signature or stamp) found by
                      self-matching ORB keypoints that share one displacement vector.
metadata            : editing-software fingerprints in EXIF (weak, easily stripped).
"""
from __future__ import annotations

from collections import Counter

import cv2
import numpy as np
from PIL import Image, ExifTags
from scipy import ndimage

from .common import block_reduce, fuse, logistic, region_anomaly, robust_z, verdict

BS = 32  # analysis block size (px)
WEIGHTS = {"noise_inconsistency": 1.0, "compression_inconsistency": 0.8, "copy_move": 1.0, "metadata": 0.5}
EDIT_SOFTWARE = ("photoshop", "gimp", "canva", "picsart", "snapseed", "lightroom", "pixlr", "affinity", "faceapp")


def _load(path_or_img) -> Image.Image:
    img = path_or_img if isinstance(path_or_img, Image.Image) else Image.open(path_or_img)
    return img


def _flat_mask(gray: np.ndarray) -> np.ndarray:
    """Pixels away from strong edges (text strokes, object borders) where noise is measurable."""
    # smooth first so that *noise* does not count as structure (a noisier pasted
    # patch must stay measurable), then dilate so stroke borders are excluded
    s = ndimage.gaussian_filter(gray, 2.0)
    g = np.hypot(ndimage.sobel(s, 0), ndimage.sobel(s, 1))
    g = ndimage.maximum_filter(g, 5)
    return g < max(np.percentile(g, 55), 8.0)


def noise_cue(gray: np.ndarray, flat: np.ndarray):
    # Immerkaer fast noise estimator: Laplacian-difference kernel cancels smooth content
    k = np.array([[1, -2, 1], [-2, 4, -2], [1, -2, 1]], np.float32)
    resid = np.abs(ndimage.convolve(gray, k, mode="reflect"))
    h, w = gray.shape
    hb, wb = h // BS, w // BS
    sig = np.zeros((hb, wb))
    valid = np.zeros((hb, wb), bool)
    for i in range(hb):
        for j in range(wb):
            r = resid[i * BS:(i + 1) * BS, j * BS:(j + 1) * BS]
            m = flat[i * BS:(i + 1) * BS, j * BS:(j + 1) * BS]
            if m.mean() > 0.3:
                sig[i, j] = np.sqrt(np.pi / 2) * r[m].mean() / 6.0 + 0.1
                valid[i, j] = True
    if valid.sum() < 8:
        return {"p": 0.0, "stat": 0.0, "note": "too little flat area"}, np.zeros((hb, wb))
    ls = np.log(np.where(valid, sig, 1.0))
    z = np.zeros_like(ls)
    z[valid] = robust_z(ls[valid], min_scale=0.08)
    z[~valid] = 0
    strength, area, bbox = region_anomaly(z, 2.5, valid)
    p = logistic(strength, 1.6, 0.35)
    cue = {"p": p, "stat": round(strength, 3), "area_frac": round(area, 4)}
    if bbox:
        cue["bbox_xyxy"] = [bbox[1] * BS, bbox[0] * BS, (bbox[3] + 1) * BS, (bbox[2] + 1) * BS]
    return cue, z


def _phase_profile(d: np.ndarray, m: np.ndarray, axis: int):
    """Per-block mean absolute pixel difference at each of the 8 JPEG-grid phases."""
    h, w = d.shape
    hb, wb = h // BS, w // BS
    idx = np.arange(d.shape[axis]) % 8
    prof = np.zeros((hb, wb, 8))
    cnt = np.zeros((hb, wb, 8))
    dm = d * m
    for ph in range(8):
        sel = (idx == ph)
        mask_ph = np.zeros_like(d, bool)
        if axis == 1:
            mask_ph[:, sel] = True
        else:
            mask_ph[sel, :] = True
        prof[..., ph] = block_reduce(np.where(mask_ph, dm, 0), BS, np.sum)[:hb, :wb]
        cnt[..., ph] = block_reduce((mask_ph & m).astype(np.float32), BS, np.sum)[:hb, :wb]
    return prof / (cnt + 1e-6), cnt.sum(-1)


def grid_cue(gray: np.ndarray, flat: np.ndarray):
    """JPEG block-grid consistency.

    The last JPEG save leaves an 8x8 grid (phase 7) everywhere. A region carrying a
    *different* compression history - pasted from another JPEG, often at an offset -
    shows grid energy at a shifted phase or a different on-grid strength.
    """
    g = gray[: gray.shape[0] // BS * BS, : gray.shape[1] // BS * BS]
    f = ~ndimage.maximum_filter(~flat, 9)[: g.shape[0], : g.shape[1]]  # stay >= 4 px clear of any structure
    feats = []
    valid = None
    for axis in (1, 0):
        d = np.abs(np.diff(g, axis=axis))
        m = (f[:, 1:] & f[:, :-1]) if axis == 1 else (f[1:, :] & f[:-1, :])
        pad = [(0, 0), (0, 1)] if axis == 1 else [(0, 1), (0, 0)]
        d, m = np.pad(d, pad), np.pad(m, pad)
        prof, n = _phase_profile(d, m, axis)
        base = np.median(prof, axis=-1) + 0.05
        on = np.log(prof[..., 7] / base + 0.05)
        off = np.log(np.delete(prof, 7, axis=-1).max(-1) / base + 0.05)
        feats += [on, off]
        v = n > 0.3 * BS * BS
        valid = v if valid is None else (valid & v)
    if valid.sum() < 8:
        return {"p": 0.0, "stat": 0.0, "note": "too little flat area"}, np.zeros_like(feats[0])
    zs = []
    for ft in feats:
        z = np.zeros_like(ft)
        z[valid] = robust_z(ft[valid], min_scale=0.1)
        zs.append(z)
    z = np.max(np.abs(np.stack(zs)), axis=0) * valid
    strength, area, bbox = region_anomaly(z, 4.0, valid)
    p = logistic(strength, 2.0, 0.4)
    cue = {"p": p, "stat": round(strength, 3), "area_frac": round(area, 4)}
    if bbox:
        cue["bbox_xyxy"] = [bbox[1] * BS, bbox[0] * BS, (bbox[3] + 1) * BS, (bbox[2] + 1) * BS]
    return cue, z


def copy_move_cue(gray: np.ndarray):
    g8 = np.clip(gray, 0, 255).astype(np.uint8)
    orb = cv2.ORB_create(nfeatures=4000, fastThreshold=10)
    kps, des = orb.detectAndCompute(g8, None)
    if des is None or len(kps) < 20:
        return {"p": 0.0, "stat": 0, "note": "too few keypoints"}
    bf = cv2.BFMatcher(cv2.NORM_HAMMING)
    matches = bf.knnMatch(des, des, k=3)
    offs, pairs = [], []
    for ms in matches:
        for m in ms[1:]:  # ms[0] is the keypoint matched to itself
            if m.distance > 32:
                continue
            a, b = np.array(kps[m.queryIdx].pt), np.array(kps[m.trainIdx].pt)
            d = b - a
            if np.hypot(*d) < 40 or abs(d[1]) < 8:  # same text line: repeated glyphs, not a clone
                continue
            if d[0] < 0 or (d[0] == 0 and d[1] < 0):  # canonical direction, count each pair once
                d, a, b = -d, b, a
            offs.append((int(round(d[0] / 6)), int(round(d[1] / 6))))
            pairs.append((a, b))
    if not offs:
        return {"p": 0.0, "stat": 0}
    # merge neighbouring offset bins (quantisation)
    cnt = Counter(offs)
    best, best_n = None, 0
    for o in cnt:
        n = sum(cnt.get((o[0] + dx, o[1] + dy), 0) for dx in (-1, 0, 1) for dy in (-1, 0, 1))
        if n > best_n:
            best, best_n = o, n
    # spatial spread of the supporting keypoints: a real cloned patch is compact but non-trivial
    sup = [p for p, o in zip(pairs, offs) if abs(o[0] - best[0]) <= 1 and abs(o[1] - best[1]) <= 1]
    src = np.array([p[0] for p in sup])
    dst = np.array([p[1] for p in sup])
    p = logistic(best_n, 105, 12)
    cue = {"p": p, "stat": int(best_n), "offset_px": [best[0] * 6, best[1] * 6]}
    if best_n >= 10:
        cue["source_xyxy"] = [int(v) for v in (*src.min(0), *src.max(0))]
        cue["clone_xyxy"] = [int(v) for v in (*dst.min(0), *dst.max(0))]
    return cue


def metadata_cue(img: Image.Image):
    try:
        exif = img.getexif()
    except Exception:
        exif = {}
    tags = {ExifTags.TAGS.get(k, k): str(v) for k, v in dict(exif).items()} if exif else {}
    sw = (tags.get("Software", "") + " " + tags.get("ProcessingSoftware", "")).lower()
    hit = [s for s in EDIT_SOFTWARE if s in sw]
    return {"p": 0.6 if hit else 0.0, "stat": hit or None, "software": tags.get("Software")}


def analyze_image(path_or_img, heatmap_path: str | None = None, max_side: int = 1600) -> dict:
    img = _load(path_or_img)
    if max(img.size) > max_side:  # keep it lightweight; note: resizing weakens noise cues
        s = max_side / max(img.size)
        img = img.resize((int(img.width * s), int(img.height * s)), Image.BICUBIC)
    gray = np.asarray(img.convert("L"), np.float32)
    flat = _flat_mask(gray)

    n_cue, nz = noise_cue(gray, flat)
    e_cue, ez = grid_cue(gray, flat)
    cues = {
        "noise_inconsistency": n_cue,
        "compression_inconsistency": e_cue,
        "copy_move": copy_move_cue(gray),
        "metadata": metadata_cue(img),
    }
    score = fuse(cues, WEIGHTS)
    out = {"modality": "image", "confidence_manipulated": round(score, 4), "verdict": verdict(score),
           "cues": {k: {kk: (round(vv, 4) if isinstance(vv, float) else vv) for kk, vv in v.items()} for k, v in cues.items()}}
    if heatmap_path:
        _save_heatmap(img, nz, ez, cues, heatmap_path)
        out["heatmap"] = heatmap_path
    return out


def _save_heatmap(img, nz, ez, cues, path):
    """Overlay only genuinely anomalous blocks (|z| >= 2.5) plus boxes for firing cues."""
    rgb = np.asarray(img.convert("RGB")).astype(np.float32)
    h, w = rgb.shape[:2]
    z = np.maximum(np.abs(nz), np.abs(ez))
    a = np.clip((z - 2.5) / 3.5, 0, 1) * 0.65
    a = cv2.resize(a.astype(np.float32), (a.shape[1] * BS, a.shape[0] * BS), interpolation=cv2.INTER_NEAREST)
    alpha = np.zeros((h, w), np.float32)
    alpha[: a.shape[0], : a.shape[1]] = a[:h, :w]
    red = np.array([230, 30, 40], np.float32)
    over = (rgb * (1 - alpha[..., None]) + red * alpha[..., None]).astype(np.uint8)
    for key in ("noise_inconsistency", "compression_inconsistency"):
        c = cues[key]
        if c["p"] >= 0.5 and "bbox_xyxy" in c:
            x0, y0, x1, y1 = c["bbox_xyxy"]
            cv2.rectangle(over, (x0, y0), (x1, y1), (230, 30, 40), 3)
    cm = cues["copy_move"]
    if cm["p"] >= 0.5 and "clone_xyxy" in cm:
        for k in ("source_xyxy", "clone_xyxy"):  # direction of a copy is not knowable; mark both
            x0, y0, x1, y1 = cm[k]
            cv2.rectangle(over, (x0 - 6, y0 - 6), (x1 + 6, y1 + 6), (200, 0, 200), 3)
    Image.fromarray(over).save(path)
