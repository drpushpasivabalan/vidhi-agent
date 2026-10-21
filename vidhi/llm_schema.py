"""Schema-constrained LLM claim extraction and LLM-only detection prompts.

The schema is the frozen claim-graph vocabulary of VIDHI (claims.py, 15 Oct 2026) plus
`isolation`, which the knowledge base (P6) already uses. Few-shot examples are taken
only from the DEV phrase bank. The same prompts are embedded in the stand-alone runner
(llm_runner/run_extractor.py), which is generated from this module.
"""
from __future__ import annotations

import json
import re

AGENCIES = {
    "police": "any police unit, crime branch, cyber cell, police officer",
    "cbi": "Central Bureau of Investigation",
    "ed": "Enforcement Directorate",
    "customs": "customs department or customs officer",
    "ncb": "Narcotics Control Bureau",
    "court": "any court, judge or magistrate (including the Supreme Court)",
    "trai": "TRAI or any telecom authority/department",
    "rbi": "Reserve Bank of India",
    "income_tax": "Income Tax Department",
    "bank": "a bank's own staff or fraud desk",
    "courier": "a courier or parcel company (FedEx, DHL, etc.)",
}
INSTRUMENTS = {
    "arrest": "the person is told they are arrested / under (digital) arrest or custody",
    "arrest_warrant": "an arrest warrant is mentioned",
    "notice_s35": "a notice of appearance under Section 35 BNSS or Section 41A CrPC",
    "summons_court": "a summons issued by a court",
    "summons_ed": "a summons issued by the Enforcement Directorate",
    "tax_notice": "an income-tax notice, demand or penalty",
    "disconnection_notice": "a notice that a mobile number / SIM will be disconnected or blocked",
    "hearing_vc": "a court hearing or examination by video conference",
    "order_produce_docs": "an order to produce documents or records",
}
DEMANDS = {
    "transfer_funds": "asked to transfer, deposit or pay money (other than through an official portal)",
    "verification_deposit": "money is said to be for verification / checking and to be refunded",
    "safe_account": "money to be kept in an 'RBI', 'safe', 'secret' or supervision account",
    "bail_payment_online": "bail to be paid online / by UPI",
    "stay_on_camera": "must stay on a video call / keep the camera on / under watch",
    "secrecy": "must not tell family or anyone",
    "isolation": "must stay alone, isolated, or not leave home",
    "appear_in_person": "asked to appear in person at an office, police station or court",
    "produce_documents": "asked to produce or submit documents",
    "pay_via_portal": "asked to pay or respond through an official government portal",
}
PAYEES = ["none", "caller_supplied", "rbi", "official_portal"]

FEWSHOT = [
    ("Please hold, the CBI officer will now speak to you on video call. Consider yourself arrested, the arrest will be done on this "
     "video call. Do not tell anyone about this, not even your family members. Send the amount by RTGS to the account number I am "
     "sharing for fund verification.",
     {"agencies": ["cbi"], "instruments": ["arrest"], "demands": ["secrecy", "transfer_funds", "verification_deposit"], "payee": "caller_supplied"}),
    ("Please find the court e-summons attached. You are directed to attend the court in person on the next date of hearing.",
     {"agencies": ["court"], "instruments": ["summons_court"], "demands": ["appear_in_person"], "payee": "none"}),
    ("I am an Assistant Director, Enforcement Directorate. You are required to appear in person at the office on the date mentioned "
     "with the documents. Deposit the funds in the Reserve Bank account for legal verification.",
     {"agencies": ["ed", "rbi"], "instruments": ["summons_ed"], "demands": ["appear_in_person", "safe_account", "verification_deposit"],
      "payee": "rbi"}),
]


def _defs(d):
    return "\n".join(f"  - {k}: {v}" for k, v in d.items())


EXTRACT_SYSTEM = (
    "You extract structured claims from a message, call transcript or report about a communication that claims to come "
    "from an Indian authority. Report only what the text states; do not judge whether it is genuine.\n"
    "Return a JSON object with exactly these keys:\n"
    "agencies: list from\n" + _defs(AGENCIES) + "\n"
    "instruments: list from\n" + _defs(INSTRUMENTS) + "\n"
    "demands: list from\n" + _defs(DEMANDS) + "\n"
    "payee: one of none | caller_supplied (an account/UPI given by the caller or sender) | rbi (an account said to be RBI's) "
    "| official_portal (a government portal)\n"
    "Use only the listed labels. Use empty lists when nothing applies."
)

DETECT_SYSTEM = (
    "You decide whether a communication that claims to come from an Indian authority (police, CBI, ED, customs, NCB, courts, "
    "TRAI, RBI, Income Tax) is a fraud/impersonation or a legitimate communication. "
    "Return a JSON object: {\"label\": \"fraud\" or \"legitimate\", \"confidence\": number between 0 and 1}."
)


def extract_messages(text, channel, date):
    msgs = [{"role": "system", "content": EXTRACT_SYSTEM}]
    for t, y in FEWSHOT:
        msgs.append({"role": "user", "content": f"Channel: whatsapp\nText: {t}"})
        msgs.append({"role": "assistant", "content": json.dumps(y)})
    msgs.append({"role": "user", "content": f"Channel: {channel}\nText: {text}"})
    return msgs


def detect_messages(text, channel, date):
    return [{"role": "system", "content": DETECT_SYSTEM},
            {"role": "user", "content": f"Date: {date}\nChannel: {channel}\nText: {text}"}]


def _as_list(v):
    if v is None:
        return []
    if isinstance(v, str):
        return [s.strip() for s in re.split(r"[,;|]", v) if s.strip()]
    if isinstance(v, (list, tuple)):
        out = []
        for e in v:
            out += _as_list(e) if not isinstance(e, str) else [e.strip()]
        return out
    return []


def _norm(s):
    return re.sub(r"[^a-z0-9_]", "", str(s).lower().replace(" ", "_").replace("-", "_"))


def parse_extraction(raw: str):
    """Parse model output into the schema; unknown labels are dropped. Returns (claims, ok)."""
    try:
        obj = json.loads(raw)
    except Exception:
        m = re.search(r"\{.*\}", raw or "", re.S)
        if not m:
            return {"agencies": [], "instruments": [], "demands": [], "payee": "none"}, False
        try:
            obj = json.loads(m.group(0))
        except Exception:
            return {"agencies": [], "instruments": [], "demands": [], "payee": "none"}, False
    out = {}
    for key, vocab in (("agencies", AGENCIES), ("instruments", INSTRUMENTS), ("demands", DEMANDS)):
        vals = [_norm(v) for v in _as_list(obj.get(key))]
        out[key] = sorted({v for v in vals if v in vocab})
    p = _norm(obj.get("payee", "none"))
    out["payee"] = p if p in PAYEES else "none"
    return out, True


def parse_detection(raw: str):
    try:
        obj = json.loads(raw)
    except Exception:
        m = re.search(r"\{.*\}", raw or "", re.S)
        try:
            obj = json.loads(m.group(0)) if m else {}
        except Exception:
            obj = {}
    lab = str(obj.get("label", "")).lower()
    try:
        conf = float(obj.get("confidence", 0.5))
    except Exception:
        conf = 0.5
    conf = min(max(conf, 0.0), 1.0)
    if "fraud" in lab or "scam" in lab or "fake" in lab:
        p = 0.5 + conf / 2
    elif "legit" in lab or "genuine" in lab:
        p = 0.5 - conf / 2
    else:
        return 0.5, False
    return p, True
