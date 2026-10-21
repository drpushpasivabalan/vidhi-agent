"""VIDHI agent: rule-driven tool orchestration over procedure, forensics and context.

Loop (adaptive planner):
  1. extract claims from the transcript/message + device metadata (channel, date)
  2. retrieve in-force procedural entries; record doc-independent impossibilities
     -> stop early if a hard impossibility already decides the case
  3. if the retrieved entries *require document evidence* (DIN, QR, seal, digital
     signature) and a document exists, call the document-perception tool, re-extract,
     re-retrieve and verify again
  4. if still undecided, query the context agent (CCS stage risk)
  5. if still undecided, call media-forensic tools in increasing cost order
  6. decide (FRAUD / LEGITIMATE) or abstain and route to verification
The counter-verification step proposes only official channels retrieved from the KB,
never a number or link supplied by the counterpart.
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field

from .claims import extract
from .fusion import Ledger
from .procedure import ProceduralKB, all_rule_ids, verify

DOC_DEPENDENT = {"R1", "R2", "R3", "A3", "A4", "A5"}
COST_ORDER = ["audio", "image", "video"]


@dataclass
class Config:
    planner: str = "adaptive"  # adaptive | all
    early_stop: str = "fraud_only"  # fraud_only (fail-safe: never clear early) | both  (adaptive planner: which decisions may end the loop early)
    oracle_claims: bool = False  # analysis only: replace extracted slots by ground-truth claims
    llm_claims: dict | None = None  # id -> {"agencies","instruments","demands","payee"} from an LLM extractor
    llm_mode: str = "replace"  # replace | union (union with the rule-based extractor)
    doc_only_requirements: bool = False  # post-hoc variant: never judge R1-R3/A3-A5 without the document itself
    use_procedure: bool = True
    use_forensic: bool = True
    use_context: bool = True
    versioned: bool = True
    retrieval: str = "rag"  # rag | all  (all = evaluate every rule, no retrieval)
    k: int = 6
    abstain: bool = True
    tau_f: float = 0.60
    tau_l: float = 0.50
    mass: dict = field(default_factory=dict)


class Env:
    """What the agent can touch for one incident (provided by the benchmark harness)."""

    def __init__(self, inc, perceive_doc, forensic, context_p):
        self.inc = inc
        self._perceive_doc = perceive_doc
        self._forensic = forensic
        self._context_p = context_p


def run(inc: dict, env: Env, kb: ProceduralKB, cfg: Config):
    t0 = time.perf_counter()
    led = Ledger(cfg.mass)
    calls = []
    seen = set()
    def done():
        if cfg.planner != "adaptive":
            return False
        d = led.decision(cfg.tau_f, cfg.tau_l)
        return d == "FRAUD" if cfg.early_stop == "fraud_only" else d != "ABSTAIN_VERIFY"

    def X(text_, doc_=None):
        cg_ = extract(text_, inc["channel"], inc["date"], doc_)
        if cfg.oracle_claims and inc.get("gold"):
            g = inc["gold"]
            cg_.agencies, cg_.instruments, cg_.demands = set(g["agencies"]), set(g["instruments"]), set(g["demands"])
            cg_.payee = g.get("payee", "none")
        elif cfg.llm_claims is not None and inc.get("id") in cfg.llm_claims:
            c = cfg.llm_claims[inc["id"]]
            if cfg.llm_mode == "union":
                cg_.agencies |= set(c["agencies"]); cg_.instruments |= set(c["instruments"]); cg_.demands |= set(c["demands"])
                if cg_.payee == "none":
                    cg_.payee = c["payee"]
            else:
                cg_.agencies, cg_.instruments, cg_.demands = set(c["agencies"]), set(c["instruments"]), set(c["demands"])
                cg_.payee = c["payee"]
        return cg_

    def retrieve(cg, text):
        if cfg.retrieval == "all":
            ids = [i for i in all_rule_ids(kb) if (not cfg.versioned) or kb.in_force(kb.entries[i], cg.date)]
        else:
            ids = kb.retrieve(cg, text, k=cfg.k, versioned=cfg.versioned)
        return ids

    def add_findings(fs, only=None):
        for f in fs:
            if f["id"] in seen or (only is not None and f["id"] not in only):
                continue
            seen.add(f["id"])
            led.add_procedure([f])

    text = inc["transcript"]
    cg = X(text)
    calls.append("extract_claims")
    findings_all = []
    retrieved = []
    if cfg.use_procedure:
        ids = retrieve(cg, text)
        retrieved = list(ids)
        calls.append("retrieve_procedure")
        fs = verify(kb, cg, ids)
        doc_needed = bool(set(ids) & DOC_DEPENDENT) or (inc.get("doc") is not None and not cg.instruments)
        # doc-independent impossibilities first
        add_findings(fs, only={f["id"] for f in fs if f["id"] not in DOC_DEPENDENT})
        findings_all = fs
        if inc.get("doc") is not None:
            if (doc_needed or cfg.planner == "all") and not done():
                doc = env._perceive_doc(inc)
                calls.append("perceive_document")
                cg = X(text, doc)
                ids2 = retrieve(cg, text + "\n" + doc["text"])
                retrieved = list(dict.fromkeys(retrieved + list(ids2)))
                calls.append("retrieve_procedure")
                fs = verify(kb, cg, ids2)
                add_findings(fs)
                findings_all = fs + [f for f in findings_all if f["id"] not in {g["id"] for g in fs}]
            # otherwise document-dependent rules stay unevaluated (never judged blind)
        else:
            # message-only case: requirements judged on the message itself (frozen design),
            # or skipped entirely in the post-hoc variant
            add_findings(fs, only=({f["id"] for f in fs if f["id"] not in DOC_DEPENDENT} if cfg.doc_only_requirements else None))
    elif inc.get("doc") is not None and cfg.planner == "all":
        env._perceive_doc(inc)
        calls.append("perceive_document")

    if cfg.use_context and not done():
        p = env._context_p(inc)
        led.add_context(p)
        calls.append("query_context")

    if cfg.use_forensic:
        for kind in COST_ORDER:
            if done():
                break
            key = {"image": "doc", "audio": "audio", "video": "video"}[kind]
            if inc.get(key) is None:
                continue
            s, cue = env._forensic(inc, kind)
            led.add_forensic(kind, s)
            calls.append(f"forensic_{kind}")

    if cfg.abstain:
        dec = led.decision(cfg.tau_f, cfg.tau_l)
    else:
        dec = "FRAUD" if led.p_fraud() > 0.5 else "LEGITIMATE"
    plan = kb.verification_routes(cg)
    return {
        "decision": dec,
        "p_fraud": led.p_fraud(),
        "bel_f": led.bel_f,
        "bel_l": led.bel_l,
        "conflict": led.max_conflict,
        "findings": [f for f in findings_all if f["id"] in seen],
        "retrieved": retrieved,
        "claims": cg.as_dict(),
        "ledger": led.items,
        "calls": calls,
        "latency_s": time.perf_counter() - t0,
        "verification_plan": plan,
    }
