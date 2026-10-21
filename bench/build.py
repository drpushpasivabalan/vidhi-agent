"""VIDHI-Bench builder: incidents = device context (CCS session) + channel/date metadata +
transcript/message text + optional document image + optional audio/video media.

Usage: python -m bench.build   (writes bench/data/*.json and doc images)
"""
from __future__ import annotations

import datetime as dt
import json
import os
import random
import zlib

OUT = os.path.join(os.path.dirname(__file__), "data")
D0, D1 = dt.date(2023, 1, 1), dt.date(2026, 10, 15)
LOOKALIKE = ["https://ed-summons-verify.in/check", "https://enforcement-dir.online/verify", "https://edgov-verify.co/s"]


def seed(*p):
    return zlib.crc32("|".join(map(str, p)).encode())


def rdate(rng, lo=D0, hi=D1):
    return (lo + dt.timedelta(days=rng.randint(0, (hi - lo).days))).isoformat()


def d(s):
    return dt.date.fromisoformat(s)


class Builder:
    def __init__(self, bank, rng):
        self.P, self.rng = bank, rng
        self.parts, self.gold = [], {"agencies": set(), "instruments": set(), "demands": set(), "payee": "none"}

    def say(self, unit, p=1.0, idx=None):
        if self.rng.random() > p:
            return self
        txt, g = self.P[unit][idx] if idx is not None else self.rng.choice(self.P[unit])
        self.parts.append(txt)
        for k in ("agencies", "instruments", "demands"):
            self.gold[k] |= set(g.get(k, []))
        if g.get("payee"):
            self.gold["payee"] = g["payee"]
        return self

    def text(self):
        return " ".join(self.parts)


def _doc(header, title, to, body, date, rng, **kw):
    ref = kw.pop("ref", f"REF/{rng.randint(100, 999)}/{date[:4]}/{rng.randint(1000, 9999)}")
    spec = dict(header=header, title=title, ref=ref, date=dt.date.fromisoformat(date).strftime("%d-%m-%Y"), to=to, body=body)
    spec.update(kw)
    return spec


NAMES = ["Mr. A. Kumar", "Ms. S. Priya", "Mr. R. Menon", "Ms. K. Lakshmi", "Mr. J. Thomas", "Mr. V. Rao"]


# ------------------------------------------------------------------- families
def fam_courier(rng, P):
    b = Builder(P, rng)
    b.say("intro_courier").say("drugs").say("transfer_police").say("officer_self", 0.6)
    b.say("arrest_by_call", 0.85).say("stay_on_camera", 0.7).say("secrecy", 0.7).say("transfer_verification", 0.75)
    date = rdate(rng)
    doc = None
    if rng.random() < 0.7:
        body = [b.P["arrest_by_call"][2][0], b.P["secrecy"][0][0]]
        doc = _doc("Central Bureau of Investigation\nEconomic Offences Wing", "ARREST WARRANT", rng.choice(NAMES), body, date, rng,
                   seal=True, seal_label="CBI", signatory="Investigating Officer")
        b.gold["agencies"].add("cbi"); b.gold["instruments"] |= {"arrest_warrant", "arrest"}; b.gold["demands"].add("secrecy")
    return dict(label=1, channel=rng.choice(["video_call", "skype", "video_call"]), date=date, text=b.text(), gold=b.gold, doc=doc,
                audio="call", video=True, ccs=rng.choice(["scam_full"] * 3 + ["scam_postpay", "scam_partial", "scam_evasive"]))


def fam_ed(rng, P):
    b = Builder(P, rng)
    b.say("aadhaar_laundering").say("officer_self", 1.0, idx=2).say("arrest_by_call", 0.5)
    if rng.random() < 0.6:
        b.say("rbi_safe")
    else:
        b.say("transfer_verification")
    b.say("secrecy", 0.6).say("stay_on_camera", 0.4)
    date = rdate(rng)
    doc = None
    if rng.random() < 0.8:
        kw = dict(seal=True, seal_label="ED", signatory="Assistant Director")
        if d(date) >= dt.date(2025, 10, 8) and rng.random() < 0.5:
            kw.update(qr_url=rng.choice(LOOKALIKE) + f"?s={rng.randint(10000, 99999)}", passcode=f"{rng.randint(100000, 999999)}")
        body = ["Your account is under investigation for money laundering under PMLA.", b.P["rbi_safe"][1][0]]
        doc = _doc("Enforcement Directorate\nZonal Office", "SUMMONS UNDER SECTION 50 PMLA, 2002", rng.choice(NAMES), body, date, rng, **kw)
        b.gold["agencies"] |= {"ed", "rbi"}; b.gold["instruments"].add("summons_ed"); b.gold["demands"] |= {"safe_account", "verification_deposit"}
        if b.gold["payee"] == "none":
            b.gold["payee"] = "rbi"
    return dict(label=1, channel=rng.choice(["whatsapp", "video_call"]), date=date, text=b.text(), gold=b.gold, doc=doc,
                audio="call" if rng.random() < 0.5 else None, video=rng.random() < 0.4,
                ccs=rng.choice(["scam_full", "scam_full", "scam_postpay", "scam_partial"]))


