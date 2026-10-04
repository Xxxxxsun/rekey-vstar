# ReKey — Paper Blueprint

Date: 2026-05-20
Method name: **ReKey** (Metadata-Grounded Visual-Key Regeneration)

**Related docs:**
- `experiment_results.md` — all numbers, settings, known issues (single source of truth for data)
- `../../HANDOVER.md` — how to run eval, benchmark structure, model IDs (for new agents)
- `terminology_and_methodology.md` — methodology terminology and design decisions
- `overleaf/sections/experiments.tex` — latest experiment writing

This file covers paper structure, contributions, and positioning.

---

## 1. One-Paragraph Summary

Static VQA benchmarks age quickly: once items leak into training corpora,
scores reflect recall as much as perception. Existing dynamic methods either
refresh content without controlling difficulty, perturb surface features
while preserving the leaked answer, or synthesize scenes lacking the
structure of real photographs. We propose ReKey, a metadata-grounded
visual-key regeneration framework. On V*Bench, human annotators mark compact
local regions where a visual key can be added or refreshed. A rule-based
pipeline then samples edit content, applies localized image edits, and
constructs questions from sampled metadata and edit-region geometry, with no
model in the answer loop. This turns each source image into many fresh
instances with different correct answers while preserving the high-resolution
small-target search regime.

---

## 2. Motivation

All eight evaluated VLMs drop 11.5–23.6pp when visual keys are switched
(contamination audit in appendix, full data in `experiment_results.md`).
Static relabeling is a one-time fix that leaks once released.

---

## 3. Method

### 3.1 Design philosophy

Humans identify WHERE a visual key can plausibly exist. The system
decides WHAT to place there at evaluation time.

### 3.2 Human-annotated edit slots

Each image carries edit slots with context box + edit box.

- **Replace**: annotator picks uniquely identifiable V*Bench visual keys.
  Pipeline recolors them, preserving search difficulty.
- **Add**: annotator checks absent objects from placement-compatible list.
  Unique by construction.

### 3.3 Edit-slot sampling

- Attr question: sample 1 slot (replace or add) + random color
- Position question: sample 2 slots (any combination)
- Different seeds → different sampling records → different answers

### 3.4 Localized image editing

Context crop → image editor (GPT-Image-2) → composite back.
Edit confined to edit region; original pixels outside preserved.

### 3.5 Metadata-grounded QA construction

- Color Q: strip color from target_ref → "What color is {object}?" Answer = sampled color.
- Position Q: compare center coordinates → "Is {A} left/right of {B}?" Fallback above/below.
- All answers determined by sampling record. No VLM judge.

---

## 4. Experiments

Structure follows tex (`sections/experiments.tex`).

### Contamination motivation (appendix)

8 models, all drop 11.5–23.6pp. Full table in appendix.
Inline: "all eight models drop 11–24pp."

### RQ1: Does ReKey remove the contamination benefit?

8 standard VLMs × 3 seeds. See `experiment_results.md` → RQ1.
Key: all drop from Original, land near Relabel (avg +4.5pp from Relabel).

Agentic VLMs: TODO (SEAL / tool-augmented models).

### RQ2: Does ReKey preserve the original difficulty?

LLaVA-1.5-13B: 48.7% → 41.5% (overall -7.2pp, position -3.5pp).
Far smaller than frontier gaps (10–17pp). See `experiment_results.md` → RQ2.

### RQ3: Why can't VLMs annotate their own benchmark?

GPT-5.5 VLM annotation → add-only benchmark (189 items).
All 6 models +7.6 to +16.5pp on VLM benchmark vs human benchmark.
VLM add regions 3.2× larger (saliency bias).
See `experiment_results.md` → RQ3.

---

## 5. Three Contributions

1. **Visual-key regeneration.** ReKey refreshes the answer-bearing visual
   evidence rather than perturbing surface features.

2. **Metadata-grounded pipeline.** Human-marked edit regions + rule-based
   sampling + programmatic QA = unbounded fresh items with constructive
   ground truth, no judge circularity.

3. **Empirical validation on V*Bench.** 8-model contamination audit
   (11.5–23.6pp inflation) + ReKey removes inflation while preserving
   difficulty and ranking stability.

---

## 6. Non-Claims

- Not "first dynamic VLM benchmark" (VLB, LiveXiv predate us)
- Not "open-set object insertion" (closed library is deliberate)
- Not claiming V*Bench is the only contaminated benchmark

---

## 7. Key Risks

| Risk | Mitigation |
|------|-----------|
| VLMs detect editing artifacts | Edits confined to small peripheral regions |
| Closed object library memorizable | Deliberate for calibration; expandable |
| Color-only attribute too simple | Unambiguity is a feature; extensible to material/depth |

---

## 8. File Map

| File | Purpose |
|------|---------|
| `paper/emnlp2026/experiment_results.md` | **All numbers** — single source of truth |
| `paper/emnlp2026/overleaf/` | LaTeX paper |
| `scripts/analyze_dynamic_eval.py` | Computes all tables from data |
| `results/benchmark/bench{1,2,3}/` | 3 seeds × 191 images |
| `results/dynamic_eval/` | All eval results |
| `results/vlm_annotator/` | VLM annotation + benchmark |
| `results/contamination_audit/` | Original vs relabel data |
| `data/annotations/dynamic_vstar_slots_latest.jsonl` | Human annotations |
| `HANDOVER.md` | Quick-start guide for new agents |
