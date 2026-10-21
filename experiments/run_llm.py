"""Experiments with the LLM claim extractor and LLM-only detectors.

python -m experiments.run_llm [path/to/llm_results.json]   -> results/llm_*.json

Evaluates (A) VIDHI-Real (78 real fraud/lawful communications from public sources) and
(B) the 400-incident synthetic test subset sent to the LLMs (25 per family), under
standard media and perfect deepfakes. Fusion parameters are the ones tuned on DEV for
the rule-based system; nothing is re-tuned for the LLM variants.
"""
from __future__ import annotations

import json
import os
import sys

import numpy as np
from sklearn.metrics import roc_auc_score

from experiments import harness as Hn
from vidhi import context as C
from vidhi.agent import Config, Env, run
from vidhi.claims import extract
from vidhi.llm_schema import parse_detection, parse_extraction
from vidhi.procedure import ProceduralKB

R = os.path.join(os.path.dirname(__file__), "..", "results")
DATA = os.path.join(os.path.dirname(__file__), "..", "bench", "data")
KB = ProceduralKB()
MODELS = ["qwen2.5:3b", "llama3.2:3b"]


def load_llm(path):
    raw = json.load(open(path, encoding="utf-8"))
    claims = {m: {} for m in MODELS}
    detect = {m: {} for m in MODELS}
    stats = {m: {"extract_ok": 0, "extract_n": 0, "detect_ok": 0, "detect_n": 0, "sec": []} for m in MODELS}
    for k, v in raw.items():
        if k.startswith("_"):
            continue
        m, task, iid = k.split("|", 2)
        if m not in claims:
            continue
        stats[m]["sec"].append(v.get("seconds", 0))
        if task == "extract":
            c, ok = parse_extraction(v["raw"])
            claims[m][iid] = c
            stats[m]["extract_ok"] += ok; stats[m]["extract_n"] += 1
        else:
            p, ok = parse_detection(v["raw"])
            detect[m][iid] = p
            stats[m]["detect_ok"] += ok; stats[m]["detect_n"] += 1
    for m in MODELS:
        s = stats[m]["sec"]
        stats[m]["mean_seconds"] = float(np.mean(s)) if s else None
        del stats[m]["sec"]
    return claims, detect, stats, raw.get("_meta", {})


def three(rows):
    f = [r for r in rows if r["label"] == 1]
    l = [r for r in rows if r["label"] == 0]
    fr = lambda xs, d: float(np.mean([r["decision"] == d for r in xs])) if xs else float("nan")  # noqa: E731
    out = dict(fraud_flagged=fr(f, "FRAUD"), fraud_verify=fr(f, "ABSTAIN_VERIFY"), fraud_cleared=fr(f, "LEGITIMATE"),
               lawful_cleared=fr(l, "LEGITIMATE"), lawful_verify=fr(l, "ABSTAIN_VERIFY"), lawful_flagged=fr(l, "FRAUD"))
    y = [r["label"] for r in rows]
    p = [r["p_fraud"] for r in rows]
    out["auc"] = float(roc_auc_score(y, p)) if len(set(y)) > 1 else float("nan")
    out["n"] = len(rows)
    return out


def boot(rows, key, n=1000, seed=0):
    rng = np.random.default_rng(seed)
    v = []
    for _ in range(n):
        s = [rows[i] for i in rng.integers(0, len(rows), len(rows))]
        v.append(three(s)[key])
    v = np.array(v, float)
    v = v[~np.isnan(v)]
    return [float(np.percentile(v, 2.5)), float(np.percentile(v, 97.5))]


def ext_prf(items, claims_of):
    out = {}
    for slot in ("agencies", "instruments", "demands"):
        tp = fp = fn = 0
        for x in items:
            c = claims_of(x)
            if c is None:
                continue
            G, P = set(x["gold"][slot]), set(c[slot])
            tp += len(G & P); fp += len(P - G); fn += len(G - P)
        p = tp / max(tp + fp, 1); r = tp / max(tp + fn, 1)
        out[slot] = {"precision": p, "recall": r, "f1": 2 * p * r / max(p + r, 1e-9)}
    pay = [(x["gold"].get("payee", "none") == claims_of(x)["payee"]) for x in items if claims_of(x) is not None]
    out["payee_acc"] = float(np.mean(pay)) if pay else None
    return out


def tuned_cfg(**kw):
    t = json.load(open(os.path.join(R, "tuning.json")))["params"]
    base = dict(tau_f=t["tau_f"], tau_l=t["tau_l"], mass=dict(t["mass"]))
    base.update(kw)
    return Config(**base)