def fam_trai(rng, P):
    b = Builder(P, rng)
    b.say("trai_disconnect").say("transfer_police").say("officer_self", 0.5).say("arrest_by_call", 0.6).say("transfer_verification", 0.7)
    date = rdate(rng)
    doc = None
    if rng.random() < 0.5:
        doc = _doc("Telecom Regulatory Authority of India", "NOTICE OF DISCONNECTION", rng.choice(NAMES),
                   [b.P["trai_disconnect"][0][0], "Contact the police cyber cell immediately to avoid legal action."], date, rng, seal=True, seal_label="TRAI")
        b.gold["agencies"] |= {"trai", "police"}; b.gold["instruments"].add("disconnection_notice")
    return dict(label=1, channel="voice_call", date=date, text=b.text(), gold=b.gold, doc=doc, audio="call", video=False,
                ccs=rng.choice(["scam_audio", "scam_full", "scam_partial"]))


def fam_fake_esummons(rng, P):
    b = Builder(P, rng)
    b.say("summons_attached").say("bail_online").say("secrecy", 0.4)
    date = rdate(rng)
    seal = rng.random() < 0.5
    doc = _doc("In the Court of the Chief Judicial Magistrate\nSample District", "SUMMONS TO ACCUSED", rng.choice(NAMES),
               ["You are summoned in the case registered against you.", b.P["bail_online"][1][0]], date, rng,
               seal=seal, seal_label="COURT", signatory="Bench Clerk")
    b.gold["agencies"].add("court"); b.gold["instruments"].add("summons_court"); b.gold["demands"].add("bail_payment_online")
    b.gold["payee"] = "caller_supplied"
    return dict(label=1, channel="whatsapp", date=date, text=b.text(), gold=b.gold, doc=doc, audio=None, video=False,
                ccs=rng.choice(["scam_postpay", "scam_partial", "scam_full"]), doc_gold=dict(has_seal=seal))


def fam_tax_scam(rng, P):
    b = Builder(P, rng)
    b.say("tax_demand_scam")
    date = rdate(rng)
    doc = _doc("Income Tax Department\nOffice of the Assessing Officer", "NOTICE OF DEMAND", rng.choice(NAMES),
               [b.P["tax_demand_scam"][1][0], "Failure to pay will lead to arrest."], date, rng, seal=rng.random() < 0.5, seal_label="ITD")
    b.gold["agencies"].add("income_tax"); b.gold["instruments"].add("tax_notice"); b.gold["demands"].add("transfer_funds")
    b.gold["payee"] = "caller_supplied"
    return dict(label=1, channel=rng.choice(["email", "whatsapp"]), date=date, text=b.text(), gold=b.gold, doc=doc, audio=None,
                video=False, ccs=rng.choice(["scam_postpay", "scam_partial"]))


def fam_s35_whatsapp(rng, P):
    b = Builder(P, rng)
    b.say("s35_whatsapp").say("stay_on_camera", 0.5).say("transfer_verification", 0.5)
    date = rdate(rng)
    doc = _doc("Office of the Station House Officer\nCyber Crime Police Station", "NOTICE UNDER SECTION 35(3) BNSS", rng.choice(NAMES),
               ["You are directed to join the video call for questioning in the case registered against you."], date, rng,
               seal=True, seal_label="SHO")
    b.gold["agencies"].add("police"); b.gold["instruments"].add("notice_s35")
    return dict(label=1, channel="whatsapp", date=date, text=b.text(), gold=b.gold, doc=doc, audio=None, video=rng.random() < 0.5,
                ccs=rng.choice(["scam_full", "scam_partial", "scam_evasive"]))


