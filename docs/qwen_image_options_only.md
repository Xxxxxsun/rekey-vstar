# Qwen3.6-Plus V* Image + Options-Only Experiment

Date: 2026-04-28

Purpose: test whether Qwen3.6-Plus can recover V* labels when it receives the image and answer options, but not the question text.

## Setup

Dataset: `lmms-lab/vstar-bench`

Dataset revision: `b44023b4dca749ed8a76b85eb576627d05a1c174`

Model: `qwen/qwen3.6-plus`

Prompt mode: options only. The question text is removed.

Example prompt text:

```text
(A) orange (B) red (C) white (D) black

Use the image. Answer with exactly one option letter: A, B, C, or D. You must answer now.
```

For binary questions, the instruction is:

```text
Use the image. Answer with exactly one option letter: A or B. You must answer now.
```

Image handling:
- original V* JPEG bytes from parquet
- resized before sending: max side 1536
- JPEG quality 85

Two response modes were run:
- direct: force exactly one letter and nothing else.
- verbose: allow explanation text, but require a final line in the format `Final answer: X`.

Both modes used:
- temperature 0
- `reasoning.effort=none`
- one run per item

Files:
- direct raw output: `results/qwen36plus_vstar_image_options_only_t0.jsonl`
- direct summary: `results/qwen36plus_vstar_image_options_only_t0_summary.md`
- verbose raw output: `results/qwen36plus_vstar_image_options_only_verbose_t0.jsonl`
- verbose summary: `results/qwen36plus_vstar_image_options_only_verbose_t0_summary.md`
- runner: `scripts/run_vstar_image_eval.py --prompt-mode options_only`

## Direct Letter-Only Results

Direct mode prompt requires the model to output exactly one uppercase option letter and nothing else.

| subset | n | correct | accuracy | random baseline | p-value |
|---|---:|---:|---:|---:|---:|
| all | 191 | 74 | 38.7% | 36.0% | 0.236 |
| direct_attributes | 115 | 36 | 31.3% | 26.7% | 0.158 |
| relative_position | 76 | 38 | 50.0% | 50.0% | 0.546 |
| 2-choice | 84 | 42 | 50.0% | 50.0% | 0.543 |
| 4-choice | 107 | 32 | 29.9% | 25.0% | 0.145 |

Global output distribution:

| A | B | C | D |
|---:|---:|---:|---:|
| 64 | 73 | 22 | 32 |

Estimated OpenRouter cost for the direct run: about `$0.10`.

## Verbose Explanation Results

Verbose mode still disables hidden reasoning via `reasoning.effort=none`, but allows visible explanation text. The model must end with `Final answer: X`.

Example instruction:

```text
Use the image and choose from A, B, C, or D. You may explain. End with 'Final answer: A', 'Final answer: B', 'Final answer: C', or 'Final answer: D'. You must answer now.
```

Most items used `max_tokens=256`; items that did not reach a final answer were rerun with larger limits up to 2048.

| subset | n | correct | accuracy | random baseline | p-value |
|---|---:|---:|---:|---:|---:|
| all | 191 | 81 | 42.4% | 36.0% | 0.039 |
| direct_attributes | 115 | 40 | 34.8% | 26.7% | 0.035 |
| relative_position | 76 | 41 | 53.9% | 50.0% | 0.283 |
| 2-choice | 84 | 45 | 53.6% | 50.0% | 0.293 |
| 4-choice | 107 | 36 | 33.6% | 25.0% | 0.028 |

Global output distribution:

| A | B | C | D |
|---:|---:|---:|---:|
| 96 | 50 | 19 | 26 |

Estimated OpenRouter cost for the verbose run: about `$0.18`.

## Direct vs Verbose

| mode | all accuracy | 4-choice accuracy | parsed | interpretation |
|---|---:|---:|---:|---|
| direct letter-only | 38.7% | 29.9% | 191/191 | mildly above random, not significant |
| verbose explanation | 42.4% | 33.6% | 191/191 | above random; significant overall and on 4-choice items |

## Interpretation

This image + options-only condition is much harder than normal VQA because the model does not know which object or relation the hidden question asks about.

The direct result is only mildly above random:
- all items: 38.7% vs 36.0%
- four-choice items: 29.9% vs 25.0%

The verbose result is stronger:
- all items: 42.4% vs 36.0%
- four-choice items: 33.6% vs 25.0%

Interpretation: allowing visible explanation helps Qwen3.6-Plus infer a plausible hidden question from the image and options. This is still not a direct leakage proof by itself, but it is a meaningful options-only signal and should be reported separately from the strict one-letter condition.
