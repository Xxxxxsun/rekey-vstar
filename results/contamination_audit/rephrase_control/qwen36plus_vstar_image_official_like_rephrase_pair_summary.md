# Qwen3.6-Plus V* Official-Like Original vs Rephrased Pair Summary

Date: 2026-04-30

Model: `qwen/qwen3.6-plus`

Setting:
- original V* image bytes
- no image resizing
- no JPEG re-encoding
- no system prompt
- OpenRouter `reasoning` field omitted
- `temperature=0`
- original condition uses the raw HF prompt
- rephrased condition replaces only the question stem and keeps the original answer options and answer suffix

Files:
- original raw output: `results/qwen36plus_vstar_image_rawprompt_originalimage_t0.jsonl`
- original summary: `results/qwen36plus_vstar_image_rawprompt_originalimage_t0_summary.md`
- rephrased raw output: `results/qwen36plus_vstar_image_rephrased_rawprompt_originalimage_t0.jsonl`
- rephrased summary: `results/qwen36plus_vstar_image_rephrased_rawprompt_originalimage_t0_summary.md`
- rephrases: `data/processed/vstar_rephrased_questions.jsonl`

## Overall

| condition | parsed | correct | accuracy |
|---|---:|---:|---:|
| original question | 191/191 | 173 | 90.6% |
| rephrased question | 191/191 | 174 | 91.1% |

## By Category

| category | n | original correct | original acc | rephrased correct | rephrased acc |
|---|---:|---:|---:|---:|---:|
| `direct_attributes` | 115 | 104 | 90.4% | 103 | 89.6% |
| `relative_position` | 76 | 69 | 90.8% | 71 | 93.4% |

## By Option Count

| option count | n | original correct | original acc | rephrased correct | rephrased acc |
|---:|---:|---:|---:|---:|---:|
| 2 | 84 | 77 | 91.7% | 79 | 94.0% |
| 4 | 107 | 96 | 89.7% | 95 | 88.8% |

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

## Changed Choices

| qid | category | label | original choice | rephrased choice | original correct | rephrased correct |
|---:|---|---|---|---|---:|---:|
| 4 | `direct_attributes` | C | D | C | false | true |
| 23 | `direct_attributes` | B | A | B | false | true |
| 25 | `direct_attributes` | D | A | C | false | false |
| 37 | `direct_attributes` | C | D | C | false | true |
| 49 | `direct_attributes` | C | C | B | true | false |
| 60 | `direct_attributes` | D | D | B | true | false |
| 78 | `direct_attributes` | C | C | D | true | false |
| 86 | `direct_attributes` | A | A | D | true | false |
| 126 | `relative_position` | A | B | A | false | true |
| 189 | `relative_position` | B | A | B | false | true |

## Interpretation

Under the official-like V* setting, replacing the original question stems with paraphrases does not reduce performance. The rephrased run is numerically one item higher than the original run, and the paired difference is not significant.

This is a strong control against an exact-surface-wording explanation for the official-like image + question score. It does not address no-image repeated-stem behavior directly; it only says that when the image is provided at full resolution, Qwen3.6-Plus remains stable under stem paraphrasing.