def fam_mimic(rng, P):
    """Adaptive adversary imitating lawful court procedure (seal + digital-signature line)."""
    b = Builder(P, rng)
    b.say("summons_attached").say("vc_hearing").say("secrecy", 0.5)
    date = rdate(rng, lo=dt.date(2024, 7, 1))
    doc = _doc("In the Court of the Chief Judicial Magistrate\nSample District", "SUMMONS TO ACCUSED", rng.choice(NAMES),
               ["You are summoned to appear for examination in the case registered against you.", b.P["vc_hearing"][0][0]], date, rng,
               seal=True, seal_label="COURT", ds_name="Presiding Officer", signatory="Chief Judicial Magistrate")
    b.gold["agencies"].add("court"); b.gold["instruments"] |= {"summons_court", "hearing_vc"}
    return dict(label=1, channel="whatsapp", date=date, text=b.text(), gold=b.gold, doc=doc, audio="call" if rng.random() < 0.5 else None,
                video=True, ccs=rng.choice(["scam_full", "scam_full", "scam_partial", "scam_evasive"]), adaptive=True)


def fam_voice_only(rng, P):
    b = Builder(P, rng)
    b.say("officer_self").say(rng.choice(["aadhaar_laundering", "drugs"])).say("arrest_by_call", 0.5).say("transfer_verification", 0.8)
    b.say("secrecy", 0.5)
    return dict(label=1, channel="voice_call", date=rdate(rng), text=b.text(), gold=b.gold, doc=None, audio="call", video=False,
                ccs=rng.choice(["scam_audio", "scam_audio", "scam_partial"]))


# legitimate ---------------------------------------------------------------------
def fam_court_esummons(rng, P):
    b = Builder(P, rng)
    b.say("summons_attached").say("appear_in_person", 1.0, idx=2)
    date = rdate(rng, lo=dt.date(2024, 7, 1))
    doc = _doc("In the Court of the Chief Judicial Magistrate\nSample District", "SUMMONS TO WITNESS", rng.choice(NAMES),
               ["You are summoned to appear as a witness.", b.P["appear_in_person"][2][0]], date, rng,
               seal=True, seal_label="COURT", ds_name="Presiding Officer", signatory="Chief Judicial Magistrate")
    b.gold["agencies"].add("court"); b.gold["instruments"].add("summons_court")
    return dict(label=0, channel=rng.choice(["whatsapp", "email"]), date=date, text=b.text(), gold=b.gold, doc=doc, audio=None,
                video=False, ccs=rng.choice(["b_delivery", "b_work_share", "b_family_video"]))


def fam_ed_valid(rng, P):
    b = Builder(P, rng)
    b.say("officer_self", 1.0, idx=2).say("appear_in_person", 1.0, idx=0)
    if rng.random() < 0.7:
        date = rdate(rng, lo=dt.date(2025, 10, 8))
        kw = dict(qr_url=f"https://enforcementdirectorate.gov.in/verify?s={rng.randint(10000, 99999)}", passcode=f"{rng.randint(100000, 999999)}")
    else:  # before the QR system existed: a lawful summons without QR
        date = rdate(rng, hi=dt.date(2025, 10, 7))
        kw = {}
    doc = _doc("Enforcement Directorate\nZonal Office", "SUMMONS UNDER SECTION 50 PMLA, 2002", rng.choice(NAMES),
               [b.P["appear_in_person"][0][0], "This summons can be verified on the ED website using the passcode below." if kw else
                "Please bring the documents listed in the annexure."], date, rng, seal=True, seal_label="ED", signatory="Assistant Director", **kw)
    b.gold["agencies"].add("ed"); b.gold["instruments"].add("summons_ed")
    return dict(label=0, channel=rng.choice(["email", "physical"]), date=date, text=b.text(), gold=b.gold, doc=doc, audio=None,
                video=False, ccs=rng.choice(["b_delivery", "b_work_share"]))


