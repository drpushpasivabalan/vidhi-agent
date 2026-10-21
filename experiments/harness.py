"""Evaluation harness: environment for the agent, baselines, metrics."""
from __future__ import annotations

import json
import os
import re
import zlib

import numpy as np
from sklearn.metrics import roc_auc_score

from vidhi import context as C
from vidhi.agent import Config, Env, run
from vidhi.procedure import ProceduralKB

DATA = os.path.join(os.path.dirname(__file__), "..", "bench", "data")


def _h(*p):
    return zlib.crc32("|".join(map(str, p)).encode())


class Split:
    def __init__(self, name, pools, condition="standard"):
        self.name = name
        self.incs = json.load(open(os.path.join(DATA, f"{name}.json")))
        self.docs = json.load(open(os.path.join(DATA, f"{name}_docs.json")))
        self.pools = pools
        self.condition = condition
        self._ccs = {}
        for x in self.incs:
            x["doc"] = x.get("doc")  # spec or None
            x["audio"] = x.get("audio")
            x["video"] = x.get("video") or None
            self._assign_media(x)

    def _assign_media(self, x):
        """Scam media are manipulated with probability 0.5 per item (standard) or
        never (perfect: forensically clean, as a flawless deepfake would be)."""
        r = np.random.default_rng(_h("media", x["id"]))
        scam = x["label"] == 1 and not x["id"].count("-tp-")
        x["_m"] = {}
        if x["audio"]:
            if scam and r.random() < 0.5:
                kind = "synthetic_voice" if r.random() < 0.75 else "splice"
            else:
                kind = "authentic"
            keys = [k for k, v in self.pools["audio"].items() if v["kind"] == kind]
            x["_m"]["audio"] = (kind, keys[r.integers(len(keys))])
        if x["video"]:
            kind = "face_swap" if (scam and r.random() < 0.5) else "authentic"
            keys = [k for k, v in self.pools["video"].items() if v["kind"] == kind]
            x["_m"]["video"] = (kind, keys[r.integers(len(keys))])
        if x["doc"]:
            x["_m"]["doc"] = "manip" if (scam and r.random() < 0.5) else "clean"

    # ---------------------------------------------------------------- tools
    def perceive_doc(self, x):
        return self.docs[x["id"]]["perception"]

    def forensic(self, x, kind):
        perfect = self.condition == "perfect"
        if kind == "image":
            d = self.docs[x["id"]]
            use = "clean" if perfect else x["_m"]["doc"]
            return (d["forensic_manip"] if use == "manip" else d["forensic_clean"]), "image"
        mk = x["_m"]["audio" if kind == "audio" else "video"]
        if perfect and mk[0] != "authentic":
            keys = [k for k, v in self.pools[kind].items() if v["kind"] == "authentic"]
            mk = ("authentic", keys[_h(x["id"], kind) % len(keys)])
        return self.pools[kind][mk[1]]["score"], kind

    def media_manipulated(self, x):
        if self.condition == "perfect":
            return False
        m = x["_m"]
        return (m.get("doc") == "manip") or (m.get("audio", ("authentic",))[0] != "authentic") or (m.get("video", ("authentic",))[0] != "authentic")

    def ccs(self, x):
        if x["id"] not in self._ccs:
            S = C.session(x["ccs"], x["ccs_seed"])
            t_d = C.first_artefact_time(S) + 2.0 if x.get("doc") else 5.0
            ts, ci = C.ci_series(S)
            j = int(np.searchsorted(ts, t_d, side="right")) - 1
            self._ccs[x["id"]] = {"ci_td": float(ci[max(j, 0)]), "ci_peak": float(ci.max()), "t_d": t_d, "ts": ts, "ci": ci,
                                  "pay": S["pay"]}
        return self._ccs[x["id"]]


def load_pools():
    return json.load(open(os.path.join(DATA, "pools.json")))


# -------------------------------------------------------------------- VIDHI runner
def run_vidhi(split: Split, cfg: Config, calib, kb=None):
    kb = kb or ProceduralKB()
    out = []
    for x in split.incs:
        env = Env(x, split.perceive_doc, split.forensic, lambda inc: calib(split.ccs(inc)["ci_td"]))
        inc = dict(x)
        inc["transcript"] = x["text"]
        if not inc.get("audio"):
            inc["audio"] = None
        r = run(inc, env, kb, cfg)
        r.update(id=x["id"], family=x["family"], label=x["label"])
        out.append(r)
    return out


