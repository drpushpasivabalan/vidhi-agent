# VIDHI — procedure-grounded agentic retrieval for government-impersonation fraud

Code, knowledge base and benchmark for the manuscript *Beyond Artifacts: Procedure-Grounded Agentic
Retrieval for Detecting Government-Impersonation ("Digital Arrest") Fraud Media* (R. Pushpalakshmi).

VIDHI asks whether the authority a communication claims to come from could lawfully have issued it.
It extracts a claim graph, retrieves the legal-procedural rules **in force on the communication date**,
tests them with cited predicates, lets the retrieved rules decide which tools to run (document perception,
training-free media forensics, CCS device context), and fuses the evidence with Dempster–Shafer combination,
abstaining with official verification routes when the evidence is inconclusive.

## Layout

```
vidhi/                 the framework
  kb/procedural_kb.json  versioned knowledge base (19 entries, sources, dates, URLs)
  claims.py              claim graph + reference extractor (lexicon from the DEV phrase bank only)
  procedure.py           time-aware hybrid retrieval (BM25 + signature) and invariant predicates
  docvision.py           OCR, QR decoding, seal and digital-signature detection
  forensics.py           wrapper around mmflag (training-free image/audio/video forensics)
  context.py             CCS stage model (reused unchanged)
  fusion.py              evidence ledger, Dempster–Shafer fusion, abstention
  agent.py               rule-driven planner (fail-safe early stop)
bench/                 VIDHI-Bench generators (families, DEV and TEST phrase banks, documents)
  data/                  incidents (*.json), document perception/forensic caches (*_docs.json),
                         media-pool scores (pools.json)
experiments/           prepare.py (render + perceive), harness.py, run_all.py
results/               every number reported in the paper (JSON)
third_party/           mmflag and the CCS simulator code (see their own licences)
```

## Reproduce

Requirements: Python 3.10+, numpy, scipy, scikit-learn, opencv-python, Pillow, pytesseract (+ Tesseract 5),
qrcode, rank_bm25, ffmpeg.

```bash
# results only (uses the cached perception/forensic outputs in bench/data)
python -m experiments.run_all            # ~8 min on 2 CPU cores -> results/*.json

# full rebuild of the benchmark (renders ~1,200 documents and media; ~1.5 h on 2 cores)
python -m bench.build 25                 # DEV split + DEV temporal probes
python -m experiments.prepare pools
python -m experiments.prepare dev && python -m experiments.prepare dev_temporal
python -m experiments.prepare test && python -m experiments.prepare test_temporal
```

The TEST split and probes are built by `bench.build.build("test", phrases_test.P, 50)` and
`temporal_probes(phrases_test.P, 30, "test")` (see `bench/build.py`).

## LLM claim extraction and VIDHI-Real

- `bench/real/` - the 78 VIDHI-Real items (40 frauds, 38 lawful) with source, URL, date, channel and gold claim graph;
  `python bench/real/assemble.py` writes `bench/data/real.json`. Texts are short excerpts (or marked paraphrases) of public reports.
- `vidhi/llm_schema.py` - the schema-constrained extraction prompt, the LLM-only detection prompt and the output parsers.
- `llm_runner/` - stand-alone runner (Python standard library only) for a local Ollama server:
  `ollama pull qwen2.5:3b`, `ollama pull llama3.2:3b`, then `python run_extractor.py` -> `llm_results.json` (resumable).
- `results/llm_results.json` - the raw outputs used in the paper (1,912 calls, Ollama 0.40.6, Windows, 8 GB RAM).

```bash
python -m experiments.run_llm results/llm_results.json   # -> results/llm_results_eval.json
python -m experiments.llm_significance                    # -> results/llm_significance.json
```

`Config(doc_only_requirements=True)` gives VIDHI-D, the post-hoc variant that judges document-dependent invariants
(R1-R3, A3-A5) only when a document is available; it was introduced after inspecting VIDHI-Real errors and leaves
all synthetic decisions unchanged.

## Important notes

* **All data are synthetic.** Every rendered document carries a "SYNTHETIC RESEARCH SAMPLE — NOT AN OFFICIAL
  DOCUMENT" band, no emblems, and only invented names and numbers.
* The knowledge base paraphrases public sources (I4C/MHA, Supreme Court, RBI, TRAI, CBDT, BNSS, Delhi rules,
  ED). It is **not legal advice** and must be reviewed by a legal expert before any deployment.
* The system is advisory: it never contacts anyone and never uses a number, link or account supplied by the
  counterpart.
