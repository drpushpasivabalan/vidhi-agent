"""Context agent: reuses the CCS stage model (Pushpalakshmi, under review) unchanged.

A CCS session is regenerated from its scenario kind and seed with the published
simulator; the coercion index CI(t) at the decision time is mapped to a
probability with a logistic calibration fitted on the DEV split.
"""
from __future__ import annotations

import sys

import numpy as np

from vidhi.paths import CCS_CODE_PATH, add  # noqa: E402
add(CCS_CODE_PATH)
import core  # noqa: E402  (CCS simulator, published repository)
from exp import ci_from, stage_series  # noqa: E402


def session(kind: str, seed: int):
    core.rng = np.random.default_rng(seed)
    return core.gen_session(kind)


def ci_series(S):
    ts, e = stage_series(S, core.W)
    return ts, ci_from(ts, e, "ccs")


def ci_at(S, t):
    ts, ci = ci_series(S)
    j = int(np.searchsorted(ts, t, side="right")) - 1
    return float(ci[max(j, 0)])


def first_artefact_time(S):
    """Time the counterpart's document/image arrives (CCS event 'file_rx'), else 5 min."""
    t = [ti for ti, k in S["ev"] if k == "file_rx"]
    return float(t[0]) if t else 5.0


class Calibrator:
    def __init__(self, a=0.0, b=1.0):
        self.a, self.b = a, b

    def fit(self, ci, y):
        from sklearn.linear_model import LogisticRegression
        m = LogisticRegression().fit(np.array(ci).reshape(-1, 1), y)
        self.a, self.b = float(m.intercept_[0]), float(m.coef_[0, 0])
        return self

    def __call__(self, ci):
        return float(1 / (1 + np.exp(-(self.a + self.b * ci))))
