# mmflag — lightweight manipulated-media flagger

A training-free detector for tampered **images**, **audio** and **video** of the kind that
circulates around official communications (forged notices and "arrest warrants",
spliced or cloned-voice calls, face-swapped "officer" video statements). Every file gets a
single **`confidence_manipulated` score in [0, 1]**, a verdict, and the per-cue evidence
behind it (where in the image, when in the clip).

* Dependencies: `numpy`, `scipy`, `opencv-python`, `Pillow`, and `ffmpeg` on the PATH
  (for compressed audio/video). `scikit-learn` + `matplotlib` only for `evaluate.py`.
* No model weights, no GPU, no network. About 0.5–1 s per document image, < 0.1 s per
  6-s audio clip, ~1 s per 4-s 480p video on a laptop-class CPU.

## Usage

```bash
python -m mmflag notice.jpg call.wav statement.mp4            # one line per file
python -m mmflag notice.jpg --heatmaps out/ --json            # full JSON + heat-map PNG
```

```python
from mmflag import analyze
r = analyze("notice.jpg", heatmap_path="notice_heatmap.png")
r["confidence_manipulated"], r["verdict"], r["cues"]
```

Verdict bands: `< 0.35` NO_STRONG_EVIDENCE · `0.35–0.65` SUSPICIOUS_REVIEW · `≥ 0.65` LIKELY_MANIPULATED.

## How the score is formed

Each cue turns a forensic statistic into a probability-like value `p_i` with a logistic
curve, and cues are combined with a **weighted noisy-OR**:
`score = 1 − Π (1 − p_i)^w_i` — one strong cue is enough to raise the flag, weak cues add up.
Thresholds use per-file robust statistics (median/MAD), so each file is judged against
itself rather than against a dataset.

| Modality | Cue | What it detects | Weight |
|---|---|---|---|
| Image | `noise_inconsistency` | Region whose scan/sensor noise differs from the rest (re-typed text, pasted patch). Immerkaer noise estimate on edge-free pixels, clustered robust-z blocks. | 1.0 |
| Image | `compression_inconsistency` | Region with a different JPEG history: 8×8 grid energy at a shifted phase or different strength. | 0.8 |
| Image | `copy_move` | Cloned seal / signature / stamp: ORB self-matches sharing one displacement vector. | 1.0 |
| Image | `metadata` | Editing-software tags in EXIF (weak; easily stripped). | 0.5 |
| Audio | `noise_floor_jump` | Background tone measured in true (stationary) pauses changes between pauses → insert from another recording. | 1.0 |
| Audio | `splice_click` | Sample-level discontinuity of a hard cut. | 0.7 |
| Audio | `digital_silence` | Pauses fall to near digital zero — generated (TTS/clone) audio, never a real mic or line. | 0.9 |
| Audio | `pitch_regularity` | Unnaturally smooth pitch micro-variation (low jitter). | 0.6 |
| Audio | `bandwidth` | No energy above ~4 kHz in a 16 kHz file (8 kHz vocoder). Weak: real phone calls look the same. | 0.35 |
| Video | `region_sharpness_inconsistency` | A persistently *softer* region (face-swap output, pasted overlay): Laplacian/gradient edge-sharpness per block, averaged over frames, only edge-bearing blocks. | 1.0 |
| Video | `temporal_discontinuity` | Abrupt jump in frame-to-frame change → inserted/removed segment. | 0.8 |
| Video | `audio_track` | The soundtrack run through the audio detector. | 0.8 |

## Results on held-out synthetic media

`python evaluate.py` regenerates fresh samples from seeds not used while choosing
thresholds and reports (threshold 0.5):

| Set | n authentic | n manipulated | ROC-AUC | Detection rate | False-alarm rate | Accuracy |
|---|---|---|---|---|---|---|
| Image (document notices) | 40 | 60 | 0.945 | 83.3% | 0.0% | 90.0% |
| Image, re-shared (75 % resize + JPEG q70) | 20 | 20 | 0.995 | 90.0% | 0.0% | 95.0% |
| Audio (call clips) | 40 | 40 | 0.915 | 75.0% | 5.0% | 85.0% |
| Video (statement clips, H.264+AAC) | 12 | 24 | 1.000 | 100.0% | 0.0% | 100.0% |

By manipulation type: copy-move 100 %, re-typed text splice 95 %, splice from another
scan 55 %; cloned/synthetic voice 100 %, audio splices ~50 % (45 % with crossfade, 56 %
hard cut); face swap 100 %, video segment insert 100 %. Full table:
`results/eval_summary.md`, per-sample scores: `results/eval_results.json`,
plots: `results/eval_plots.png`.

**Read these numbers as a functional test, not a benchmark.** All media are synthetic and
the manipulations were written by the same author as the detector, so they exercise the
cues they were designed for. Expect lower numbers on real material.

v0.2 change: the copy-move cue now ignores repeats on the same text line, and the JPEG-grid cue keeps
further away from ruled lines and strokes. On text-dense official documents (the VIDHI benchmark) this
removed false flags on clean documents (0 of 611 flagged) at the cost of one fewer detected
foreign-scan splice in the table above.

## Known limitations (important)

* **Not a trained deepfake classifier.** Fully AI-generated images, modern neural TTS with
  added room noise, and high-quality face-reenactment that preserves sharpness can pass.
  The design leaves room for a learned cue: add any model's output as another
  `{"p": ..., "stat": ...}` entry in `cues` with a weight, and `fuse` handles the rest.
* **Re-encoding erases evidence.** Heavy compression, screenshots and resizing weaken the
  noise and grid cues (the forwarded set held up here; aggressive chains will not).
* **Legitimate edits flag too.** A letterhead logo used twice, a genuine scene cut in a
  video, or telephone noise suppression (comfort-noise / gating) can raise cues.
* **Audio splices are the weakest case** (~50 %): an insert with a similar background and no
  pauses leaves little evidence for a content-free method.
* The score is **evidence for human review**, not proof. Do not use it alone to accuse
  anyone or to declare a communication genuine.

## Layout

```
mmflag/           detector package (common.py, image.py, audio.py, video.py, CLI)
samples/          generators for synthetic authentic/manipulated media (fictitious content)
demo/             one sample of each kind + image heat-maps
evaluate.py       held-out evaluation  ->  results/
make_demo.py      rebuilds demo/
```

Demo set note: of the 10 demo files, two manipulated ones are deliberately left as
misses (`notice_splice_foreign.jpg`, `call_splice.wav`) — they are representative of the
cases above that the detector does not reliably catch.