# ------------------------------------------------------------------ (A) real set
def run_real(claims, detect):
    real = json.load(open(os.path.join(DATA, "real.json"), encoding="utf-8"))

    def vidhi(cfg):
        rows = []
        for x in real:
            inc = dict(x)
            env = Env(inc, None, None, None)
            r = run(inc, env, KB, cfg)
            rows.append({"id": x["id"], "label": x["label"], "decision": r["decision"], "p_fraud": r["p_fraud"],
                         "findings": [f["id"] for f in r["findings"]], "claims": r["claims"]})
        return rows

    base = dict(use_forensic=False, use_context=False)
    systems = {"VIDHI (rule extractor)": vidhi(tuned_cfg(**base))}
    for m in MODELS:
        if claims[m]:
            systems[f"VIDHI ({m} extractor)"] = vidhi(tuned_cfg(**base, llm_claims=claims[m]))
            systems[f"VIDHI ({m} + rules)"] = vidhi(tuned_cfg(**base, llm_claims=claims[m], llm_mode="union"))
    systems["VIDHI (oracle claims, analysis)"] = vidhi(tuned_cfg(**base, oracle_claims=True))
    # post-hoc variant (disclosed): document-dependent requirements never judged without the document
    pv = dict(base, doc_only_requirements=True)
    systems["VIDHI-D (rule extractor)"] = vidhi(tuned_cfg(**pv))
    for m in MODELS:
        if claims[m]:
            systems[f"VIDHI-D ({m} extractor)"] = vidhi(tuned_cfg(**pv, llm_claims=claims[m]))
            systems[f"VIDHI-D ({m} + rules)"] = vidhi(tuned_cfg(**pv, llm_claims=claims[m], llm_mode="union"))
    systems["VIDHI-D (oracle claims, analysis)"] = vidhi(tuned_cfg(**pv, oracle_claims=True))
    # baselines
    kw = [{"id": x["id"], "label": x["label"], "p_fraud": float(bool(__import__("re").search(Hn.KEYWORDS, x["text"], 2))),
           } for x in real]
    for r in kw:
        r["decision"] = "FRAUD" if r["p_fraud"] >= 0.5 else "LEGITIMATE"
    systems["Keyword rule"] = kw
    dev = Hn.Split("dev", Hn.load_pools())
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.linear_model import LogisticRegression
    from sklearn.neighbors import KNeighborsClassifier
    Xd = [x["text"] + " " + Hn.doc_text(dev, x) + f" channel_{x['channel']}" for x in dev.incs]
    yd = [x["label"] for x in dev.incs]
    vec = TfidfVectorizer(ngram_range=(1, 2), min_df=2, sublinear_tf=True).fit(Xd)
    A = vec.transform(Xd)
    T = vec.transform([x["text"] + f" channel_{x['channel']}" for x in real])
    for name, mdl in (("TF-IDF + LR (trained on VIDHI-Bench)", LogisticRegression(max_iter=3000, C=4.0)),
                      ("kNN example retrieval (VIDHI-Bench memory)", KNeighborsClassifier(n_neighbors=7, metric="cosine"))):
        P = mdl.fit(A, yd).predict_proba(T)[:, 1]
        systems[name] = [{"id": x["id"], "label": x["label"], "p_fraud": float(p), "decision": "FRAUD" if p >= 0.5 else "LEGITIMATE"}
                         for x, p in zip(real, P)]
    for m in MODELS:
        if detect[m]:
            systems[f"LLM-only detector ({m})"] = [
                {"id": x["id"], "label": x["label"], "p_fraud": detect[m].get(x["id"], 0.5),
                 "decision": "FRAUD" if detect[m].get(x["id"], 0.5) > 0.5 else ("LEGITIMATE" if detect[m].get(x["id"], 0.5) < 0.5 else "ABSTAIN_VERIFY")}
                for x in real]
    res = {}
    for k, rows in systems.items():
        m = three(rows)
        m["fraud_flagged_ci95"] = boot(rows, "fraud_flagged")
        m["lawful_flagged_ci95"] = boot(rows, "lawful_flagged")
        res[k] = m
    rule = {x["id"]: extract(x["text"], x["channel"], x["date"]) for x in real}
    ext = {"rules": ext_prf(real, lambda x: {"agencies": rule[x["id"]].agencies, "instruments": rule[x["id"]].instruments,
                                             "demands": rule[x["id"]].demands, "payee": rule[x["id"]].payee})}
    for m in MODELS:
        if claims[m]:
            ext[m] = ext_prf(real, lambda x, m=m: claims[m].get(x["id"]))
    by_form = {}
    for k in ("VIDHI (rule extractor)",) + tuple(f"VIDHI ({m} extractor)" for m in MODELS if claims[m]):
        rows = systems[k]
        form = {x["id"]: x["form"] for x in real}
        by_form[k] = {f: three([r for r in rows if form[r["id"]] == f]) for f in ("excerpts", "paraphrase")}
    return {"systems": res, "extraction": ext, "by_form": by_form, "n": len(real),
            "rows": {k: [{kk: r[kk] for kk in ("id", "label", "decision", "p_fraud") if kk in r} for r in v] for k, v in systems.items()}}


