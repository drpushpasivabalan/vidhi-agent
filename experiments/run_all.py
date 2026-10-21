"""Run every experiment reported in the paper. Writes results/*.json.

python -m experiments.run_all
"""
from __future__ import annotations

import itertools
import json
import os
import time

import numpy as np

from experiments import harness as Hn
from vidhi import context as C
from vidhi.agent import Config
from vidhi.claims import ClaimGraph, OFFICIAL_DOMAINS
from vidhi.procedure import ProceduralKB, _p
from urllib.parse import urlparse

RES = os.path.join(os.path.dirname(__file__), "..", "results")
os.makedirs(RES, exist_ok=True)
KB = ProceduralKB()


def dump(name, obj):
    json.dump(obj, open(os.path.join(RES, name), "w"), indent=1, default=float)


def strip(rows):
    keep = ("id", "family", "label", "decision", "p_fraud", "bel_f", "bel_l", "conflict", "calls", "findings", "retrieved", "claims")
    return [{k: r[k] for k in keep if k in r} for r in rows]


# ------------------------------------------------------------------ gold invariants
def gold_cg(x):
    g = x["gold"]
    d = x.get("doc") or {}
    cg = ClaimGraph(date=x["date"], channel=x["channel"])
    cg.agencies, cg.instruments, cg.demands = set(g["agencies"]), set(g["instruments"]), set(g["demands"])
    cg.payee = g.get("payee", "none")
    cg.has_din = bool(d.get("din"))
    cg.has_seal = bool(d.get("seal"))
    cg.has_ds = bool(d.get("ds_name"))
    if d.get("qr_url"):
        cg.has_qr = True
        cg.qr_official = urlparse(d["qr_url"]).netloc in OFFICIAL_DOMAINS
    txt = x["text"] + " " + d.get("title", "")
    if "41A" in txt or "CrPC" in txt:
        cg.cites.add("old")
    if "BNSS" in txt:
        cg.cites.add("new")
    return cg


def gold_rules(x):
    cg = gold_cg(x)
    pr = _p(cg)
    return {i for i, v in pr.items() if v and KB.in_force(KB.entries[i], x["date"])}


# ------------------------------------------------------------------ helpers
def bootstrap(rows, fn, n=1000, seed=0):
    r = np.random.default_rng(seed)
    vals = []
    for _ in range(n):
        idx = r.integers(0, len(rows), len(rows))
        vals.append(fn([rows[i] for i in idx]))
    return float(np.percentile(vals, 2.5)), float(np.percentile(vals, 97.5))


def utility(rows, wrong_cost=2.0):
    s = 0.0
    for r in rows:
        if r["decision"] == "ABSTAIN_VERIFY":
            continue
        ok = (r["decision"] == "FRAUD") == (r["label"] == 1)
        s += 1.0 if ok else -wrong_cost
    return s / len(rows)


