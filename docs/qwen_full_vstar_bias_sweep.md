# Qwen3.6-Plus Full V* Bias Sweep

Date: 2026-04-28

Scope: scale the motorcycle prompt test to every V* question and measure whether Qwen3.6-Plus shows repeated no-image option bias.

Condition:
- dataset: `lmms-lab/vstar-bench`, 191 questions
- model: `qwen/qwen3.6-plus`
- image withheld
- prompt variant: original question/options plus `You must answer now.`
- system prompt: `Output exactly one uppercase option letter from A, B, C, or D. Do not explain.`
- `reasoning.effort=none`
- temperature: `0.1`
- repeats: 20 per question

Raw output:
- `results/qwen36plus_vstar_all_strict_t01_r20.jsonl`

Analyzer output:
- `results/qwen36plus_vstar_all_strict_t01_r20_bias_summary.md`
- `results/qwen36plus_vstar_all_strict_t01_r20_bias_summary.items.json`

## Item-Level Summary

Threshold: `>=90%` of parsed repeats.

| subset | items | strong top-choice bias | strong target-label bias | strong stem-seen-label bias |
|---|---:|---:|---:|---:|
| all V* | 191 | 150 (78.5%) | 50 (26.2%) | 61 (31.9%) |
| conflict/repeated-answer items | 33 | 30 (90.9%) | 12 (36.4%) | 22 (66.7%) |
| non-conflict items | 158 | 120 (75.9%) | 38 (24.1%) | 39 (24.7%) |

Definitions:
- strong top-choice bias: one option gets at least 90% of repeats.
- strong target-label bias: the V* correct label gets at least 90% of repeats.
- strong stem-seen-label bias: the output falls in the set of option letters that appear as labels for the same repeated stem in V* at least 90% of repeats. This is the closest label-level analogue of the motorcycle `{B,D}` effect.

## Conflict Group Summary

There are 13 answer-conflicting repeated stems. At the stem-group level:

- label-level seen-set concentration `>=90%`: 7/13 groups
- answer-text seen-set concentration `>=90%`: 7/13 groups

Label-level strong groups:
- `what is the color of the bottle cap`
- `what is the color of the dog`
- `what is the color of the flag`
- `what is the color of the man's cap`
- `what is the color of the motorcycle`
- `what is the color of the plastic stool`
- `what is the color of the umbrella`

Answer-text strong groups:
- `what is the color of the bottle cap`
- `what is the color of the dog`
- `what is the color of the helmet`
- `what is the color of the man's cap`
- `what is the color of the motorcycle`
- `what is the color of the plastic stool`
- `what is the color of the trash can`

## Motorcycle Group

Stem: `what is the color of the motorcycle`

Group labels: `B,D`

Group answers: `black, orange`

Item-level results:
- `qid=27`, target `B=orange`: counts `D=19, A=1`; label seen-set rate 95%; answer seen-set rate 95%.
- `qid=62`, target `D=black`: counts `D=19, A=1`; label seen-set rate 95%; answer seen-set rate 100%.

Group-level result:
- counts across both items: `D=38, A=2`
- label seen-set rate: 95%
- answer-text seen-set rate: 97.5%

## Interpretation

This run shows that the motorcycle effect is not isolated. Under the same low-temperature strict no-image condition, 22/33 conflict items and 7/13 conflict stem groups strongly concentrate on labels that appear for the same repeated stem in V*.

However, it is not safe to call the 150/191 top-choice concentration a leakage rate. Low-temperature strict decoding naturally makes many questions deterministic. The more meaningful leakage-like signal is the repeated/conflicting-stem concentration, especially cases where the selected label or answer is seen elsewhere for the same stem but is wrong for the current item.
