"""Shared helpers: robust statistics, block maps, anomaly scoring and score fusion."""
from __future__ import annotations

import numpy as np
from scipy import ndimage

EPS = 1e-9


def logistic(x: float, center: float, width: float) -> float:
    """Map a raw statistic to (0,1). `center` is where p=0.5, `width` the softness."""
    return float(1.0 / (1.0 + np.exp(-(x - center) / max(width, EPS))))


def robust_z(values: np.ndarray, min_scale: float = 0.0) -> np.ndarray:
    """Robust z-score (median / MAD) so a tampered region cannot mask itself.

    `min_scale` floors the spread so near-identical blocks (e.g. blank paper)
    do not turn tiny absolute differences into huge z-scores.
    """
    med = np.median(values)
    mad = max(np.median(np.abs(values - med)) * 1.4826, min_scale) + EPS
    return (values - med) / mad


def block_reduce(arr: np.ndarray, bs: int, fn=np.mean) -> np.ndarray:
    """Reduce a 2-D array to a grid of `bs`x`bs` blocks with `fn` (edges trimmed)."""
    h, w = arr.shape[:2]
    hb, wb = h // bs, w // bs
    a = arr[: hb * bs, : wb * bs].reshape(hb, bs, wb, bs)
    return fn(a, axis=(1, 3))


def region_anomaly(zmap: np.ndarray, z_thresh: float = 3.0, valid: np.ndarray | None = None):
    """Find the largest connected cluster of anomalous blocks in a robust-z map.

    Isolated single outlier blocks are expected by chance; a spatially coherent
    cluster is what a pasted/spliced region looks like.
    Returns (strength, area_fraction, bbox_in_blocks or None).
    strength = sum of |z| over the largest cluster / sqrt(total blocks)  (scale-free).
    """
    mask = np.abs(zmap) > z_thresh
    if valid is not None:
        mask &= valid
    lab, n = ndimage.label(mask, structure=np.ones((3, 3)))
    if n == 0:
        return 0.0, 0.0, None
    sizes = ndimage.sum(np.ones_like(zmap), lab, index=np.arange(1, n + 1))
    k = int(np.argmax(sizes)) + 1
    comp = lab == k
    if comp.sum() < 2:  # single block -> treat as chance
        return 0.0, 0.0, None
    strength = float(np.abs(zmap[comp]).sum() / np.sqrt(zmap.size))
    ys, xs = np.where(comp)
    total = valid.sum() if valid is not None else zmap.size
    return strength, float(comp.sum() / max(total, 1)), (int(ys.min()), int(xs.min()), int(ys.max()), int(xs.max()))


def fuse(cues: dict, weights: dict) -> float:
    """Weighted noisy-OR: any single strong cue can raise the flag, weak cues add up.

    P(tampered) = 1 - prod_i (1 - p_i) ** w_i
    """
    log_keep = 0.0
    for name, c in cues.items():
        p = min(max(c["p"], 0.0), 0.999)
        log_keep += weights.get(name, 1.0) * np.log(1.0 - p)
    return float(1.0 - np.exp(log_keep))


def verdict(score: float, lo: float = 0.35, hi: float = 0.65) -> str:
    if score >= hi:
        return "LIKELY_MANIPULATED"
    if score >= lo:
        return "SUSPICIOUS_REVIEW"
    return "NO_STRONG_EVIDENCE"


def pca_noise_map(gray: np.ndarray, bs: int = 16, patch: int = 4, k_low: int = 3) -> np.ndarray:
    """Texture-robust per-block noise sigma (patch-PCA, after Pyatykh et al. 2013).

    Inside a block, scene texture concentrates in a few principal components of the
    small-patch covariance; white sensor noise spreads evenly over all of them. The
    smallest eigenvalues therefore estimate noise variance largely independent of
    texture - which a simple high-pass residual cannot do.
    """
    from numpy.lib.stride_tricks import sliding_window_view

    h, w = gray.shape
    hb, wb = h // bs, w // bs
    g = gray[: hb * bs, : wb * bs].reshape(hb, bs, wb, bs).transpose(0, 2, 1, 3)  # hb,wb,bs,bs
    P = sliding_window_view(g, (patch, patch), axis=(2, 3))  # hb,wb,n,n,p,p
    P = P.reshape(hb, wb, -1, patch * patch)
    P = P - P.mean(2, keepdims=True)
    C = np.einsum("abni,abnj->abij", P, P) / P.shape[2]
    ev = np.linalg.eigvalsh(C)  # ascending
    return np.sqrt(np.maximum(ev[..., :k_low].mean(-1), 0)) + 0.05
