"""Command line:  python -m mmflag FILE [FILE ...] [--heatmaps DIR] [--json]"""
from __future__ import annotations

import argparse
import json
import os
import sys

from . import analyze


def main(argv=None):
    ap = argparse.ArgumentParser(prog="mmflag", description="Flag manipulated images / audio / video with a confidence score.")
    ap.add_argument("files", nargs="+")
    ap.add_argument("--heatmaps", metavar="DIR", help="write a suspicion heat-map PNG for each image")
    ap.add_argument("--json", action="store_true", help="print full JSON reports")
    a = ap.parse_args(argv)
    if a.heatmaps:
        os.makedirs(a.heatmaps, exist_ok=True)
    out = []
    for f in a.files:
        hm = os.path.join(a.heatmaps, os.path.splitext(os.path.basename(f))[0] + "_heatmap.png") if a.heatmaps else None
        try:
            r = analyze(f, heatmap_path=hm)
        except Exception as e:  # keep going on bad files
            r = {"file": os.path.basename(f), "error": str(e)}
        out.append(r)
        if not a.json:
            if "error" in r:
                print(f"{r['file']:<40} ERROR {r['error']}")
                continue
            top = max(r["cues"].items(), key=lambda kv: kv[1]["p"])
            print(f"{r['file']:<40} {r['modality']:<6} score={r['confidence_manipulated']:.3f}  {r['verdict']:<20} strongest cue: {top[0]} (p={top[1]['p']:.2f})")
    if a.json:
        json.dump(out if len(out) > 1 else out[0], sys.stdout, indent=2, default=str)
        print()


if __name__ == "__main__":
    main()
