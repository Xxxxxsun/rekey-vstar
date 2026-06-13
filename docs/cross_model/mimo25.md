# xiaomi/mimo-v2.5 — original vs relabel V*

original V*: `results/mimo25_original.jsonl` (n=191)
relabel V*: `results/mimo25_relabel.jsonl` (n=191)

## Single-Condition Metrics

| metric | original V* | relabel V* |
|---|---:|---:|
| overall accuracy | 153/183 (83.6%) | 122/188 (64.9%) |
| acc · `direct_attributes` | 91/109 (83.5%) | 69/114 (60.5%) |
| acc · `relative_position` | 62/74 (83.8%) | 53/74 (71.6%) |
| acc · 2-choice | 70/82 (85.4%) | 58/82 (70.7%) |
| acc · 4-choice | 83/101 (82.2%) | 64/106 (60.4%) |
| acc · first 32 | 29/32 (90.6%) | 16/32 (50.0%) |
| acc · remaining 159 | 124/151 (82.1%) | 106/156 (67.9%) |
| parse rate | 183/191 (95.8%) | 188/191 (98.4%) |
| total cost (USD) | $0.1013 | $0.1016 |

## Output Choice Distribution

| condition | A | B | C | D |
|---|---:|---:|---:|---:|
| original V* | 71 | 71 | 20 | 21 |
| relabel V* | 72 | 69 | 20 | 27 |

## Paired Comparison

| metric | value |
|---|---:|
| paired n (both parsed) | 181 |
| both correct | 98 |
| both wrong | 11 |
| original correct only | 55 |
| relabel correct only | 17 |
| choice agreement | 37.6% |
| McNemar exact p-value | 8.14e-06 |
