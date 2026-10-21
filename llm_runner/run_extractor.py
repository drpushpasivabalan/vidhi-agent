#!/usr/bin/env python3
"""VIDHI LLM runner - runs claim extraction and LLM-only detection with local Ollama models.

Usage (Windows Command Prompt, macOS or Linux terminal), from this folder:
    python run_extractor.py

Requirements: Python 3.8+ and Ollama running with the models pulled:
    ollama pull qwen2.5:3b
    ollama pull llama3.2:3b
The script is resumable: if you stop it (Ctrl+C) or the computer sleeps, run it again and it continues.
When it finishes (or whenever you want to stop), send the file  llm_results.json  back.
"""
import json, os, sys, time, urllib.request, urllib.error, platform

HERE = os.path.dirname(os.path.abspath(__file__))
OLLAMA = os.environ.get("OLLAMA_HOST", "http://127.0.0.1:11434").rstrip("/")
if not OLLAMA.startswith("http"):
    OLLAMA = "http://" + OLLAMA
OUT = os.path.join(HERE, "llm_results.json")
EXTRACT_SYSTEM = "You extract structured claims from a message, call transcript or report about a communication that claims to come from an Indian authority. Report only what the text states; do not judge whether it is genuine.\nReturn a JSON object with exactly these keys:\nagencies: list from\n  - police: any police unit, crime branch, cyber cell, police officer\n  - cbi: Central Bureau of Investigation\n  - ed: Enforcement Directorate\n  - customs: customs department or customs officer\n  - ncb: Narcotics Control Bureau\n  - court: any court, judge or magistrate (including the Supreme Court)\n  - trai: TRAI or any telecom authority/department\n  - rbi: Reserve Bank of India\n  - income_tax: Income Tax Department\n  - bank: a bank's own staff or fraud desk\n  - courier: a courier or parcel company (FedEx, DHL, etc.)\ninstruments: list from\n  - arrest: the person is told they are arrested / under (digital) arrest or custody\n  - arrest_warrant: an arrest warrant is mentioned\n  - notice_s35: a notice of appearance under Section 35 BNSS or Section 41A CrPC\n  - summons_court: a summons issued by a court\n  - summons_ed: a summons issued by the Enforcement Directorate\n  - tax_notice: an income-tax notice, demand or penalty\n  - disconnection_notice: a notice that a mobile number / SIM will be disconnected or blocked\n  - hearing_vc: a court hearing or examination by video conference\n  - order_produce_docs: an order to produce documents or records\ndemands: list from\n  - transfer_funds: asked to transfer, deposit or pay money (other than through an official portal)\n  - verification_deposit: money is said to be for verification / checking and to be refunded\n  - safe_account: money to be kept in an 'RBI', 'safe', 'secret' or supervision account\n  - bail_payment_online: bail to be paid online / by UPI\n  - stay_on_camera: must stay on a video call / keep the camera on / under watch\n  - secrecy: must not tell family or anyone\n  - isolation: must stay alone, isolated, or not leave home\n  - appear_in_person: asked to appear in person at an office, police station or court\n  - produce_documents: asked to produce or submit documents\n  - pay_via_portal: asked to pay or respond through an official government portal\npayee: one of none | caller_supplied (an account/UPI given by the caller or sender) | rbi (an account said to be RBI's) | official_portal (a government portal)\nUse only the listed labels. Use empty lists when nothing applies."
DETECT_SYSTEM = 'You decide whether a communication that claims to come from an Indian authority (police, CBI, ED, customs, NCB, courts, TRAI, RBI, Income Tax) is a fraud/impersonation or a legitimate communication. Return a JSON object: {"label": "fraud" or "legitimate", "confidence": number between 0 and 1}.'
FEWSHOT = [('Please hold, the CBI officer will now speak to you on video call. Consider yourself arrested, the arrest will be done on this video call. Do not tell anyone about this, not even your family members. Send the amount by RTGS to the account number I am sharing for fund verification.', {'agencies': ['cbi'], 'instruments': ['arrest'], 'demands': ['secrecy', 'transfer_funds', 'verification_deposit'], 'payee': 'caller_supplied'}), ('Please find the court e-summons attached. You are directed to attend the court in person on the next date of hearing.', {'agencies': ['court'], 'instruments': ['summons_court'], 'demands': ['appear_in_person'], 'payee': 'none'}), ('I am an Assistant Director, Enforcement Directorate. You are required to appear in person at the office on the date mentioned with the documents. Deposit the funds in the Reserve Bank account for legal verification.', {'agencies': ['ed', 'rbi'], 'instruments': ['summons_ed'], 'demands': ['appear_in_person', 'safe_account', 'verification_deposit'], 'payee': 'rbi'})]
# (stage, model, task): stage 1 = 78 real messages, stage 2 = 400 benchmark incidents
PLAN = [(1, "qwen2.5:3b", "extract"), (1, "qwen2.5:3b", "detect"),
        (1, "llama3.2:3b", "extract"), (1, "llama3.2:3b", "detect"),
        (2, "qwen2.5:3b", "extract"), (2, "qwen2.5:3b", "detect"),
        (2, "llama3.2:3b", "extract"), (2, "llama3.2:3b", "detect")]


