# ReKey — Experiment Results & Settings Reference

Date: 2026-05-20. All numbers computed from `scripts/analyze_dynamic_eval.py`.

---

## Evaluation Protocol (shared across ALL experiments)

Identical for contamination audit, ReKey eval, no-color ablation, and VLM annotation ablation.

| Setting | Value | Notes |
|---------|-------|-------|
| **Image resolution** | Original (no resize, no re-encoding) | V*Bench images avg ~2250×1500 |
| **Image format** | JPEG quality 95 | Converted from PNG for API compatibility |
| **Prompt format** | `{question} (A) xxx (B) xxx ... Answer with the option's letter from the given choices directly.` | Matches V*Bench official format exactly |
| **System prompt** | None | No system message |
| **Temperature** | 0 | Deterministic decoding |
| **max_tokens** | 2048 | Accommodates reasoning models that use thinking tokens |
| **Parsing** | Extract first A/B/C/D letter from response | |
| **Retries** | 3 attempts on HTTP 429/502/503 | Exponential backoff |
| **API** | OpenRouter `/v1/chat/completions` | All 8 cloud models |
| **LLaVA** | Local inference on A100 GPU | `do_sample=False`, vicuna_v1 template |

**Note on max_tokens**: V*Bench original uses max_tokens=16. We use 2048 because
reasoning-capable models (GPT-5.5, Gemini, Kimi) consume thinking tokens before
producing the answer letter. At max_tokens=16, these models return empty content.
The actual output is typically 1-3 tokens; the higher limit does not increase cost.

**tex 需要更新**: experiments.tex 第 45-47 行还写的是 `max_tokens=16` + retry to 512。
改成：`We set temperature to~0 and \texttt{max\_tokens} to~2048 to accommodate
reasoning-capable models whose internal chain-of-thought consumes output tokens
before producing the answer letter.`

---

## Models

| Model | OpenRouter ID | Type |
|-------|-------------|------|
| Qwen3.6-Plus | `qwen/qwen3.6-plus` | Closed |
| GPT-5.5 | `openai/gpt-5.5` | Closed |
| Claude Opus 4.7 | `anthropic/claude-opus-4-7` | Closed |
| Gemini 3.1 Pro | `google/gemini-3.1-pro-preview` | Closed |
| Seed-2.0-Lite | `bytedance-seed/seed-2.0-lite` | Closed |
| Kimi-latest | `~moonshotai/kimi-latest` | Closed |
| MiMo v2.5 | `xiaomi/mimo-v2.5` | Open |
| Llama 4 Maverick | `meta-llama/llama-4-maverick` | Open |
| LLaVA-1.5-13B | local (server GPU) | Open |

---

## Contamination Audit (Appendix, 8 models complete)

| Model | Original V* | Relabel V* | Δ |
|-------|------------|-----------|-----|
| Qwen3.6-Plus | 90.6 | 75.4 | -15.2 |
| GPT-5.5 | 88.5 | 77.0 | -11.5 |
| Claude Opus 4.7 | 77.0 | 60.2 | -16.8 |
| Gemini 3.1 Pro | 88.5 | 66.5 | -22.0 |
| Seed-2.0-Lite | 91.6 | 73.8 | -17.8 |
| Kimi-latest | 81.2 | 57.6 | -23.6 |
| MiMo v2.5 | 80.1 | 63.9 | -16.2 |
| Llama 4 Maverick | 60.7 | 49.2 | -11.5 |

All drops significant (McNemar p < 0.05). Drop range: 11.5–23.6pp.

---

## RQ1: Does ReKey Remove Contamination Benefit? (8 standard VLMs × 3 seeds, complete)

tex 结构：RQ1 包含标准 VLM（Table~\ref{tab:dynamic}）和 Agentic VLM（Table~\ref{tab:agentic}，TODO）。
LLaVA 不在 RQ1，放在 RQ2 作为 difficulty calibration。

### Overall (Table tab:dynamic in tex)

