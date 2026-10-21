"""Claim graph and a lightweight claim extractor (gazetteer + patterns).

The extractor's lexicon was built from the DEV phrase bank only and frozen before
the TEST bank was written. An LLM-based extractor can replace `extract` without
changing the rest of the pipeline (same ClaimGraph output).
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from urllib.parse import urlparse

LE = {"police", "cbi", "ed", "customs", "ncb", "court"}
ELECTRONIC = {"whatsapp", "email", "sms", "video_call", "voice_call", "skype"}
OFFICIAL_DOMAINS = {"enforcementdirectorate.gov.in", "www.enforcementdirectorate.gov.in", "incometax.gov.in",
                    "www.incometax.gov.in", "ecourts.gov.in", "services.ecourts.gov.in"}


@dataclass
class ClaimGraph:
    date: str
    channel: str
    agencies: set = field(default_factory=set)
    instruments: set = field(default_factory=set)
    demands: set = field(default_factory=set)
    payee: str = "none"
    has_din: bool = False
    has_qr: bool = False
    qr_official: bool | None = None
    has_seal: bool = False
    has_ds: bool = False
    cites: set = field(default_factory=set)
    evidence: dict = field(default_factory=dict)  # slot -> matched text (for explanations)

    def as_dict(self):
        d = self.__dict__.copy()
        for k in ("agencies", "instruments", "demands", "cites"):
            d[k] = sorted(d[k])
        return d


# ---- lexicon (DEV-derived) --------------------------------------------------------
AGENCY = {
    "police": r"\bpolice\b|crime branch|cyber ?crime|inspector|police station|investigating officer",
    "cbi": r"\bcbi\b|central bureau of investigation",
    "ed": r"enforcement directorate|\bed\b(?= office| officer| zonal|\b)|assistant director",
    "customs": r"\bcustoms?\b",
    "ncb": r"narcotics control bureau|\bncb\b",
    "court": r"\bcourt\b|magistrate|presiding officer|\bjudge\b",
    "trai": r"\btrai\b|telecom regulatory",
    "rbi": r"\brbi\b|reserve bank",
    "income_tax": r"income[- ]?tax|e-filing|\bitd\b",
    "bank": r"your bank|fraud monitoring|back of your card",
    "courier": r"courier|parcel|package",
}
INSTRUMENT = {
    "arrest": r"digital arrest|under arrest|arrested on this|arrest will be done|consider yourself arrested",
    "arrest_warrant": r"arrest warrant|warrant of arrest",
    "notice_s35": r"section 35\b|section 35\(|41a|41 a",
    "summons_court": r"court.*summons|summons.*court|summons to (?:appear|witness)|e-summons",
    "summons_ed": r"summons under section 50|pmla",
    "tax_notice": r"notice under section 1[0-9]{2}|income[- ]?tax.*notice|tax dues|penalty",
    "disconnection_notice": r"disconnect|sim cards? will be blocked|number will be blocked",
    "hearing_vc": r"video conferenc|hearing will be conducted through video",
    "order_produce_docs": r"produce the|production of (?:the )?documents|section 94",
}
DEMAND = {
    "transfer_funds": r"transfer (?:all )?(?:the )?(?:money|amount|funds)|move your funds|send the amount|penalty must be transferred|pay immediately to this account",
    "verification_deposit": r"verification account|fund verification|for (?:rbi |legal )?verification|refundable",
    "safe_account": r"safe account|reserve bank account|rbi account",
    "bail_payment_online": r"bail (?:amount|security).*(?:upi|online)|(?:upi|online).*bail",
    "stay_on_camera": r"camera on|stay on video|switch off the camera|leave the room|monitoring you",
    "secrecy": r"do not tell anyone|cannot discuss|inform anybody|confidential national security",
    "appear_in_person": r"appear in person|attend the court in person|appear at the police station",
    "produce_documents": r"produce the|produce .*documents",
    "pay_via_portal": r"challan|e-filing portal|official .*portal",
}
CALLER_ACCOUNT = r"account (?:number )?(?:i am sharing|we give you|given below)|this upi id|this account|account number i"


def _find(pat, text):
    m = re.search(pat, text, re.I)
    return m.group(0) if m else None


def extract(text: str, channel: str, date: str, doc: dict | None = None) -> ClaimGraph:
    t = text if not doc else text + "\n" + doc.get("text", "")
    cg = ClaimGraph(date=date, channel=channel)
    for k, p in AGENCY.items():
        if (m := _find(p, t)):
            cg.agencies.add(k)
            cg.evidence[f"agency:{k}"] = m
    for k, p in INSTRUMENT.items():
        if (m := _find(p, t)):
            cg.instruments.add(k)
            cg.evidence[f"instrument:{k}"] = m
    for k, p in DEMAND.items():
        if (m := _find(p, t)):
            cg.demands.add(k)
            cg.evidence[f"demand:{k}"] = m
    if cg.demands & {"transfer_funds", "verification_deposit", "safe_account", "bail_payment_online"}:
        if "safe_account" in cg.demands or re.search(r"\brbi\b|reserve bank", t, re.I):
            cg.payee = "rbi" if "safe_account" in cg.demands else "caller_supplied"
        else:
            cg.payee = "caller_supplied"
        if re.search(CALLER_ACCOUNT, t, re.I):
            cg.payee = "rbi" if cg.payee == "rbi" else "caller_supplied"
    elif "pay_via_portal" in cg.demands:
        cg.payee = "official_portal"
    cg.has_din = bool(re.search(r"\bDIN\b\s*[:\-]?\s*[A-Z0-9/\-()]{8,}", t))
    if re.search(r"section\s+\d+[A-Z]?\s*(?:of\s+the\s+)?(?:crpc|code of criminal|ipc)|41a crpc|\bipc\b|\bcrpc\b", t, re.I):
        cg.cites.add("old")
    if re.search(r"bnss|bharatiya|\bbns\b", t, re.I):
        cg.cites.add("new")
    if doc:
        cg.has_seal = bool(doc.get("seal"))
        cg.has_ds = bool(doc.get("digital_signature"))
        if doc.get("qr"):
            cg.has_qr = True
            host = urlparse(doc["qr"]).netloc.lower()
            cg.qr_official = host in OFFICIAL_DOMAINS
        if re.search(r"\bsummons\b", doc.get("text", ""), re.I) and "court" in cg.agencies:
            cg.instruments.add("summons_court")
        if re.search(r"\bsummons\b", doc.get("text", ""), re.I) and "ed" in cg.agencies:
            cg.instruments.add("summons_ed")
    # channel-implied: a WhatsApp/Skype video call is also a call
    return cg
