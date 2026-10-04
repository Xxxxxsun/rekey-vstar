# Dynamic V* (ReKey) — Handover

## Goal

Static VLM benchmarks leak — models memorize (image, question, answer) triples and score high without real visual reasoning. We build a contamination-resistant benchmark for V*Bench (191 high-res small-target visual search images) that refreshes answers at eval time so memorization doesn't help.

## How It Works

1. **Human annotation**: annotators mark edit slots on V*Bench images — a context region (scene reference) + edit region (target area), with either a target_ref for recoloring (replace) or absent-object checklist (add)
2. **Sampling**: pipeline picks a random color from 11-color pool + random object from candidate list
3. **Image generation**: sends crop to image editing API (gpt-image-2), composites result back
4. **Rule-based QA**: constructs question/answer/options deterministically from sampled metadata — no VLM judge
5. **Different seeds → different benchmarks**: same annotations, different random sampling → different correct answers each run

## Project Structure

```
scripts/
  run_dynamic_eval.py          — evaluate VLMs on Dynamic V* benchmark
  build_eval_dataset.py        — convert generated bench to eval JSONL
  run_dynamic_vstar_pipeline.py — generate benchmark images
  run_vstar_image_eval.py      — evaluate on original/relabel V*

results/benchmark/
  bench1/                      — seed 1 (191 images)
  bench2/                      — seed 2 (191 images)
  bench3/                      — seed 3 (191 images)

data/annotations/
  dynamic_vstar_slots_latest.jsonl — human annotations (191 images)
```

## Benchmark Structure

Each bench directory:
```
results/benchmark/bench1/
  eval_dataset.jsonl                          — 191 items, the eval input
  vstar_0000__bench1/artifacts/composite.jpg  — edited image (JPEG 95)
  vstar_0001__bench1/artifacts/composite.png
  ...
```

### eval_dataset.jsonl format

```json
{
  "image_id": "vstar_0000",
  "question_id": "0",
  "category": "direct_attributes",
  "question_type": "color",
  "question": "What color is the clock?",
  "options": "(A) white (B) brown (C) pink (D) black",
  "options_dict": {"A": "white", "B": "brown", "C": "pink", "D": "black"},
  "correct_label": "D",
  "answer": "black",
  "image_path": "vstar_0000__bench1/artifacts/composite.jpg"
}
```

- `image_path` is **relative to the eval_dataset.jsonl's parent directory**
- `category`: `direct_attributes` (color Q, 4 options) or `relative_position` (position Q, 2 options)
- Each bench has different sampled colors/objects → different correct answers

## How to Run Eval

```bash
export OPENROUTER_API_KEY="sk-or-v1-..."

python scripts/run_dynamic_eval.py \
  --eval-dataset results/benchmark/bench1/eval_dataset.jsonl \
  --out results/dynamic_eval/gpt55_bench1.jsonl \
  --model openai/gpt-5.5
```

Key behavior:
- Reads `eval_dataset.jsonl`, resolves `image_path` relative to the jsonl's parent dir
- Sends each image + question to the model via OpenRouter chat completions
- No system prompt, temperature 0, max_tokens 16
- Prompt: `{question} (A) xxx (B) xxx ... Answer with the option's letter from the given choices directly.`
- Supports resume: skips `image_id`s already in output file
- `--concurrency 5` (default), `--model` accepts any OpenRouter model ID

### Run all 3 seeds for a model

```bash
for bench in bench1 bench2 bench3; do
  python scripts/run_dynamic_eval.py \
    --eval-dataset results/benchmark/$bench/eval_dataset.jsonl \
    --out results/dynamic_eval/gpt55_${bench}.jsonl \
    --model openai/gpt-5.5 &
done
```

### Output format

```json
{
  "image_id": "vstar_0000",
  "question_id": "0",
  "category": "direct_attributes",
  "question_type": "color",
  "correct_label": "D",
  "prediction": "D",
  "correct": true,
  "raw_response": "D",
  "model": "openai/gpt-5.5",
  ...
}
```

## Models to Evaluate

| Model | OpenRouter ID |
|-------|-------------|
| Qwen3.6-Plus | `qwen/qwen3.6-plus` |
| GPT-5.5 | `openai/gpt-5.5` |
| Claude Opus 4.7 | `anthropic/claude-opus-4-7` |
| Gemini 3.1 Pro | `google/gemini-3.1-pro-preview` |
| Seed-2.0-Lite | `bytedance-seed/seed-2.0-lite` |
| Kimi K2.6 | `~moonshotai/kimi-latest` |
| MiMo v2.5 | `xiaomi/mimo-v2.5` |
| Llama 4 Maverick | `meta-llama/llama-4-maverick` |

All 8 models × 3 seeds = 24 eval runs.

## Current Status

| Task | Status |
|------|--------|
| Benchmark generation (3 seeds × 191 images) | **Done** (JPEG 95) |
| RQ1: 9 models × 3 seeds eval | **Done** (all 0 errors, 0 empty) |
| RQ1: Agentic VLMs | **TODO** — see below |
| RQ2: LLaVA-1.5 × 3 seeds | **Done** (mean 42.6%, pos Δ=-0.4pp) |
| RQ3: VLM annotation ablation (8 models) | **Done** (+5.2 to +16.8pp) |
| RQ3: Region size analysis | **Done** (VLM add 3.2× larger) |
| Qwen3-VL scaling (3 sizes × 3 seeds) | **Done** |
| Qwen3-VL CoT (3 sizes × 3 seeds + orig/relab) | **Done** |

All numbers in `paper/emnlp2026/experiment_results.md`.
Compute from data: `python scripts/compute_tables.py`.

### Agentic VLM Eval (TODO)

Qwen3-VL-235B-Instruct reports **93.7+** on V*Bench with tool use (agentic visual search)
in the official tech report (arXiv:2511.21631, Table 2). Our non-agentic eval gives 73.8.

To evaluate agentic VLMs on ReKey:
1. Use `results/benchmark/bench{1,2,3}/eval_dataset.jsonl` as input
   - Attr questions: "What color is the clock? (A)... Answer with..."
   - Position questions: replace objects carry new color ("the orange phone"),
     add objects use category only ("the cat")
2. Allow the agent to use visual search tools (crop, zoom, etc.)
3. Same prompt suffix, temperature 0, max_tokens 8192
4. Parse last A/B/C/D letter from response
5. Run on all 3 seeds, report mean ± σ

Candidate models:
- Qwen3-VL-235B with tool use (matches their 93.7+ setup)
- SEAL (V* agent from the original paper)

### Position Question Format

Position questions use hybrid color: replace objects carry new color
("the **orange** phone"), add objects use category only ("the cat").
This preserves identification precision for recolored objects while
testing genuine search for added objects.

### Known Issues

- **bench3/vstar_0141**: API persistently times out. Copied from bench2. 1/573 = 0.17%.
- **10 items missing intermediate files**: guide_context/restored_context lost during git restore. Core files correct. Re-run pipeline to regenerate. Items: bench1/(0181,0182,0186,0188), bench2/(0153,0182), bench3/(0153,0163,0181,0182).

## Environment Variables

```
OPENROUTER_API_KEY — for VLM evaluation (required by run_dynamic_eval.py)
```