def main():
    t0 = time.time()
    pools = Hn.load_pools()
    dev = Hn.Split("dev", pools)
    # CCS probability calibration on DEV
    calib = C.Calibrator().fit([dev.ccs(x)["ci_td"] for x in dev.incs], [x["label"] for x in dev.incs])
    calib_peak = C.Calibrator().fit([dev.ccs(x)["ci_peak"] for x in dev.incs], [x["label"] for x in dev.incs])

    # ---------------- tuning on DEV (standard condition)
    grid = list(itertools.product([0.5, 0.6, 0.7], [0.4, 0.5, 0.6], [0.6, 0.75, 0.9], [0.4, 0.55, 0.7], [0.5, 0.6, 0.7]))
    best = None
    for tf, tl, fr, cr, cs in grid:
        cfg = Config(tau_f=tf, tau_l=tl, mass={"forensic_rel": fr, "context_rel": cr, "consistent": cs})
        u = utility(Hn.run_vidhi(dev, cfg, calib, KB))
        if best is None or u > best[0]:
            best = (u, dict(tau_f=tf, tau_l=tl, mass={"forensic_rel": fr, "context_rel": cr, "consistent": cs}))
    tuned = best[1]
    dump("tuning.json", {"dev_utility": best[0], "params": tuned, "grid_size": len(grid), "calib_td": [calib.a, calib.b],
                         "calib_peak": [calib_peak.a, calib_peak.b]})
    print("tuned", best, f"{time.time() - t0:.0f}s")

    def cfg(**kw):
        base = dict(tau_f=tuned["tau_f"], tau_l=tuned["tau_l"], mass=dict(tuned["mass"]))
        base.update(kw)
        return Config(**base)

    # ---------------- TEST: main comparison under two media conditions
    main_res, fam_res, rows_store = {}, {}, {}
    for cond in ("standard", "perfect"):
        test = Hn.Split("test", pools, cond)
        dev_c = Hn.Split("dev", pools, cond)
        systems = {
            "VIDHI (full)": Hn.run_vidhi(test, cfg(), calib, KB),
            "VIDHI pipeline (all tools)": Hn.run_vidhi(test, cfg(planner="all"), calib, KB),
            "VIDHI eager early stop": Hn.run_vidhi(test, cfg(early_stop="both"), calib, KB),
            "VIDHI + oracle claims (analysis)": Hn.run_vidhi(test, cfg(oracle_claims=True), calib, KB),
            "w/o procedure RAG": Hn.run_vidhi(test, cfg(use_procedure=False), calib, KB),
            "w/o forensics": Hn.run_vidhi(test, cfg(use_forensic=False), calib, KB),
            "w/o context (CCS)": Hn.run_vidhi(test, cfg(use_context=False), calib, KB),
            "w/o temporal versioning": Hn.run_vidhi(test, cfg(versioned=False), calib, KB),
            "w/o retrieval (all rules)": Hn.run_vidhi(test, cfg(retrieval="all"), calib, KB),
            "w/o abstention": Hn.run_vidhi(test, cfg(abstain=False), calib, KB),
            "Procedure only": Hn.run_vidhi(test, cfg(use_forensic=False, use_context=False), calib, KB),
        }
        lr, knn = Hn.text_models(dev_c, test)
        baselines = {
            "Artifact forensics only (mmflag)": Hn.artifact_only(test),
            "CCS context only (at decision time)": Hn.ccs_only(test, calib, "td"),
            "CCS context only (whole session)": Hn.ccs_only(test, calib_peak, "peak"),
            "Keyword rule": Hn.keyword_rule(test),
            "TF-IDF + logistic regression": lr,
            "Example retrieval (kNN vote)": knn,
        }
        allsys = {**systems, **baselines}
        main_res[cond] = {}
        for name, rows in allsys.items():
            m = Hn.metrics(rows)
            m["acc_ci95"] = bootstrap(rows, lambda rs: Hn.metrics(rs)["acc"])
            if any("calls" in r for r in rows):
                m["mean_tool_calls"] = float(np.mean([len(r["calls"]) for r in rows]))
            main_res[cond][name] = m
        fam_res[cond] = {n: Hn.per_family(allsys[n]) for n in ("VIDHI (full)", "VIDHI + oracle claims (analysis)", "Artifact forensics only (mmflag)", "TF-IDF + logistic regression",
                                                                "CCS context only (at decision time)", "Procedure only")}
        rows_store[cond] = {n: strip(r) for n, r in allsys.items()}
        # McNemar: VIDHI forced decisions vs each baseline
        y = np.array([r["label"] for r in systems["VIDHI (full)"]])
        vf = np.array([(r["decision"] == "FRAUD") if r["decision"] != "ABSTAIN_VERIFY" else r["p_fraud"] > 0.5 for r in systems["VIDHI (full)"]])
        mc = {}
        from scipy.stats import binomtest
        for name, rows in baselines.items():
            bf = np.array([r["decision"] == "FRAUD" for r in rows])
            b = int(((vf == y) & (bf != y)).sum()); c = int(((vf != y) & (bf == y)).sum())
            mc[name] = {"vidhi_only_correct": b, "baseline_only_correct": c,
                        "p_value": float(binomtest(min(b, c), b + c, 0.5).pvalue) if b + c else 1.0}
        main_res[cond]["_mcnemar_vs_vidhi"] = mc
        # media-manipulated vs clean scam subsets (standard condition)
        if cond == "standard":
            man = {x["id"]: test.media_manipulated(x) for x in test.incs}
            sub = {}
            for name in ("VIDHI (full)", "Artifact forensics only (mmflag)", "Procedure only"):
                rs = [r for r in allsys[name] if r["label"] == 1]
                for flag in (True, False):
                    q = [r for r in rs if man[r["id"]] == flag]
                    sub.setdefault(name, {})["manipulated" if flag else "clean_media"] = {
                        "n": len(q), "detected": float(np.mean([r["decision"] == "FRAUD" for r in q]))}
            main_res[cond]["_scam_by_media"] = sub
        print(cond, "done", f"{time.time() - t0:.0f}s")
    dump("main.json", main_res)
    dump("per_family.json", fam_res)
    dump("rows.json", rows_store)

    # ---------------- temporal probes
    tp = Hn.Split("test_temporal", pools)
    tres = {}
    for name, c in (("versioned", cfg()), ("unversioned", cfg(versioned=False))):
        rows = Hn.run_vidhi(tp, c, calib, KB)
        per = {}
        for x, r in zip(tp.incs, rows):
            fired = x["rule"] in {f["id"] for f in r["findings"] if f["type"] == "violation"}
            per.setdefault(x["probe"], []).append(fired == x["should_fire"])
        tres[name] = {k: {"n": len(v), "rule_application_acc": float(np.mean(v))} for k, v in per.items()}
        tres[name]["overall"] = float(np.mean([a for v in per.values() for a in v]))
    dump("temporal.json", tres)

    # ---------------- retrieval quality + extraction accuracy (standard, test, all tools)
    test = Hn.Split("test", pools)
    rows = Hn.run_vidhi(test, cfg(planner="all"), calib, KB)
    rec, prec_list, k_hits = [], [], []
    slot = {s: {"tp": 0, "fp": 0, "fn": 0} for s in ("agencies", "instruments", "demands")}
    for x, r in zip(test.incs, rows):
        gr = gold_rules(x)
        ret = set(r["retrieved"])
        if gr:
            rec.append(len(gr & ret) / len(gr))
        viol = {f["id"] for f in r["findings"]}
        if viol:
            prec_list.append(len(viol & gr) / len(viol))
        for s in slot:
            G, P = set(x["gold"][s]), set(r["claims"][s])
            slot[s]["tp"] += len(G & P); slot[s]["fp"] += len(P - G); slot[s]["fn"] += len(G - P)
    ext = {}
    for s, v in slot.items():
        p = v["tp"] / max(v["tp"] + v["fp"], 1); rr = v["tp"] / max(v["tp"] + v["fn"], 1)
        ext[s] = {"precision": p, "recall": rr, "f1": 2 * p * rr / max(p + rr, 1e-9)}
    # same on DEV (lexicon source) for the generalisation gap
    rows_d = Hn.run_vidhi(dev, cfg(planner="all"), calib, KB)
    ext_dev = {}
    for s in slot:
        tp_ = fp_ = fn_ = 0
        for x, r in zip(dev.incs, rows_d):
            G, P = set(x["gold"][s]), set(r["claims"][s])
            tp_ += len(G & P); fp_ += len(P - G); fn_ += len(G - P)
        p = tp_ / max(tp_ + fp_, 1); rr = tp_ / max(tp_ + fn_, 1)
        ext_dev[s] = {"precision": p, "recall": rr, "f1": 2 * p * rr / max(p + rr, 1e-9)}
    # document perception accuracy
    per = {"seal": [], "digital_signature": [], "qr": [], "din": []}
    for x in test.incs:
        if not x.get("doc"):
            continue
        d, pp = x["doc"], test.docs[x["id"]]["perception"]
        per["seal"].append(bool(d.get("seal")) == pp["seal"])
        per["digital_signature"].append(bool(d.get("ds_name")) == pp["digital_signature"])
        per["qr"].append((d.get("qr_url") or None) == (pp["qr"] or None))
        import re
        per["din"].append(bool(d.get("din")) == bool(re.search(r"\bDIN\b\s*[:\-]?\s*[A-Z0-9/\-()]{8,}", pp["text"])))
    dump("components.json", {
        "retrieval_recall_of_gold_rules": float(np.mean(rec)), "n_with_gold_rules": len(rec),
        "grounding_precision_of_findings": float(np.mean(prec_list)), "n_with_findings": len(prec_list),
        "extraction_test": ext, "extraction_dev": ext_dev,
        "doc_perception_acc": {k: float(np.mean(v)) for k, v in per.items()}, "n_docs": len(per["seal"]),
    })

    # ---------------- leave-one-family-out: unseen scam scripts / unseen lawful practice
    from bench.build import LEGIT, SCAM
    lofo = {"fraud_unseen": {}, "legit_unseen": {}}
    for cond in ("standard", "perfect"):
        test_c = Hn.Split("test", pools, cond)
        dev_c = Hn.Split("dev", pools, cond)
        vr = {r["id"]: r for r in Hn.run_vidhi(test_c, cfg(), calib, KB)}
        for fams, key in ((SCAM, "fraud_unseen"), (LEGIT, "legit_unseen")):
            for f in fams:
                fam = f.__name__[4:]
                dsub = Hn.Split.__new__(Hn.Split); dsub.__dict__.update(dev_c.__dict__)
                dsub.incs = [x for x in dev_c.incs if x["family"] != fam]
                lr_rows, knn_rows = Hn.text_models(dsub, test_c)
                sel = [i for i, x in enumerate(test_c.incs) if x["family"] == fam]
                pos = lambda rows: float(np.mean([rows[i]["decision"] == "FRAUD" for i in sel]))  # noqa: E731
                vd = float(np.mean([vr[test_c.incs[i]["id"]]["decision"] == "FRAUD" for i in sel]))
                vc = float(np.mean([vr[test_c.incs[i]["id"]]["decision"] == "LEGITIMATE" for i in sel]))
                lofo[key].setdefault(cond, {})[fam] = {"lr_flag": pos(lr_rows), "knn_flag": pos(knn_rows), "vidhi_flag": vd, "vidhi_clear": vc}
    dump("lofo.json", lofo)
    # text classifier on temporal probes (it has no notion of rule start dates)
    lr_tp, knn_tp = Hn.text_models(Hn.Split("dev", pools), Hn.Split("test_temporal", pools))
    tp_inc = Hn.Split("test_temporal", pools).incs
    tr = json.load(open(os.path.join(RES, "temporal.json")))
    tr["tfidf_lr_label_acc"] = float(np.mean([(r["decision"] == "FRAUD") == x["should_fire"] for r, x in zip(lr_tp, tp_inc)]))
    tr["knn_label_acc"] = float(np.mean([(r["decision"] == "FRAUD") == x["should_fire"] for r, x in zip(knn_tp, tp_inc)]))
    dump("temporal.json", tr)

    # ---------------- early warning vs CCS alerting (standard, test, scams with payment)
    dev_peaks = np.array([dev.ccs(x)["ci_peak"] for x in dev.incs if x["label"] == 0])
    thr = float(np.sort(dev_peaks)[::-1][int(0.05 * len(dev_peaks))]) + 1e-6
    vrows = {r["id"]: r for r in Hn.run_vidhi(test, cfg(), calib, KB)}
    ew = {"vidhi_before_payment": [], "ccs_before_payment": [], "vidhi_lead_min": [], "ccs_lead_min": [], "ccs_never": 0}
    for x in test.incs:
        if x["label"] != 1:
            continue
        c = test.ccs(x)
        if c["pay"] is None:
            continue
        v_alert = c["t_d"] if vrows[x["id"]]["decision"] == "FRAUD" else None
        j = np.where(c["ci"] >= thr)[0]
        c_alert = float(c["ts"][j[0]]) if len(j) else None
        ew["vidhi_before_payment"].append(v_alert is not None and v_alert < c["pay"])
        ew["ccs_before_payment"].append(c_alert is not None and c_alert < c["pay"])
        if v_alert is not None:
            ew["vidhi_lead_min"].append(c["pay"] - v_alert)
        if c_alert is not None:
            ew["ccs_lead_min"].append(c["pay"] - c_alert)
        else:
            ew["ccs_never"] += 1
    dump("early_warning.json", {"ccs_threshold_5pct_fpr": thr, "n": len(ew["vidhi_before_payment"]),
                                "vidhi_alert_before_payment": float(np.mean(ew["vidhi_before_payment"])),
                                "ccs_alert_before_payment": float(np.mean(ew["ccs_before_payment"])),
                                "vidhi_median_lead_min": float(np.median(ew["vidhi_lead_min"])),
                                "ccs_median_lead_min": float(np.median(ew["ccs_lead_min"])) if ew["ccs_lead_min"] else None,
                                "ccs_never_alerted": ew["ccs_never"]})
    print("all done", f"{time.time() - t0:.0f}s")


if __name__ == "__main__":
    main()