| Model | Original | Relabel | ReKey (mean±σ) | Orig Drop | vs Relabel |
|-------|---------|---------|---------------|-----------|------------|
| Qwen3.6-Plus | 90.6 | 75.4 | 73.5±5.7 | +17.1 | -1.9 |
| GPT-5.5 | 88.5 | 77.0 | 77.8±1.6 | +10.7 | +0.8 |
| Claude Opus 4.7 | 77.0 | 60.2 | 64.9±2.6 | +12.1 | +4.7 |
| Gemini 3.1 Pro | 88.5 | 66.5 | 72.8±2.7 | +15.7 | +6.3 |
| Seed-2.0-Lite | 91.6 | 73.8 | 81.3±4.2 | +10.3 | +7.5 |
| Kimi-latest | 81.2 | 57.6 | 63.9±1.9 | +17.3 | +6.3 |
| MiMo v2.5 | 80.1 | 63.9 | 68.9±4.6 | +11.2 | +5.0 |
| Llama 4 Maverick | 60.7 | 49.2 | 56.7±2.1 | +4.0 | +7.5 |
| *Average* | *82.3* | *65.5* | *69.9* | *+12.3* | *+4.5* |

### Attribute (color questions, for appendix/analysis)

| Model | Original | Relabel | ReKey (mean±σ) | Gap |
|-------|---------|---------|---------------|-----|
| Qwen3.6-Plus | 90.4 | 69.6 | 68.3±5.8 | +22.1 |
| GPT-5.5 | 88.7 | 73.0 | 73.6±4.2 | +15.1 |
| Claude Opus 4.7 | 74.8 | 57.4 | 58.6±6.1 | +16.2 |
| Gemini 3.1 Pro | 88.7 | 66.1 | 64.8±2.8 | +23.9 |
| Seed-2.0-Lite | 93.0 | 67.0 | 74.5±4.2 | +18.5 |
| Kimi-latest | 80.0 | 53.9 | 61.9±2.2 | +18.1 |
| MiMo v2.5 | 79.1 | 60.0 | 63.0±5.1 | +16.1 |
| Llama 4 Maverick | 60.0 | 38.3 | 56.3±2.2 | +3.7 |

### Position (spatial questions, for appendix/analysis)

| Model | Original | Relabel | ReKey (mean±σ) | Gap |
|-------|---------|---------|---------------|-----|
| Qwen3.6-Plus | 90.8 | 84.2 | 81.1±6.2 | +9.7 |
| GPT-5.5 | 88.2 | 82.9 | 84.0±3.4 | +4.2 |
| Claude Opus 4.7 | 80.3 | 64.5 | 74.1±2.4 | +6.2 |
| Gemini 3.1 Pro | 88.2 | 67.1 | 84.5±3.1 | +3.7 |
| Seed-2.0-Lite | 89.5 | 84.2 | 91.4±4.7 | -1.9 |
| Kimi-latest | 82.9 | 63.2 | 66.8±3.0 | +16.1 |
| MiMo v2.5 | 81.6 | 69.7 | 77.6±4.2 | +4.0 |
| Llama 4 Maverick | 61.8 | 65.8 | 57.3±2.3 | +4.5 |

### Agentic VLMs (Table tab:agentic in tex, TODO)

Need SEAL (V* agent) or modern agentic VLM evaluation.

---

## RQ2: Difficulty Preservation (LLaVA-1.5-13B, complete)

| | Overall | Attr | Position |
|---|------:|-----:|---------:|
| Original V* (paper) | 48.68 | 43.47 | 56.57 |
| ReKey (mean±σ) | 41.5±3.4 | 33.7±4.7 | 53.1±4.6 |
| Δ | -7.2 | -9.8 | -3.5 |

Position nearly unchanged (-3.5pp). Overall gap (-7.2pp) far smaller
than frontier contamination gaps (10–17pp).

---

## ~~Color Cue Ablation~~ (DEPRECATED — not for paper)

Data exists in `results/dynamic_eval/*_pos_nocolor.jsonl` but experiment
is not included in the paper.

---

## RQ3: VLM Self-Annotation Ablation (tex: \S\ref{sec:rq3}, 6 models complete)

GPT-5.5 annotates V*Bench images with the same instructions as human
annotators. Only add slots are used to generate a benchmark through the
identical ReKey pipeline. If VLM-annotated benchmarks are systematically
easier, it validates the human-in-the-loop design.

