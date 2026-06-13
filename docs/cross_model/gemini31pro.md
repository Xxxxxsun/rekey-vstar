# google/gemini-3.1-pro-preview — original vs relabel V*

original V*: `results/gemini31pro_original.jsonl` (n=191)
relabel V*: `results/gemini31pro_relabel.jsonl` (n=191)

## Single-Condition Metrics

| metric | original V* | relabel V* |
|---|---:|---:|
| overall accuracy | 169/189 (89.4%) | 127/186 (68.3%) |
| acc · `direct_attributes` | 102/114 (89.5%) | 76/112 (67.9%) |
| acc · `relative_position` | 67/75 (89.3%) | 51/74 (68.9%) |
| acc · 2-choice | 75/83 (90.4%) | 57/82 (69.5%) |
| acc · 4-choice | 94/106 (88.7%) | 70/104 (67.3%) |
| acc · first 32 | 29/32 (90.6%) | 20/30 (66.7%) |
| acc · remaining 159 | 140/157 (89.2%) | 107/156 (68.6%) |
| parse rate | 189/191 (99.0%) | 186/191 (97.4%) |
| total cost (USD) | $1.0665 | $1.3222 |

## Output Choice Distribution

| condition | A | B | C | D |
|---|---:|---:|---:|---:|
| original V* | 70 | 70 | 26 | 23 |
| relabel V* | 78 | 61 | 23 | 24 |

## Paired Comparison

| metric | value |
|---|---:|
| paired n (both parsed) | 185 |
| both correct | 115 |
| both wrong | 8 |
| original correct only | 50 |
| relabel correct only | 12 |
| choice agreement | 36.8% |
| McNemar exact p-value | 1.214e-06 |
