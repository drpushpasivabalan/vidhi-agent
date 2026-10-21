"""Time-versioned procedural RAG: retrieve KB entries for a claim graph, then test them.

Retrieval = BM25 over entry text + structured signature match, filtered by the
effective date of each entry relative to the communication date.
Verification = an auditable predicate per entry evaluated on the claim graph.
"""
from __future__ import annotations

import json
import os
import re

from rank_bm25 import BM25Okapi

from .claims import ELECTRONIC, LE, ClaimGraph

KB_PATH = os.path.join(os.path.dirname(__file__), "kb", "procedural_kb.json")
CALLS = {"video_call", "voice_call", "whatsapp", "skype"}
MONEY = {"transfer_funds", "verification_deposit", "bail_payment_online"}


def _tok(s):
    return re.findall(r"[a-z0-9]+", s.lower())


class ProceduralKB:
    def __init__(self, path=KB_PATH):
        kb = json.load(open(path))
        self.meta = kb["_meta"]
        self.entries = {e["id"]: e for e in kb["entries"]}
        self.ids = list(self.entries)
        docs = []
        for i in self.ids:
            e = self.entries[i]
            sig = " ".join(" ".join(v) for v in e["signature"].values())
            docs.append(_tok(e["title"] + " " + e["text"] + " " + sig.replace("_", " ")))
        self.bm25 = BM25Okapi(docs)

    # ---------------------------------------------------------------- retrieval
    def query_tokens(self, cg: ClaimGraph, text: str):
        slots = list(cg.agencies) + list(cg.instruments) + list(cg.demands) + [cg.channel, cg.payee]
        return _tok(" ".join(s.replace("_", " ") for s in slots) + " " + text[:600])

    def sig_match(self, e, cg: ClaimGraph):
        s = e["signature"]
        m = 0.0
        if "agency" in s and ("*" in s["agency"] or set(s["agency"]) & cg.agencies):
            m += 1
        if "instrument" in s and set(s["instrument"]) & cg.instruments:
            m += 1.5
        if "demand" in s and set(s["demand"]) & cg.demands:
            m += 1.5
        if "channel" in s and cg.channel in s["channel"]:
            m += 0.5
        if "cites" in s and "old" in cg.cites:
            m += 1
        return m

    def in_force(self, e, date):
        ef = e.get("effective_from")
        return ef is None or date >= ef

    def retrieve(self, cg: ClaimGraph, text: str, k=6, versioned=True, kinds=("prohibitive", "requirement", "permissive")):
        q = self.query_tokens(cg, text)
        bm = self.bm25.get_scores(q)
        mx = max(bm.max(), 1e-9)
        scored = []
        for i, idx in zip(self.ids, range(len(self.ids))):
            e = self.entries[i]
            if e["kind"] not in kinds:
                continue
            if versioned and not self.in_force(e, cg.date):
                continue
            s = bm[idx] / mx + self.sig_match(e, cg)
            scored.append((s, i))
        scored.sort(reverse=True)
        return [i for s, i in scored[:k] if s > 0.5]

    def verification_routes(self, cg: ClaimGraph):
        out = []
        for i, e in self.entries.items():
            if e["kind"] != "verification" or not self.in_force(e, cg.date):
                continue
            ag = e["signature"].get("agency", [])
            if "*" in ag or set(ag) & cg.agencies:
                out.append({"id": i, "action": e["text"], "url": e["urls"][0]})
        return out


# ---------------------------------------------------------------- predicates
def _p(cg: ClaimGraph):
    a, ins, d, ch = cg.agencies, cg.instruments, cg.demands, cg.channel
    le = bool(a & LE)
    return {
        "P1": "arrest" in ins and ch in CALLS and le,
        "P2": "notice_s35" in ins and ch in ELECTRONIC,
        "P3": bool(d & (MONEY | {"safe_account"})) and cg.payee in ("caller_supplied", "rbi") and bool(a & (LE | {"rbi", "trai", "income_tax"})),
        "P4": ("rbi" in a or cg.payee == "rbi") and bool(d & (MONEY | {"safe_account"})),
        "P5": "trai" in a and "disconnection_notice" in ins,
        "P6": bool(d & {"stay_on_camera", "secrecy", "isolation"}) and le,
        "R1": "income_tax" in a and "tax_notice" in ins and not cg.has_din,
        "R2": "summons_court" in ins and ch in {"whatsapp", "email", "sms"} and not (cg.has_seal and cg.has_ds),
        "R3": "ed" in a and "summons_ed" in ins and (not cg.has_qr or cg.qr_official is False),
        "R4": cg.cites == {"old"},
        "A1": "court" in a and "hearing_vc" in ins,
        "A2": "order_produce_docs" in ins and not (d & MONEY),
        "A3": "summons_court" in ins and cg.has_seal and cg.has_ds,
        "A4": "income_tax" in a and cg.has_din,
        "A5": "ed" in a and "summons_ed" in ins and cg.has_qr and cg.qr_official is True and "appear_in_person" in d,
    }


def verify(kb: ProceduralKB, cg: ClaimGraph, ids):
    """Evaluate retrieved entries; return findings with citations."""
    preds = _p(cg)
    out = []
    for i in ids:
        if i not in preds or not preds[i]:
            continue
        e = kb.entries[i]
        strength = e["strength"]
        if i == "R3" and cg.has_qr and cg.qr_official is False:
            strength = "hard"  # QR present but resolves outside the agency's domain
        kind = "violation" if e["kind"] in ("prohibitive", "requirement") else "consistent"
        out.append({"id": i, "type": kind, "strength": strength, "title": e["title"],
                    "citation": e["sources"][0], "url": e["urls"][0]})
    return out


def all_rule_ids(kb):
    return [i for i, e in kb.entries.items() if e["kind"] != "verification"]
