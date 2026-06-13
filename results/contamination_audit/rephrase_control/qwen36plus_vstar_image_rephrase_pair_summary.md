# Qwen3.6-Plus V* Original vs Rephrased Question Pair Summary

Date: 2026-04-28

Model: `qwen/qwen3.6-plus`

Setting: resized image + question + options, `temperature=0`, `reasoning.effort=none`, visible brief reasoning required, final answer parsed from `Final answer: X`.

Files:
- original-question raw output: `results/qwen36plus_vstar_image_original_brief_t0.jsonl`
- original-question summary: `results/qwen36plus_vstar_image_original_brief_t0_summary.md`
- rephrased-question raw output: `results/qwen36plus_vstar_image_rephrased_brief_t0.jsonl`
- rephrased-question summary: `results/qwen36plus_vstar_image_rephrased_brief_t0_summary.md`
- rephrases: `data/processed/vstar_rephrased_questions.jsonl`

## Overall

| condition | parsed | correct | accuracy |
|---|---:|---:|---:|
| original question | 191/191 | 145 | 75.9% |
| rephrased question | 191/191 | 150 | 78.5% |

## By Category

| category | n | original correct | original acc | rephrased correct | rephrased acc |
|---|---:|---:|---:|---:|---:|
| `direct_attributes` | 115 | 84 | 73.0% | 87 | 75.7% |
| `relative_position` | 76 | 61 | 80.3% | 63 | 82.9% |

## By Option Count

| option count | n | original correct | original acc | rephrased correct | rephrased acc |
|---:|---:|---:|---:|---:|---:|
| 2 | 84 | 68 | 81.0% | 70 | 83.3% |
| 4 | 107 | 77 | 72.0% | 80 | 74.8% |

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

Interpretation: the rephrased condition is numerically higher by 5 items, but this paired difference is not statistically significant. In this resized image + question ablation, Qwen3.6-Plus is not relying on the exact original wording in a way that produces a measurable advantage for the original V* stems in this one-run condition.

## Changed Choices

| qid | category | label | original choice | rephrased choice | original correct | rephrased correct |
|---:|---|---|---|---|---:|---:|
| 20 | `direct_attributes` | C | D | C | false | true |
| 21 | `direct_attributes` | A | D | A | false | true |
| 25 | `direct_attributes` | D | A | D | false | true |
| 75 | `direct_attributes` | A | A | D | true | false |
| 99 | `direct_attributes` | D | A | D | false | true |
| 134 | `relative_position` | B | B | A | true | false |
| 135 | `relative_position` | B | B | A | true | false |
| 136 | `relative_position` | B | B | A | true | false |
| 145 | `relative_position` | A | B | A | false | true |
| 149 | `relative_position` | B | A | B | false | true |
| 152 | `relative_position` | A | A | B | true | false |
| 154 | `relative_position` | A | B | A | false | true |
| 156 | `relative_position` | A | B | A | false | true |
| 164 | `relative_position` | A | A | B | true | false |
| 178 | `relative_position` | B | A | B | false | true |
| 189 | `relative_position` | B | A | B | false | true |
| 190 | `relative_position` | A | B | A | false | true |