def fam_it_valid(rng, P):
    b = Builder(P, rng)
    b.say("tax_portal")
    date = rdate(rng, lo=dt.date(2019, 10, 1))
    din = f"ITBA/AST/S/148A/{date[:4]}-{int(date[2:4]) + 1:02d}/{rng.randint(10 ** 9, 10 ** 10 - 1)}(1)"
    doc = _doc("Income Tax Department\nOffice of the Assessing Officer", "NOTICE UNDER SECTION 148A(b)", rng.choice(NAMES),
               ["Please furnish your response on the e-filing portal within the time allowed.", b.P["tax_portal"][1][0]], date, rng,
               din=din, seal=False, signatory="Assessing Officer")
    b.gold["agencies"].add("income_tax"); b.gold["instruments"].add("tax_notice")
    return dict(label=0, channel=rng.choice(["email", "portal"]), date=date, text=b.text(), gold=b.gold, doc=doc, audio=None, video=False,
                ccs=rng.choice(["b_pay_during_call", "b_delivery"]), doc_gold=dict(has_din=True))


def fam_s35_lawful(rng, P):
    b = Builder(P, rng)
    b.say("s35_lawful")
    date = rdate(rng, lo=dt.date(2024, 7, 1))
    doc = _doc("Office of the Station House Officer\nSample Police Station", "NOTICE UNDER SECTION 35(3) BNSS", rng.choice(NAMES),
               ["You are directed to appear at the police station on the date mentioned below.", b.P["appear_in_person"][1][0]], date, rng,
               seal=True, seal_label="SHO", signatory="Station House Officer")
    b.gold["agencies"].add("police"); b.gold["instruments"].add("notice_s35"); b.gold["demands"].add("appear_in_person")
    return dict(label=0, channel="physical", date=date, text=b.text(), gold=b.gold, doc=doc, audio=None, video=False,
                ccs=rng.choice(["b_delivery", "b_family_video"]))


def fam_produce_docs(rng, P):
    b = Builder(P, rng)
    b.say("produce_docs")
    date = rdate(rng, lo=dt.date(2024, 7, 1))
    doc = _doc("Office of the Investigating Officer\nEconomic Offences Wing, Sample Police", "ORDER UNDER SECTION 94 BNSS", rng.choice(NAMES),
               [b.P["produce_docs"][0][0], "1. Bank statements for the last twelve months. 2. Copies of property records."], date, rng,
               seal=True, seal_label="EOW", signatory="Investigating Officer")
    b.gold["agencies"].add("police"); b.gold["instruments"].add("order_produce_docs"); b.gold["demands"].add("produce_documents")
    return dict(label=0, channel="email", date=date, text=b.text(), gold=b.gold, doc=doc, audio=None, video=False,
                ccs=rng.choice(["b_work_share", "b_delivery"]))


def fam_bank_alert(rng, P):
    b = Builder(P, rng)
    b.say("bank_alert", 1.0, idx=0).say("bank_alert", 1.0, idx=1).say("bank_alert", 0.7, idx=2)
    return dict(label=0, channel="voice_call", date=rdate(rng), text=b.text(), gold=b.gold, doc=None, audio="call", video=False,
                ccs=rng.choice(["b_delivery", "b_pay_during_call"]))


def fam_court_vc(rng, P):
    b = Builder(P, rng)
    b.say("summons_attached").say("vc_hearing")
    date = rdate(rng, lo=dt.date(2024, 7, 1))
    doc = _doc("In the Court of the Chief Judicial Magistrate\nSample District", "SUMMONS TO WITNESS", rng.choice(NAMES),
               ["You are summoned to give evidence in the case.", b.P["vc_hearing"][1][0]], date, rng,
               seal=True, seal_label="COURT", ds_name="Presiding Officer", signatory="Chief Judicial Magistrate")
    b.gold["agencies"].add("court"); b.gold["instruments"] |= {"summons_court", "hearing_vc"}
    return dict(label=0, channel="email", date=date, text=b.text(), gold=b.gold, doc=doc, audio=None, video=False,
                ccs=rng.choice(["b_work_share", "b_telehealth"]))


def fam_news_chat(rng, P):
    b = Builder(P, rng)
    for i in rng.sample(range(3), 2):
        b.say("news_chat", 1.0, idx=i)
    return dict(label=0, channel="video_call", date=rdate(rng), text=b.text(), gold=b.gold, doc=None, audio="call", video=True,
                ccs="b_family_video")


SCAM = [fam_courier, fam_ed, fam_trai, fam_fake_esummons, fam_tax_scam, fam_s35_whatsapp, fam_mimic, fam_voice_only]
LEGIT = [fam_court_esummons, fam_ed_valid, fam_it_valid, fam_s35_lawful, fam_produce_docs, fam_bank_alert, fam_court_vc, fam_news_chat]


