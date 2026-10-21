"""Held-out evaluation on freshly generated synthetic media.

Seeds here ('eval-...') are disjoint from the ones used while setting thresholds.
Writes results/eval_results.json, results/eval_summary.md and results/eval_plots.png.
Usage: python evaluate.py [--n-img 40] [--n-aud 40] [--n-vid 12]
"""
from __future__ import annotations

import argparse
import io
import json
import os
import random
import tempfile
import time
import zlib

import numpy as np
from PIL import Image
from sklearn.metrics import roc_auc_score

from mmflag.audio import analyze_audio
from mmflag.image import analyze_image
from mmflag.video import analyze_video
from samples import make_audio as MA
from samples import make_images as MI
from samples.make_video import render

THR = 0.5


def seed(*parts):
    return zlib.crc32("-".join(map(str, ("eval",) + parts)).encode())


def forwarded(im: Image.Image) -> Image.Image:
    """Messaging-app style re-share: downscale to 75 % and re-JPEG at q=70."""
    im = im.resize((int(im.width * 0.75), int(im.height * 0.75)), Image.BILINEAR)
    b = io.BytesIO()
    im.save(b, "JPEG", quality=70)
    return Image.open(io.BytesIO(b.getvalue())).convert("RGB")


def run(n_img, n_aud, n_vid):
    rows = []
    t0 = time.time()
    # ---------------- images
    for i in range(n_img):
        im, m = MI.authentic(random.Random(seed("img", "auth", i)))
        rows.append(("image", "authentic", 0, analyze_image(im)["confidence_manipulated"]))
    for kind in ("splice_clean", "splice_foreign", "copy_move"):
        for i in range(n_img // 2):
            im, m = MI.tamper(kind, random.Random(seed("img", kind, i)))
            rows.append(("image", kind, 1, analyze_image(im)["confidence_manipulated"]))
    for i in range(n_img // 2):  # stress: everything re-shared through a messaging app
        im, _ = MI.authentic(random.Random(seed("img", "fauth", i)))
        rows.append(("image_forwarded", "authentic", 0, analyze_image(forwarded(im))["confidence_manipulated"]))
        kind = ("splice_clean", "splice_foreign", "copy_move")[i % 3]
        im, _ = MI.tamper(kind, random.Random(seed("img", "f" + kind, i)))
        rows.append(("image_forwarded", kind, 1, analyze_image(forwarded(im))["confidence_manipulated"]))
    print(f"images done {time.time() - t0:.0f}s")
    # ---------------- audio
    for i in range(n_aud):
        x, m = MA.authentic(np.random.default_rng(seed("aud", "auth", i)))
        rows.append(("audio", m["kind"], 0, analyze_audio(x)["confidence_manipulated"]))
    for kind in ("splice", "synthetic_voice"):
        for i in range(n_aud // 2):
            x, m = getattr(MA, kind)(np.random.default_rng(seed("aud", kind, i)))
            sub = kind + ("_xfade" if m.get("crossfade") else "_hardcut" if kind == "splice" else "")
            rows.append(("audio", sub, 1, analyze_audio(x)["confidence_manipulated"]))
    print(f"audio done {time.time() - t0:.0f}s")
    # ---------------- video
    with tempfile.TemporaryDirectory() as td:
        for kind in ("authentic", "face_swap", "splice"):
            for i in range(n_vid):
                p, m = render(np.random.default_rng(seed("vid", kind, i)), kind, os.path.join(td, f"{kind}{i}.mp4"))
                rows.append(("video", kind, int(kind != "authentic"), analyze_video(p)["confidence_manipulated"]))
    print(f"video done {time.time() - t0:.0f}s")
    return rows


def summarise(rows):
    out = {"threshold": THR, "modalities": {}}
    lines = ["| Set | n authentic | n manipulated | ROC-AUC | Detection rate (TPR) | False-alarm rate (FPR) | Accuracy |",
             "|---|---|---|---|---|---|---|"]
    per_type = ["| Set | Sample type | n | Flagged (score >= 0.5) | Median score |", "|---|---|---|---|---|"]
    for mod in dict.fromkeys(r[0] for r in rows):
        R = [r for r in rows if r[0] == mod]
        y = np.array([r[2] for r in R])
        s = np.array([r[3] for r in R])
        pred = s >= THR
        auc = roc_auc_score(y, s)
        tpr, fpr = pred[y == 1].mean(), pred[y == 0].mean()
        acc = (pred == y).mean()
        out["modalities"][mod] = {"auc": round(float(auc), 4), "tpr": round(float(tpr), 4), "fpr": round(float(fpr), 4),
                                  "accuracy": round(float(acc), 4), "n_pos": int(y.sum()), "n_neg": int((1 - y).sum()),
                                  "types": {}}
        lines.append(f"| {mod} | {int((1 - y).sum())} | {int(y.sum())} | {auc:.3f} | {tpr:.1%} | {fpr:.1%} | {acc:.1%} |")
        for t in dict.fromkeys(r[1] for r in R):
            st = np.array([r[3] for r in R if r[1] == t])
            fl = (st >= THR).mean()
            out["modalities"][mod]["types"][t] = {"n": len(st), "flag_rate": round(float(fl), 4), "median": round(float(np.median(st)), 4)}
            per_type.append(f"| {mod} | {t} | {len(st)} | {fl:.0%} | {np.median(st):.3f} |")
    out["rows"] = [{"set": r[0], "type": r[1], "label": r[2], "score": r[3]} for r in rows]
    md = "## Held-out evaluation (synthetic media)\n\n" + "\n".join(lines) + "\n\n### By sample type\n\n" + "\n".join(per_type) + "\n"
    return out, md


def plot(rows, path):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from sklearn.metrics import roc_curve

    mods = list(dict.fromkeys(r[0] for r in rows))
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.2))
    for mod in mods:
        R = [r for r in rows if r[0] == mod]
        fpr, tpr, _ = roc_curve([r[2] for r in R], [r[3] for r in R])
        axes[0].plot(fpr, tpr, lw=2, label=mod)
    axes[0].plot([0, 1], [0, 1], ls=":", c="grey")
    axes[0].set(xlabel="False-alarm rate", ylabel="Detection rate", title="ROC (held-out synthetic media)")
    axes[0].legend(frameon=False)
    for k, mod in enumerate(mods):
        for lab, c in ((0, "#2a7ab9"), (1, "#d1495b")):
            s = [r[3] for r in rows if r[0] == mod and r[2] == lab]
            axes[1].scatter(np.full(len(s), k) + (lab - 0.5) * 0.35 + np.random.uniform(-0.08, 0.08, len(s)), s,
                            s=12, c=c, alpha=0.7, label=("authentic" if lab == 0 else "manipulated") if k == 0 else None)
    axes[1].axhline(THR, ls="--", c="grey", lw=1)
    axes[1].set_xticks(range(len(mods)), mods)
    axes[1].set(ylabel="confidence_manipulated", title="Score per sample", ylim=(-0.03, 1.03))
    axes[1].legend(frameon=False, loc="upper center", bbox_to_anchor=(0.5, -0.1), ncol=2)
    for ax in axes:
        ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    fig.savefig(path, dpi=140)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--n-img", type=int, default=40)
    ap.add_argument("--n-aud", type=int, default=40)
    ap.add_argument("--n-vid", type=int, default=12)
    a = ap.parse_args()
    os.makedirs("results", exist_ok=True)
    rows = run(a.n_img, a.n_aud, a.n_vid)
    res, md = summarise(rows)
    json.dump(res, open("results/eval_results.json", "w"), indent=1)
    open("results/eval_summary.md", "w").write(md)
    plot(rows, "results/eval_plots.png")
    print(md)
