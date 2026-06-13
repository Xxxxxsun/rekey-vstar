# Qwen3.6-Plus V* Official-Like Rephrase Experiment

Date: 2026-04-30

Purpose: test whether Qwen3.6-Plus depends on the exact original V* question wording under the official-like VQA setting.

## Setup

Dataset: `lmms-lab/vstar-bench`

Dataset revision: `b44023b4dca749ed8a76b85eb576627d05a1c174`

Model: `qwen/qwen3.6-plus`

Rephrase file: `data/processed/vstar_rephrased_questions.jsonl`

Official-like evaluation setting:
- original V* image bytes
- no image resizing
- no JPEG re-encoding
- no system prompt
- OpenRouter `reasoning` field omitted
- `temperature=0`
- one run per item

Original condition:
- raw HF prompt

Rephrased condition:
- question stem replaced by the rephrased stem
- answer options unchanged
- answer suffix unchanged: `Answer with the option's letter from the given choices directly.`

Example:

```text
What material is the glove made of? (A) rubber (B) cotton (C) kevlar (D) leather Answer with the option's letter from the given choices directly.
```

Unparsed handling:
- initial run used `max_tokens=16`
- 8 truncated/unparsed rows were rerun with `max_tokens=512`
- after parser update, all 191 rows were parsed

Files:
- original raw output: `results/qwen36plus_vstar_image_rawprompt_originalimage_t0.jsonl`
- original summary: `results/qwen36plus_vstar_image_rawprompt_originalimage_t0_summary.md`
- rephrased raw output: `results/qwen36plus_vstar_image_rephrased_rawprompt_originalimage_t0.jsonl`
- rephrased summary: `results/qwen36plus_vstar_image_rephrased_rawprompt_originalimage_t0_summary.md`
- paired summary: `results/qwen36plus_vstar_image_official_like_rephrase_pair_summary.md`

## Results

| condition | parsed | correct | accuracy |
|---|---:|---:|---:|
| original question | 191/191 | 173 | 90.6% |
| rephrased question | 191/191 | 174 | 91.1% |

By category:

| category | n | original correct | original acc | rephrased correct | rephrased acc |
|---|---:|---:|---:|---:|---:|
| `direct_attributes` | 115 | 104 | 90.4% | 103 | 89.6% |
| `relative_position` | 76 | 69 | 90.8% | 71 | 93.4% |

By option count:

| option count | n | original correct | original acc | rephrased correct | rephrased acc |
|---:|---:|---:|---:|---:|---:|
| 2 | 84 | 77 | 91.7% | 79 | 94.0% |
| 4 | 107 | 96 | 89.7% | 95 | 88.8% |

Recorded OpenRouter usage for the rephrased run:
- cost: about `$1.20`
- prompt tokens: 487,599
- completion tokens: 534,571

## Paired Comparison

| pair outcome | count |
|---|---:|
| both correct | 169 |
| original correct only | 4 |
| rephrased correct only | 5 |
| both wrong | 13 |

Choice agreement: 181/191 = 94.8%.

Changed choices: 10/191.

Exact McNemar/binomial p-value: 1.0.

## Interpretation

Under the official-like V* setting, rephrasing the question stems does not hurt Qwen3.6-Plus. The rephrased condition is numerically one item higher than the original condition, and the paired difference is not significant.

This is a stronger wording-sensitivity control than the earlier resized-image rephrase experiment. With full-resolution images and dataset-native answer suffixes, there is no evidence that the normal VQA score depends on exact original question wording.

This does not remove the no-image repeated-stem concern. It only shows that when the image is available at full resolution, exact wording memorization is not needed to achieve the official-like V* score.

## Review Tool

A local review tool is available at `scripts/review_vstar_labels.py`.

It displays:
- image
- original question
- rephrased question
- options
- dataset label and answer text
- editable reviewed label
- notes

Annotations are appended to `data/annotations/vstar_review.jsonl`.