# ------------------------------------------------------------------- temporal probes
def temporal_probes(P, n_each, split):
    """Pairs that differ only by date across a rule's start date. Each probe is lawful
    in every respect except possibly the date-sensitive rule."""
    out = []
    for i in range(n_each):
        for before in (True, False):
            rng = random.Random(seed("tp", split, i, before))
            # T1: Section 35 notice served on WhatsApp, appear in person, no other demand (P2 from 2025-01-21)
            date = rdate(rng, dt.date(2024, 7, 1), dt.date(2025, 1, 20)) if before else rdate(rng, dt.date(2025, 1, 21))
            b = Builder(P, rng).say("s35_whatsapp", 1.0, idx=0)
            doc = _doc("Office of the Station House Officer\nSample Police Station", "NOTICE UNDER SECTION 35(3) BNSS", rng.choice(NAMES),
                       ["You are directed to appear at the police station on the date mentioned below."], date, rng, seal=True, seal_label="SHO")
            out.append(dict(probe="T1_s35_electronic", rule="P2", should_fire=not before, channel="whatsapp", date=date, text=b.text(),
                            gold=b.gold, doc=doc, audio=None, video=False, ccs="b_delivery", label=int(not before)))
            # T2: ED summons without QR (R3 from 2025-10-08)
            rng = random.Random(seed("tp2", split, i, before))
            date = rdate(rng, dt.date(2024, 1, 1), dt.date(2025, 10, 7)) if before else rdate(rng, dt.date(2025, 10, 8))
            b = Builder(P, rng).say("officer_self", 1.0, idx=2).say("appear_in_person", 1.0, idx=0)
            doc = _doc("Enforcement Directorate\nZonal Office", "SUMMONS UNDER SECTION 50 PMLA, 2002", rng.choice(NAMES),
                       [P["appear_in_person"][0][0]], date, rng, seal=True, seal_label="ED", signatory="Assistant Director")
            out.append(dict(probe="T2_ed_no_qr", rule="R3", should_fire=not before, channel="email", date=date, text=b.text(), gold=b.gold,
                            doc=doc, audio=None, video=False, ccs="b_delivery", label=int(not before)))
            # T3: income-tax notice without DIN (R1 from 2019-10-01)
            rng = random.Random(seed("tp3", split, i, before))
            date = rdate(rng, dt.date(2018, 1, 1), dt.date(2019, 9, 30)) if before else rdate(rng, dt.date(2019, 10, 1))
            b = Builder(P, rng).say("tax_portal", 1.0, idx=0)
            doc = _doc("Income Tax Department\nOffice of the Assessing Officer", "NOTICE UNDER SECTION 143(2)", rng.choice(NAMES),
                       ["Please furnish your response within the time allowed."], date, rng, seal=False, signatory="Assessing Officer")
            out.append(dict(probe="T3_it_no_din", rule="R1", should_fire=not before, channel="email", date=date, text=b.text(), gold=b.gold,
                            doc=doc, audio=None, video=False, ccs="b_delivery", label=int(not before)))
    for j, x in enumerate(out):
        x["id"] = f"{split}-tp-{x['probe']}-{j}"
        x["family"] = x["probe"]
        x["split"] = split + "_temporal"
        x["ccs_seed"] = seed("ccs-tp", split, j)
    return out


def build(split, bank, per_family):
    incs = []
    for fams in (SCAM, LEGIT):
        for f in fams:
            for i in range(per_family):
                rng = random.Random(seed(split, f.__name__, i))
                x = f(rng, bank)
                x.update(id=f"{split}-{f.__name__[4:]}-{i}", family=f.__name__[4:], split=split, ccs_seed=seed("ccs", split, f.__name__, i))
                incs.append(x)
    return incs


def finalize(incs):
    for x in incs:
        x["gold"] = {k: sorted(v) if isinstance(v, set) else v for k, v in x["gold"].items()}
    return incs


if __name__ == "__main__":
    import sys
    from bench import phrases_dev
    os.makedirs(OUT, exist_ok=True)
    dev = finalize(build("dev", phrases_dev.P, int(sys.argv[1]) if len(sys.argv) > 1 else 25))
    dev_tp = finalize(temporal_probes(phrases_dev.P, 10, "dev"))
    json.dump(dev, open(os.path.join(OUT, "dev.json"), "w"), indent=0)
    json.dump(dev_tp, open(os.path.join(OUT, "dev_temporal.json"), "w"), indent=0)
    print(len(dev), len(dev_tp))