# ------------------------------------------------------------------ (B) synthetic subset
def run_synth(claims, detect):
    pools = Hn.load_pools()
    dev = Hn.Split("dev", pools)
    calib = C.Calibrator().fit([dev.ccs(x)["ci_td"] for x in dev.incs], [x["label"] for x in dev.incs])
    out = {}
    for cond in ("standard", "perfect"):
        sp = Hn.Split("test", pools, cond)
        sp.incs = [x for x in sp.incs if int(x["id"].rsplit("-", 1)[1]) < 25]
        systems = {"VIDHI (rule extractor)": Hn.run_vidhi(sp, tuned_cfg(), calib, KB)}
        for m in MODELS:
            if claims[m]:
                systems[f"VIDHI ({m} extractor)"] = Hn.run_vidhi(sp, tuned_cfg(llm_claims=claims[m]), calib, KB)
                systems[f"VIDHI ({m} + rules)"] = Hn.run_vidhi(sp, tuned_cfg(llm_claims=claims[m], llm_mode="union"), calib, KB)
        systems["VIDHI (oracle claims, analysis)"] = Hn.run_vidhi(sp, tuned_cfg(oracle_claims=True), calib, KB)
        systems["Media forensics only"] = Hn.artifact_only(sp)
        for m in MODELS:
            if detect[m]:
                systems[f"LLM-only detector ({m})"] = [
                    {"id": x["id"], "family": x["family"], "label": x["label"], "p_fraud": detect[m].get(x["id"], 0.5),
                     "decision": "FRAUD" if detect[m].get(x["id"], 0.5) > 0.5 else ("LEGITIMATE" if detect[m].get(x["id"], 0.5) < 0.5 else "ABSTAIN_VERIFY")}
                    for x in sp.incs]
        out[cond] = {k: three(v) for k, v in systems.items()}
        if cond == "standard":
            fam = {}
            for k in systems:
                if k.startswith("VIDHI (") or k.startswith("LLM-only"):
                    fam[k] = Hn.per_family(systems[k])
            out["per_family_standard"] = fam
    test = [x for x in json.load(open(os.path.join(DATA, "test.json"))) if int(x["id"].rsplit("-", 1)[1]) < 25]
    docs = json.load(open(os.path.join(DATA, "test_docs.json")))
    rule = {}
    for x in test:
        cg = extract(x["text"], x["channel"], x["date"], docs[x["id"]]["perception"] if x.get("doc") else None)
        rule[x["id"]] = {"agencies": cg.agencies, "instruments": cg.instruments, "demands": cg.demands, "payee": cg.payee}
    out["extraction"] = {"rules": ext_prf(test, lambda x: rule[x["id"]])}
    for m in MODELS:
        if claims[m]:
            out["extraction"][m] = ext_prf(test, lambda x, m=m: claims[m].get(x["id"]))
    return out


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(__file__), "..", "llm_runner", "llm_results.json")
    if os.path.exists(path):
        claims, detect, stats, meta = load_llm(path)
    else:
        print("no LLM results found at", path, "- running rule/oracle/baseline parts only")
        claims, detect, stats, meta = {m: {} for m in MODELS}, {m: {} for m in MODELS}, {}, {}
    real = run_real(claims, detect)
    synth = run_synth(claims, detect)
    tag = os.environ.get("VIDHI_TAG", "")
    json.dump({"meta": meta, "parse_stats": stats, "real": real, "synthetic_subset": synth},
              open(os.path.join(R, f"llm_results_eval{tag}.json"), "w"), indent=1, default=float)
    for k, v in real["systems"].items():
        print(f"REAL {k:45s} fraud flagged {v['fraud_flagged']:.3f} verify {v['fraud_verify']:.3f} cleared {v['fraud_cleared']:.3f} | "
              f"lawful cleared {v['lawful_cleared']:.3f} verify {v['lawful_verify']:.3f} FLAGGED {v['lawful_flagged']:.3f} | auc {v['auc']:.3f}")
    for cond in ("standard", "perfect"):
        for k, v in synth[cond].items():
            print(f"SYN-{cond[:4]} {k:40s} fraud flagged {v['fraud_flagged']:.3f} cleared {v['fraud_cleared']:.3f} | lawful flagged {v['lawful_flagged']:.3f} | auc {v['auc']:.3f}")
    print(json.dumps(real["extraction"], indent=0, default=float)[:1500])


if __name__ == "__main__":
    main()
