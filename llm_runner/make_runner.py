"""Generate the stand-alone runner (stdlib only) with the prompts embedded from vidhi/llm_schema.py."""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from vidhi import llm_schema as S

TEMPLATE = r'''#!/usr/bin/env python3
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
EXTRACT_SYSTEM = __EXTRACT_SYSTEM__
DETECT_SYSTEM = __DETECT_SYSTEM__
FEWSHOT = __FEWSHOT__
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
'''
code = (TEMPLATE.replace("__EXTRACT_SYSTEM__", repr(S.EXTRACT_SYSTEM))
        .replace("__DETECT_SYSTEM__", repr(S.DETECT_SYSTEM))
        .replace("__FEWSHOT__", repr([(t, y) for t, y in S.FEWSHOT])))
open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "run_extractor.py"), "w").write(code)
print("written")