# -------------------------------------------------------------------- metrics
def metrics(rows, abstain_key="decision"):
    y = np.array([r["label"] for r in rows])
    p = np.array([r["p_fraud"] for r in rows])
    dec = [r[abstain_key] for r in rows]
    decided = np.array([d != "ABSTAIN_VERIFY" for d in dec])
    pred = np.array([d == "FRAUD" for d in dec])
    forced = np.where(decided, pred, p > 0.5)
    cov = decided.mean()
    sel_acc = (pred[decided] == y[decided]).mean() if decided.any() else float("nan")
    tp = (forced & (y == 1)).sum(); fp = (forced & (y == 0)).sum(); fn = (~forced & (y == 1)).sum(); tn = (~forced & (y == 0)).sum()
    prec = tp / max(tp + fp, 1); rec = tp / max(tp + fn, 1)
    try:
        auc = roc_auc_score(y, p)
    except ValueError:
        auc = float("nan")
    return {
        "n": int(len(y)), "acc": float((forced == y).mean()), "f1": float(2 * prec * rec / max(prec + rec, 1e-9)),
        "tpr": float(rec), "fpr": float(fp / max(fp + tn, 1)), "auc": float(auc), "coverage": float(cov),
        "selective_acc": float(sel_acc), "errors_when_decided": int(((pred != y) & decided).sum()),
    }


def per_family(rows):
    fam = {}
    for r in rows:
        fam.setdefault(r["family"], []).append(r)
    out = {}
    for f, rs in fam.items():
        lab = rs[0]["label"]
        flagged = np.mean([r["decision"] == "FRAUD" for r in rs])
        cleared = np.mean([r["decision"] == "LEGITIMATE" for r in rs])
        abst = np.mean([r["decision"] == "ABSTAIN_VERIFY" for r in rs])
        out[f] = {"label": lab, "n": len(rs), "fraud": float(flagged), "legit": float(cleared), "abstain": float(abst),
                  "correct": float(flagged if lab == 1 else cleared)}
    return out


# -------------------------------------------------------------------- baselines
KEYWORDS = r"\barrest|\bpolice\b|\bcbi\b|enforcement directorate|warrant|\bcourt\b|summons|customs|money laundering|\bed\b"


def doc_text(split, x):
    return split.docs[x["id"]]["perception"]["text"] if x.get("doc") else ""


def baseline_rows(split: Split, name, fn):
    rows = []
    for x in split.incs:
        p = fn(x)
        rows.append({"id": x["id"], "family": x["family"], "label": x["label"], "p_fraud": p,
                     "decision": "FRAUD" if p >= 0.5 else "LEGITIMATE"})
    return rows


def artifact_only(split):
    def f(x):
        s = [split.forensic(x, k)[0] for k, key in (("image", "doc"), ("audio", "audio"), ("video", "video")) if x.get(key)]
        return max(s) if s else 0.0
    return baseline_rows(split, "artifact", f)


def ccs_only(split, calib, at="td"):
    return baseline_rows(split, "ccs", lambda x: calib(split.ccs(x)["ci_td" if at == "td" else "ci_peak"]))


def keyword_rule(split):
    return baseline_rows(split, "kw", lambda x: float(bool(re.search(KEYWORDS, x["text"] + " " + doc_text(split, x), re.I))))


def text_models(dev: Split, test: Split):
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.linear_model import LogisticRegression
    from sklearn.neighbors import KNeighborsClassifier
    tx = lambda s, x: x["text"] + " " + doc_text(s, x) + f" channel_{x['channel']}"  # noqa: E731
    Xd = [tx(dev, x) for x in dev.incs]
    yd = [x["label"] for x in dev.incs]
    vec = TfidfVectorizer(ngram_range=(1, 2), min_df=2, sublinear_tf=True).fit(Xd)
    A = vec.transform(Xd)
    lr = LogisticRegression(max_iter=3000, C=4.0).fit(A, yd)
    knn = KNeighborsClassifier(n_neighbors=7, metric="cosine").fit(A, yd)
    T = vec.transform([tx(test, x) for x in test.incs])
    plr, pk = lr.predict_proba(T)[:, 1], knn.predict_proba(T)[:, 1]
    mk = lambda P: [{"id": x["id"], "family": x["family"], "label": x["label"], "p_fraud": float(p),  # noqa: E731
                     "decision": "FRAUD" if p >= 0.5 else "LEGITIMATE"} for x, p in zip(test.incs, P)]
    return mk(plr), mk(pk)
