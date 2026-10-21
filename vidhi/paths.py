"""Locations of the two sibling projects VIDHI reuses (override with environment variables).

MMFLAG_PATH   : folder containing the `mmflag` package and its `samples` generators
CCS_CODE_PATH : the `code` folder of https://github.com/drpushpasivabalan/ccs-digital-arrest-dataset
"""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MMFLAG_PATH = os.environ.get("MMFLAG_PATH", os.path.join(ROOT, "third_party", "mmflag"))
CCS_CODE_PATH = os.environ.get("CCS_CODE_PATH", os.path.join(ROOT, "third_party", "ccs", "code"))


def add(p):
    if p not in sys.path:
        sys.path.insert(0, p)
