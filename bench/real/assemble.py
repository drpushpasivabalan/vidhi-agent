"""Assemble VIDHI-Real from the item files into bench/data/real.json."""
import importlib, json, os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
PARAPHRASE = {"R-S01", "R-S02", "R-S03", "R-S06", "R-S10", "R-S11", "R-L03"}   # source summaries, not exact excerpts
CHAN = {"skype": "skype", "video_call": "video_call", "voice_call": "voice_call", "whatsapp": "whatsapp", "email": "email",
        "sms": "sms", "physical": "physical", "portal": "portal"}
items = []
for k in range(1, 12):
    m = importlib.import_module(f"bench.real.items_part{k}")
    items += m.ITEMS
ids = [x["id"] for x in items]
assert len(ids) == len(set(ids)), "duplicate ids"
out = []
for x in items:
    x = dict(x)
    x.setdefault("form", "paraphrase" if x["id"] in PARAPHRASE else "excerpts")
    if x["id"] in PARAPHRASE:
        x["form"] = "paraphrase"
    assert x["channel"] in CHAN, x["channel"]
    g = x["gold"]
    g.setdefault("payee", "none")
    x["gold_raw"] = json.loads(json.dumps(g))
    # map to the frozen claim schema (labels outside it carry no procedural rule)
    from vidhi.llm_schema import AGENCIES, INSTRUMENTS, DEMANDS
    g["agencies"] = [a for a in g["agencies"] if a in AGENCIES]
    g["instruments"] = [a for a in g["instruments"] if a in INSTRUMENTS]
    g["demands"] = [a for a in g["demands"] if a in DEMANDS]
    x.update(family=("real_fraud" if x["label"] else "real_lawful"), split="real", doc=None, audio=None, video=None,
             transcript=x["text"])
    out.append(x)
json.dump(out, open("bench/data/real.json", "w"), indent=1, ensure_ascii=False)
import collections
print(len(out), collections.Counter(x["label"] for x in out), collections.Counter(x["form"] for x in out))
print(collections.Counter(x["channel"] for x in out))
print(sorted(collections.Counter(a for x in out for a in x["gold"]["agencies"]).items()))
print(min(x["date"] for x in out), max(x["date"] for x in out))
