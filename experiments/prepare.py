"""Prepare a split: render documents, run perception + forensic tools once, cache results.

python -m experiments.prepare dev|test|dev_temporal|test_temporal
python -m experiments.prepare pools
"""
from __future__ import annotations

import json
import os
import random
import sys
import zlib
from multiprocessing import Pool

import numpy as np

from vidhi.paths import MMFLAG_PATH, add  # noqa: E402
add(MMFLAG_PATH)
from bench.render_docs import render  # noqa: E402

DATA = os.path.join(os.path.dirname(__file__), "..", "bench", "data")
DOCS = os.path.join(DATA, "docs")
MEDIA = os.path.join(DATA, "media")


def _h(*p):
    return zlib.crc32("|".join(map(str, p)).encode())


def _doc_job(x):
    cp = os.path.join(DATA, "cache", x["id"] + ".json")
    if os.path.exists(cp):
        return json.load(open(cp))
    out = _doc_job_inner(x)
    json.dump(out, open(cp, "w"))
    return out


def _doc_job_inner(x):
    from vidhi.docvision import perceive
    from mmflag.image import analyze_image
    rng = random.Random(_h("doc", x["id"]))
    spec = dict(x["doc"])
    img, meta = render(spec, rng)
    path = os.path.join(DOCS, x["id"] + ".jpg")
    img.save(path, quality=90)
    per = perceive(img)
    clean_score = analyze_image(img)["confidence_manipulated"]
    out = {"id": x["id"], "perception": per, "forensic_clean": clean_score}
    if x["label"] == 1:  # a manipulated variant of the same scam document
        spec["manip"] = "copy_move" if spec.get("seal") else "splice"
        rng2 = random.Random(_h("doc", x["id"]))
        img2, _ = render(spec, rng2)
        img2.save(os.path.join(DOCS, x["id"] + "_manip.jpg"), quality=90)
        out["forensic_manip"] = analyze_image(img2)["confidence_manipulated"]
        out["manip_type"] = spec["manip"]
    return out


def prepare_split(name):
    incs = json.load(open(os.path.join(DATA, f"{name}.json")))
    os.makedirs(DOCS, exist_ok=True)
    os.makedirs(os.path.join(DATA, "cache"), exist_ok=True)
    jobs = [x for x in incs if x.get("doc")]
    with Pool(2) as p:
        res = p.map(_doc_job, jobs, chunksize=4)
    json.dump({r["id"]: r for r in res}, open(os.path.join(DATA, f"{name}_docs.json"), "w"))
    print(name, len(res), "documents")


def prepare_pools():
    from mmflag.audio import analyze_audio
    from mmflag.video import analyze_video
    from samples import make_audio as MA
    from samples.make_video import render as vrender
    os.makedirs(MEDIA, exist_ok=True)
    pools = {"audio": {}, "video": {}}
    for kind, n in (("authentic", 60), ("synthetic_voice", 40), ("splice", 20)):
        for i in range(n):
            x, m = getattr(MA, kind)(np.random.default_rng(_h("pool-a", kind, i)))
            pools["audio"][f"{kind}-{i}"] = {"kind": kind, "score": analyze_audio(x)["confidence_manipulated"]}
    for kind, n in (("authentic", 24), ("face_swap", 24)):
        for i in range(n):
            path = os.path.join(MEDIA, f"{kind}-{i}.mp4")
            vrender(np.random.default_rng(_h("pool-v", kind, i)), kind, path)
            pools["video"][f"{kind}-{i}"] = {"kind": kind, "score": analyze_video(path)["confidence_manipulated"]}
    json.dump(pools, open(os.path.join(DATA, "pools.json"), "w"), indent=1)
    for m in pools:
        for k in sorted({v["kind"] for v in pools[m].values()}):
            s = [v["score"] for v in pools[m].values() if v["kind"] == k]
            print(m, k, len(s), "flag rate %.2f" % np.mean(np.array(s) >= 0.5))


if __name__ == "__main__":
    a = sys.argv[1]
    prepare_pools() if a == "pools" else prepare_split(a)