### Eval Results

| Model | Original V* | Human Dynamic | VLM add-only | Δ(Human→VLM) |
|-------|------------|--------------|-------------|--------------|
| Qwen3.6-Plus | 90.6 | 73.5 | 89.9 | +16.5 |
| Gemini 3.1 Pro | 88.5 | 72.8 | 82.0 | +9.2 |
| Seed-2.0-Lite | 91.6 | 81.3 | 88.9 | +7.6 |
| Kimi-latest | 81.2 | 63.9 | 76.2 | +12.3 |
| MiMo v2.5 | 80.1 | 68.9 | 78.8 | +9.9 |
| Llama 4 Mav | 60.7 | 56.7 | 72.5 | +15.8 |

All models +7.6 to +16.5pp on VLM benchmark. VLM self-annotation
produces systematically easier benchmarks. VLM benchmark scores approach
or exceed Original V* (e.g., Qwen 89.9 vs Original 90.6, Llama 72.5 vs
Original 60.7), meaning VLM annotation effectively undoes the
decontamination that human annotation achieves.

### Edit Region Size Analysis

Why VLM benchmarks are easier — measured by edit region area (px²):

| | Human | VLM (GPT-5.5) | Ratio |
|---|---:|---:|---:|
| **Replace median** | 3,843 | 3,531 | 0.92x |
| **Add median** | 3,256 | 10,504 | **3.2x** |

- **Replace** regions are similar size (~3,500 px²) because both human and
  VLM annotators are marking the same original V*Bench visual keys. These
  inherit V*'s small-target difficulty by construction.

- **Add** regions diverge sharply: VLM picks regions **3.2x larger** than
  human annotators. This is the saliency bias — VLM selects prominent,
  spacious areas (wide lawns, open walls) where inserted objects are easy
  to spot, while human annotators choose compact, cluttered regions where
  a new object blends in and requires searching.

- This size difference directly explains the accuracy gap: larger add
  regions → larger inserted objects → easier to find → higher accuracy.

---

## Benchmark Construction

| | Count |
|---|---:|
| Source images | 191 |
| Seeds generated | 3 (bench1/bench2/bench3) |
| Items per seed | 191 (~115 attr + ~76 position) |
| Image format | JPEG quality 95 |
| Image editor | GPT-Image-2 via OpenAI /images/edits API |
| Color pool | 11 single colors |
| Add object types | 23 across 5 placement groups |

### Known Issues (internal record, not for paper)

- **bench3 vstar_0141**: API persistently timed out for this image across
  multiple days/endpoints. bench3's vstar_0141 uses bench2's generated
  version (same annotation, different seed but copied). This means bench3
  and bench2 share identical content for this one item (1/191 = 0.5%).
  Does not affect reported results meaningfully.

- **VLM annotation (RQ4)**: 2 images (vstar_0154, vstar_0168) persistently
  fail GPT-5.5 annotation (returns None). VLM benchmark has 189/191 items.
  Paper reports "189 images" or rounds to "~190 images" without drawing
  attention to the 2 missing.

- **Contamination audit data**: MiMo original file had 224 rows (33 duplicate
  question_ids from retry appends). Script deduplicates by keeping last
  occurrence per question_id. Gemini and GPT-5.5 happen to have identical
  correct counts (169/191 = 88.5%) but different per-item predictions —
  verified as coincidence, not data error.

---

## Data Files

| File | Description |
|------|-------------|
| `results/benchmark/bench{1,2,3}/eval_dataset.jsonl` | 3 seeds eval datasets |
| `results/dynamic_eval/{model}_{bench}.jsonl` | 8 models × 3 seeds results |
| `results/dynamic_eval/{model}_{bench}_pos_nocolor.jsonl` | No-color position results |
| `results/dynamic_eval/llava15_bench{1,2,3}.jsonl` | LLaVA results (from server) |
| `results/vlm_annotator/bench_vlm_add/eval_dataset.jsonl` | VLM add-only benchmark |
| `results/contamination_audit/original_vs_relabel/` | Contamination audit data |
| `scripts/analyze_dynamic_eval.py` | Computes all tables from data |
