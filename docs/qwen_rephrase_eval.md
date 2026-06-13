# Qwen3.6-Plus V* Original vs Rephrased Question Experiment

Date: 2026-04-28

Purpose: test whether Qwen3.6-Plus changes behavior when V* question stems are rewritten in different words while keeping the image and answer options fixed.

Note: this run used resized images (`max_side=1536`) and a custom brief-reasoning prompt. It is a wording-sensitivity ablation, not the official-like V* reproduction setting. The official-like reproduction is documented in `docs/qwen_vstar_official_like_reproduction.md`.

## Data

Dataset: `lmms-lab/vstar-bench`

Dataset revision: `b44023b4dca749ed8a76b85eb576627d05a1c174`

Rephrase file: `data/processed/vstar_rephrased_questions.jsonl`

Rephrase model: `openai/gpt-4.1-mini` through OpenRouter.

Coverage:
- total V* rows: 191
- rephrased rows: 191
- options are unchanged
- only the question stem is rewritten

Manual quality check:
- relative-position stems were checked for subject/object reversals
- 7 relative-position rewrites were manually corrected after generation: `118`, `122`, `139`, `145`, `153`, `180`, `181`

Example:

```text
Original: What is the material of the glove?
Rephrased: What material is the glove made of?
```

## Evaluation Setup

Model: `qwen/qwen3.6-plus`

Two conditions:
- original question: image + original V* question stem + original options
- rephrased question: image + rephrased question stem + original options

Shared settings:
- `temperature=0`
- `reasoning.effort=none`
- one run per item
- image max side: 1536
- JPEG quality: 85
- visible brief reasoning is allowed and required
- hidden reasoning is excluded

System prompt:

```text
You answer visual multiple-choice questions using the provided image. Give one short sentence of visible reasoning, then end with a separate line in the exact format 'Final answer: X', where X is one allowed option letter.
```

Four-choice user instruction:

```text
Use the image and choose from A, B, C, or D. Give one short sentence of reasoning, then end with 'Final answer: A', 'Final answer: B', 'Final answer: C', or 'Final answer: D'. You must answer now.
```

Binary user instruction:

```text
Use the image and choose from A or B. Give one short sentence of reasoning, then end with 'Final answer: A' or 'Final answer: B'. You must answer now.
```

Initial runs used `max_tokens=160`. Items that did not produce a parseable final answer were moved to backup files and rerun with `max_tokens=512`.

Files:
- original raw output: `results/qwen36plus_vstar_image_original_brief_t0.jsonl`
- original summary: `results/qwen36plus_vstar_image_original_brief_t0_summary.md`
- rephrased raw output: `results/qwen36plus_vstar_image_rephrased_brief_t0.jsonl`
- rephrased summary: `results/qwen36plus_vstar_image_rephrased_brief_t0_summary.md`
- paired summary: `results/qwen36plus_vstar_image_rephrase_pair_summary.md`
- original unparsed backup before rerun: `results/qwen36plus_vstar_image_original_brief_t0.unparsed_t160.jsonl`
- rephrased unparsed backup before rerun: `results/qwen36plus_vstar_image_rephrased_brief_t0.unparsed_t160.jsonl`

## Results

| condition | parsed | correct | accuracy |
|---|---:|---:|---:|
| original question | 191/191 | 145 | 75.9% |
| rephrased question | 191/191 | 150 | 78.5% |

By category:

| category | n | original correct | original acc | rephrased correct | rephrased acc |
|---|---:|---:|---:|---:|---:|
| `direct_attributes` | 115 | 84 | 73.0% | 87 | 75.7% |
| `relative_position` | 76 | 61 | 80.3% | 63 | 82.9% |

By option count:

| option count | n | original correct | original acc | rephrased correct | rephrased acc |
|---:|---:|---:|---:|---:|---:|
| 2 | 84 | 68 | 81.0% | 70 | 83.3% |
| 4 | 107 | 77 | 72.0% | 80 | 74.8% |

Estimated OpenRouter cost from recorded usage:
- original-question eval: `$0.1178`
- rephrased-question eval: `$0.1169`

## Paired Comparison

| pair outcome | count |
|---|---:|
| both correct | 139 |
| original correct only | 6 |
| rephrased correct only | 11 |
| both wrong | 35 |

Choice agreement: 174/191 = 91.1%.

Discordant correctness pairs: 17.

Exact McNemar/binomial p-value: 0.332306.

## Interpretation

The rephrased condition is numerically higher by 5 items, but the paired difference is not statistically significant.

In this resized image + question VQA ablation, Qwen3.6-Plus does not show a measurable advantage for the exact original V* wording in this one-run condition. The model's choices are also stable under rephrasing: 174/191 items keep the same selected option.

This result should be treated as a control for wording sensitivity. It does not negate the no-image repeated-stem signal, because that earlier signal is about benchmark-seen labels when the image is removed. It does suggest that under this resized-image prompt condition, exact surface-form memorization is not the dominant driver of Qwen3.6-Plus accuracy.
