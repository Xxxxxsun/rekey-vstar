# bytedance-seed/seed-2.0-lite — original vs relabel V*

original V*: `results/seed20lite_original.jsonl` (n=191)
relabel V*: `results/seed20lite_relabel.jsonl` (n=191)

## Single-Condition Metrics

| metric | original V* | relabel V* |
|---|---:|---:|
| overall accuracy | 175/191 (91.6%) | 141/191 (73.8%) |
| acc · `direct_attributes` | 107/115 (93.0%) | 77/115 (67.0%) |
| acc · `relative_position` | 68/76 (89.5%) | 64/76 (84.2%) |
| acc · 2-choice | 76/84 (90.5%) | 69/84 (82.1%) |
| acc · 4-choice | 99/107 (92.5%) | 72/107 (67.3%) |
| acc · first 32 | 30/32 (93.8%) | 21/32 (65.6%) |
| acc · remaining 159 | 145/159 (91.2%) | 120/159 (75.5%) |
| parse rate | 191/191 (100.0%) | 191/191 (100.0%) |
| total cost (USD) | $0.1460 | $0.1495 |

## Output Choice Distribution

| condition | A | B | C | D |
|---|---:|---:|---:|---:|
| original V* | 72 | 71 | 27 | 21 |
| relabel V* | 76 | 68 | 22 | 25 |

## Paired Comparison

| metric | value |
|---|---:|
| paired n (both parsed) | 191 |
| both correct | 131 |
| both wrong | 6 |
| original correct only | 44 |
| relabel correct only | 10 |
| choice agreement | 39.3% |
| McNemar exact p-value | 3.386e-06 |