def post(path, payload, timeout=600):
    req = urllib.request.Request(OLLAMA + path, data=json.dumps(payload).encode("utf-8"),
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8"))


def get(path, timeout=30):
    with urllib.request.urlopen(OLLAMA + path, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8"))


def messages(task, it):
    if task == "extract":
        msgs = [{"role": "system", "content": EXTRACT_SYSTEM}]
        for t, y in FEWSHOT:
            msgs.append({"role": "user", "content": "Channel: whatsapp\nText: " + t})
            msgs.append({"role": "assistant", "content": json.dumps(y)})
        msgs.append({"role": "user", "content": "Channel: %s\nText: %s" % (it["channel"], it["text"])})
        return msgs
    return [{"role": "system", "content": DETECT_SYSTEM},
            {"role": "user", "content": "Date: %s\nChannel: %s\nText: %s" % (it["date"], it["channel"], it["text"])}]


def call(model, task, it):
    payload = {"model": model, "messages": messages(task, it), "stream": False, "format": "json",
               "keep_alive": "30m",
               "options": {"temperature": 0, "seed": 7, "num_predict": 220 if task == "extract" else 60, "num_ctx": 4096}}
    t0 = time.time()
    r = post("/api/chat", payload)
    return {"raw": r.get("message", {}).get("content", ""), "seconds": round(time.time() - t0, 2),
            "prompt_tokens": r.get("prompt_eval_count"), "output_tokens": r.get("eval_count")}


def save(res):
    tmp = OUT + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(res, f, ensure_ascii=False)
    os.replace(tmp, OUT)


def main():
    items = json.load(open(os.path.join(HERE, "vidhi_inputs.json"), encoding="utf-8"))["items"]
    try:
        tags = get("/api/tags")
    except Exception as e:
        print("\nCannot reach Ollama at %s.\nOpen the Ollama app (or run 'ollama serve') and try again.\n(%s)" % (OLLAMA, e))
        sys.exit(1)
    have = {m.get("name") for m in tags.get("models", [])} | {m.get("model") for m in tags.get("models", [])}
    models = sorted({m for _, m, _ in PLAN})
    missing = [m for m in models if m not in have]
    if missing:
        print("\nThese models are not installed yet: %s\nRun:  %s\nthen start this script again.\n"
              % (", ".join(missing), "   ".join("ollama pull " + m for m in missing)))
        sys.exit(1)
    res = json.load(open(OUT, encoding="utf-8")) if os.path.exists(OUT) else {}
    res.setdefault("_meta", {"machine": platform.platform(), "python": platform.python_version(), "ollama": OLLAMA, "started": time.ctime()})
    try:
        res["_meta"]["ollama_version"] = get("/api/version").get("version")
    except Exception:
        pass
    total = sum(1 for st, _, _ in PLAN for it in items if it["stage"] == st)
    done = sum(1 for k in res if not k.startswith("_"))
    times = []
    print("VIDHI LLM runner: %d of %d calls already done. Press Ctrl+C to pause at any time.\n" % (done, total))
    for st, model, task in PLAN:
        for it in items:
            if it["stage"] != st:
                continue
            key = "%s|%s|%s" % (model, task, it["id"])
            if key in res:
                continue
            for attempt in range(3):
                try:
                    res[key] = call(model, task, it)
                    break
                except (urllib.error.URLError, TimeoutError, ConnectionError) as e:
                    print("  retrying after error: %s" % e)
                    time.sleep(5)
            else:
                print("  giving up on %s for now" % key)
                continue
            done += 1
            times.append(res[key]["seconds"])
            if done % 5 == 0 or done == total:
                save(res)
                avg = sum(times[-50:]) / len(times[-50:])
                left = (total - done) * avg / 3600
                print("  %4d / %d done  (stage %d, %s, %s)  ~%.1f h left" % (done, total, st, model, task, left))
        save(res)
        if st == 1 and all(("%s|%s|%s" % (m, t, it["id"])) in res for s2, m, t in PLAN if s2 == 1 for it in items if it["stage"] == 1):
            print("\nStage 1 (real messages) complete. You can already send llm_results.json; the script continues with stage 2.\n")
    res["_meta"]["finished"] = time.ctime()
    save(res)
    print("\nAll done. Please send the file: %s" % OUT)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nPaused. Progress is saved in llm_results.json - run the script again to continue.")
